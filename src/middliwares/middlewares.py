import configparser
import aiosqlite
import asyncio
import aiogram
import logging

from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from datetime import datetime, timedelta
from aiogram import Bot, types
# TODO: Refactor all middlewares
# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    DELETE = int(config['SETTINGS']['DELETE'])
    ADMIN = int(config['ID']['ADMIN'])
    BAN = int(config['SPAM']['BAN'])
    SPEED = int(config['SPAM']['SPEED'])
    MESSAGES = int(config['SPAM']['MESSAGES'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в middlewares.py: {e}")
    exit()

# Ініціалізація бота
bot = Bot(token=TOKEN)

# Змінні для захисту від спаму
banlist = {}
BANN = timedelta(minutes=BAN)
SPEEDD = timedelta(seconds=SPEED)


# Захист від спаму
class RateLimit(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        user_id = message.from_user.id

        if user_id == ADMIN:
            return
            
        current_time = datetime.now()

        if user_id in banlist:
            first_message_time, message_count, mute_time = banlist[user_id]

            if mute_time and current_time < mute_time + BANN:
                raise CancelHandler()

            if current_time - first_message_time <= SPEEDD:
                message_count += 1
                if message_count >= MESSAGES:
                    banlist[user_id] = (first_message_time, message_count, current_time)
                    send = await bot.send_voice(chat_id=message.chat.id, voice=open('src/spam.ogg', 'rb'))
                    await asyncio.sleep(DELETE)
                    try:
                        await bot.delete_message(message.chat.id, send.message_id)
                    except (MessageCantBeDeleted, MessageToDeleteNotFound):
                        pass
                    raise CancelHandler()
                else:
                    banlist[user_id] = (first_message_time, message_count, mute_time)
            else:
                banlist[user_id] = (current_time, 1, mute_time)
        else:
            banlist[user_id] = (current_time, 1, None)
