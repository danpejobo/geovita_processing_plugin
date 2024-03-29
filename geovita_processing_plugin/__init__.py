# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeovitaProcessingPlugin
                                 A QGIS plugin
 This plugin adds different geovita processing plugins
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-03-02
        copyright            : (C) 2022 by DPE
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
 This script initializes the plugin, making it known to QGIS.
"""

__author__ = 'DPE'
__date__ = '2024-01-17'
__copyright__ = '(C) 2024 by DPE'

__version__ = "3.1.1"

import sys
from pathlib import Path


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GeovitaProcessingPlugin class from file GeovitaProcessingPlugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    # Directory of the current file (__init__.py)
    plugin_dir = Path(__file__).parent

    # Add the plugin directory to sys.path if not already there
    if str(plugin_dir) not in sys.path:
        sys.path.append(str(plugin_dir))

    # If you need to add the submodule directory to sys.path
    submodule_dir = plugin_dir / "REMEDY_GIS_RiskTool"
    if str(submodule_dir) not in sys.path:
        sys.path.append(str(submodule_dir))

    # The styles are provided in a styles.zip archive. 
    # It is neccessary to extract them the first time the plugin is loaded
    styles_dir = plugin_dir / "styles"
    if not styles_dir.is_dir():
        import zipfile
        import os
        # Ensure the styles directory exists
        # styles_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(plugin_dir / 'styles.zip', 'r') as zip_ref:
            zip_ref.extractall(plugin_dir)
        os.remove(plugin_dir / 'styles.zip')

    # Now you can import your main plugin class
    from .geovita_processing_plugin import GeovitaProcessingPluginPlugin
    return GeovitaProcessingPluginPlugin(iface, __version__)