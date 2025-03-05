# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GeovitaProcessingPlugin
                                 A QGIS plugin
 This plugin adds different geovita processing plugins
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-01-17
        copyright            : (C) 2024 by DPE
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

__author__ = "DPE"
__date__ = "2024-01-17"
__copyright__ = "(C) 2024 by DPE"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    Qgis,
    QgsProject,
    QgsProcessing,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterString,
    QgsProcessingParameterCrs,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterLayer,
    QgsMessageLog,
)

import traceback
from pathlib import Path

from .base_algorithm import GvBaseProcessingAlgorithms
from ..utilities.AddLayersTask import AddLayersTask
from ..utilities.gui import GuiUtils
from ..utilities.logger import CustomLogger
from ..utilities.methodslib import (
    get_shapefile_as_json_pyqgis,
    process_raster_for_impactmap,
    reproject_is_needed,
    reproject_layers,
)

from ..REMEDY_GIS_RiskTool.BegrensSkade import mainBegrensSkade_ImpactMap


class BegrensSkadeImpactMap(GvBaseProcessingAlgorithms):
    """
    The `BegrensSkadeImpactMap` algorithm performs geospatial analysis to simulate the impact of excavation activities on the surrounding terrain.
    It utilizes excavation polygons to calculate settlements across a grid, offering a detailed view of potential terrain deformation.
    The algorithm is part of the GeovitaProcessingPlugin suite, designed to support urban planning and geotechnical engineering by
    providing insights into the subsurface impact of construction activities.

    Key Features:
    - Calculation of terrain settlements based on excavation depth and geotechnical parameters.
    - Support for both short-term and long-term settlement analysis.
    - Uses depth to bedrock raster data for settlements calculations.
    - Advanced options for output customization, including grid size and clipping range.
    - Generation of a detailed impact map as a raster layer, visualizing the potential settlement across the terrain.

    Parameters:
    - INPUT_EXCAVATION_POLY: Polygon layer representing excavation areas.
    - RASTER_ROCK_SURFACE: Raster layer indicating depth to bedrock.
    - OUTPUT_FOLDER: Directory for storing the output raster.
    - OUTPUT_FEATURE_NAME: Naming convention for analysis and output features.
    - OUTPUT_CRS: Coordinate reference system for the output data.
    - Various parameters for geotechnical analysis, such as excavation depth, soil density, and consolidation time.

    Outputs:
    - OUTPUT_RASTER: A raster layer visualizing the calculated terrain settlements.

    Usage:
    This algorithm is accessible through the QGIS Processing Toolbox under the GeovitaProcessingPlugin suite.
    Ensure all required input layers are prepared and parameters are appropriately set to conduct the impact analysis.
    The output raster can be used for further analysis or visualized in QGIS for planning and decision-making purposes.

    The algorithm leverages the mainBegrensSkade_ImpactMap function from the REMEDY_GIS_RiskTool for spatial analysis,
    aiding in the assessment of construction impacts on the urban and natural environment.
    """

    def __init__(self):
        super().__init__()

        # Initialize the logger in the users download folder
        home_dir = Path.home()
        log_dir_path = home_dir / "Downloads" / "REMEDY" / "log"
        self.logger = CustomLogger(
            log_dir_path, "BegrensSkadeII_QGIS_IMPACTMAP.log", "IMPACTMAP_LOGGER"
        ).get_logger()
        
        # Retrieve version number from BaseAlgorithm class "GvBaseProcessingAlgorithms"
        self.version = self.getVersion()
        self.logger.info(f"__INIT__ - VERSION: {self.version} ")

        # instanciate variables used in postprocessing to add layers to GUI
        self.feature_name = None  # Default value
        self.layers_info = {}
        self.styles_dir_path = Path()
        self.add_layers_task = AddLayersTask()
        self.logger.info("__INIT__ - Finished initialize BegrensSkadeImpactMap ")

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "begrensskadeimpactmap"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Begrens Skade - Impact Map")

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
        return "remedygisrisktool"

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr(
            "The BegrensSkade ImpactMap alorithm calculates both short-term and long-term settlements that occur due to the establishment of a construction pit. The difference is that ImpactMap calculates terrain settlements, meaning the settlement is calculated for each cell in a grid that covers the same area as the rock model instead of only at the corner points of the building polygons. ImpactMap only provides total settlements as output.\nThe algorithm creates a log directory under the users Downloads folder called 'REMEDY'."
        )

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        return BegrensSkadeImpactMap()

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return GuiUtils.get_icon(icon="impactmap.png")

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    INPUT_EXCAVATION_POLY = "INPUT_EXCAVATION_POLY"
    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    OUTPUT_FEATURE_NAME = "OUTPUT_FEATURE_NAME"

    OUTPUT_CRS = "OUTPUT_CRS"
    # return shapefiles from mainBegrensSkade_ImpactMap()
    OUTPUT_RASTER = "OUTPUT_RASTER"

    OUTPUT_RESOLUTION = ["OUTPUT_RESOLUTION", "Output grid size [meters]"]  # in meters
    SHORT_TERM_SETTLEMENT = ["SHORT_TERM_SETTLEMENT", "Short term settlements"]
    EXCAVATION_DEPTH = ["EXCAVATION_DEPTH", "Depth of excavation [m]"]
    SETTLEMENT_ENUM = ["SETTLEMENT_ENUM", "Settlement curves"]
    enum_settlment = [
        r"0,5 % av byggegropdybde",
        r"1 % av byggegropdybde",
        r"2 % av byggegropdybde",
        r"3 % av byggegropdybde",
    ]
    RASTER_ROCK_SURFACE = ["RASTER_ROCK_SURFACE", "Input raster of depth to bedrock"]
    CLIPPING_RANGE = [
        "CLIPPING_RANGE",
        "Clip distance in case of high resolution (buffer distance in [meters])",
    ]

    POREWP_REDUCTION_M = ["POREWP_REDUCTION_M", "Porewater pressure reduction [m]"]
    DRY_CRUST_THICKNESS = [
        "DRY_CRUST_THICKNESS",
        "Thickness of overburden not affected by porewater drawdown [m]",
    ]
    DEPTH_GROUNDWATER = ["DEPTH_GROUNDWATER", "Depht to groundwater table [m]"]
    SOIL_DENSITY = ["SOIL_DENSITY", "Soil saturation density [kN/m3]"]
    OCR = ["OCR", "Over consolidation ratio"]
    JANBU_REF_STRESS = ["JANBU_REF_STRESS", "Janbu reference stress, p`r (kPa)"]
    JANBU_CONSTANT = ["JANBU_CONSTANT", "Janbu constant [M0/(m*p`c)]"]
    JANBU_COMP_MODULUS = ["JANBU_COMP_MODULUS", "Janbu compression modulus"]
    CONSOLIDATION_TIME = ["CONSOLIDATION_TIME", "Consolidation time [years]"]

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It must have polygon
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_EXCAVATION_POLY,
                self.tr("Input Excavation polygon(s)"),
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        # We add the input raster features source. It must contain depth to bedrock values
        param = QgsProcessingParameterRasterLayer(
            self.RASTER_ROCK_SURFACE[0],
            self.tr(f"{self.RASTER_ROCK_SURFACE[1]}"),
            defaultValue=None,
        )
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterString(
                self.OUTPUT_FEATURE_NAME,
                self.tr(
                    "Naming Conventions for Analysis and Features (Output feature name appended to file-names)"
                ),
            )
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.OUTPUT_CRS,
                self.tr("Output CRS"),
                defaultValue=QgsProject.instance().crs(),
            )
        )
        param = QgsProcessingParameterNumber(
            self.OUTPUT_RESOLUTION[0],
            self.tr(f"{self.OUTPUT_RESOLUTION[1]}"),
            QgsProcessingParameterNumber.Double,
            defaultValue=10,
            minValue=0,
        )
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                self.tr("Output Folder"),
            )
        )

        # SHORT TERM GROUP
        param = QgsProcessingParameterBoolean(
            self.SHORT_TERM_SETTLEMENT[0],
            self.tr(f"{self.SHORT_TERM_SETTLEMENT[1]}"),
            defaultValue=False,
        )
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.EXCAVATION_DEPTH[0],
            self.tr(f"{self.EXCAVATION_DEPTH[1]}"),
            QgsProcessingParameterNumber.Double,
            defaultValue=0,
            minValue=0,
        )
        self.addParameter(param)
        param = QgsProcessingParameterEnum(
            self.SETTLEMENT_ENUM[0],
            self.tr(f"{self.SETTLEMENT_ENUM[1]}"),
            self.enum_settlment,
            defaultValue=1,
            allowMultiple=False,
        )
        self.addParameter(param)

        # DEFINING ADVANCED PARAMETERS
        param = QgsProcessingParameterNumber(
            self.CLIPPING_RANGE[0],
            self.tr(f"{self.CLIPPING_RANGE[1]}"),
            defaultValue=150,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        
        param = QgsProcessingParameterNumber(
            self.POREWP_REDUCTION_M[0],
            self.tr(f"{self.POREWP_REDUCTION_M[1]}"),
            defaultValue=10,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.DRY_CRUST_THICKNESS[0],
            self.tr(f"{self.DRY_CRUST_THICKNESS[1]}"),
            defaultValue=5,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.DEPTH_GROUNDWATER[0],
            self.tr(f"{self.DEPTH_GROUNDWATER[1]}"),
            defaultValue=3,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.SOIL_DENSITY[0],
            self.tr(f"{self.SOIL_DENSITY[1]}"),
            QgsProcessingParameterNumber.Double,
            defaultValue=18.5,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.OCR[0],
            self.tr(f"{self.OCR[1]}"),
            QgsProcessingParameterNumber.Double,
            defaultValue=1.2,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.JANBU_REF_STRESS[0],
            self.tr(f"{self.JANBU_REF_STRESS[1]}"),
            defaultValue=0,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.JANBU_CONSTANT[0],
            self.tr(f"{self.JANBU_CONSTANT[1]}"),
            defaultValue=4,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.JANBU_COMP_MODULUS[0],
            self.tr(f"{self.JANBU_COMP_MODULUS[1]}"),
            defaultValue=15,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.CONSOLIDATION_TIME[0],
            self.tr(f"{self.CONSOLIDATION_TIME[1]}"),
            defaultValue=1000,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        feedback.pushInfo(
                f"PROCESS - Version: {self.version}"
            )
        bShortterm = self.parameterAsBoolean(
            parameters, self.SHORT_TERM_SETTLEMENT[0], context
        )
        self.logger.info(f"PROCESS - bShortterm value: {bShortterm}")

        self.feature_name = self.parameterAsString(
            parameters, self.OUTPUT_FEATURE_NAME, context
        )
        self.logger.info(f"PROCESS - Feature name: {self.feature_name}")

        output_proj = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        output_srid = output_proj.postgisSrid()
        self.logger.info(f"PROCESS - Output CRS(SRID): {output_srid}")
        feedback.setProgress(10)
        clipping_range = self.parameterAsInt(
            parameters, self.CLIPPING_RANGE[0], context
        )

        output_resolution = self.parameterAsDouble(
            parameters, self.OUTPUT_RESOLUTION[0], context
        )

        dry_crust_thk = self.parameterAsDouble(
            parameters, self.DRY_CRUST_THICKNESS[0], context
        )
        dep_groundwater = self.parameterAsDouble(
            parameters, self.DEPTH_GROUNDWATER[0], context
        )
        density_sat = self.parameterAsDouble(parameters, self.SOIL_DENSITY[0], context)
        ocr_value = self.parameterAsDouble(parameters, self.OCR[0], context)
        porewp_red_m = self.parameterAsInt(
            parameters, self.POREWP_REDUCTION_M[0], context
        )
        janbu_ref_stress = self.parameterAsInt(
            parameters, self.JANBU_REF_STRESS[0], context
        )
        janbu_const = self.parameterAsInt(parameters, self.JANBU_CONSTANT[0], context)
        janbu_m = self.parameterAsInt(parameters, self.JANBU_COMP_MODULUS[0], context)
        consolidation_time = self.parameterAsInt(
            parameters, self.CONSOLIDATION_TIME[0], context
        )

        source_raster_rock_surface = self.parameterAsRasterLayer(
            parameters, self.RASTER_ROCK_SURFACE[0], context
        )
        self.logger.info(
            f"PROCESS - Rock raster DTM layer: {source_raster_rock_surface}"
        )

        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        # Ensure the output directory exists
        output_folder_path = Path(output_folder)
        output_folder_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"PROCESS - Output folder: {str(output_folder_path)}")
        feedback.setProgress(20)
        ############### HANDELING OF INPUT RASTER ################
        if source_raster_rock_surface is not None:
            ############### RASTER REPROJECT ################
            if reproject_is_needed(source_raster_rock_surface, output_proj):
                feedback.pushInfo(
                    f"PROCESS - Reprojection needed for layer: {source_raster_rock_surface.name()}, ORIGINAL CRS: {source_raster_rock_surface.crs().postgisSrid()}"
                )
                try:
                    _, source_raster_rock_surface = reproject_layers(
                        output_proj,
                        vector_layer=None,
                        raster_layer=source_raster_rock_surface,
                        context=context,
                        logger=self.logger,
                    )
                except Exception as e:
                    feedback.reportError(
                        f"Error during reprojection of RASTER LAYER: {e}"
                    )
                    return {}

            # Get the file path of the raster layer
            path_source_raster_rock_surface = (
                source_raster_rock_surface.source().split("|")[0]
            )
            self.logger.info(
                f"PROCESS - Rock raster DTM File path: {path_source_raster_rock_surface}"
            )
            # Check if the file extension is .tif
            if path_source_raster_rock_surface.endswith(
                ".tif"
            ) or path_source_raster_rock_surface.endswith(".tiff"):
                feedback.pushInfo("The raster layer is a TIFF file.")
                # Continue processing...
            else:
                feedback.reportError(
                    "The raster layer is not a TIFF file. Convert it to TIF/TIFF!"
                )
                return {}

        #################  CHECK INPUT PROJECTIONS OF VECTOR LAYERS #################
        # Retrive the parameter as vector layer
        source_excavation_poly = self.parameterAsVectorLayer(
            parameters, self.INPUT_EXCAVATION_POLY, context
        )
        # Check if each layer matches the output CRS --> If False is returned, reproject the layers.
        if reproject_is_needed(source_excavation_poly, output_proj):
            feedback.pushInfo(
                f"PROCESS - Reprojection needed for layer: {source_excavation_poly.name()}, ORIGINAL CRS: {source_excavation_poly.crs().postgisSrid()}"
            )
            try:
                source_excavation_poly, _ = reproject_layers(
                    output_proj,
                    vector_layer=source_excavation_poly,
                    raster_layer=None,
                    context=context,
                    logger=self.logger,
                )
            except Exception as e:
                feedback.reportError(f"Error during reprojection of EXCAVATION: {e}")
                return {}

        path_source_excavation_poly = source_excavation_poly.source().split("|")[0]
        self.logger.info(
            f"PROCESS - Path to source excavation: {path_source_excavation_poly}"
        )

        source_excavation_poly_as_json = get_shapefile_as_json_pyqgis(
            source_excavation_poly, self.logger
        )
        # source_excavation_poly_as_json = Utils.getShapefileAsJson(path_source_excavation_poly, logger)
        self.logger.info(f"PROCESS - JSON structure: {source_excavation_poly_as_json}")

        feedback.pushInfo("PROCESS - Running process_raster_for_impactmap...")
        path_processed_raster = process_raster_for_impactmap(
            source_excavation_poly=source_excavation_poly,
            dtb_raster_layer=source_raster_rock_surface,
            clipping_range=clipping_range,
            output_resolution=output_resolution,
            output_folder=output_folder_path,
            output_crs=output_proj,
            context=context,
            logger=self.logger,
        )
        feedback.pushInfo("PROCESS - Done running process_raster_for_impactmap...")
        feedback.setProgress(30)
        if bShortterm:
            self.logger.info("PROCESS - ######## SHORTTERM ########")
            self.logger.info("PROCESS - Defining short term input")
            excavation_depth = self.parameterAsDouble(
                parameters, self.EXCAVATION_DEPTH[0], context
            )
            short_term_curve_index = self.parameterAsEnum(
                parameters, self.SETTLEMENT_ENUM[0], context
            )
            short_term_curve = self.enum_settlment[short_term_curve_index]

        else:
            excavation_depth = None
            short_term_curve = None

        #################  LOG PROJECTIONS #################
        feedback.pushInfo(
            f"PROCESS - CRS EXCAVATION-vector: {source_excavation_poly.crs().postgisSrid()}"
        )
        feedback.pushInfo(
            f"PROCESS - CRS DTB-raster: {source_raster_rock_surface.crs().postgisSrid()}"
        )

        ###### FEEDBACK ALL PARAMETERS #########
        feedback.pushInfo(
            f"PROCESS - PARAM excavationJson: {source_excavation_poly_as_json}"
        )
        feedback.pushInfo(f"PROCESS - PARAM output_ws: {str(output_folder_path)}")
        feedback.pushInfo(f"PROCESS - PARAM output_name: {self.feature_name}")
        feedback.pushInfo(f"PROCESS - PARAM CALCULATION_RANGE: {clipping_range}")
        feedback.pushInfo(f"PROCESS - PARAM output_proj: {output_srid}")
        feedback.pushInfo(f"PROCESS - PARAM dtb_raster: {str(path_processed_raster)}")
        feedback.pushInfo(f"PROCESS - PARAM dry_crust_thk: {dry_crust_thk}")
        feedback.pushInfo(f"PROCESS - PARAM dep_groundwater: {dep_groundwater}")
        feedback.pushInfo(f"PROCESS - PARAM density_sat: {density_sat}")
        feedback.pushInfo(f"PROCESS - PARAM OCR: {ocr_value}")
        feedback.pushInfo(f"PROCESS - PARAM porewp_red_m: {porewp_red_m}")
        feedback.pushInfo(f"PROCESS - PARAM janbu_ref_stress: {janbu_ref_stress}")
        feedback.pushInfo(f"PROCESS - PARAM janbu_const: {janbu_const}")
        feedback.pushInfo(f"PROCESS - PARAM janbu_m: {janbu_m}")
        feedback.pushInfo(f"PROCESS - PARAM consolidation_time: {consolidation_time}")
        feedback.pushInfo(f"PROCESS - PARAM bShortterm: {bShortterm}")
        feedback.pushInfo(f"PROCESS - PARAM excavation_depth: {excavation_depth}")
        feedback.pushInfo(f"PROCESS - PARAM short_term_curve: {short_term_curve}")
        feedback.pushInfo("PROCESS - Running mainBegrensSkade_ImpactMap...")
        self.logger.info("PROCESS - Running mainBegrensSkade_ImpactMap...")
        feedback.setProgress(50)
        try:
            output_raster_path = mainBegrensSkade_ImpactMap(
                logger=self.logger,
                excavationJson=source_excavation_poly_as_json,
                output_ws=str(output_folder_path),
                output_name=self.feature_name,
                CALCULATION_RANGE=clipping_range,  # '380' hardcoded constant used in the underlying submodule's method.
                output_proj=output_srid,
                dtb_raster=str(path_processed_raster),
                dry_crust_thk=dry_crust_thk,
                dep_groundwater=dep_groundwater,
                density_sat=density_sat,
                OCR=ocr_value,
                porewp_red_m=porewp_red_m,
                janbu_ref_stress=janbu_ref_stress,
                janbu_const=janbu_const,
                janbu_m=janbu_m,
                consolidation_time=consolidation_time,
                bShortterm=bShortterm,
                excavation_depth=excavation_depth,
                short_term_curve=short_term_curve,
            )
            feedback.pushInfo("PROCESS - Finished with mainBegrensSkade_ImpactMap...")
            self.logger.info("PROCESS - Finished with mainBegrensSkade_ImpactMap...")
        except Exception as e:
            error_msg = f"Unexpected error: {e}\nTraceback:\n{traceback.format_exc()}"
            QgsMessageLog.logMessage(error_msg, level=Qgis.Critical)
            feedback.reportError(error_msg)
            return {}

        #################### HANDLE THE RESULT ###############################
        feedback.setProgress(80)
        self.logger.info(f"PROCESS - OUTPUT RASTER: {output_raster_path}")
        feedback.pushInfo("PROCESS - Finished with processing!")

        # Path to the "styles" directory
        self.styles_dir_path = Path(__file__).resolve().parent.parent / "styles"
        self.logger.info(f"RESULTS - Styles directory path: {self.styles_dir_path}")

        self.layers_info = {
            "IMPACT-MAP": {
                "shape_path": output_raster_path,
                "style_name": "IMPACT-MAP.qml",
            }
        }

        feedback.setProgress(90)
        feedback.pushInfo("PROCESS - Finished processing!")
        # Return the results of the algorithm.
        return {self.OUTPUT_FOLDER: output_raster_path}

    def postProcessAlgorithm(self, context, feedback):
        """
        Handles the post-processing steps of the algorithm, specifically adding output layers to the QGIS project.

        This method creates and executes a process to add layers to the QGIS interface, applying predefined styles 
        and organizing them within a specified group. It leverages the `AddLayersTask` class to manage layer 
        addition in a way that ensures thread safety and proper GUI updates.

        Parameters:
        - context (QgsProcessingContext): The context of the processing, providing access to the QGIS project and other relevant settings.
        - feedback (QgsProcessingFeedback): The object used to report progress and log messages back to the user.

        Returns:
        - dict: An empty dictionary. This method does not produce output parameters but instead focuses on the side effect of adding layers to the project.

        Note:
        This method sets up a task for layer addition, defining success and failure callbacks to provide user feedback. 
        It manually starts the process and handles its completion.
        """
        ######### EXPERIMENTAL ADD LAYERS TO GUI #########
        # Create the task
        self.add_layers_task.setParameters(
            self.layers_info, self.feature_name, self.styles_dir_path, self.logger
        )

        # Define a slot to handle the task completion
        def onTaskCompleted(success):
            if success:
                feedback.pushInfo("POSTPROCESS - Layers added successfully.")
                feedback.setProgress(100)
            else:
                feedback.reportError("POSTPROCESS - Failed to add layers.")
                feedback.setProgress(100)

        # Connect the task's completed signal to the slot
        self.add_layers_task.taskCompleted.connect(onTaskCompleted)

        # Start the task
        success = self.add_layers_task.run()
        self.add_layers_task.finished(success)
        return {}
