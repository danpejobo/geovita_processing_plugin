from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (QgsTask,
                       QgsProject,
                       QgsRasterLayer,
                       QgsVectorLayer,
                       QgsLayerTreeGroup,
                       QgsLayerTreeLayer)

from pathlib import Path
from datetime import datetime

from geovita_processing_plugin.utilities import logger

class AddLayersTask(QgsTask):
    """
    A QGIS task for adding layers (vector or raster) to the QGIS interface.
    This task handles the addition of layers in a background thread and updates
    the GUI in the main thread upon completion.

    Attributes:
        taskCompleted (pyqtSignal): Signal emitted when the task is completed.
        layers_info (list[tuple[str, str, str]]): List of tuples containing layer information (name, path, style).
        group_name (str): The name of the group to which layers are related.
        styles_dir_path (Path): The directory path where style files are located.
        logger (logging.Logger): Logger for logging messages.
        prepared_layers (list[tuple[str, str, str, str]]): Prepared layer information for adding to QGIS.
        completed (bool): Flag indicating whether the task has completed.
    """

    taskCompleted = pyqtSignal(bool)

    def __init__(self, description: str = "Add Layers", layers_info: dict = {}, group_name: str = None, style_dir_path: Path = None, logger: logger.CustomLogger = None) -> None:
        """
        Initializes the AddLayersTask.

        Args:
            description (str): The description of the task.
            layers_info (dict): A dict containing layer information where the layer name is the key (Key: name, {path, style}).
            group_name (str): The name of the group to which layers are related.
            style_dir_path (Path): Path to styles directory
            logger (Logger): Logger for logging messages.
        """
        super().__init__("Add Layers Task", QgsTask.CanCancel)
        self.layers_info = []
        self.group_name = ""
        self.styles_dir_path = None
        self.logger = None
        self.prepared_layers = []  # Initialize prepared layers list
        self.completed = False
    
    def setParameters(self, layers_info, group_name, style_dir_path, logger):
        self.layers_info = layers_info
        self.group_name = group_name
        self.style_dir_path = style_dir_path
        self.logger = logger

    def run(self) -> bool:
        """
         Runs the task. The method that runs when the task is started. Used for non-GUI operations 
         such as data preparation and validation.

        Returns:
            bool: True if preparation is successful, False otherwise.
        """
        for layer_name, info in self.layers_info.items():
            layer_path = info["shape_path"]
            style_name = info["style_name"]
            # Validate file paths
            if not Path(layer_path).is_file():
                self.logger.error(f"@AddLayersTask-run()@ - Layer file not found: {layer_path}")
                return False
            
            # Generate a timestamp string
            timestamp = datetime.now().strftime("_%Y%m%d_%H:%M")
            modified_layer_name = f"{layer_name}{timestamp}"
            
            # Determine layer type without loading it
            # add supported extensions
            raster_ext  = ('.tif', '.tiff')
            # Determine layer type and create the layer object
            if layer_path.endswith(raster_ext):
                layer = QgsRasterLayer(layer_path, modified_layer_name)
            else:
                layer = QgsVectorLayer(layer_path, modified_layer_name, 'ogr')

            if not layer.isValid():
                self.logger.error(f"@AddLayersTask-run()@ - Failed to load layer: {layer_path}")
                return False

            # Store the prepared layer along with its style name
            self.prepared_layers.append((layer, style_name))
            self.logger.info(f"@AddLayersTask-run()@ - Layer prepared for addition: {modified_layer_name}")
        return True

    def finished(self, success: bool) -> None:
        """
        The method that runs when the task is finished. It is executed in the main thread,
        making it safe for GUI operations like adding layers and refreshing the layer tree.

        Args:
            success (bool): Indicates whether the task preparation was successful.
        """
        if success:
            # GUI operations are performed here
            for layer, style_name in self.prepared_layers:
                style_path = self.style_dir_path / style_name
                if not style_path.is_file():
                    self.logger.error(f"@AddLayersTask-run()@ - File not found: {style_path}")
                if not self.add_layer_to_qgis(layer, str(style_path), self.group_name, self.logger):
                    self.logger.error(f"Failed to add layer {layer.name()}")
                    self.taskCompleted.emit(False)
                    return

        self.completed = True
        self.taskCompleted.emit(success)
        
    def add_layer_to_qgis(self, layer: QgsRasterLayer or QgsVectorLayer, style_path: str, group_name: str = None, logger: logger.CustomLogger = None) -> bool:
        """
        Adds a prepared layer to QGIS with a specified style. Optionally adds it to a specified group.

        Args:
            layer (QgsRasterLayer or QgsVectorLayer): The prepared layer to be added.
            style_path (str): Path to the QML style file.
            group_name (str, optional): Name of the group to add the layer to. If None, adds without a group.
            logger (logging.Logger, optional): Logger for logging messages.

        Returns:
            bool: True if the layer is added successfully, False otherwise.
        """
        # Apply the style and trigger refresh of layer
        if Path(style_path).is_file():
            layer.loadNamedStyle(style_path)
            layer.triggerRepaint()

        # Add the layer to the specified group or directly to the project
        if group_name:
            self._add_layer_to_group(layer, group_name, logger)
        else:
            QgsProject.instance().addMapLayer(layer, True) # True - add layer directly to the root
        if logger:
            logger.info(f"@add_layer_to_qgis@ - Layer '{layer.name()}' added to QGIS.")

        return True

    def _add_layer_to_group(self, layer: QgsRasterLayer or QgsVectorLayer, group_name: str, logger: logger.CustomLogger = None) -> None:
        """
        Adds the specified layer to a group in the QGIS project.

        Args:
            layer (QgsRasterLayer or QgsVectorLayer): The layer to add.
            group_name (str): The name of the group.
            logger (logging.Logger): Logger for logging messages.
        """
        root = QgsProject.instance().layerTreeRoot()
        group = root.findGroup(group_name)
        if not group:
            group = QgsLayerTreeGroup(group_name)
            root.insertChildNode(0, group)
            if logger:
                logger.debug(f"@_add_layer_to_group@ - Created new group '{group_name}' and added it to the top of the Layer Tree.")
        else:
            if logger:
                logger.debug(f"@_add_layer_to_group@ - Found existing group '{group_name}'.")

        QgsProject.instance().addMapLayer(layer, False)
        node_layer = QgsLayerTreeLayer(layer)
        group.addChildNode(node_layer)
        # Log layer addition
        if logger:
            logger.debug(f"@_add_layer_to_group@ - Added layer '{layer.name()}' to group '{group_name}'.")

