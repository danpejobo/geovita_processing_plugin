# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GeovitaProcessingPlugin - Tests
                              -------------------
        begin                : 2024-02-09
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
__date__ = "2024.02.09"
__copyright__ = "(C) 2024 by DPE"

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = "$Format:%H$"

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
    QgsPointXY,
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
        self.excavation_layer_path = self.data_dir / "byggegrop.shp"
        self.raster_rock_surface_path = self.data_dir / "DTB-dummy-25833-clip.tif"

        # Assuming these layers exist for testing purposes
        self.excavation_layer = QgsVectorLayer(
            str(self.excavation_layer_path), "test_byggegrop", "ogr"
        )
        self.raster_rock_surface_layer = QgsRasterLayer(
            str(self.raster_rock_surface_path), "test_DTB-dummy-25833-clip"
        )

        # Ensure layers are valid
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
            "INPUT_EXCAVATION_POLY": self.excavation_layer,
            "RASTER_ROCK_SURFACE": self.raster_rock_surface_layer,
            "OUTPUT_FOLDER": str(self.output_data_dir),
            "OUTPUT_FEATURE_NAME": "test_output-impactmap-all",
            "OUTPUT_CRS": self.out_crs,
            "OUTPUT_RESOLUTION": 10,
            "SHORT_TERM_SETTLEMENT": True,
            "EXCAVATION_DEPTH": 10.0,
            "SETTLEMENT_ENUM": 1,  # index
            "CLIPPING_RANGE": 150,
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
        }

        # Define a dictionary of points to test with their expected raster values
        # Format: {"point_name": (x, y, expected_value)}
        self.test_points = {
            "point1": (
                429883.5,
                2323447.6,
                0.106683,
            ),  # Example coordinates and expected value
            "point2": (429896.7, 2323504.7, 0.0896728),
            "point3": (429865.0, 2323425.2, 0.111367),
            "point4": (429864.0, 2323457.4, 0.0725033),
            "point5": (429845.5, 2323466.2, 0.0308721),
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

    def test_algorithm_execution_all(self):
        """Test executing the BegrensSkadeExcavation algorithm with a basic set of parameters."""

        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run(
            "geovita:begrensskadeimpactmap",
            self.params,
            feedback=feedback,
            context=context,
        )

        # Verify results
        # For example, check if output shapefiles exist
        self.assertTrue(Path(results["OUTPUT_FOLDER"]).exists())

        # Further checks can include verifying the contents of the output shapefiles
        # Load the raster and perform additional checks
        output_raster = QgsRasterLayer(results["OUTPUT_FOLDER"], "Output Raster")
        self.assertTrue(output_raster.isValid(), "Output raster layer is not valid.")

    def test_algorithm_exec_long(self):
        """Test executing the BegrensSkadeExcavation algorithm with only long term parameters"""
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        params_long = self.params.copy()
        params_long["SHORT_TERM_SETTLEMENT"] = False
        results = processing.run(
            "geovita:begrensskadeimpactmap",
            params_long,
            feedback=feedback,
            context=context,
        )

        # Verify results
        # For example, check if output shapefiles exist
        self.assertTrue(Path(results["OUTPUT_FOLDER"]).exists())

        # Further checks can include verifying the contents of the output shapefiles

    def test_output_raster_values_at_points(self):
        """
        Test sampling raster values at specific points and compare with expected values.
        """
        feedback = QgsProcessingFeedback()
        context = QgsProcessingContext()
        results = processing.run(
            "geovita:begrensskadeimpactmap",
            self.params,
            feedback=feedback,
            context=context,
        )

        # Load the output layer for verification
        output_layer = QgsRasterLayer(results["OUTPUT_FOLDER"], "Output Corners")

        for point_name, (x, y, expected_value) in self.test_points.items():
            point = QgsPointXY(x, y)
            value, result = output_layer.dataProvider().sample(
                point, 1
            )  # Assuming band 1

            self.assertTrue(result, f"Failed to sample raster at {point_name}")
            self.assertAlmostEqual(
                value,
                expected_value,
                places=5,
                msg=f"Raster value at {point_name} does not match expected value",
            )


if __name__ == "__main__":
    unittest.main()
