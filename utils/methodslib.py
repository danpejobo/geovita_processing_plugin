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
                       QgsProcessingContext,
                       QgsProcessingFeedback,
                       QgsCoordinateReferenceSystem,
                       QgsLayerTreeGroup,
                       QgsLayerTreeLayer)

from qgis import processing
from pathlib import Path
from typing import Union
import shutil

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
        layer = QgsRasterLayer(layer_path, f'{layer_name}')
        logger.info(f"Loaded RASTER layer to style it: {layer}")
    else:
        layer = QgsVectorLayer(layer_path, f'{layer_name}', 'ogr')
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
            #group = root.insertGroup(0, group_name)
            group = QgsLayerTreeGroup(group_name)
            root.insertChildNode(0, group)
            logger.info(f"Created group node with name: {group.name()}")

        QgsProject.instance().addMapLayer(layer, False)  # False means do not add to the layer tree root
        node_layer = QgsLayerTreeLayer(layer)
        group.insertChildNode(1, node_layer)
        #group.addLayer(layer)
        logger.info(f"Added {layer} to group: {group.name()}")
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

def reproject_if_needed(layer: Union[QgsVectorLayer, QgsRasterLayer], 
                        output_crs: QgsCoordinateReferenceSystem):
    """Checks the layers CRS agains the specified output_crs, and return True if they match, False otherwise.

    Args:
        layer (Union[QgsVectorLayer, QgsRasterLayer]): The specified layer, can either be a vector or raster layer.
        output_crs (QgsCoordinateReferenceSystem): The output coordinate system.

    Returns:
        Bool: True if reprojection is not needed, False if reprojection is needed
    """
    if layer.crs() != output_crs:
        return False
    else:
        return True
    
def reproject_layers(keep_interm_layer: bool,
                     output_crs: QgsCoordinateReferenceSystem, 
                     output_folder: Path, 
                     vector_layer: QgsVectorLayer = None,
                     raster_layer: QgsRasterLayer = None, 
                     context: QgsProcessingContext = None, 
                     logger = None):
    """
    Reprojects vector and optionally raster layers to a specified CRS.

    Args:
    - keep_interm_layer (bool): Save the reprojected layers in the output directory
    - output_crs (QgsCoordinateReferenceSystem): The desired output CRS.
    - output_folder (Path): The folder path where the reprojected layers will be saved.
    - vector_layer (QgsVectorLayer, optional): The vector layer to be reprojected, or None if not applicable.
    - raster_layer (QgsRasterLayer, optional): The raster layer to be reprojected, or None if not applicable.
    - context (QgsProcessingContext, optional): The context for processing. Default is None.
    - logger (logging.Logger, optional): Logger for logging messages. Default is None.

    Returns:
    - Tuple: (reprojected_vector_path, reprojected_raster_path) Paths to the reprojected layers.
    """
    # Processing temp folder
    temp_folder = Path(QgsProcessingContext.temporaryFolder(context) if context else QgsProcessingUtils.tempFolder())

    # Prepare processing context and feedback
    if not context:
        context = QgsProcessingContext()
    feedback = context.feedback() if context else QgsProcessingFeedback()
    
    # Initialize reprojected layer variables
    reprojected_vector_layer = None
    reprojected_raster_layer = None

    # Reproject vector layer
    if vector_layer is not None:
        feedback.pushInfo(f"Vector layer to reproject: Valid: {vector_layer.isValid()}, Name: {vector_layer.name()}, Source: {vector_layer.source()}")
        reprojected_vector_path = temp_folder / f"reprojected_{vector_layer.name()}.shp"
        processing.run("native:reprojectlayer", {
            'INPUT': vector_layer,
            'TARGET_CRS': output_crs,
            'OUTPUT': str(reprojected_vector_path)
        }, context=context, feedback=feedback)
        
        # Determine the final path based on the keep_interm_layer flag
        final_vector_path = output_folder / f"reprojected_{vector_layer.name()}.shp" if keep_interm_layer else reprojected_vector_path
        if keep_interm_layer:
            move_file_components(reprojected_vector_path, final_vector_path)
            
        reprojected_vector_layer = QgsVectorLayer(str(final_vector_path), f"reprojected_{vector_layer.name()}.shp", 'ogr')
        if not reprojected_vector_layer.isValid():
            raise Exception(f"Failed to load reprojected vector layer from {final_vector_path}")
        feedback.pushInfo(f"VECTOR layer reprojected and saved to {final_vector_path}, NEW CRS: {reprojected_vector_layer.crs().postgisSrid()}")
        if logger:
            logger.info(f"VECTOR layer reprojected and saved to {final_vector_path}")
                  
    # Reproject raster layer if provided
    if raster_layer is not None:
        feedback.pushInfo(f"Raster layer to reproject: Valid: {raster_layer.isValid()}, Name: {raster_layer.name()}.tif, Source: {raster_layer.source()}")
        reprojected_raster_path = temp_folder / f"reprojected_{raster_layer.name()}.tif"
        processing.run("gdal:warpreproject", {
            'INPUT': raster_layer.source(),
            'SOURCE_CRS': raster_layer.crs().authid(),
            'TARGET_CRS': output_crs,
            'OUTPUT': str(reprojected_raster_path)
        }, context=context, feedback=feedback)
        
        # Save the reprojected raster layer to the output folder, else return the temporary interm. layer
        final_raster_path = output_folder / f"reprojected_{raster_layer.name()}.tif" if keep_interm_layer else reprojected_raster_path
        if keep_interm_layer:
            move_file_components(reprojected_raster_path, final_raster_path)
        reprojected_raster_layer = QgsRasterLayer(str(final_raster_path), f"reprojected_{raster_layer.name()}.tif")
        if not reprojected_raster_layer.isValid():
            raise Exception(f"Failed to load reprojected raster layer from {final_raster_path}")
        feedback.pushInfo(f"RASTER layer reprojected and saved to {final_raster_path}, NEW CRS: {reprojected_raster_layer.crs().postgisSrid()}")
        if logger:
            logger.info(f"RASTER layer reprojected and saved to {final_raster_path}")       

    return reprojected_vector_layer, reprojected_raster_layer

def move_file_components(original_file_path: Path, destination_file_path: Path):
    """
    Moves all components of a Shapefile or a TIFF file to a specified destination folder.
    
    Args:
    - original_file_path (pathlib.Path): The full path to any component of the Shapefile or TIFF file.
    - destination_file_path (pathlib.Path): The full destination file path where the file components should be moved.
    """
    file_extension = original_file_path.suffix.lower()
    destination_folder = destination_file_path.parent
    destination_base_name = destination_file_path.stem

    if file_extension in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qpj']:
        # Handle Shapefile components
        extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qpj']
    elif file_extension in ['.tif', '.tiff']:
        # Handle TIFF and associated files (including .aux.xml and .tfw)
        extensions = ['.tif', '.tiff', '.tfw', '.tif.aux.xml', '.tiff.aux.xml']
    else:
        raise ValueError("Unsupported file format")

    # Iterate over the file extensions and move each file
    for ext in extensions:
        src_file = original_file_path.with_suffix(ext)
        dest_file = destination_folder / (destination_base_name + ext)
        if src_file.exists():
            shutil.move(str(src_file), str(dest_file))