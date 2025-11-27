import sys
import logging
from logging.handlers import RotatingFileHandler
import pathlib

logger = logging.getLogger('CopyHelper')

def handle_exception(exc_type, exc_value, exc_traceback):
    if not issubclass(exc_type, KeyboardInterrupt):
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


def init_logging():
    pathlib.Path("logs").mkdir(exist_ok=True)

    # full_log_handler = RotatingFileHandler('logs\\full_log.txt', maxBytes=1024 * 1024, backupCount=2, encoding='UTF-8')
    # full_log_handler.setLevel(logging.DEBUG)
    # full_log_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    # full_log_handler.formatter.default_msec_format=''

    standard_log_handler = RotatingFileHandler('logs\\log.txt', maxBytes=1024 * 1024, backupCount=4, encoding='UTF-8')
    standard_log_handler.setLevel(logging.INFO)
    standard_log_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
    standard_log_handler.formatter.default_msec_format = ''

#    logger.addHandler(full_log_handler)
    logger.addHandler(standard_log_handler)
    logger.setLevel(logging.DEBUG)

    sys.excepthook = handle_exception
