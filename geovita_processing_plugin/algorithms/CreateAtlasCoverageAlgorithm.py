# -*- coding: utf-8 -*-

import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink,
    QgsProperty,
    QgsProcessingException,
    QgsWkbTypes # Import WkbTypes
)
import processing

from .base_algorithm import GvBaseProcessingAlgorithms

class CreateAtlasCoverageAlgorithm(GvBaseProcessingAlgorithms):
    """
    Creates atlas coverage points and polygons from a centerline.
    
    This algorithm takes a line layer and layout parameters
    to generate a point layer for atlas control and a polygon
    layer representing the coverage of each atlas page.
    """

    # --- Define parameter and output names ---
    INPUT_LINE = 'INPUT_LINE'
    INPUT_SCALE = 'INPUT_SCALE'
    INPUT_PAPER_LONG_MM = 'INPUT_PAPER_LONG_MM'
    INPUT_PAPER_SHORT_MM = 'INPUT_PAPER_SHORT_MM'
    INPUT_OVERLAP = 'INPUT_OVERLAP'
    
    OUTPUT_POINTS = 'OUTPUT_POINTS'
    OUTPUT_POLYGONS = 'OUTPUT_POLYGONS'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CreateAtlasCoverageAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name.
        """
        return 'create_atlas_coverage'

    def displayName(self):
        """
        Returns the human-readable name.
        """
        return self.tr('Create Atlas Coverage')

    def group(self):
        """
        Returns the group name.
        """
        return self.tr('Geovita') # Or your preferred group name

    def groupId(self):
        """
        Returns the group ID.
        """
        return 'geovita' # Must match your provider ID
        
    def iconPath(self):
        """
        Sets the icon for the algorithm.
        """
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'icons', 'atlas.png')
        if not os.path.exists(icon_path):
            # Fallback to the main plugin icon if 'atlas.png' doesn't exist
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'icons', 'geovita.ico')
        return icon_path


    def shortHelpString(self):
        """
        Returns a brief description for the algorithm's help panel.
        """
        return self.tr('Generates atlas control points and polygon coverage '
                       'along a line based on paper size, scale, and overlap.\n\n'
                       'The "long axis" of the paper will be aligned parallel to the line.')

    def initAlgorithm(self, config=None):
        """
        Defines the inputs and outputs.
        """

        # --- Inputs ---
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT_LINE,
                self.tr('Input Centerline'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        param_line = self.parameterDefinition(self.INPUT_LINE)
        param_line.setHelp(self.tr('The road or rail line to follow.'))


        param_scale = QgsProcessingParameterNumber(
            self.INPUT_SCALE,
            self.tr('Map Scale (e.g., 1000)'),
            QgsProcessingParameterNumber.Integer,
            defaultValue=1000
        )
        param_scale.setHelp(self.tr('Enter the denominator of the map scale (e.g., 1000 for 1:1000).'))
        self.addParameter(param_scale)

        param_long = QgsProcessingParameterNumber(
            self.INPUT_PAPER_LONG_MM,
            self.tr('Paper Long Axis (Usable mm)'),
            QgsProcessingParameterNumber.Double,
            defaultValue=410.0
        )
        param_long.setHelp(self.tr('The dimension of the paper you want aligned parallel to the road (in millimeters).\n\nExample: For a 420mm A3 sheet with 5mm margins, use 410.'))
        self.addParameter(param_long)
        
        param_short = QgsProcessingParameterNumber(
            self.INPUT_PAPER_SHORT_MM,
            self.tr('Paper Short Axis (Usable mm)'),
            QgsProcessingParameterNumber.Double,
            defaultValue=287.0
        )
        param_short.setHelp(self.tr('The dimension of the paper perpendicular to the road (in millimeters).\n\Example: For a 297mm A3 sheet with 5mm margins, use 287.'))
        self.addParameter(param_short)

        param_overlap = QgsProcessingParameterNumber(
            self.INPUT_OVERLAP,
            self.tr('Overlap (in meters)'),
            QgsProcessingParameterNumber.Double,
            defaultValue=50.0
        )
        param_overlap.setHelp(self.tr('The real-world overlap distance between atlas pages (in meters).'))
        self.addParameter(param_overlap)

        # --- Outputs ---
        
        param_out_pts = QgsProcessingParameterFeatureSink(
            self.OUTPUT_POINTS,
            self.tr('Atlas Points')
        )
        param_out_pts.setHelp(self.tr('Output point layer to be used as the atlas coverage layer. Contains the "angle" field for rotation.'))
        self.addParameter(param_out_pts)

        param_out_poly = QgsProcessingParameterFeatureSink(
            self.OUTPUT_POLYGONS,
            self.tr('Atlas Coverage Polygons')
        )
        param_out_poly.setHelp(self.tr('Output polygon layer showing the footprint of each atlas page. Useful for an index map.'))
        self.addParameter(param_out_poly)


    def processAlgorithm(self, parameters, context, feedback):
        """
        The main processing logic.
        """
        
        # --- 1. Get Inputs ---
        source_line = self.parameterAsSource(parameters, self.INPUT_LINE, context)
        scale = self.parameterAsDouble(parameters, self.INPUT_SCALE, context)
        paper_long_mm = self.parameterAsDouble(parameters, self.INPUT_PAPER_LONG_MM, context)
        paper_short_mm = self.parameterAsDouble(parameters, self.INPUT_PAPER_SHORT_MM, context)
        overlap = self.parameterAsDouble(parameters, self.INPUT_OVERLAP, context)
        
        # Check for valid inputs
        if not source_line:
            raise QgsProcessingException(self.tr('Invalid input layer. Please select a line layer.'))

        # --- 2. Run Calculations ---
        real_long_m = (paper_long_mm * scale) / 1000.0
        real_short_m = (paper_short_mm * scale) / 1000.0
        step_distance = real_long_m - overlap

        feedback.pushInfo(self.tr(f'Real-world page size (LxW): {real_long_m}m x {real_short_m}m'))
        feedback.pushInfo(self.tr(f'Point step distance (with overlap): {step_distance}m'))

        if step_distance <= 0:
            raise QgsProcessingException(self.tr('Overlap ({0}m) is larger than or equal to the real-world long axis ({1}m). Please reduce overlap or check paper size.').format(overlap, real_long_m))

        if feedback.isCanceled():
            return {}

        # --- 3. Run "Points along geometry" ---
        feedback.pushInfo(self.tr('Generating points along line...'))
        
        # If input is 3D (25D), we must make sure the output is 2D for the atlas
        # This removes the Z and M values from the geometry
        force_2d_result = processing.run(
            'native:dropmzvalues',
            {
                'INPUT': parameters[self.INPUT_LINE],
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        line_2d_layer = context.takeResultLayer(force_2d_result['OUTPUT'])

        points_result = processing.run(
            'native:pointsalonglines',
            {
                'INPUT': line_2d_layer, # Use the 2D line
                'DISTANCE': step_distance,
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )
        
        if feedback.isCanceled():
            return {}
            
        points_layer = context.takeResultLayer(points_result['OUTPUT'])
        
        if points_layer.featureCount() == 0:
            feedback.pushWarning(self.tr('No points were created. The input line might be shorter than the calculated step distance.'))
            return {self.OUTPUT_POINTS: None, self.OUTPUT_POLYGONS: None}
        
        # --- 4. Define POINTS Sink and Add Features ---
        #
        # *** THIS IS THE FIRST CORRECTED BLOCK ***
        # The argument order is (fields, wkbType, crs)
        #
        (sink_points, dest_id_points) = self.parameterAsSink(
            parameters, self.OUTPUT_POINTS, context,
            points_layer.fields(),   # Argument 4: Fields
            points_layer.wkbType(),  # Argument 5: WKB Type
            points_layer.crs()       # Argument 6: CRS
        )
        sink_points.addFeatures(points_layer.getFeatures())


        # --- 5. Run "Rectangles, Ovals, Diamonds" ---
        feedback.pushInfo(self.tr('Creating coverage polygons...'))
        polygons_result = processing.run(
            'native:rectanglesovalsdiamonds',
            {
                'INPUT': points_layer, # Use the memory layer
                'SHAPE': 0,  # 0 = Rectangle
                'WIDTH': real_short_m, # Short side is the "Width"
                'HEIGHT': real_long_m, # Long side is the "Height"
                'ROTATION': QgsProperty.fromField('angle'), # Use data-defined override
                'OUTPUT': 'memory:'
            },
            context=context,
            feedback=feedback,
            is_child_algorithm=True
        )

        if feedback.isCanceled():
            return {}
            
        polygons_layer = context.takeResultLayer(polygons_result['OUTPUT'])
        
        # --- 6. Define POLYGONS Sink and Add Features ---
        #
        # *** THIS IS THE SECOND CORRECTED BLOCK ***
        # The argument order is (fields, wkbType, crs)
        #
        (sink_polygons, dest_id_polygons) = self.parameterAsSink(
            parameters, self.OUTPUT_POLYGONS, context,
            polygons_layer.fields(),  # Argument 4: Fields
            polygons_layer.wkbType(), # Argument 5: WKB Type
            polygons_layer.crs()      # Argument 6: CRS
        )
        sink_polygons.addFeatures(polygons_layer.getFeatures())


        # --- 7. Return Outputs ---
        feedback.pushInfo(self.tr('Atlas coverage created successfully.'))
        return {
            self.OUTPUT_POINTS: dest_id_points,
            self.OUTPUT_POLYGONS: dest_id_polygons
        }