import errno
import logging
import os
from logging.handlers import RotatingFileHandler

CACHE_PATH = "/tmp/pcluster-completions-daemon-cache.json"


def config_logger(logger: logging.Logger, log_path: str) -> None:
    log_path = "/tmp/pcluster-completions-log.txt"
    try:
        os.makedirs(os.path.dirname(log_path))
    except OSError as os_error:
        if os_error.errno != errno.EEXIST:
            raise

    log_file_handler = RotatingFileHandler(log_path, maxBytes=5 * 1024 * 1024, backupCount=1)
    log_file_handler.setLevel(logging.DEBUG)
    log_file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    )
    logger.addHandler(log_file_handler)
    logger.setLevel(logging.DEBUG)
