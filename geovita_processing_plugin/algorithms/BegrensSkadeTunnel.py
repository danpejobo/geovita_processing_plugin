# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GeovitaProcessingPlugin
                                 A QGIS plugin
 This plugin adds different geovita processing plugins
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-03-02
        copyright            : (C) 2022 by DPE
        email                : dpe@geovita.no
 ***************************************************************************/

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
__date__ = '2023.03.20'
__copyright__ = '(C) 2023 by DPE'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication, QEventLoop
from qgis.core import (Qgis,
                       QgsApplication,
                       QgsProject,
                       QgsMessageLog,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterDefinition,
                       QgsProcessingParameterString,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterFolderDestination,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingException,
                       )

from .base_algorithm import GvBaseProcessingAlgorithms

import traceback
from pathlib import Path

from ..REMEDY_GIS_RiskTool.BegrensSkade import mainBegrensSkade_Tunnel

from ..utilities.AddLayersTask import AddLayersTask
from ..utilities.gui import GuiUtils
from ..utilities.logger import CustomLogger
from ..utilities.methodslib import (get_shapefile_as_json_pyqgis,
                                map_porepressure_curve_names, 
                                reproject_is_needed, 
                                reproject_layers)


class BegrensSkadeTunnel(GvBaseProcessingAlgorithms):
    """
    The `BegrensSkadeTunnel` algorithm is part of the GeovitaProcessingPlugin suite, designed to evaluate the impact of tunnel construction on 
    surface structures and the surrounding terrain. It utilizes advanced geotechnical models to simulate both short-term and long-term settlements 
    resulting from tunnel excavation activities, providing critical insights for urban planning, infrastructure development, and risk management.

    Key Features:
    - Analysis of short-term settlements due to tunnel construction, incorporating parameters such as tunnel depth, diameter, and volume loss.
    - Long-term settlement analysis considering factors like pore pressure reduction, soil saturation density, and over-consolidation ratios.
    - Vulnerability assessment for buildings near the tunnel path, evaluating the risk of damage due to settlements.
    - Customizable outputs, allowing for analysis under various geotechnical conditions and construction scenarios.

    Parameters:
    - INPUT_BUILDING_POLY: Polygon layer representing buildings or structures of interest.
    - INPUT_TUNNEL_POLY: Polygon layer depicting the planned tunnel path.
    - RASTER_ROCK_SURFACE: Raster layer indicating depth to bedrock for detailed geological analysis.
    - Various geotechnical parameters to tailor the analysis to specific conditions and construction plans.

    Outputs:
    - OUTPUT_BUILDING: Shapefile indicating potential settlements and risks for buildings.
    - OUTPUT_WALL: Shapefile detailing wall inclinations and potential structural impacts.
    - OUTPUT_CORNER: Shapefile showing corner point settlements for detailed vulnerability assessment.

    Usage:
    The algorithm is integrated within the QGIS Processing Toolbox, enabling users to easily apply it to their geospatial projects. 
    By inputting the required layers and specifying geotechnical parameters, users can generate detailed analyses of tunneling impacts, 
    assisting in the decision-making process for tunnel construction projects.

    The algorithm leverages the mainBegrensSkade_Tunnel function from the REMEDY_GIS_RiskTool for spatial analysis,
    aiding in the assessment of construction impacts on the urban and natural environment.

    """
    def __init__(self):
        super().__init__()
        
        # Initialize the logger in the users download folder
        home_dir = Path.home()
        log_dir_path = home_dir / "Downloads" / "REMEDY" / "log"
        self.logger = CustomLogger(log_dir_path, "BegrensSkadeII_QGIS_TUNNEL.log", "TUNNEL_LOGGER").get_logger()
        self.logger.info(f"__INIT__ - Finished initialize BegrensSkadeTunnel ")

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.        

    INPUT_BUILDING_POLY = 'INPUT_BUILDING_POLY'
    INPUT_TUNNEL_POLY = 'INPUT_TUNNEL_POLY'
    INTERMEDIATE_LAYERS = ['INTERMEDIATE_LAYERS', 'Keep reprojected layers? (No point if you save to a temp folder)']
    
    OUTPUT_FOLDER = 'OUTPUT_FOLDER'
    OUTPUT_FEATURE_NAME = 'OUTPUT_FEATURE_NAME'
    OUTPUT_CRS = 'OUTPUT_CRS'
    
    #SHORT TERM CONSTANTS
    SHORT_TERM_SETTLEMENT = ['SHORT_TERM_SETTLEMENT', 'Short term settlements']
    TUNNEL_DEPTH = ['TUNNEL_DEPTH', 'Depth of tunnel [m]']
    TUNNEL_DIAM = ['TUNNEL_DIAM', 'Diameter of tunnel [m]']
    VOLUME_LOSS = ['VOLUME_LOSS', 'Loss of volume [%]']
    TROUGH_WIDTH = ['TROUGH_WIDTH', "Width of trough [m]"]
    
    #LONG TERM CONSTANTS
    LONG_TERM_SETTLEMENT = ['LONG_TERM_SETTLEMENT', 'Long term settlements']
    RASTER_ROCK_SURFACE = ['RASTER_ROCK_SURFACE', "Input raster of depth to bedrock"]
    POREPRESSURE_ENUM_CURVES = ['POREPRESSURE_ENUM', 'Calculation curves for pore pressure reduction']
    CURVES_enum_porepressure = ["Upper", "Typical", "Lower", "Manual"]    
    TUNNEL_LEAKAGE = ["TUNNEL_LEAKAGE", "Leakage of water into the tunnel [L/min each 100m of tunnelsection]"]
    POREPRESSURE_REDUCTION = ['POREPRESSURE_REDUCTION', 'Porepressure reduction with tunnel (only used if the curve is "Manual" [kPa]']
    DRY_CRUST_THICKNESS = ['DRY_CRUST_THICKNESS', 'Thickness of overburden not affected by porewater drawdown [m]']
    DEPTH_GROUNDWATER = ['DEPTH_GROUNDWATER', 'Depht to groundwater table [m]']
    SOIL_DENSITY = ['SOIL_DENSITY', 'Soil saturation density [kN/m3]']
    OCR = ['OCR', 'Over consolidation ratio']
    JANBU_REF_STRESS = ['JANBU_REF_STRESS', 'Janbu reference stress, p`r (kPa)']
    JANBU_CONSTANT = ['JANBU_CONSTANT', 'Janbu constant [M0/(m*p`c)]']
    JANBU_COMP_MODULUS = ['JANBU_COMP_MODULUS', 'Janbu compression modulus']
    CONSOLIDATION_TIME = ['CONSOLIDATION_TIME', 'Consolidation time [years]']
    
    VULNERABILITY_ANALYSIS = ['VULNERABILITY_ANALYSIS', 'Building vulnerability analysis']
    FILED_NAME_BUILDING_FOUNDATION = ['FILED_NAME_BUILDING_FOUNDATION', 'Building Foundation column']
    FILED_NAME_BUILDING_STRUCTURE = ['FILED_NAME_BUILDING_STRUCTURE', 'Building Structure column']
    FILED_NAME_BUILDING_STATUS = ['FILED_NAME_BUILDING_STATUS', 'Building Condition column']
    
    # return shapefiles from mainBegrensSkade_Excavation()
    OUTPUT_BUILDING = 'OUTPUT_BUILDING'
    OUTPUT_WALL = 'OUTPUT_WALL'
    OUTPUT_CORNER = 'OUTPUT_CORNER'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.logger.info(f"INIT ALGORITHM - Start setup parameters")
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_BUILDING_POLY,
                self.tr('Input Building polygon(s)'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_TUNNEL_POLY,
                self.tr('Input Tunnel polygon(s)'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        
        #SHORT TERM Advanced features
        param = QgsProcessingParameterBoolean(
                        self.SHORT_TERM_SETTLEMENT[0],
                        self.tr(f'{self.SHORT_TERM_SETTLEMENT[1]}'),
                        defaultValue=False
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
                        self.TUNNEL_DEPTH[0],
                        self.tr(f'{self.TUNNEL_DEPTH[1]}'),
                        QgsProcessingParameterNumber.Double,
                        defaultValue=15,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
                        self.TUNNEL_DIAM[0],
                        self.tr(f'{self.TUNNEL_DIAM[1]}'),
                        QgsProcessingParameterNumber.Double,
                        defaultValue=9.5,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
                        self.VOLUME_LOSS[0],
                        self.tr(f'{self.VOLUME_LOSS[1]}'),
                        QgsProcessingParameterNumber.Integer,
                        defaultValue=2,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
                        self.TROUGH_WIDTH[0],
                        self.tr(f'{self.TROUGH_WIDTH[1]}'),
                        QgsProcessingParameterNumber.Double,
                        defaultValue=0.5,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        #LONG TERM Advanced features      
        param = QgsProcessingParameterBoolean(
                        self.LONG_TERM_SETTLEMENT[0],
                        self.tr(f'{self.LONG_TERM_SETTLEMENT[1]}'),
                        defaultValue=False
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterRasterLayer(
                    self.RASTER_ROCK_SURFACE[0],
                    self.tr(f'{self.RASTER_ROCK_SURFACE[1]}'),
                    defaultValue=None,
                    optional=True
            )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced | QgsProcessingParameterDefinition.FlagOptional)
        self.addParameter(param)
        param = QgsProcessingParameterEnum(
                        self.POREPRESSURE_ENUM_CURVES[0],
                        self.tr(f'{self.POREPRESSURE_ENUM_CURVES[1]}'),
                        self.CURVES_enum_porepressure,
                        defaultValue=1,
                        allowMultiple=False
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.TUNNEL_LEAKAGE[0],
                        self.tr(f'{self.TUNNEL_LEAKAGE[1]}'),
                        defaultValue=10,
                        optional=True,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
                        self.POREPRESSURE_REDUCTION[0],
                        self.tr(f'{self.POREPRESSURE_REDUCTION[1]}'),
                        defaultValue=0,
                        optional=True,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.DRY_CRUST_THICKNESS[0],
                        self.tr(f'{self.DRY_CRUST_THICKNESS[1]}'),
                        defaultValue=5,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.DEPTH_GROUNDWATER[0],
                        self.tr(f'{self.DEPTH_GROUNDWATER[1]}'),
                        defaultValue=3,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.SOIL_DENSITY[0],
                        self.tr(f'{self.SOIL_DENSITY[1]}'),
                        QgsProcessingParameterNumber.Double,
                        defaultValue=18.5,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.OCR[0],
                        self.tr(f'{self.OCR[1]}'),
                        QgsProcessingParameterNumber.Double,
                        defaultValue=1.2,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.JANBU_REF_STRESS[0],
                        self.tr(f'{self.JANBU_REF_STRESS[1]}'),
                        defaultValue=0,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.JANBU_CONSTANT[0],
                        self.tr(f'{self.JANBU_CONSTANT[1]}'),
                        defaultValue=4,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.JANBU_COMP_MODULUS[0],
                        self.tr(f'{self.JANBU_COMP_MODULUS[1]}'),
                        defaultValue=15,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
                        self.CONSOLIDATION_TIME[0],
                        self.tr(f'{self.CONSOLIDATION_TIME[1]}'),
                        defaultValue=1000,
                        minValue=0
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        #VULNERABILITY_ANALYSIS Advanced features
        param = QgsProcessingParameterBoolean(
                        self.VULNERABILITY_ANALYSIS[0],
                        self.tr(f'{self.VULNERABILITY_ANALYSIS[1]}'),
                        defaultValue=False
                    )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField(
            self.FILED_NAME_BUILDING_FOUNDATION[0],
            self.tr(f'{self.FILED_NAME_BUILDING_FOUNDATION[1]}'),
            parentLayerParameterName=self.INPUT_BUILDING_POLY,
            allowMultiple=False,
            optional=True,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField(
            self.FILED_NAME_BUILDING_STRUCTURE[0],
            self.tr(f'{self.FILED_NAME_BUILDING_STRUCTURE[1]}'),
            parentLayerParameterName=self.INPUT_BUILDING_POLY,
            allowMultiple=False,
            optional=True,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField(
            self.FILED_NAME_BUILDING_STATUS[0],
            self.tr(f'{self.FILED_NAME_BUILDING_STATUS[1]}'),
            parentLayerParameterName=self.INPUT_BUILDING_POLY,
            allowMultiple=False,
            optional=True,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        
        #DEFINE OUTPUTS
        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_FEATURE_NAME,
                self.tr('Naming Conventions for Analysis and Features (Output feature name appended to file-names)'),
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.OUTPUT_CRS,
                self.tr('Output CRS'),
                defaultValue=QgsProject.instance().crs(),
            )
        )
        param = QgsProcessingParameterBoolean(
                        self.INTERMEDIATE_LAYERS[0],
                        self.tr(f'{self.INTERMEDIATE_LAYERS[1]}'),
                        defaultValue=False
                    )
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                self.tr('Output Folder'),
            )
        )
        
        self.logger.info(f"initAlgorithm - Done setting up the inputs.")

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """        
        bShortterm = self.parameterAsBoolean(parameters, self.SHORT_TERM_SETTLEMENT[0], context)
        self.logger.info(f"PROCESS - bShortterm value: {bShortterm}")
        bLongterm = self.parameterAsBoolean(parameters, self.LONG_TERM_SETTLEMENT[0], context)
        self.logger.info(f"PROCESS - bLongterm value: {bLongterm}")
        if not bShortterm and not bLongterm:
            error_msg = "Please choose Short term or Long term settlements, or both"
            self.logger.error(error_msg)
            feedback.reportError(error_msg)
            return {}
        
        bVulnerability = self.parameterAsBoolean(parameters, self.VULNERABILITY_ANALYSIS[0], context)
        self.logger.info(f"PROCESS - bVulnerability value: {bVulnerability}")
        bIntermediate = self.parameterAsBoolean(parameters, self.INTERMEDIATE_LAYERS[0], context)
        self.logger.info(f"PROCESS - bIntermediate value: {bIntermediate}")
        feedback.setProgress(10)

        source_building_poly = self.parameterAsVectorLayer(parameters, self.INPUT_BUILDING_POLY, context)
        path_source_building_poly = source_building_poly.source().split('|')[0]
        self.logger.info(f"PROCESS - Path to source buildings: {path_source_building_poly}")
        
        source_tunnel_poly = self.parameterAsVectorLayer(parameters, self.INPUT_TUNNEL_POLY, context)
        path_source_tunnel_poly = source_tunnel_poly.source().split('|')[0]
        self.logger.info(f"PROCESS - Path to source excavation: {path_source_tunnel_poly}")
        
        source_tunnel_poly_as_json = get_shapefile_as_json_pyqgis(source_tunnel_poly, self.logger)
        self.logger.info(f"PROCESS - JSON structure: {source_tunnel_poly_as_json}")
        
        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        # Ensure the output directory exists
        output_folder_path = Path(output_folder)
        output_folder_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"PROCESS - Output folder: {output_folder}")
        
        feature_name = self.parameterAsString(parameters, self.OUTPUT_FEATURE_NAME, context)
        self.logger.info(f"PROCESS - Feature name: {feature_name}")
        
        output_proj = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        output_srid = output_proj.postgisSrid()
        self.logger.info(f"PROCESS - Output CRS(SRID): {output_srid}")
            
        #################  CHECK INPUT PROJECTIONS OF VECTOR LAYERS #################
        
        # Check if each layer matches the output CRS --> If False is returned, reproject the layers.
        if reproject_is_needed(source_building_poly, output_proj):
            feedback.pushInfo(f"PROCESS - Reprojection needed for layer: {source_building_poly.name()}, ORIGINAL CRS: {source_building_poly.crs().postgisSrid()}")
            try:
                source_building_poly, _ = reproject_layers(bIntermediate, output_proj, output_folder_path, vector_layer=source_building_poly, raster_layer=None, context=context, logger=self.logger)
            except Exception as e:
                feedback.reportError(f"Error during reprojection of BUILDINGS: {e}")
                return {}
        if reproject_is_needed(source_tunnel_poly, output_proj):
            feedback.pushInfo(f"PROCESS - Reprojection needed for layer: {source_tunnel_poly.name()}, ORIGINAL CRS: {source_tunnel_poly.crs().postgisSrid()}")
            try:
                source_tunnel_poly, _ = reproject_layers(bIntermediate, output_proj, output_folder_path, vector_layer=source_tunnel_poly, raster_layer=None, context=context, logger=self.logger)
            except Exception as e:
                feedback.reportError(f"Error during reprojection of EXCAVATION: {e}")
                return {}
        
        path_source_building_poly = source_building_poly.source().split('|')[0]
        self.logger.info(f"PROCESS - Path to source buildings: {path_source_building_poly}")
        
        path_source_tunnel_poly = source_tunnel_poly.source().split('|')[0]
        self.logger.info(f"PROCESS - Path to source excavation: {path_source_tunnel_poly}")
        
        source_tunnel_poly_as_json = get_shapefile_as_json_pyqgis(source_tunnel_poly, self.logger)
        #source_excavation_poly_as_json = Utils.getShapefileAsJson(path_source_excavation_poly, logger)
        self.logger.info(f"PROCESS - JSON structure: {source_tunnel_poly_as_json}")
            
        feedback.setProgress(30)
        if bShortterm:
            tunnel_depth = self.parameterAsDouble(parameters, self.TUNNEL_DEPTH[0], context)
            tunnel_diameter = self.parameterAsDouble(parameters, self.TUNNEL_DIAM[0], context)
            volume_loss = self.parameterAsInt(parameters, self.VOLUME_LOSS[0], context)
            trough_width = self.parameterAsDouble(parameters, self.TROUGH_WIDTH[0], context)
        else:
            tunnel_depth = None
            tunnel_diameter = None
            volume_loss = None
            trough_width = None
            
        source_raster_rock_surface = self.parameterAsRasterLayer(parameters, self.RASTER_ROCK_SURFACE[0], context )
        self.logger.info(f"PROCESS - Rock raster DTM: {source_raster_rock_surface}")
        if bLongterm:
            self.logger.info(f"PROCESS - ######## LONGTERM ########")
            self.logger.info(f"PROCESS - Defining long term input")
            
        ############### HANDELING OF INPUT RASTER ################
            if source_raster_rock_surface is not None:
                ############### RASTER REPROJECT ################
                if reproject_is_needed(source_raster_rock_surface, output_proj):
                    feedback.pushInfo(f"PROCESS - Reprojection needed for layer: {source_raster_rock_surface.name()}, ORIGINAL CRS: {source_raster_rock_surface.crs().postgisSrid()}")
                    try:
                        _, source_raster_rock_surface = reproject_layers(bIntermediate, output_proj, output_folder_path, vector_layer=None, raster_layer=source_raster_rock_surface, context=context, logger=self.logger)
                    except Exception as e:
                        feedback.reportError(f"Error during reprojection of RASTER LAYER: {e}")
                        return {}
                
                # Get the file path of the raster layer
                path_source_raster_rock_surface = source_raster_rock_surface.source().lower().split('|')[0]
                self.logger.info(f"PROCESS - Rock raster DTM File path: {path_source_raster_rock_surface}")
                # Check if the file extension is .tif
                if path_source_raster_rock_surface.endswith('.tif') or path_source_raster_rock_surface.endswith('.tiff'):
                    feedback.pushInfo("The raster layer is a TIFF file.")
                    # Continue processing...
                else:
                    feedback.reportError("The raster layer is not a TIFF file. Convert it to TIF/TIFF!")
                    return {}
            else:
                feedback.reportError("PROCESS - Something is wrong with the raster.")
                return {}
            
            porepressure_index = self.parameterAsEnum(parameters, self.POREPRESSURE_ENUM_CURVES[0],context)
            porewp_calc_type_english = self.CURVES_enum_porepressure[porepressure_index]
            porewp_calc_type = map_porepressure_curve_names(porewp_calc_type_english)
            tunnel_leakage = self.parameterAsDouble(parameters, self.TUNNEL_LEAKAGE[0], context)
            porewp_red_at_site = self.parameterAsInt(parameters, self.POREPRESSURE_REDUCTION[0], context)
            dry_crust_thk = self.parameterAsDouble(parameters, self.DRY_CRUST_THICKNESS[0], context)
            dep_groundwater = self.parameterAsDouble(parameters, self.DEPTH_GROUNDWATER[0], context)
            density_sat = self.parameterAsDouble(parameters, self.SOIL_DENSITY[0], context)
            ocr_value = self.parameterAsDouble(parameters, self.OCR[0], context)
            janbu_ref_stress = self.parameterAsInt(parameters, self.JANBU_REF_STRESS[0], context)
            janbu_const = self.parameterAsInt(parameters, self.JANBU_CONSTANT[0], context)
            janbu_m = self.parameterAsInt(parameters, self.JANBU_COMP_MODULUS[0], context)
            consolidation_time = self.parameterAsInt(parameters, self.CONSOLIDATION_TIME[0], context)
            
        else:
            porewp_calc_type = None
            porewp_red_at_site = None
            tunnel_leakage = None
            path_source_raster_rock_surface = None
            dry_crust_thk = None
            dep_groundwater = None
            density_sat = None
            ocr_value = None
            janbu_ref_stress = None
            janbu_const = None
            janbu_m = None
            consolidation_time = None
        
        if bVulnerability:
            self.logger.info(f"PROCESS - ######## VULNERABILITY ########")
            self.logger.info(f"PROCESS - Defining vulnerability input")
            foundation_field = self.parameterAsString(parameters, self.FILED_NAME_BUILDING_FOUNDATION[0], context)
            self.logger.info(f"PROCESS - Foundation: {foundation_field} Type: {type(foundation_field)}")
            
            structure_field = self.parameterAsString(parameters, self.FILED_NAME_BUILDING_STRUCTURE[0], context)
            self.logger.info(f"PROCESS - Structure: {structure_field} Type: {type(structure_field)}")
            
            status_field = self.parameterAsString(parameters, self.FILED_NAME_BUILDING_STATUS[0], context)
            self.logger.info(f"PROCESS - Condition: {status_field} Type: {type(status_field)}")
            
        else:
            foundation_field = None
            structure_field = None
            status_field = None
        
        #################  LOG PROJECTIONS #################
        feedback.pushInfo(f"PROCESS - CRS BUILDINGS-vector: {source_building_poly.crs().postgisSrid()}")
        feedback.pushInfo(f"PROCESS - CRS EXCAVATION-vector: {source_tunnel_poly.crs().postgisSrid()}")
        if source_raster_rock_surface is not None:
            feedback.pushInfo(f"PROCESS - CRS DTB-raster: {source_raster_rock_surface.crs().postgisSrid()}")
        
        ###### FEEDBACK ALL PARAMETERS #########
        feedback.pushInfo("PROCESS - Running mainBegrensSkade_Excavation...")
        self.logger.info("PROCESS - Running mainBegrensSkade_Excavation...")
        feedback.pushInfo(f"PROCESS - Param: buildingsFN = {path_source_building_poly}")
        feedback.pushInfo(f"PROCESS - Param: excavationJson = {source_tunnel_poly_as_json}")
        feedback.pushInfo(f"PROCESS - Param: Output folder = {output_folder}")
        feedback.pushInfo(f"PROCESS - Param: feature_name = {feature_name}")
        feedback.pushInfo(f"PROCESS - Param: output_proj = {output_srid}")
        feedback.pushInfo(f"PROCESS - Param: bShortterm = {bShortterm}")
        feedback.pushInfo(f"PROCESS - Param: tunnel_depth = {tunnel_depth}")
        feedback.pushInfo(f"PROCESS - Param: tunnel_diameter = {tunnel_diameter}")
        feedback.pushInfo(f"PROCESS - Param: volume_loss = {volume_loss}")
        feedback.pushInfo(f"PROCESS - Param: trough_width = {trough_width}")
        feedback.pushInfo(f"PROCESS - Param: bLongterm = {bLongterm}")
        feedback.pushInfo(f"PROCESS - Param: tunnel_leakage = {tunnel_leakage}")
        feedback.pushInfo(f"PROCESS - Param: porewp_calc_type = {porewp_calc_type}")
        feedback.pushInfo(f"PROCESS - Param: porewp_red_at_site = {porewp_red_at_site}")
        feedback.pushInfo(f"PROCESS - Param: dtb_raster = {path_source_raster_rock_surface}")
        feedback.pushInfo(f"PROCESS - Param: dry_crust_thk = {dry_crust_thk}")
        feedback.pushInfo(f"PROCESS - Param: dep_groundwater = {dep_groundwater}")
        feedback.pushInfo(f"PROCESS - Param: density_sat = {density_sat}")
        feedback.pushInfo(f"PROCESS - Param: OCR = {ocr_value}")
        feedback.pushInfo(f"PROCESS - Param: janbu_ref_stress = {janbu_ref_stress}")
        feedback.pushInfo(f"PROCESS - Param: janbu_const = {janbu_const}")
        feedback.pushInfo(f"PROCESS - Param: janbu_m = {janbu_m}")
        feedback.pushInfo(f"PROCESS - Param: consolidation_time = {consolidation_time}")
        feedback.pushInfo(f"PROCESS - Param: bVulnerability = {bVulnerability}")
        feedback.pushInfo(f"PROCESS - Param: fieldNameFoundation = {foundation_field}")
        feedback.pushInfo(f"PROCESS - Param: fieldNameStructure = {structure_field}")
        feedback.pushInfo(f"PROCESS - Param: fieldNameStatus = {status_field}")
        feedback.setProgress(50)
        try:
            output_shapefiles = mainBegrensSkade_Tunnel(
                logger=self.logger,
                buildingsFN=str(path_source_building_poly),
                tunnelJson=source_tunnel_poly_as_json,
                output_ws=output_folder,
                feature_name=feature_name,
                output_proj=output_srid,
                bShortterm=bShortterm,
                tunnel_depth=tunnel_depth,
                tunnel_diameter=tunnel_diameter,
                volume_loss=volume_loss,
                trough_width=trough_width,
                bLongterm=bLongterm,
                tunnel_leakage=tunnel_leakage,
                porewp_calc_type=porewp_calc_type,
                porewp_red_at_site=porewp_red_at_site,
                dtb_raster=str(path_source_raster_rock_surface),
                dry_crust_thk=dry_crust_thk,
                dep_groundwater=dep_groundwater,
                density_sat=density_sat,
                OCR=ocr_value,
                janbu_ref_stress=janbu_ref_stress,
                janbu_const=janbu_const,
                janbu_m=janbu_m,
                consolidation_time=consolidation_time,
                bVulnerability=bVulnerability,
                fieldNameFoundation=foundation_field,
                fieldNameStructure=structure_field,
                fieldNameStatus=status_field,
            )
            feedback.pushInfo("PROCESS - Finished with mainBegrensSkade_Excavation...")
            self.logger.info("PROCESS - Finished with mainBegrensSkade_Excavation...")
        except Exception as e:
            error_msg = f"Unexpected error: {e}\nTraceback:\n{traceback.format_exc()}"
            QgsMessageLog.logMessage(error_msg, level=Qgis.Critical)
            feedback.reportError(error_msg)
            return {}
        
        #################### HANDLE THE RESULT ###############################
        self.logger.info(f"PROCESS - OUTPUT BUILDINGS: {output_shapefiles[0]}")
        self.logger.info(f"PROCESS - OUTPUT WALL: {output_shapefiles[1]}")
        self.logger.info(f"PROCESS - OUTPUT CORNER: {output_shapefiles[2]}")
        feedback.pushInfo("PROCESS - Finished with processing!")
        
        # Path to the "styles" directory
        styles_dir_path = Path(__file__).resolve().parent.parent / "styles"
        self.logger.info(f"RESULTS - Styles directory path: {styles_dir_path}")
        
        layers_info = [
        ("TUNNEL_CORNERS-SETTLEMENT", output_shapefiles[2], "CORNERS-SETTLMENT_mm.qml"),
        ("TUNNEL_WALLS-ANGLE", output_shapefiles[1], "WALL-ANGLE.qml"),
        ("TUNNEL_BUILDING-TOTAL-SETTLMENT", output_shapefiles[0], "BUILDING-TOTAL-SETTLMENT_sv_tot.qml"),
        ("TUNNEL_BUILDING-TOTAL-ANGLE", output_shapefiles[0], "BUILDING-TOTAL-ANGLE_max_angle.qml")
        ]
        # Add additional layers if bVulnerability is True
        if bVulnerability:
            layers_info.extend([
                ("TUNNEL_BUILDING-RISK-SETTLMENT", output_shapefiles[0], "BUILDING-TOTAL-RISK-SELLMENT_risk_tots.qml"),
                ("TUNNEL_BUILDING-RISK-ANGLE", output_shapefiles[0], "BUILDING-TOTAL-RISK-ANGLE_risk_angle.qml")
            ])

######### EXPERIMENTAL ADD LAYERS TO GUI #########
        # Create the task
        add_layers_task = AddLayersTask("Add Layers", layers_info, feature_name, styles_dir_path, self.logger)
        # Local event loop
        loop = QEventLoop()
        # Define a slot to handle the task completion
        def onTaskCompleted(success):
            if success:
                feedback.pushInfo("Layers added successfully.")
            else:
                feedback.reportError("Failed to add layers.")
            loop.quit()  # Quit the event loop
            
        # Connect the task's completed signal to the slot
        add_layers_task.taskCompleted.connect(onTaskCompleted)

        # Start the task
        QgsApplication.taskManager().addTask(add_layers_task)
        # Start the event loop
        loop.exec_()

        # Check if the task was successful
        if not add_layers_task.completed:
            raise QgsProcessingException("Error occurred while adding layers.")
        
        feedback.setProgress(100)
        feedback.pushInfo(f"RESULTS - Finished adding results!")
        
        return {
            self.OUTPUT_BUILDING: output_shapefiles[0],
            self.OUTPUT_WALL: output_shapefiles[1],
            self.OUTPUT_CORNER: output_shapefiles[2],
        }

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'begrensskadesunnel'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Begrens Skade - Tunnel")

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr("REMEDY_GIS_RiskTool")

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'remedygisrisktool'
    
    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr("The BegrensSkade Tunnel alorithm provides a comprehensive analysis of building settlements and risks associated with subsidence and inclination due to tunnel excavation. Key features include:\nSHORT TERM AND LONG TERM\n1. Calculation of total settlements at all corners or breakpoints of a building.\n2. Determination of wall inclinations, classified based on the slope between two corner points of each wall.\n3. Assessment of the building's risk of settlement damage with respect to total settlements, classified based on the highest risk category of the corner with the greatest settlement.\n4. Assessment of the building's risk of settlement damage with respect to inclination, classified based on the highest risk category of wall inclination.\nVULNERABILITY\n5. Classification of a building's risk of damage due to total settlements, considering the vulnerability and the highest risk category of the corner with the greatest settlement.\n6. Classification of a building's risk of damage due to inclination, considering both the vulnerability and the highest risk category of wall inclination.\nThe algorithm creates a log directory under the users Downloads folder called 'REMEDY'.")

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return BegrensSkadeTunnel()
    
    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return GuiUtils.get_icon(icon='tunnel.png')
