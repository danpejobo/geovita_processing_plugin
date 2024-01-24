"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'DPE'
__date__ = '2024-01-17'
__copyright__ = '(C) 2024 by DPE'

from qgis.core import (QgsProject, 
                       QgsWkbTypes, 
                       QgsProcessingUtils, 
                       QgsRasterFileWriter, 
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsLayerTreeGroup,
                       QgsProcessingContext)
from qgis import processing
from osgeo import gdal
from pathlib import Path

def get_shapefile_as_json_pyqgis(layer, logger=None):
        if logger is not None:
            logger.debug("Logger sent, shapeFN name: {}".format(layer.id()))
        if not layer.isValid():
            logger.error("Layer is not valid")

        epsgNum = layer.crs().postgisSrid()

        features = []
        fieldNames = [field.name() for field in layer.fields()]

        for feature in layer.getFeatures():
            geom = feature.geometry()
            attributes = feature.attributes()
            geomType = QgsWkbTypes.flatType(geom.wkbType()) # removes Z and M dimentions from the geomtype

            feature_dict = {
                "attributes": {fieldNames[i]: attributes[i] for i in range(len(fieldNames))}
            }

            if geomType == QgsWkbTypes.Point:
                point = geom.asPoint()
                feature_dict["geometry"] = {
                    "x": point.x(),
                    "y": point.y(),
                    "spatialReference": {"wkid": epsgNum}
                }
            elif geomType == QgsWkbTypes.Polygon:
                rings = [[[point.x(), point.y()] for point in ring] for ring in geom.asPolygon()]
                feature_dict["geometry"] = {
                    "rings": rings,
                    "spatialReference": {"wkid": epsgNum}
                }
            elif geomType == QgsWkbTypes.MultiPolygon:
                all_rings = [[[point.x(), point.y()] for point in ring] for poly in geom.asMultiPolygon() for ring in poly]
                feature_dict["geometry"] = {
                    "rings": all_rings,
                    "spatialReference": {"wkid": epsgNum}
                }

            features.append(feature_dict)

        return {"features": features}
    
def process_raster_for_impactmap(source_excavation_poly, dtb_raster_layer, clipping_range, output_resolution, output_folder, context=None, logger=None):
    """
    Processes raster data for excavation polygons by clipping, resampling, 
    and converting it to TIFF format, and then returns the path to the processed file.

    Parameters:
    - source_excavation_poly (QgsVectorLayer): Polygon layer for excavation areas.
    - dtb_raster_layer (QgsRasterLayer): QGIS Raster layer for processing.
    - clipping_range (int): Clipping range for adjusting extents of the excavation.
    - output_resolution (float): Desired output resolution for resampling.
    - output_folder (Path): Folder path for storing output files, as a Path object.
    - context (QgsProcessingContext): Processing context for managing temporary files. Defaults to None.
    - logger: Logger object for logging messages. Defaults to None.

    Returns:
    - Path: Path object of the processed raster in TIFF format.
    """
    # Processing temp folder
    temp_folder = Path(QgsProcessingContext.temporaryFolder(context) if context else QgsProcessingUtils.tempFolder())
    
    for feature in source_excavation_poly.getFeatures():
        geom = feature.geometry()
        polygon_extent = geom.boundingBox() # Returns a QgsRectangle of the polygon feature
        raster_extent = dtb_raster_layer.extent()
        
        # Expanding the extent by the specified calculation range
        polygon_extent.grow(clipping_range)
        #logger.debug(f"POLYGON Extent RAW: {polygon_extent}")
               
        # Compare and adjust the polygon_extent if it exceeds the raster_extent
        #xmin = max(polygon_extent.xMinimum(), raster_extent.xMinimum())
        #xmax = min(polygon_extent.xMaximum(), raster_extent.xMaximum())
        #ymin = max(polygon_extent.yMinimum(), raster_extent.yMinimum())
        #ymax = min(polygon_extent.yMaximum(), raster_extent.yMaximum())


        # Calculate the area and determine if clipping of the raster is needed
        # area = polygon_extent.width() * polygon_extent.height()

        # Ensure the expanded polygon extent is within the raster extent
        #adjusted_extent = [xmin, ymax, xmax, ymin]  # Format for PROJWIN
        #logger.debug(f"ADJUSTED Extent RAW: {adjusted_extent}")
        
        # Initialize paths for temporary raster files
        dtb_clip_raster_path = None
        dtb_raster_resample_path = None
        #if float(output_resolution) / area < 10 / 820000:
        #if adjusted_extent != [polygon_extent.xMinimum(), polygon_extent.yMaximum(), polygon_extent.xMaximum(), polygon_extent.yMinimum()]:
        if raster_extent.contains(polygon_extent):
            logger.debug("START raster clipping")
            dtb_clip_raster_path = temp_folder / "clip_temp-raster.tif"
            # Clipping the raster to the modified extent
            processing.run("gdal:cliprasterbyextent", {
                'INPUT': dtb_raster_layer.source(),
                'PROJWIN': f"{polygon_extent.xMinimum()}, {polygon_extent.xMaximum()}, {polygon_extent.yMinimum()}, {polygon_extent.yMaximum()}", # correct format to pass
                'NODATA': None,
                'OPTIONS': '',
                'DATA_TYPE': 0,  # Use 5 for Float32
                'OUTPUT': str(dtb_clip_raster_path)
            })
            dtb_raster_layer = QgsRasterLayer(str(dtb_clip_raster_path), "clip_temp-raster")
            logger.debug("DONE raster clipping")
        
        # Get raster properties (columns and rows count) before resample
        n_cols = dtb_raster_layer.width()
        n_rows = dtb_raster_layer.height()
        logger.info(f"Dtb raster cols and rows before resampling: {n_cols}, {n_rows}")
        # Resampling the raster to the desired output resolution
        dtb_raster_resample_path = temp_folder / "resampl_temp-raster.tif"
        logger.debug("START raster resampling")
        processing.run("gdal:warpreproject", {
            'INPUT': dtb_raster_layer.source(),
            'TARGET_CRS': dtb_raster_layer.crs().authid(),
            'RESAMPLING': 0,  # 0 for Nearest Neighbour
            'CELLSIZE': output_resolution,
            'OUTPUT': str(dtb_raster_resample_path)
        })
        dtb_raster_layer = QgsRasterLayer(str(dtb_raster_resample_path), "resampl_temp-raster")
        logger.debug("DONE raster resampling")

        # Get raster properties (columns and rows count) after resample
        n_cols = dtb_raster_layer.width()
        n_rows = dtb_raster_layer.height()
        logger.info(f"Dtb raster cols and rows after resampling: {n_cols}, {n_rows}")

        # Convert to TIFF if needed
        dtb_raster_tiff = output_folder / "dtb_raster.tif"
        if not dtb_raster_layer.source().endswith(('.tif', '.tiff')): #checks a tuple
            logger.info("START raster to TIFF conversion")
            QgsRasterFileWriter.writeRasterLayer(dtb_raster_layer, str(dtb_raster_tiff), "GTiff")
            logger.info("DONE raster to TIFF conversion")
        else:
            dtb_raster_tiff = Path(dtb_raster_layer.source())

        # Return the Path object of the final processed raster file
        return dtb_raster_tiff
    
def add_layer_to_qgis(layer_path, layer_name, style_path, group_name=None, logger=None):
    """
    Adds a layer (vector or raster) to QGIS with a specified style, and optionally adds it to a specified group.

    Parameters:
    layer_path (str): Path to the layer file.
    layer_name (str): Name for the layer in QGIS.
    style_path (str): Path to the QML style file.
    group_name (str, optional): Name of the group to add the layer to. If None, the layer is added without a group.
    logger (logging.Logger, optional): Logger for logging messages.

    Returns:
    bool: True if the layer is added successfully, False otherwise.
    """

    # Determine layer type (raster or vector) based on file extension
    if layer_path.endswith('.tif') or layer_path.endswith('.tiff'):
        layer = QgsRasterLayer(layer_path, f'{layer_name}_{group_name}')
        logger.info(f"Loaded RASTER layer to style it: {layer}")
    else:
        layer = QgsVectorLayer(layer_path, f'{layer_name}_{group_name}', 'ogr')
        logger.info(f"Loaded VECTOR layer to style it: {layer}")

    if not layer.isValid():
        if logger:
            logger.debug(f"Failed to load layer: {layer_path}")
        return False

    # Apply the style
    layer.loadNamedStyle(style_path)
    logger.info(f"Loaded style on this path: {style_path}")
    layer.triggerRepaint()

    # Get the root of the layer tree
    root = QgsProject.instance().layerTreeRoot()

    # Add layer to group if group_name is specified
    if group_name:
        group = root.findGroup(group_name)
        if not group:
            group = root.insertGroup(0, group_name)
            logger.info(f"Created group: {group_name}")
        QgsProject.instance().addMapLayer(layer, False)  # False means do not add to the layer tree root
        group.addLayer(layer)
        logger.info(f"Added {layer} to group: {group_name}")
    else:
        QgsProject.instance().addMapLayer(layer, True)  # Add layer directly to the layer tree
        logger.info(f"No group prensen. Directly add layer: {layer}")

    return True

def map_porepressure_curve_names(curve_name):
        """
        Translates an English pore pressure curve name to its Norwegian equivalent.

        This method is intended for mapping English curve names used in a UI dropdown menu
        to the corresponding Norwegian names. These Norwegian names are then used in the
        mainBegrensSkade_Tunnel process metod.

        Args:
            curve_name (str): The English name of the pore pressure curve. 
                            Expected values are 'Upper', 'Typical', 'Lower', or 'Manual'.

        Returns:
            str: The Norwegian equivalent of the given English curve name. If the provided 
                curve name does not match any of the expected values, None is returned.

        Example:
            >>> porepressure_curve_names_to_pass_to_mainBegrensSkade_Tunnel("Upper")
            'Øvre'
        """
        mapping_dict = {'Upper': 'Øvre', 
                        'Typical': 'Typisk', 
                        'Lower': 'Nedre', 
                        'Manual': 'Manuell'
                        }
        return mapping_dict.get(curve_name, None)