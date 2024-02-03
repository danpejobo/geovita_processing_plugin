from qgis.core import (QgsApplication, QgsProcessingFeedback, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsRasterLayer, QgsProcessingContext)
from qgis.analysis import QgsNativeAlgorithms
from qgis import processing
from qgis.testing import unittest, start_app
from pathlib import Path

start_app()  # Start a QGIS application instance

class TestBegrensSkadeExcavation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize processing and load your plugin."""
        cls.qgis_app = QgsApplication([], False)
        cls.qgis_app.initQgis()
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
        # Optionally, load your plugin here if it's not automatically detected

    def setUp(self):        
        # Use pathlib to get the current directory (where this test file resides)
        current_dir = Path(__file__).parent
        # Define the path to the data directory relative to this file
        data_dir = current_dir / 'data'
        
        # Construct paths to your test datasets within the data directory
        self.building_layer_path = data_dir / 'bygninger.shp'
        self.excavation_layer_path = data_dir / 'byggegrop.shp'
        self.raster_rock_surface_path = data_dir / 'DTB-dummy-25833-clip.tif'

        # Assuming these layers exist for testing purposes
        self.building_layer = QgsVectorLayer(str(self.building_layer_path), 'test_building', 'ogr')
        self.excavation_layer = QgsVectorLayer(str(self.excavation_layer_path), 'test_excavation', 'ogr')
        self.raster_rock_surface_layer = QgsRasterLayer(str(self.raster_rock_surface_path), 'test_raster_rock_surface')

        # Ensure layers are valid
        self.assertTrue(self.building_layer.isValid(), "Building layer failed to load.")
        self.assertTrue(self.excavation_layer.isValid(), "Excavation layer failed to load.")
        self.assertTrue(self.raster_rock_surface_layer.isValid(), "Raster rock surface layer failed to load.")
        
        #Output CRS
        self.out_crs = QgsCoordinateReferenceSystem('EPSG:25832')
        self.assertTrue(self.out_crs.isValid(), "OUTPUT CRS is invalid!")
        
        # # Set parameters
        self.params = {
            'INPUT_BUILDING_POLY': self.building_layer,
            'INPUT_EXCAVATION_POLY': self.excavation_layer,
            'OUTPUT_FOLDER': str(data_dir),
            'OUTPUT_CRS': self.out_crs,
            'SHORT_TERM_SETTLEMENT': True,
            'EXCAVATION_DEPTH': 10.0,
            'SETTLEMENT_ENUM': 1, #index
            'LONG_TERM_SETTLEMENT': False,
            'RASTER_ROCK_SURFACE': self.raster_rock_surface_layer,
            'POREPRESSURE_ENUM': 1, #index
            'POREPRESSURE_REDUCTION': 50,
            'DRY_CRUST_THICKNESS': 2.0,
            'DEPTH_GROUNDWATER': 3.5,
            'SOIL_DENSITY': 18.5,
            'OCR': 1.2,
            'JANBU_REF_STRESS': 100,
            'JANBU_CONSTANT': 0.02,
            'JANBU_COMP_MODULUS': 15,
            'CONSOLIDATION_TIME': 10,
            'VULNERABILITY_ANALYSIS': False,
            'FILED_NAME_BUILDING_FOUNDATION': 'Foundation',  # Field name
            'FILED_NAME_BUILDING_STRUCTURE': 'Structure',  # Field name
            'FILED_NAME_BUILDING_STATUS': 'Condition',  # Field name
            'INTERMEDIATE_LAYERS': False,
            'OUTPUT_FEATURE_NAME': 'test_output-exca-all'
        }

    def test_algorithm_execution(self):
        """Test executing the BegrensSkadeExcavation algorithm with a basic set of parameters."""

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run("geovita:begrensskadeexcavation", self.params, feedback=feedback, context=context)

        # Verify results
        # For example, check if output shapefiles exist
        self.assertTrue(Path(results['OUTPUT_BUILDING']).exists())
        self.assertTrue(Path(results['OUTPUT_WALL']).exists())
        self.assertTrue(Path(results['OUTPUT_CORNER']).exists())

        # Further checks can include verifying the contents of the output shapefiles

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are run."""
        cls.qgis_app.exitQgis()

if __name__ == '__main__':
    unittest.main()