import pytest
from qgis.core import QgsApplication
import os
import sys

# Legg til prosjekt-roten OG submodule-mappen i sys.path
# slik at importer som 'import geovita_processing_plugin' og 'import Utils' fungerer
project_root = os.path.abspath(os.path.dirname(__file__))
submodule_path = os.path.join(project_root, "geovita_processing_plugin", "REMEDY_GIS_RiskTool")

sys.path.insert(0, project_root)
sys.path.insert(0, submodule_path)

@pytest.fixture(scope="session", autouse=True)
def init_qgis_processing(qgis_app):
    """Initialiserer QGIS Processing framework og registrerer plugin-provider."""
    
    print("Initializing QGIS Processing Framework...")
    try:
        from processing.core.Processing import Processing
        Processing.initialize()
        print("Processing Framework Initialized.")
    except ImportError as e:
        print(f"Could not import Processing: {e}")
        pytest.skip("Failed to import QGIS Processing framework")

    print("Registering Geovita provider...")
    try:
        # Nå som prosjekt-roten er i sys.path, kan vi importere den direkte
        from geovita_processing_plugin.geovita_processing_plugin_provider import Geovita_processing_pluginProvider
        provider = Geovita_processing_pluginProvider()
        
        if QgsApplication.processingRegistry().addProvider(provider):
            print(f"Successfully added provider: {provider.id()}")
        else:
            print("Failed to add provider.")
    except ImportError as e:
        print(f"Could not import Geovita provider: {e}")
        pytest.skip("Failed to import Geovita provider")

    yield

    # Nedrigging
    print("Deinitializing Processing Framework...")
    # Vi må sjekke om 'provider' ble definert i tilfelle importen feilet
    if 'provider' in locals() and provider:
        QgsApplication.processingRegistry().removeProvider(provider.id())
    Processing.deinitialize()
