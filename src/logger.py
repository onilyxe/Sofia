# Імпорти
import logging
import os
from datetime import datetime


# Створюємо папку logs якщо її немає
if not os.path.exists('src/logs'):
    os.makedirs('src/logs')


# Логування у файл і на консоль
current_date = datetime.now().strftime("%d_%m_%Y")
logger = logging.getLogger()
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(f'src/logs/{current_date}.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s', datefmt='%d.%m.%Y, %H:%M:%S'))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%d.%m.%Y, %H:%M:%S'))
logger.addHandler(console_handler)