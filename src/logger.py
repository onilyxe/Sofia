import logging
import os

from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Створюємо папку logs якщо її немає
if not os.path.exists("src/logs"):
    os.makedirs("src/logs")

# Логування у файл і на консоль
logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_file_name = "src/logs/log.log"
file_handler = TimedRotatingFileHandler(
    log_file_name, when="midnight", interval=1, backupCount=30, encoding="utf-8"
)
file_handler.suffix = "%d-%m-%Y.log"
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s [%(levelname)s] - %(message)s", datefmt="%d.%m.%Y, %H:%M:%S"
    )
)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(message)s", datefmt="%d.%m.%Y, %H:%M:%S")
)
logger.addHandler(console_handler)
