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

from qgis.core import (Qgis,
                       QgsWkbTypes, 
                       QgsProcessingUtils, 
                       QgsRasterFileWriter, 
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsProcessingContext,
                       QgsProcessingFeedback,
                       QgsCoordinateReferenceSystem,
                       QgsRectangle)

from qgis import processing
from pathlib import Path
from typing import Union
import shutil

def get_shapefile_as_json_pyqgis(layer, logger=None):
        if logger is not None:
            logger.debug("@get_shapefile_as_json_pyqgis@: ShapeFN id: {}".format(layer.id()))
        if not layer.isValid():
            logger.error("@get_shapefile_as_json_pyqgis@: Layer is not valid")

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
    
def process_raster_for_impactmap(source_excavation_poly, dtb_raster_layer, clipping_range, output_resolution, output_folder, output_crs, context=None, logger=None):
    """
    Processes raster data for excavation polygons by clipping, resampling, 
    and converting it to TIFF format, and then returns the path to the processed file.

    Parameters:
    - source_excavation_poly (QgsVectorLayer): Polygon layer for excavation areas.
    - dtb_raster_layer (QgsRasterLayer): QGIS Raster layer for processing.
    - clipping_range (int): Clipping range for adjusting extents of the excavation.
    - output_resolution (float): Desired output resolution for resampling.
    - output_folder (Path): Folder path for storing output files, as a Path object.
    - output_crs (QgsCoordinateReferenceSystem): The desired output CRS
    - context (QgsProcessingContext): Processing context for managing temporary files. Defaults to None.
    - logger: Logger object for logging messages. Defaults to None.

    Returns:
    - Path: Path object of the processed raster in TIFF format.
    """

    
    # Prepare processing context and feedback
    if not context:
        context = QgsProcessingContext()
    feedback = context.feedback() if context else QgsProcessingFeedback()
    
    # Check if the running version of QGIS is lower than the requirement, and create temp_folder based on that
    temp_folder = create_temp_folder_for_version(Qgis.QGIS_VERSION_INT, context)
    
    for feature in source_excavation_poly.getFeatures():
        geom = feature.geometry()
        polygon_extent = geom.boundingBox() # Returns a QgsRectangle of the polygon feature
        raster_extent = dtb_raster_layer.extent()
        
        # Adjust the polygon extent using the intersected extent
        adjusted_polygon_extent = get_intersected_extent(polygon_extent, raster_extent, clipping_range)
    ### START RASTER CLIP ####
        logger.debug("@process_raster_for_impactmap@ - START raster clipping")
        feedback.pushInfo("@process_raster_for_impactmap@ --> Start clipping")
        dtb_clip_raster_path = temp_folder / "clip_temp-raster.tif"
        # Clipping the raster to the modified extent
        processing.run("gdal:cliprasterbyextent", {
            'INPUT': dtb_raster_layer.source(),
            'PROJWIN': f"{adjusted_polygon_extent.xMinimum()}, {adjusted_polygon_extent.xMaximum()}, {adjusted_polygon_extent.yMinimum()}, {adjusted_polygon_extent.yMaximum()}", # correct format to pass
            'NODATA': None,
            'OPTIONS': '',
            'DATA_TYPE': 0,  # Use 5 for Float32
            'OUTPUT': str(dtb_clip_raster_path)
        })
        dtb_raster_layer = QgsRasterLayer(str(dtb_clip_raster_path), "clip_temp-raster")
        if dtb_raster_layer.crs().isValid():
            logger.debug(f"@process_raster_for_impactmap@ - CRS Description: {dtb_raster_layer.crs().description()}")
            logger.debug(f"@process_raster_for_impactmap@ - CRS text: {dtb_raster_layer.crs().toProj()}")
        else:
            logger.debug(f"@process_raster_for_impactmap@ - INVALID CRS AFTER CLIP")
        
        logger.debug("@process_raster_for_impactmap@ - DONE raster clipping")
        feedback.pushInfo("@process_raster_for_impactmap@ --> Done clipping")
        
    ### START RASTER RESAMPLE ####        
        # Resampling the raster to the desired output resolution
        dtb_raster_resample_path = temp_folder / "resampl_temp-raster.tif"
        logger.debug("@process_raster_for_impactmap@ - START raster resampling")
        feedback.pushInfo("@process_raster_for_impactmap@ --> Start resampling")
        
        # Get raster properties (columns and rows count) before resample
        n_cols = dtb_raster_layer.width()
        n_rows = dtb_raster_layer.height()
        logger.info(f"@process_raster_for_impactmap@ - Before resampling: {n_cols} cols, {n_rows} rows")
        feedback.pushInfo(f"@process_raster_for_impactmap@ - Before resampling: {n_cols} cols, {n_rows} rows")
        
        processing.run("gdal:warpreproject", {
            'INPUT': dtb_raster_layer.source(),
            'SOURCE_CRS': dtb_raster_layer.crs(),
            'TARGET_CRS': output_crs.authid(),
            'RESAMPLING': 0,  # 0 for Nearest Neighbour
            'TARGET_RESOLUTION': output_resolution,
            'OUTPUT': str(dtb_raster_resample_path)
        })
        dtb_raster_layer = QgsRasterLayer(str(dtb_raster_resample_path), "resampl_temp-raster")
        if dtb_raster_layer.crs().isValid():
            logger.debug(f"@process_raster_for_impactmap@ - CRS Description: {dtb_raster_layer.crs().description()}")
            logger.debug(f"@process_raster_for_impactmap@ - CRS text: {dtb_raster_layer.crs().toProj()}")
        else:
            logger.debug(f"@process_raster_for_impactmap@ - INVALID CRS AFTER RESAMPLE")
        logger.debug("@process_raster_for_impactmap@ DONE raster resampling")
        feedback.pushInfo("@process_raster_for_impactmap@ --> Done resampling")
    
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

def get_intersected_extent(polygon_extent, raster_extent, clipping_range):
    """
    Expands a given polygon extent by a specified clipping range and then intersects it with a raster extent.

    The function first expands the polygon extent uniformly in all directions by the clipping range. 
    It then computes the intersection of this expanded extent with the given raster extent. 
    This ensures that the final extent does not exceed the bounds of the raster.

    Args:
        polygon_extent (QgsRectangle): The bounding box of the polygon feature.
        raster_extent (QgsRectangle): The extent of the raster layer.
        clipping_range (float): The distance by which to expand the polygon extent.

    Returns:
        QgsRectangle: The intersected extent as a QgsRectangle object, representing the common area between the expanded polygon extent and the raster extent.
    """
    # Expand the polygon extent
    expanded_extent = QgsRectangle(polygon_extent)
    expanded_extent.grow(clipping_range)

    # Intersect with the raster extent
    expanded_extent.intersect(raster_extent)
    return expanded_extent

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

def reproject_is_needed(layer: Union[QgsVectorLayer, QgsRasterLayer], 
                        output_crs: QgsCoordinateReferenceSystem):
    """Checks the layers CRS agains the specified output_crs, and return True if they match, False otherwise.

    Args:
        layer (Union[QgsVectorLayer, QgsRasterLayer]): The specified layer, can either be a vector or raster layer.
        output_crs (QgsCoordinateReferenceSystem): The output coordinate system.

    Returns:
        Bool: True if reprojection is needed, False if reprojection is not needed
    """
    if layer.crs() != output_crs:
        return True
    else:
        return False
    
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
    # Prepare processing context and feedback
    if not context:
        context = QgsProcessingContext()
    feedback = context.feedback() if context else QgsProcessingFeedback()
    
    # Check if the running version of QGIS is lower than the requirement, and create temp_folder based on that
    temp_folder = create_temp_folder_for_version(Qgis.QGIS_VERSION_INT, context)
    if logger:
        logger.info(f"@reproject_layers@ - Temp folder path: {str(temp_folder)}")    
    
    # Initialize reprojected layer variables
    reprojected_vector_layer = None
    reprojected_raster_layer = None

    # Reproject vector layer
    if vector_layer is not None:
        feedback.pushInfo(f"@reproject_layers@ - Vector layer to reproject: Valid: {vector_layer.isValid()}, Name: {vector_layer.name()}, Source: {vector_layer.source()}")
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
            raise Exception(f"@reproject_layers@ - Failed to load reprojected vector layer from {final_vector_path}")
        feedback.pushInfo(f"@reproject_layers@ - VECTOR layer reprojected and saved to {final_vector_path}, NEW CRS: {reprojected_vector_layer.crs().postgisSrid()}")
        if logger:
            logger.info(f"@reproject_layers@ - VECTOR layer reprojected and saved to {final_vector_path}")
                  
    # Reproject raster layer if provided
    if raster_layer is not None:
        feedback.pushInfo(f"Raster layer to reproject: Valid: {raster_layer.isValid()}, Name: {raster_layer.name()}.tif, Source: {raster_layer.source()}")
        reprojected_raster_path = temp_folder / f"reprojected_{raster_layer.name()}.tif"
        if logger:
            logger.info(f"@reproject_layers@ - Raster to reproject 'INPUT': {raster_layer.source()}")
            logger.info(f"@reproject_layers@ - Raster to reproject 'SOURCE_CRS': {raster_layer.crs().authid()}")
            logger.info(f"@reproject_layers@ - Raster to reproject 'TARGET_CRS': {output_crs.authid()}")
        processing.run("gdal:warpreproject", {
            'INPUT': raster_layer.source(),
            'SOURCE_CRS': raster_layer.crs().authid(),
            'TARGET_CRS': output_crs.authid(),
            'OUTPUT': str(reprojected_raster_path)
        }, context=context, feedback=feedback)
        if logger:
            logger.info(f"@reproject_layers@ - Raster to reproject 'OUTPUT': {str(reprojected_raster_path)}")
        # Save the reprojected raster layer to the output folder, else return the temporary interm. layer
        final_raster_path = output_folder / f"reprojected_{raster_layer.name()}.tif" if keep_interm_layer else reprojected_raster_path
        if keep_interm_layer:
            move_file_components(reprojected_raster_path, final_raster_path)
        reprojected_raster_layer = QgsRasterLayer(str(final_raster_path), f"reprojected_{raster_layer.name()}.tif")
        if not reprojected_raster_layer.isValid():
            raise Exception(f"@reproject_layers@ - Failed to load reprojected raster layer from {final_raster_path}")
        feedback.pushInfo(f"@reproject_layers@ - RASTER layer reprojected and saved to {final_raster_path}, NEW CRS: {reprojected_raster_layer.crs().postgisSrid()}")
        if logger:
            logger.info(f"@reproject_layers@ - RASTER layer reprojected and saved to {final_raster_path}")       

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
            
def create_temp_folder_for_version(qgis_version_int : int, context: QgsProcessingContext = None) -> Path:
    """
    Creates a temporary folder based on the QGIS version.

    Args:
        qgis_version_int  (int): The integer representation of the QGIS version.
        context (QgsProcessingContext, optional): The context for processing. Default is None.

    Returns:
        Path: The path to the temporary folder.
    """
    # Check if the running version of QGIS is lower than the requirement
    if qgis_version_int >= 33200 and context is not None:
        # For QGIS versions 3.32.0 and above
        temp_folder = Path(context.temporaryFolder())
        temp_folder.mkdir(parents=True, exist_ok=True)
    else:
        # For older versions, or if no context is provided, use the global Processing temporary folder
        temp_folder = Path(QgsProcessingUtils.tempFolder())
        temp_folder.mkdir(parents=True, exist_ok=True)
        
    return temp_folder
