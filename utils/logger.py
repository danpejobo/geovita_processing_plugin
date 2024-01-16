import logging.handlers
from pathlib import Path

class CustomLogger:
    """
    A custom logging class that sets up a rotating file logger.

    This logger creates log files in a specified directory and manages them
    by rotating them once they reach a maximum file size.

    Attributes:
        log_dir_path (Path): The directory where log files will be stored.
        log_filename (str): The name of the log file. Defaults to "CustomLog.log".
        logger_name (str): The name of the logger itself. Defaults to "CustomLogger".
        max_file_size (int): The maximum size in bytes of a log file before it's rotated. Defaults to 2MB.
        logger (logging.Logger): The actual logging object.

    Methods:
        setup_logger: Initializes and configures the logger.
        get_logger: Returns the logger object for external use.
    """
    def __init__(self, log_dir_path, log_filename="CustomLog.log", logger_name="CustomLogger", max_file_size=2*1024*1024):
        """
        Initializes a new instance of the CustomLogger class.

        Parameters:
            log_dir_path (str or Path): The path to the directory where log files will be stored.
            log_filename (str, optional): The filename for the log file. Defaults to "CustomLog.log".
            logger_name (str, optional): The name of the logger itself. Defaults to "CustomLogger".
            max_file_size (int, optional): Maximum file size in bytes before log rotation. Defaults to 2MB.
        """
        self.log_dir_path = Path(log_dir_path)
        self.log_filename = log_filename
        self.logger_name = logger_name
        self.max_file_size = max_file_size
        self.logger = None
        self.setup_logger()

    def setup_logger(self):
        """
        Sets up the logger with a rotating file handler.
        
        This method configures the logger to write to a file in the specified directory,
        rotating the log files when they reach the maximum specified size.
        """
        self.log_dir_path.mkdir(parents=True, exist_ok=True)
        log_file = self.log_dir_path / self.log_filename

        self.logger = logging.getLogger(self.logger_name)
        if not self.logger.handlers:
            hdlr = logging.handlers.RotatingFileHandler(str(log_file), "a", self.max_file_size, 20)
            formatter = logging.Formatter("%(asctime)s %(levelname)s Thread %(thread)d %(message)s ")
            hdlr.setFormatter(formatter)
            self.logger.addHandler(hdlr)
            self.logger.setLevel(logging.DEBUG)

    def get_logger(self):
        """
        Returns the logger object.

        This method can be used to obtain the logger instance for logging purposes in other parts of the application.

        Returns:
            logging.Logger: The configured logger instance.
        """
        return self.logger