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

import traceback
from pathlib import Path

from qgis.core import (
    Qgis,
    QgsMessageLog,
    QgsProcessing,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsProject,
)
from qgis.PyQt.QtCore import QCoreApplication

from ..REMEDY_GIS_RiskTool.BegrensSkade import mainBegrensSkade_Excavation
from ..utilities.AddLayersTask import AddLayersTask
from ..utilities.gui import GuiUtils
from ..utilities.logger import CustomLogger
from ..utilities.methodslib import (
    get_shapefile_as_json_pyqgis,
    reproject_is_needed,
    reproject_layers,
)
from .base_algorithm import GvBaseProcessingAlgorithms


class BegrensSkadeExcavation(GvBaseProcessingAlgorithms):
    """
    The BegrensSkadeExcavation algorithm performs a detailed analysis of building settlements
    and risks associated with subsidence and inclination due to excavation activities. It is
    designed to process vector layers representing buildings and excavation areas, optionally
    incorporating raster data for depth to bedrock analysis.

    This algorithm is capable of computing both short-term and long-term settlements at various
    points of a building, such as corners or breakpoints, and classifying the risk of settlement
    damage. It supports vulnerability analysis based on the building's foundation, structure,
    and condition, offering a comprehensive risk assessment tool for geotechnical engineers and
    urban planners.

    Parameters:
    - INPUT_BUILDING_POLY: Vector layer of building polygons.
    - INPUT_EXCAVATION_POLY: Vector layer of excavation polygons.
    - RASTER_ROCK_SURFACE: Raster layer representing depth to bedrock (optional).
    - OUTPUT_FOLDER: Destination folder for output files.
    - Various parameters to configure the analysis, including excavation depth, settlement
      curves, pore pressure reduction, soil density, and more.

    Outputs:
    - OUTPUT_BUILDING, OUTPUT_WALL, OUTPUT_CORNER: Shapefiles representing the analysis results,
      including total settlements, wall inclinations, and classified risk levels.

    The algorithm leverages the mainBegrensSkade_Excavation function from the REMEDY_GIS_RiskTool
    module and includes advanced options for intermediate layer management and output customization.

    Usage:
    This algorithm can be executed within QGIS's Processing Toolbox. Ensure all necessary input
    layers are prepared and parameters are set according to the specific analysis requirements.
    """

    def __init__(self):
        super().__init__()

        # Initialize the logger in the users download folder
        home_dir = Path.home()
        log_dir_path = home_dir / "Downloads" / "REMEDY" / "log"
        self.logger = CustomLogger(
            log_dir_path,
            "BegrensSkadeII_QGIS_EXCAVATION.log",
            "EXCAVATION_LOGGER",
        ).get_logger()
        self.logger.info("__INIT__ - Finished initialize BegrensSkadeExcavation ")

        # instanciate variables used in postprocessing to add layers to GUI
        self.feature_name = None  # Default value
        self.layers_info = {}
        self.styles_dir_path = Path()
        self.add_layers_task = AddLayersTask()

    def tr(self, string):
        return QCoreApplication.translate("Processing", string)

    def createInstance(self):
        self.logger.info("INSTANCE - Finished defining the instance")
        return BegrensSkadeExcavation()

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return GuiUtils.get_icon(icon="excavation.png")

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return "begrensskadeexcavation"

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr("Begrens Skade - Excavation")

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
            "The Begrens Skade - Excavation algorithm provides a comprehensive analysis of building settlements and risks associated with subsidence and inclination. Key features include:\nSHORT TERM AND LONG TERM\n1. Calculation of total settlements at all corners or breakpoints of a building.\n2. Determination of wall inclinations, classified based on the slope between two corner points of each wall.\n3. Assessment of the building's risk of settlement damage with respect to total settlements, classified based on the highest risk category of the corner with the greatest settlement.\n4. Assessment of the building's risk of settlement damage with respect to inclination, classified based on the highest risk category of wall inclination.\nVULNERABILITY\n5. Classification of a building's risk of damage due to total settlements, considering the vulnerability and the highest risk category of the corner with the greatest settlement.\n6. Classification of a building's risk of damage due to inclination, considering both the vulnerability and the highest risk category of wall inclination.\nThe algorithm creates a log directory under the users Downloads folder called 'REMEDY'."
        )

    def __getstate__(self):
        return None

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    OUTPUT_FOLDER = "OUTPUT_FOLDER"
    OUTPUT_CRS = "OUTPUT_CRS"
    OUTPUT_FEATURE_NAME = "OUTPUT_FEATURE_NAME"

    INPUT_BUILDING_POLY = "INPUT_BUILDING_POLY"
    INPUT_EXCAVATION_POLY = "INPUT_EXCAVATION_POLY"

    SHORT_TERM_SETTLEMENT = ["SHORT_TERM_SETTLEMENT", "Short term settlements"]
    EXCAVATION_DEPTH = ["EXCAVATION_DEPTH", "Depth of excavation [m]"]
    SETTLEMENT_ENUM = ["SETTLEMENT_ENUM", "Settlement curves"]
    enum_settlment = [
        r"0,5 % av byggegropdybde",
        r"1 % av byggegropdybde",
        r"2 % av byggegropdybde",
        r"3 % av byggegropdybde",
    ]

    LONG_TERM_SETTLEMENT = ["LONG_TERM_SETTLEMENT", "Long term settlements"]
    RASTER_ROCK_SURFACE = [
        "RASTER_ROCK_SURFACE",
        "Input raster of depth to bedrock",
    ]
    POREPRESSURE_ENUM = ["POREPRESSURE_ENUM", "Pore pressure reduction curves"]
    enum_porepressure = [
        "Lav poretrykksreduksjon",
        "Middels poretrykksreduksjon",
        "Høy poretrykksreduksjon",
    ]
    POREPRESSURE_REDUCTION = [
        "POREPRESSURE_REDUCTION",
        "Porepressure reduction [kPa]",
    ]
    DRY_CRUST_THICKNESS = [
        "DRY_CRUST_THICKNESS",
        "Thickness of overburden not affected by porewater drawdown [m]",
    ]
    DEPTH_GROUNDWATER = ["DEPTH_GROUNDWATER", "Depht to groundwater table [m]"]
    SOIL_DENSITY = ["SOIL_DENSITY", "Soil saturation density [kN/m3]"]
    OCR = ["OCR", "Over consolidation ratio"]
    JANBU_REF_STRESS = [
        "JANBU_REF_STRESS",
        "Janbu reference stress, p`r (kPa)",
    ]
    JANBU_CONSTANT = ["JANBU_CONSTANT", "Janbu constant [M0/(m*p`c)]"]
    JANBU_COMP_MODULUS = ["JANBU_COMP_MODULUS", "Janbu compression modulus"]
    CONSOLIDATION_TIME = ["CONSOLIDATION_TIME", "Consolidation time [years]"]

    VULNERABILITY_ANALYSIS = [
        "VULNERABILITY_ANALYSIS",
        "Building vulnerability analysis",
    ]
    FILED_NAME_BUILDING_FOUNDATION = [
        "FILED_NAME_BUILDING_FOUNDATION",
        "Building Foundation column",
    ]
    FILED_NAME_BUILDING_STRUCTURE = [
        "FILED_NAME_BUILDING_STRUCTURE",
        "Building Structure column",
    ]
    FILED_NAME_BUILDING_STATUS = [
        "FILED_NAME_BUILDING_STATUS",
        "Building Condition column",
    ]

    # return shapefiles from mainBegrensSkade_Excavation()
    OUTPUT_BUILDING = "OUTPUT_BUILDING"
    OUTPUT_WALL = "OUTPUT_WALL"
    OUTPUT_CORNER = "OUTPUT_CORNER"

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.logger.info("INIT ALGORITHM - Start setup parameters")
        # We add the input vector features source. It must have polygon
        # geometry.
        # layer
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_BUILDING_POLY,
                self.tr("Input Building polygon(s)"),
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_EXCAVATION_POLY,
                self.tr("Input Excavation polygon(s)"),
                [QgsProcessing.TypeVectorPolygon],
            )
        )
        # SHORT TERM Advanced features
        param = QgsProcessingParameterBoolean(
            self.SHORT_TERM_SETTLEMENT[0],
            self.tr(f"{self.SHORT_TERM_SETTLEMENT[1]}"),
            defaultValue=False,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.EXCAVATION_DEPTH[0],
            self.tr(f"{self.EXCAVATION_DEPTH[1]}"),
            QgsProcessingParameterNumber.Double,
            defaultValue=0,
            minValue=0,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterEnum(
            self.SETTLEMENT_ENUM[0],
            self.tr(f"{self.SETTLEMENT_ENUM[1]}"),
            self.enum_settlment,
            defaultValue=1,
            allowMultiple=False,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # LONG TERM Advanced features
        param = QgsProcessingParameterBoolean(
            self.LONG_TERM_SETTLEMENT[0],
            self.tr(f"{self.LONG_TERM_SETTLEMENT[1]}"),
            defaultValue=False,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        param = QgsProcessingParameterRasterLayer(
            self.RASTER_ROCK_SURFACE[0],
            self.tr(f"{self.RASTER_ROCK_SURFACE[1]}"),
            defaultValue=None,
            optional=True,
        )
        param.setFlags(
            QgsProcessingParameterDefinition.FlagAdvanced
            | QgsProcessingParameterDefinition.FlagOptional
        )
        self.addParameter(param)

        param = QgsProcessingParameterEnum(
            self.POREPRESSURE_ENUM[0],
            self.tr(f"{self.POREPRESSURE_ENUM[1]}"),
            self.enum_porepressure,
            defaultValue=1,
            allowMultiple=False,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            self.POREPRESSURE_REDUCTION[0],
            self.tr(f"{self.POREPRESSURE_REDUCTION[1]}"),
            defaultValue=50,
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
        # VULNERABILITY_ANALYSIS Advanced features
        param = QgsProcessingParameterBoolean(
            self.VULNERABILITY_ANALYSIS[0],
            self.tr(f"{self.VULNERABILITY_ANALYSIS[1]}"),
            defaultValue=False,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField(
            self.FILED_NAME_BUILDING_FOUNDATION[0],
            self.tr(f"{self.FILED_NAME_BUILDING_FOUNDATION[1]}"),
            parentLayerParameterName=self.INPUT_BUILDING_POLY,
            allowMultiple=False,
            optional=True,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField(
            self.FILED_NAME_BUILDING_STRUCTURE[0],
            self.tr(f"{self.FILED_NAME_BUILDING_STRUCTURE[1]}"),
            parentLayerParameterName=self.INPUT_BUILDING_POLY,
            allowMultiple=False,
            optional=True,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterField(
            self.FILED_NAME_BUILDING_STATUS[0],
            self.tr(f"{self.FILED_NAME_BUILDING_STATUS[1]}"),
            parentLayerParameterName=self.INPUT_BUILDING_POLY,
            allowMultiple=False,
            optional=True,
        )
        param.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        # DEFINE OUTPUTS
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
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_FOLDER,
                self.tr("Output Folder"),
            )
        )

        self.logger.info("initAlgorithm - Done setting up the inputs.")

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        self.logger.info("PROCESS - Starting the processing")
        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        # Advanced option flags

        bShortterm = self.parameterAsBoolean(
            parameters, self.SHORT_TERM_SETTLEMENT[0], context
        )
        self.logger.info(f"PROCESS - bShortterm value: {bShortterm}")

        bLongterm = self.parameterAsBoolean(
            parameters, self.LONG_TERM_SETTLEMENT[0], context
        )
        self.logger.info(f"PROCESS - bLongterm value: {bLongterm}")

        if not bShortterm and not bLongterm:
            error_msg = "Please choose Short term or Long term settlements, or both"
            self.logger.error(error_msg)
            feedback.reportError(error_msg)
            return {}

        bVulnerability = self.parameterAsBoolean(
            parameters, self.VULNERABILITY_ANALYSIS[0], context
        )
        self.logger.info(f"PROCESS - bVulnerability value: {bVulnerability}")
        feedback.setProgress(10)

        source_building_poly = self.parameterAsVectorLayer(
            parameters, self.INPUT_BUILDING_POLY, context
        )

        source_excavation_poly = self.parameterAsVectorLayer(
            parameters, self.INPUT_EXCAVATION_POLY, context
        )

        output_folder = self.parameterAsString(parameters, self.OUTPUT_FOLDER, context)
        # Ensure the output directory exists
        output_folder_path = Path(output_folder)
        output_folder_path.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"PROCESS - Output folder: {output_folder}")

        self.feature_name = self.parameterAsString(
            parameters, self.OUTPUT_FEATURE_NAME, context
        )
        self.logger.info(f"PROCESS - Feature name: {self.feature_name}")

        output_proj = self.parameterAsCrs(parameters, self.OUTPUT_CRS, context)
        output_srid = output_proj.postgisSrid()
        self.logger.info(f"PROCESS - Output CRS(SRID): {output_srid}")
        feedback.setProgress(20)

        #################  CHECK INPUT PROJECTIONS OF VECTOR LAYERS #################

        # Check if each layer matches the output CRS --> If False is returned, reproject the layers.
        if reproject_is_needed(source_building_poly, output_proj):
            feedback.pushInfo(
                f"PROCESS - Reprojection needed for layer: {source_building_poly.name()}, ORIGINAL CRS: {source_building_poly.crs().postgisSrid()}"
            )
            try:
                source_building_poly, _ = reproject_layers(
                    output_proj,
                    source_building_poly,
                    raster_layer=None,
                    context=context,
                    logger=self.logger,
                )
            except Exception as e:
                feedback.reportError(f"Error during reprojection of BUILDINGS: {e}")
                return {}
        if reproject_is_needed(source_excavation_poly, output_proj):
            feedback.pushInfo(
                f"PROCESS - Reprojection needed for layer: {source_excavation_poly.name()}, ORIGINAL CRS: {source_excavation_poly.crs().postgisSrid()}"
            )
            try:
                source_excavation_poly, _ = reproject_layers(
                    output_proj,
                    source_excavation_poly,
                    raster_layer=None,
                    context=context,
                    logger=self.logger,
                )
            except Exception as e:
                feedback.reportError(f"Error during reprojection of EXCAVATION: {e}")
                return {}

        path_source_building_poly = source_building_poly.source().split("|")[0]
        self.logger.info(
            f"PROCESS - Path to source buildings: {path_source_building_poly}"
        )

        path_source_excavation_poly = source_excavation_poly.source().split("|")[0]
        self.logger.info(
            f"PROCESS - Path to source excavation: {path_source_excavation_poly}"
        )

        source_excavation_poly_as_json = get_shapefile_as_json_pyqgis(
            source_excavation_poly, self.logger
        )
        # source_excavation_poly_as_json = Utils.getShapefileAsJson(path_source_excavation_poly, logger)
        self.logger.info(f"PROCESS - JSON structure: {source_excavation_poly_as_json}")

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

        source_raster_rock_surface = self.parameterAsRasterLayer(
            parameters, self.RASTER_ROCK_SURFACE[0], context
        )
        self.logger.info(f"PROCESS - Rock raster DTM: {source_raster_rock_surface}")
        if bLongterm:
            self.logger.info("PROCESS - ######## LONGTERM ########")
            ############### HANDELING OF INPUT RASTER ################
            if source_raster_rock_surface is None:
                feedback.reportError(
                    "PROCESS - No raster chosen! Chose a raster to perform long-term analysis"
                )
                raise QgsProcessingException(
                    self.invalidRasterError(parameters, self.RASTER_ROCK_SURFACE[0])
                )

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
                        f"PROCESS - Error during reprojection of RASTER LAYER: {e}"
                    )
                    return {}

            # Get the file path of the raster layer
            path_source_raster_rock_surface = (
                source_raster_rock_surface.source().split("|")[0]
            )
            self.logger.info(
                f"PROCESS - Rock raster DTM File path: {path_source_raster_rock_surface}"
            )
            feedback.pushInfo(
                f"PROCESS - Rock raster DTM File path: {path_source_raster_rock_surface}"
            )
            # Check if the file extension is .tif
            if path_source_raster_rock_surface.endswith((".tif", ".tiff")):
                feedback.pushInfo("PROCESS - The raster layer is a TIFF file.")
                # Continue processing...
            else:
                feedback.reportError(
                    "PROCESS - The raster layer is not a TIFF file. Convert it to TIF/TIFF!"
                )
                return {}

            porepressure_index = self.parameterAsEnum(
                parameters, self.POREPRESSURE_ENUM[0], context
            )
            pw_reduction_curve = self.enum_porepressure[porepressure_index]
            dry_crust_thk = self.parameterAsDouble(
                parameters, self.DRY_CRUST_THICKNESS[0], context
            )
            dep_groundwater = self.parameterAsDouble(
                parameters, self.DEPTH_GROUNDWATER[0], context
            )
            density_sat = self.parameterAsDouble(
                parameters, self.SOIL_DENSITY[0], context
            )
            ocr_value = self.parameterAsDouble(parameters, self.OCR[0], context)
            porewp_red = self.parameterAsInt(
                parameters, self.POREPRESSURE_REDUCTION[0], context
            )
            janbu_ref_stress = self.parameterAsInt(
                parameters, self.JANBU_REF_STRESS[0], context
            )
            janbu_const = self.parameterAsInt(
                parameters, self.JANBU_CONSTANT[0], context
            )
            janbu_m = self.parameterAsInt(
                parameters, self.JANBU_COMP_MODULUS[0], context
            )
            consolidation_time = self.parameterAsInt(
                parameters, self.CONSOLIDATION_TIME[0], context
            )

        else:
            path_source_raster_rock_surface = None
            pw_reduction_curve = None
            dry_crust_thk = None
            dep_groundwater = None
            density_sat = None
            ocr_value = None
            porewp_red = None
            janbu_ref_stress = None
            janbu_const = None
            janbu_m = None
            consolidation_time = None

        if bVulnerability:
            self.logger.info("PROCESS - ######## VULNERABILITY ########")
            self.logger.info("PROCESS - Defining vulnerability input")
            foundation_field = self.parameterAsString(
                parameters, self.FILED_NAME_BUILDING_FOUNDATION[0], context
            )
            self.logger.info(
                f"PROCESS - Foundation: {foundation_field} Type: {type(foundation_field)}"
            )

            structure_field = self.parameterAsString(
                parameters, self.FILED_NAME_BUILDING_STRUCTURE[0], context
            )
            self.logger.info(
                f"PROCESS - Structure: {structure_field} Type: {type(structure_field)}"
            )

            status_field = self.parameterAsString(
                parameters, self.FILED_NAME_BUILDING_STATUS[0], context
            )
            self.logger.info(
                f"PROCESS - Condition: {status_field} Type: {type(status_field)}"
            )

        else:
            foundation_field = None
            structure_field = None
            status_field = None

        #################  LOG PROJECTIONS #################
        feedback.pushInfo(
            f"PROCESS - CRS BUILDINGS-vector: {source_building_poly.crs().postgisSrid()}"
        )
        feedback.pushInfo(
            f"PROCESS - CRS EXCAVATION-vector: {source_excavation_poly.crs().postgisSrid()}"
        )
        if source_raster_rock_surface is not None:
            feedback.pushInfo(
                f"PROCESS - CRS DTB-raster: {source_raster_rock_surface.crs().postgisSrid()}"
            )

        ###### FEEDBACK ALL PARAMETERS #########
        feedback.pushInfo("PROCESS - Running mainBegrensSkade_Excavation...")
        self.logger.info("PROCESS - Running mainBegrensSkade_Excavation...")
        feedback.pushInfo(f"PROCESS - Param: buildingsFN = {path_source_building_poly}")
        feedback.pushInfo(
            f"PROCESS - Param: excavationJson = {source_excavation_poly_as_json.keys()}"
        )
        feedback.pushInfo(f"PROCESS - Param: Output folder = {output_folder}")
        feedback.pushInfo(f"PROCESS - Param: feature_name = {self.feature_name}")
        feedback.pushInfo(f"PROCESS - Param: output_proj = {output_srid}")
        feedback.pushInfo(f"PROCESS - Param: bShortterm = {bShortterm}")
        feedback.pushInfo(f"PROCESS - Param: excavation_depth = {excavation_depth}")
        feedback.pushInfo(f"PROCESS - Param: short_term_curve = {short_term_curve}")
        feedback.pushInfo(f"PROCESS - Param: bLongterm = {bLongterm}")
        feedback.pushInfo(
            f"PROCESS - Param: dtb_raster = {path_source_raster_rock_surface}"
        )
        feedback.pushInfo(f"PROCESS - Param: pw_reduction_curve = {pw_reduction_curve}")
        feedback.pushInfo(f"PROCESS - Param: dry_crust_thk = {dry_crust_thk}")
        feedback.pushInfo(f"PROCESS - Param: dep_groundwater = {dep_groundwater}")
        feedback.pushInfo(f"PROCESS - Param: density_sat = {density_sat}")
        feedback.pushInfo(f"PROCESS - Param: OCR = {ocr_value}")
        feedback.pushInfo(f"PROCESS - Param: porewp_red = {porewp_red}")
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
            output_shapefiles = mainBegrensSkade_Excavation(
                logger=self.logger,
                buildingsFN=str(path_source_building_poly),
                excavationJson=source_excavation_poly_as_json,
                output_ws=output_folder,
                feature_name=self.feature_name,
                output_proj=output_srid,
                bShortterm=bShortterm,
                excavation_depth=excavation_depth,
                short_term_curve=short_term_curve,
                bLongterm=bLongterm,
                dtb_raster=str(path_source_raster_rock_surface),
                pw_reduction_curve=pw_reduction_curve,
                dry_crust_thk=dry_crust_thk,
                dep_groundwater=dep_groundwater,
                density_sat=density_sat,
                OCR=ocr_value,
                porewp_red=porewp_red,
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
        feedback.setProgress(80)
        self.logger.info(f"PROCESS - OUTPUT BUILDINGS: {output_shapefiles[0]}")
        self.logger.info(f"PROCESS - OUTPUT WALL: {output_shapefiles[1]}")
        self.logger.info(f"PROCESS - OUTPUT CORNER: {output_shapefiles[2]}")
        feedback.pushInfo("PROCESS - Finished with processing!")

        # Path to the "styles" directory
        self.styles_dir_path = Path(__file__).resolve().parent.parent / "styles"
        self.logger.info(f"RESULTS - Styles directory path: {self.styles_dir_path}")

        self.layers_info = {
            "CORNERS-SETTLEMENT": {
                "shape_path": output_shapefiles[2],
                "style_name": "CORNERS-SETTLMENT_mm.qml",
            },
            "WALLS-ANGLE": {
                "shape_path": output_shapefiles[1],
                "style_name": "WALL-ANGLE.qml",
            },
            "BUILDING-TOTAL-SETTLMENT": {
                "shape_path": output_shapefiles[0],
                "style_name": "BUILDING-TOTAL-SETTLMENT_sv_tot.qml",
            },
            "BUILDING-TOTAL-ANGLE": {
                "shape_path": output_shapefiles[0],
                "style_name": "BUILDING-TOTAL-ANGLE_max_angle.qml",
            },
        }
        if bVulnerability:
            self.layers_info.update(
                {
                    "BUILDING-RISK-SETTLMENT": {
                        "shape_path": output_shapefiles[0],
                        "style_name": "BUILDING-TOTAL-RISK-SELLMENT_risk_tots.qml",
                    },
                    "BUILDING-TOTAL-ANGLE": {
                        "shape_path": output_shapefiles[0],
                        "style_name": "BUILDING-TOTAL-RISK-ANGLE_risk_angle.qml",
                    },
                }
            )

        feedback.setProgress(90)
        feedback.pushInfo("PROCESS - Finished processing!")
        # Return the results of the algorithm.
        return {
            self.OUTPUT_BUILDING: output_shapefiles[0],
            self.OUTPUT_WALL: output_shapefiles[1],
            self.OUTPUT_CORNER: output_shapefiles[2],
        }

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
            self.layers_info,
            self.feature_name,
            self.styles_dir_path,
            self.logger,
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
