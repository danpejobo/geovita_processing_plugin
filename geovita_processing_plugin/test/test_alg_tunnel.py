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
)

import logging
from pathlib import Path

from geovita_processing_plugin.geovita_processing_plugin_provider import (
    GeovitaProcessingPluginProvider,
)

# Set up logging at the beginning of your test file
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestBegrensSkadeTunnel(unittest.TestCase):
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
        self.tunnel_layer_path = self.data_dir / "tunnel.shp"
        self.raster_rock_surface_path = self.data_dir / "DTB-dummy-25833-clip.tif"

        # Assuming these layers exist for testing purposes
        self.building_layer = QgsVectorLayer(
            str(self.building_layer_path), "test_bygninger", "ogr"
        )
        self.tunnel_layer = QgsVectorLayer(
            str(self.tunnel_layer_path), "test_tunnel", "ogr"
        )
        self.raster_rock_surface_layer = QgsRasterLayer(
            str(self.raster_rock_surface_path), "test_DTB-dummy-25833-clip"
        )

        # Ensure layers are valid
        self.assertTrue(self.building_layer.isValid(), "Building layer failed to load.")
        self.assertTrue(self.tunnel_layer.isValid(), "Tunnel layer failed to load.")
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
            "INPUT_TUNNEL_POLY": self.tunnel_layer,
            "OUTPUT_FOLDER": str(self.output_data_dir),
            "OUTPUT_CRS": self.out_crs,
            "SHORT_TERM_SETTLEMENT": True,
            "TUNNEL_DEPTH": 10.0,
            "TUNNEL_DIAM": 9.5,
            "VOLUME_LOSS": 2,
            "TROUGH_WIDTH": 0.5,
            "LONG_TERM_SETTLEMENT": True,
            "RASTER_ROCK_SURFACE": self.raster_rock_surface_layer,
            "POREPRESSURE_ENUM": 1,  # index
            "TUNNEL_LEAKAGE": 10,
            "POREPRESSURE_REDUCTION": 50,  # only used if POREPRESSURE_ENUM = 3
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
            "OUTPUT_FEATURE_NAME": "test_output-tunnel-all",
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
        """Test executing the BegrensSkadeTunnel algorithm with the default set of all parameters."""

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run(
            "geovita:begrensskadetunnel",
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
        """Test executing the BegrensSkadeTunnel algorithm with short term parameters"""
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        params_short = self.params.copy()
        params_short["LONG_TERM_SETTLEMENT"] = False
        results = processing.run(
            "geovita:begrensskadetunnel",
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
        """Test executing the BegrensSkadeTunnel algorithm with long term parameters"""
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        params_long = self.params.copy()
        params_long["SHORT_TERM_SETTLEMENT"] = False
        results = processing.run(
            "geovita:begrensskadetunnel",
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


if __name__ == "__main__":
    unittest.main()
