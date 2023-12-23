# Імпорти
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


# Логування кожного повідомлення
class Logging(BaseMiddleware):
    CONTENT_TYPES = {
        "text": lambda m: m.text,
        "sticker": lambda m: "sticker",
        "audio": lambda m: "audio",
        "photo": lambda m: "photo",
        "video": lambda m: "video",}

    async def on_pre_process_message(self, message: types.Message, data: dict):
        user = getattr(message.from_user, "username", None) or getattr(message.from_user, "first_name", "Unknown")
        chat = getattr(message.chat, "title", None) or f"ID {message.chat.id}"
        content_type = next((self.CONTENT_TYPES[type](message) for type in self.CONTENT_TYPES if getattr(message, type, None)), "other_content")
        logging.info(f"{chat}: {user} - {content_type}")


# Запис у базу даних кількість запитів до бота для команди /ping
class Database(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if message.text and message.text.startswith('/'):
            async with aiosqlite.connect('src/database.db') as db:
                nowtime = datetime.now()
                cursor = await db.execute('SELECT id, count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1', (nowtime.replace(hour=0, minute=0, second=0, microsecond=0), nowtime.replace(hour=23, minute=59, second=59, microsecond=999999)))

                row = await cursor.fetchone()
                if row:
                    await db.execute('UPDATE queries SET count = count + 1 WHERE id = ?', (row[0],))
                else:
                    await db.execute('INSERT INTO queries (datetime, count) VALUES (?, 1)', (nowtime,))

                await db.commit()


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