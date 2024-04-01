import datetime
import coloredlogs
import logging
from .telegram import echo
from config import LOG_FOLDER


class Logger:
    def __init__(self, log_file: str):
        if log_file[-1] != "/":
            log_file += "/"

        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file += f"{current_datetime}_sybilis_logs"
        self.log_file = log_file
        coloredlogs.install(level="INFO")

    def log(self, message, level="INFO"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}\n"
        with open(self.log_file, "a") as file:
            file.write(log_message)
        if level == "INFO":
            logging.info(message)
        elif level == "WARN":
            logging.warning(message)
        elif level == "ERROR":
            logging.error(message)
        elif level == "FATAL":
            logging.critical(message)

        echo(log_message)

    def info(self, message):
        self.log(f"{message}", "INFO")

    def warn(self, message):
        self.log(f"{message}", "WARN")

    def error(self, message):
        self.log(f"{message}", "ERROR")

    def fatal(self, message):
        self.log(f"{message}", "FATAL")


logger = Logger(LOG_FOLDER)

# Example usage:
if __name__ == "__main__":
    logger = Logger()
    logger.info("This is an informational message.")
    logger.warn("This is a warning message.")
    logger.error("This is an error message.")
    logger.fatal("This is a fatal message.")
