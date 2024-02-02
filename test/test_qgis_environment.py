# coding=utf-8
"""Tests for QGIS functionality.


.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
__author__ = 'tim@linfiniti.com'
__date__ = '20/01/2011'
__copyright__ = ('Copyright 2012, Australia Indonesia Facility for '
                 'Disaster Reduction')

import os
import unittest
from qgis.core import (
    QgsProviderRegistry,
    QgsCoordinateReferenceSystem,
    QgsRasterLayer)

from .utilities import get_qgis_app
QGIS_APP = get_qgis_app()


class QGISTest(unittest.TestCase):
    """Test the QGIS Environment"""

    def test_qgis_environment(self):
        """QGIS environment has the expected providers"""

        r = QgsProviderRegistry.instance()
        self.assertIn('gdal', r.providerList())
        self.assertIn('ogr', r.providerList())
        self.assertIn('postgres', r.providerList())

    def test_projection(self):
        """Test that QGIS properly parses a wkt string.
        """
        crs = QgsCoordinateReferenceSystem()
        wkt = ('GEOGCRS["WGS 84",ENSEMBLE["World Geodetic System 1984 ensemble", MEMBER["World Geodetic System 1984 (Transit)", ID["EPSG",1166]], MEMBER["World Geodetic System 1984 (G730)", ID["EPSG",1152]], MEMBER["World Geodetic System 1984 (G873)", ID["EPSG",1153]], MEMBER["World Geodetic System 1984 (G1150)", ID["EPSG",1154]], MEMBER["World Geodetic System 1984 (G1674)", ID["EPSG",1155]], MEMBER["World Geodetic System 1984 (G1762)", ID["EPSG",1156]], MEMBER["World Geodetic System 1984 (G2139)", ID["EPSG",1309]], ELLIPSOID["WGS 84",6378137,298.257223563,LENGTHUNIT["metre",1,ID["EPSG",9001]],ID["EPSG",7030]], ENSEMBLEACCURACY[2],ID["EPSG",6326]],CS[ellipsoidal,2,ID["EPSG",6422]],AXIS["Geodetic latitude (Lat)",north],AXIS["Geodetic longitude (Lon)",east],ANGLEUNIT["degree",0.0174532925199433,ID["EPSG",9102]],ID["EPSG",4326]]')
        crs.createFromWkt(wkt)
        auth_id = crs.authid()
        expected_auth_id = 'EPSG:4326'
        self.assertEqual(auth_id, expected_auth_id)

        # now test for a loaded layer
        path = os.path.join(os.path.dirname(__file__), 'tenbytenraster.asc')
        title = 'TestRaster'
        layer = QgsRasterLayer(path, title)
        auth_id = layer.crs().authid()
        self.assertEqual(auth_id, expected_auth_id)

if __name__ == '__main__':
    unittest.main()
