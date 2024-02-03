from pathlib import Path
import unittest
from qgis.core import QgsApplication, QgsVectorLayer, QgsRasterLayer, QgsProcessingContext, QgsProcessingFeedback, QgsCoordinateReferenceSystem
from qgis.analysis import QgsNativeAlgorithms
from qgis.PyQt.QtCore import QVariant
from qgis.utils import plugins

from .. algorithms.BegrensSkadeExcavation import BegrensSkadeExcavation

class TestBegrensSkadeExcavationAlgorithm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize QGIS Application for testing
        QgsApplication.initQgis()
        # Register algorithms
        QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    def setUp(self):
        self.algorithm = BegrensSkadeExcavation()
        
        # Use pathlib to get the current directory (where this test file resides)
        current_dir = Path(__file__).parent
        # Define the path to the data directory relative to this file
        data_dir = current_dir / 'data'
        
        # Construct paths to your test datasets within the data directory
        building_layer_path = data_dir / 'bygninger.shp'
        excavation_layer_path = data_dir / 'byggegrop.shp'
        raster_rock_surface_path = data_dir / 'DTB-dummy-25833-clip.tif'

        # Assuming these layers exist for testing purposes
        self.building_layer = QgsVectorLayer(str(building_layer_path), 'test_building', 'ogr')
        self.excavation_layer = QgsVectorLayer(str(excavation_layer_path), 'test_excavation', 'ogr')
        self.raster_rock_surface_layer = QgsRasterLayer(str(raster_rock_surface_path), 'test_raster_rock_surface')

        # Ensure layers are valid
        self.assertTrue(self.building_layer.isValid(), "Building layer failed to load.")
        self.assertTrue(self.excavation_layer.isValid(), "Excavation layer failed to load.")
        self.assertTrue(self.raster_rock_surface_layer.isValid(), "Raster rock surface layer failed to load.")
        
        #Output CRS
        self.out_crs = QgsCoordinateReferenceSystem('EPSG:25832')
        self.assertTrue(self.out_crs.isValid(), "OUTPUT CRS is invalid!")

        # Set parameters
        self.params = {
            self.algorithm.INPUT_BUILDING_POLY: self.building_layer,
            self.algorithm.INPUT_EXCAVATION_POLY: self.excavation_layer,
            self.algorithm.OUTPUT_FOLDER: str(data_dir),
            self.algorithm.OUTPUT_CRS: self.out_crs,
            self.algorithm.SHORT_TERM_SETTLEMENT[0]: True,
            self.algorithm.EXCAVATION_DEPTH[0]: 10.0,
            self.algorithm.SETTLEMENT_ENUM[0]: "2 % av byggegropdybde",
            self.algorithm.LONG_TERM_SETTLEMENT[0]: False,
            self.algorithm.RASTER_ROCK_SURFACE[0]: self.raster_rock_surface_layer,
            self.algorithm.POREPRESSURE_ENUM[0]: "Middels poretrykksreduksjon",
            self.algorithm.POREPRESSURE_REDUCTION[0]: 50,
            self.algorithm.DRY_CRUST_THICKNESS[0]: 2.0,
            self.algorithm.DEPTH_GROUNDWATER[0]: 3.5,
            self.algorithm.SOIL_DENSITY[0]: 18.5,
            self.algorithm.OCR[0]: 1.2,
            self.algorithm.JANBU_REF_STRESS[0]: 100,
            self.algorithm.JANBU_CONSTANT[0]: 0.02,
            self.algorithm.JANBU_COMP_MODULUS[0]: 15,
            self.algorithm.CONSOLIDATION_TIME[0]: 10,
            self.algorithm.VULNERABILITY_ANALYSIS[0]: False,
            self.algorithm.FILED_NAME_BUILDING_FOUNDATION[0]: 'Foundation',  # Field name
            self.algorithm.FILED_NAME_BUILDING_STRUCTURE[0]: 'Structure',  # Field name
            self.algorithm.FILED_NAME_BUILDING_STATUS[0]: 'Condition',  # Field name
            self.algorithm.INTERMEDIATE_LAYERS[0]: False,
            self.algorithm.OUTPUT_FEATURE_NAME: 'test_output-exca-all'
        }

    def test_algorithm_execution(self):
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()
        
        try:
            results = self.algorithm.run(self.params, context, feedback)
            
            # Assuming you want to check that the output files exist
            expected_outputs = ['OUTPUT_BUILDING', 'OUTPUT_CORNER', 'OUTPUT_WALL']
            for output_key in expected_outputs:
                self.assertIn(output_key, results)
                output_path = results[output_key]
                self.assertTrue(Path(output_path).exists(), f"{output_key} output file does not exist: {output_path}")
        except Exception as e:
            # Log the exception or do additional cleanup here
            print(f"Error executing algorithm: {e}")
            # Make sure to fail the test if an exception is caught
            self.fail(f"Algorithm execution raised an exception: {e}")
            
        # Validate the results
        #self.assertIn(self.algorithm.OUTPUT_BUILDING, results)
        #self.assertIn(self.algorithm.OUTPUT_WALL, results)
        #self.assertIn(self.algorithm.OUTPUT_CORNER, results)

        # Further checks can be added here to inspect the contents of the output shapefiles

    @classmethod
    def tearDownClass(cls):
        QgsApplication.exitQgis()

if __name__ == '__main__':
    unittest.main()
