import configparser
import aiogram
import logging

from aiogram.utils.executor import start_polling
from aiogram import Bot, Dispatcher

from src.middlewares import Logging, Database, RateLimit
from src.functions import startup, shutdown
from src.messages import messages_handlers
from src.admins import admins_handlers
from src.games import games_handlers
from src.logger import logger

# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    SKIPUPDATES = config['SETTINGS']['SKIPUPDATES'] == 'True'
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в sofia.py: {e}")
    exit()

# Ініціалізація бота та диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Ініціалізація проміжного ПЗ
dp.middleware.setup(Logging())
dp.middleware.setup(Database())
dp.middleware.setup(RateLimit())

# Ініціалізація обробників
games_handlers(dp, bot)
admins_handlers(dp, bot)
messages_handlers(dp, bot)

if __name__ == '__main__':
    start_polling(dp, skip_updates=SKIPUPDATES, on_startup=startup, on_shutdown=shutdown)
