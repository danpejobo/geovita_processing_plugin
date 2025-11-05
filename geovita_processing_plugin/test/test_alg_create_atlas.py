# -*- coding: utf-8 -*-

"""
/***************************************************************************
 GeovitaProcessingPlugin - Tests
                              -------------------
        begin                : 2024-06-07
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

from pathlib import Path

from qgis import processing
from qgis.testing import unittest
from qgis.core import (
    QgsApplication,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
)

from geovita_processing_plugin.algorithms.CreateAtlasCoverageAlgorithm import (
    CreateAtlasCoverageAlgorithm,
)
from geovita_processing_plugin.geovita_processing_plugin_provider import (
    GeovitaProcessingPluginProvider,
)


class TestCreateAtlasCoverageAlgorithm(unittest.TestCase):
    def setUp(self):
        registry = QgsApplication.processingRegistry()
        if not registry.providerById("geovita"):
            self.provider = GeovitaProcessingPluginProvider()
            registry.addProvider(self.provider)

        base_dir = Path(__file__).parent
        self.data_dir = base_dir / "data"
        self.centerline_path = self.data_dir / "centerline.shp"
        self.assertTrue(
            self.centerline_path.is_file(),
            "Centerline shape source file does not exist.",
        )

        self.centerline_layer = QgsVectorLayer(
            str(self.centerline_path), "test_centerline", "ogr"
        )
        self.assertTrue(
            self.centerline_layer.isValid(),
            "Centerline layer failed to load.",
        )

        self.default_params = {
            CreateAtlasCoverageAlgorithm.INPUT_LINE: self.centerline_layer,
            CreateAtlasCoverageAlgorithm.INPUT_SCALE: 1000,
            CreateAtlasCoverageAlgorithm.INPUT_PAPER_LONG_MM: 410.0,
            CreateAtlasCoverageAlgorithm.INPUT_PAPER_SHORT_MM: 287.0,
            CreateAtlasCoverageAlgorithm.INPUT_OVERLAP: 50.0,
        }

    def test_algorithm_discoverable(self):
        algorithm = QgsApplication.processingRegistry().algorithmById(
            "geovita:create_atlas_coverage"
        )
        self.assertIsNotNone(
            algorithm,
            "geovita:create_atlas_coverage was not discovered in the processing registry.",
        )

    def test_happy_path_geometry_generation(self):
        params = dict(self.default_params)
        context = QgsProcessingContext()
        feedback = QgsProcessingFeedback()

        results = processing.run(
            "geovita:create_atlas_coverage",
            params,
            context=context,
            feedback=feedback,
        )

        points_result = results.get(CreateAtlasCoverageAlgorithm.OUTPUT_POINTS)
        polygons_result = results.get(CreateAtlasCoverageAlgorithm.OUTPUT_POLYGONS)

        points_layer = context.getMapLayer(points_result) if points_result else None
        polygons_layer = (
            context.getMapLayer(polygons_result) if polygons_result else None
        )

        self.assertIsNotNone(points_layer, "Points layer was not returned.")
        self.assertIsNotNone(polygons_layer, "Polygons layer was not returned.")

        self.assertTrue(points_layer.isValid(), "Points layer is not valid.")
        self.assertTrue(polygons_layer.isValid(), "Polygons layer is not valid.")

        points_count = points_layer.featureCount()
        polygons_count = polygons_layer.featureCount()

        self.assertGreater(points_count, 0, "Points layer contains no features.")
        self.assertGreater(polygons_count, 0, "Polygons layer contains no features.")
        self.assertEqual(
            points_count,
            polygons_count,
            "Points and polygons feature counts do not match.",
        )

        point_field_names = [field.name() for field in points_layer.fields()]
        self.assertIn("angle", point_field_names, "Angle field missing in points layer.")

        real_long_m = (
            self.default_params[CreateAtlasCoverageAlgorithm.INPUT_PAPER_LONG_MM]
            * self.default_params[CreateAtlasCoverageAlgorithm.INPUT_SCALE]
            / 1000.0
        )
        real_short_m = (
            self.default_params[CreateAtlasCoverageAlgorithm.INPUT_PAPER_SHORT_MM]
            * self.default_params[CreateAtlasCoverageAlgorithm.INPUT_SCALE]
            / 1000.0
        )
        expected_area = real_long_m * real_short_m

        first_polygon = next(polygons_layer.getFeatures())
        self.assertAlmostEqual(
            first_polygon.geometry().area(),
            expected_area,
            places=3,
            msg="Output polygon area does not match the expected atlas coverage area.",
        )

    def test_edge_case_overlap_too_large(self):
        params = dict(self.default_params)
        params[CreateAtlasCoverageAlgorithm.INPUT_OVERLAP] = 500.0

        with self.assertRaises(QgsProcessingException):
            processing.run(
                "geovita:create_atlas_coverage",
                params,
                context=QgsProcessingContext(),
                feedback=QgsProcessingFeedback(),
            )

    def test_edge_case_line_too_short(self):
        short_line_layer = QgsVectorLayer("LineString?crs=EPSG:25833", "short_line", "memory")
        provider = short_line_layer.dataProvider()

        feature = QgsFeature()
        feature.setGeometry(
            QgsGeometry.fromPolylineXY(
                [QgsPointXY(0, 0), QgsPointXY(10, 0)]
            )
        )
        provider.addFeature(feature)
        short_line_layer.updateExtents()

        params = dict(self.default_params)
        params[CreateAtlasCoverageAlgorithm.INPUT_LINE] = short_line_layer

        results = processing.run(
            "geovita:create_atlas_coverage",
            params,
            context=QgsProcessingContext(),
            feedback=QgsProcessingFeedback(),
        )

        self.assertEqual(
            results,
            {
                CreateAtlasCoverageAlgorithm.OUTPUT_POINTS: None,
                CreateAtlasCoverageAlgorithm.OUTPUT_POLYGONS: None,
            },
            "Algorithm should return None outputs when the line is too short.",
        )


if __name__ == "__main__":
    unittest.main()
