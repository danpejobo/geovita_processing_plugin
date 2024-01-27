from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import QgsTask

from pathlib import Path

from utils.methodslib import add_layer_to_qgis

class AddLayersTask(QgsTask):
    """
    A QGIS task for adding layers to the QGIS interface. This task handles layer additions 
    in a background thread and updates the GUI in the main thread upon completion.

    Attributes:
        taskCompleted (pyqtSignal): Signal emitted when the task is completed.
        layers_info (list): A list of tuples containing layer information (name, path, style).
        feature_name (str): The name of the feature to which layers are related.
        styles_dir_path (Path): The directory path where style files are located.
        logger (Logger): Logger for logging messages.
        completed (bool): Flag indicating whether the task has completed.
    """

    taskCompleted = pyqtSignal(bool)

    def __init__(self, description, layers_info, feature_name, styles_dir_path, logger):
        """
        Initializes the AddLayersTask.

        Args:
            description (str): The description of the task.
            layers_info (list): A list of tuples containing layer information (name, path, style).
            feature_name (str): The name of the feature to which layers are related.
            styles_dir_path (Path): The directory path where style files are located.
            logger (Logger): Logger for logging messages.
        """
        super().__init__(description, QgsTask.CanCancel)
        self.layers_info = layers_info
        self.feature_name = feature_name
        self.styles_dir_path = styles_dir_path
        self.logger = logger
        self.completed = False

    def run(self):
        """
        The method that runs when the task is started. It should be used for 
        non-GUI operations such as data preparation and validation.

        Returns:
            bool: True if preparation is successful, False otherwise.
        """
        for layer_name, layer_path, style_name in self.layers_info:
            # Validate file paths
            if not Path(layer_path).is_file():
                self.logger.error(f"File not found: {layer_path}")
                return False
            # Log information about the layers to be added
            self.logger.info(f"Preparing to add layer: {layer_name}")
        return True

    def finished(self, success):
        """
        The method that runs when the task is finished. It is executed in the main thread,
        making it safe for GUI operations like adding layers and refreshing the layer tree.

        Args:
            success (bool): Indicates whether the task preparation was successful.
        """
        if success:
            # GUI operations are performed here
            for layer_name, layer_path, style_name in self.layers_info:
                style_path = str(self.styles_dir_path / style_name)
                if not add_layer_to_qgis(layer_path, layer_name, style_path, self.feature_name, self.logger):
                    self.logger.error(f"Failed to add layer {layer_name}")
                    self.taskCompleted.emit(False)
                    return

        self.completed = True
        self.taskCompleted.emit(success)