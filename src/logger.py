import logging
import os

from logging.handlers import TimedRotatingFileHandler


def init_logger():
    # Створюємо теку logs якщо її немає
    if not os.path.exists("logs"):
        os.makedirs("logs")

    class ExcludeUpdateHandledFilter(logging.Filter):
        def filter(self, record):
            return "Update id=" not in record.getMessage()

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    log_file_name = "logs/log.log"
    file_handler = TimedRotatingFileHandler(
        log_file_name, when="midnight", interval=1, backupCount=30, encoding="utf-8"
    )
    file_handler.suffix = "%d-%m-%Y.log"
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] - %(message)s", datefmt="%d.%m.%Y, %H:%M:%S"
        )
    )
    file_handler.addFilter(ExcludeUpdateHandledFilter())
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(message)s", datefmt="%d.%m.%Y, %H:%M:%S")
    )
    console_handler.addFilter(ExcludeUpdateHandledFilter())
    logger.addHandler(console_handler)
