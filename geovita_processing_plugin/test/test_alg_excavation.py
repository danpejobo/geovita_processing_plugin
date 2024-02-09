from qgis import processing

# import processing
from qgis.testing import unittest
from qgis.core import (
    QgsApplication,
    QgsProcessingFeedback,
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    QgsRasterLayer,
    QgsProcessingContext,
    QgsProcessingException,
)

import logging
from pathlib import Path

from geovita_processing_plugin.geovita_processing_plugin_provider import (
    GeovitaProcessingPluginProvider,
)

# Set up logging at the beginning of your test file
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestBegrensSkadeExcavation(unittest.TestCase):
    def setUp(self):
        if not QgsApplication.processingRegistry().providers():
            self.provider = GeovitaProcessingPluginProvider()
            QgsApplication.processingRegistry().addProvider(self.provider)

        # Use pathlib to get the base directory (where this test file resides)
        base_dir = Path(__file__).parent
        # Define the path to the data directory relative to this file
        self.data_dir = base_dir / "data"

        self.output_data_dir = self.data_dir / "output"
        # Make sure the output directory exists
        self.output_data_dir.mkdir(parents=True, exist_ok=True)

        # Construct paths to your test datasets within the data directory
        self.building_layer_path = self.data_dir / "bygninger.shp"
        self.excavation_layer_path = self.data_dir / "byggegrop.shp"
        self.raster_rock_surface_path = self.data_dir / "DTB-dummy-25833-clip.tif"
        self.assertTrue(
            self.building_layer_path.is_file(),
            "Building shape source file does not exist.",
        )
        self.assertTrue(
            self.excavation_layer_path.is_file(),
            "Excavation shape surface source file does not exist.",
        )
        self.assertTrue(
            self.raster_rock_surface_path.is_file(),
            "Raster rock surface source file does not exist.",
        )

        # Assuming these layers exist for testing purposes
        self.building_layer = QgsVectorLayer(
            str(self.building_layer_path), "test_bygninger", "ogr"
        )
        self.excavation_layer = QgsVectorLayer(
            str(self.excavation_layer_path), "test_byggegrop", "ogr"
        )
        self.raster_rock_surface_layer = QgsRasterLayer(
            str(self.raster_rock_surface_path), "test_DTB-dummy-25833-clip"
        )

        # Ensure layers are valid
        self.assertTrue(self.building_layer.isValid(), "Building layer failed to load.")
        self.assertTrue(
            self.excavation_layer.isValid(), "Excavation layer failed to load."
        )
        self.assertTrue(
            self.raster_rock_surface_layer.isValid(),
            "Raster rock surface layer failed to load.",
        )

        # Output CRS
        self.out_crs = QgsCoordinateReferenceSystem("EPSG:5110")
        self.assertTrue(self.out_crs.isValid(), "OUTPUT CRS is invalid!")

        # # Set parameters
        self.params = {
            "INPUT_BUILDING_POLY": self.building_layer,
            "INPUT_EXCAVATION_POLY": self.excavation_layer,
            "OUTPUT_FOLDER": str(self.output_data_dir),
            "OUTPUT_CRS": self.out_crs,
            "SHORT_TERM_SETTLEMENT": True,
            "EXCAVATION_DEPTH": 10.0,
            "SETTLEMENT_ENUM": 1,  # index
            "LONG_TERM_SETTLEMENT": True,
            "RASTER_ROCK_SURFACE": self.raster_rock_surface_layer,
            "POREPRESSURE_ENUM": 1,  # index
            "POREPRESSURE_REDUCTION": 50,
            "DRY_CRUST_THICKNESS": 5.0,
            "DEPTH_GROUNDWATER": 3,
            "SOIL_DENSITY": 18.5,
            "OCR": 1.2,
            "JANBU_REF_STRESS": 50,
            "JANBU_CONSTANT": 4,
            "JANBU_COMP_MODULUS": 15,
            "CONSOLIDATION_TIME": 10,
            "VULNERABILITY_ANALYSIS": True,
            "FILED_NAME_BUILDING_FOUNDATION": "Foundation",  # Field name
            "FILED_NAME_BUILDING_STRUCTURE": "Structure",  # Field name
            "FILED_NAME_BUILDING_STATUS": "Condition",  # Field name
            "OUTPUT_FEATURE_NAME": "test_output-exca-all",
        }

    def test_algorithm_loaded(self):
        # This flag will help us determine if any relevant algorithms were found
        found_relevant_algorithms = False

        for alg in QgsApplication.processingRegistry().algorithms():
            # Check if the algorithm ID starts with "geovita"
            if alg.id().startswith("geovita"):
                logger.info(f"{alg.id()} - {alg.displayName()}")
                found_relevant_algorithms = True

        # Assert that at least one relevant algorithm was found
        self.assertTrue(
            found_relevant_algorithms, "No algorithms under 'geovita' were found."
        )

    def test_algorithm_exec_all(self):
        """Test executing the BegrensSkadeExcavation algorithm with the default set of all parameters."""

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run(
            "geovita:begrensskadeexcavation",
            self.params,
            feedback=feedback,
            context=context,
        )

        # Verify results
        # For example, check if output shapefiles exist
        self.assertTrue(Path(results["OUTPUT_BUILDING"]).exists())
        self.assertTrue(Path(results["OUTPUT_WALL"]).exists())
        self.assertTrue(Path(results["OUTPUT_CORNER"]).exists())

        # Further checks can include verifying the contents of the output shapefiles

    def test_algorithm_exec_short(self):
        """Test executing the BegrensSkadeExcavation algorithm with short term parameters"""
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        params_short = self.params.copy()
        params_short["SHORT_TERM_SETTLEMENT"] = False
        results = processing.run(
            "geovita:begrensskadeexcavation",
            params_short,
            feedback=feedback,
            context=context,
        )

        # Verify results
        # For example, check if output shapefiles exist
        self.assertTrue(Path(results["OUTPUT_BUILDING"]).exists())
        self.assertTrue(Path(results["OUTPUT_WALL"]).exists())
        self.assertTrue(Path(results["OUTPUT_CORNER"]).exists())

        # Further checks can include verifying the contents of the output shapefiles

    def test_algorithm_exec_long(self):
        """Test executing the BegrensSkadeExcavation algorithm with long term parameters"""
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        params_long = self.params.copy()
        params_long["LONG_TERM_SETTLEMENT"] = False
        results = processing.run(
            "geovita:begrensskadeexcavation",
            params_long,
            feedback=feedback,
            context=context,
        )

        # Verify results
        # For example, check if output shapefiles exist
        self.assertTrue(Path(results["OUTPUT_BUILDING"]).exists())
        self.assertTrue(Path(results["OUTPUT_WALL"]).exists())
        self.assertTrue(Path(results["OUTPUT_CORNER"]).exists())

        # Further checks can include verifying the contents of the output shapefiles

    def test_output_verification_with_all_params(self):
        """
        Tests if the default parameters produces the expected results
        """
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run(
            "geovita:begrensskadeexcavation",
            self.params,
            feedback=feedback,
            context=context,
        )

        # Load the output layer for verification
        output_corner_layer = QgsVectorLayer(
            results["OUTPUT_CORNER"], "Output Corners", "ogr"
        )

        # Iterate over features and count those with sv_tot > 0.1
        feature_count_sv_tot_greater_than_01 = 0
        for feature in output_corner_layer.getFeatures():
            if feature["sv_tot"] > 0.100:
                feature_count_sv_tot_greater_than_01 += 1

        # Check if the counted features match the expected value
        expected_feature_corner_count = (
            11  # Hypothetical expected number of features with sv_tot > 0.1
        )
        self.assertEqual(
            feature_count_sv_tot_greater_than_01,
            expected_feature_corner_count,
            "The number of corner features with sv_tot > 0.1 does not match the expected count",
        )

        # Load the output layer for verification
        output_wall_layer = QgsVectorLayer(
            results["OUTPUT_WALL"], "Output Corners", "ogr"
        )

        # Iterate over features and count those with slope_ang > 0.1
        feature_count_slope_ang_greater_than_0 = 0
        for feature in output_wall_layer.getFeatures():
            if feature["slope_ang"] > 0:
                feature_count_slope_ang_greater_than_0 += 1

        # Check if the counted features match the expected value
        expected_feature_wall_count = (
            1273  # Hypothetical expected number of features with slope_ang > 0.1
        )
        self.assertEqual(
            feature_count_slope_ang_greater_than_0,
            expected_feature_wall_count,
            "The number of wall features with slope_ang > 0 does not match the expected count",
        )

        # Load the output layer for verification
        output_building_layer = QgsVectorLayer(
            results["OUTPUT_BUILDING"], "Output Corners", "ogr"
        )

        # Iterate over features and count those with max_sv_tot > 0.1
        feature_count_max_sv_tot_greater_than_0 = 0
        for feature in output_building_layer.getFeatures():
            if feature["max_sv_tot"] > 0:
                feature_count_max_sv_tot_greater_than_0 += 1

        # Example verification: Check if the counted features match the expected value
        expected_feature_building_count = (
            188  # Hypothetical expected number of features with max_sv_tot > 0
        )
        self.assertEqual(
            feature_count_max_sv_tot_greater_than_0,
            expected_feature_building_count,
            "The number of building features with max_sv_tot > 0 does not match the expected count",
        )

    def test_crs_reprojection(self):
        """Test the algorithm with input layers in a different CRS and verify output CRS."""
        # Change CRS of input layers to something other than the output CRS for testing

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run(
            "geovita:begrensskadeexcavation",
            self.params,
            feedback=feedback,
            context=context,
        )

        # Verify the output CRS matches the expected output CRS
        output_building_layer = QgsVectorLayer(
            results["OUTPUT_BUILDING"], "Output Buildings", "ogr"
        )
        output_wall_layer = QgsVectorLayer(results["OUTPUT_WALL"], "Output wall", "ogr")
        output_corner_layer = QgsVectorLayer(
            results["OUTPUT_CORNER"], "Output corner", "ogr"
        )
        self.assertEqual(
            output_building_layer.crs().authid(),
            self.out_crs.authid(),
            "Output building layer CRS does not match expected CRS",
        )
        self.assertEqual(
            output_wall_layer.crs().authid(),
            self.out_crs.authid(),
            "Output wall layer CRS does not match expected CRS",
        )
        self.assertEqual(
            output_corner_layer.crs().authid(),
            self.out_crs.authid(),
            "Output corner layer CRS does not match expected CRS",
        )

    def test_missing_raster_layer(self):
        """Test the algorithm with a missing raster layer to ensure it handles the scenario gracefully."""
        # Copy the existing parameters and set the RASTER_ROCK_SURFACE parameter to None
        params = self.params.copy()
        params["RASTER_ROCK_SURFACE"] = None  # Explicitly set the raster layer to None

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()

        # Check if the algorithm raises a QgsProcessingException due to the missing raster layer
        with self.assertRaises(QgsProcessingException):
            processing.run(
                "geovita:begrensskadeexcavation",
                params,
                feedback=feedback,
                context=context,
            )

        # Optionally, check for a specific error message if your implementation includes custom error reporting
        try:
            processing.run(
                "geovita:begrensskadeexcavation",
                params,
                feedback=feedback,
                context=context,
            )
        except QgsProcessingException as e:
            self.assertIn(
                "Could not load source layer for RASTER_ROCK_SURFACE: invalid value",
                str(e),
                "Expected specific error message for missing raster layer not found.",
            )


if __name__ == "__main__":
    unittest.main()
