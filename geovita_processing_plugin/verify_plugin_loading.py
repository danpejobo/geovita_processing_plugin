# verify_plugin_loading.py

from qgis.core import QgsApplication

# Initialize QGIS Application without GUI
QgsApplication.setPrefixPath("/usr", True)
app = QgsApplication([], False)
app.initQgis()

# Replace 'your_plugin' with the ID of your plugin
plugin_id = 'geovita_processing_plugin'

# Check if the plugin is loaded
is_plugin_loaded = plugin_id in QgsApplication.pluginRegistry().pluginIds()

if is_plugin_loaded:
    print(f"Plugin '{plugin_id}' is loaded.")
else:
    print(f"Plugin '{plugin_id}' is NOT loaded.")
    app.exitQgis()
    exit(1)  # Exit with error status if the plugin is not loaded

# Clean up
app.exitQgis()
