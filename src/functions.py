import aiosqlite
import asyncio

import aiosqlite
from aiogram import types


# TODO: Refactor all functions and remove unused

# Підключення до бази даних SQLite і створення таблиць
async def setup_database():
    async with aiosqlite.connect('src/database.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS user_values (user_id INTEGER, chat_id INTEGER, value INTEGER, PRIMARY KEY(user_id, chat_id))''')
        await db.execute('''CREATE TABLE IF NOT EXISTS cooldowns (user_id INTEGER, chat_id INTEGER, killru TIMESTAMP, give TIMESTAMP, game TIMESTAMP, dice TIMESTAMP, darts TIMESTAMP, basketball TIMESTAMP, football TIMESTAMP, bowling TIMESTAMP, casino TIMESTAMP, PRIMARY KEY(user_id, chat_id))''')
        await db.execute('CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY, minigame BOOLEAN , give BOOLEAN)')
        await db.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, datetime TIMESTAMP NOT NULL, count INTEGER NOT NULL DEFAULT 0)''')
        await db.commit()

# Функція під час старту
async def startup(dp):
    await setup_database()
    commands = [
        types.BotCommand(command="/killru", description="Спробувати підвищити свою русофобію"),
        types.BotCommand(command="/my", description="Моя русофобія"),
        types.BotCommand(command="/game", description="Знайди і вбий москаля"),
        types.BotCommand(command="/dice", description="Міні гра, кинь кістки"),
        types.BotCommand(command="/darts", description="Гра в дартс"),
        types.BotCommand(command="/basketball", description="Гра в баскетбол"),
        types.BotCommand(command="/football", description="Гра у футбол"),
        types.BotCommand(command="/bowling", description="Гра в боулінг"),
        types.BotCommand(command="/casino", description="Гра в казино"),
        types.BotCommand(command="/help", description="Допомога"),
        types.BotCommand(command="/settings", description="Тільки для адмінів чату"),
        types.BotCommand(command="/give", description="Поділиться русофобією"),
        types.BotCommand(command="/top10", description="Топ 10 гравців"),
        types.BotCommand(command="/top", description="Топ гравців"),
        types.BotCommand(command="/globaltop10", description="Топ 10 серед всіх гравців"),
        types.BotCommand(command="/globaltop", description="Топ всіх гравців"),
        types.BotCommand(command="/leave", description="Покинути гру"),
        types.BotCommand(command="/about", description="Про бота"),
        types.BotCommand(command="/ping", description="Статус бота"),
        ]
    await dp.bot.set_my_commands(commands)
    if STATUS == 'True':
        try:
            await dp.bot.send_message(CHANNEL, f"🚀 Бот запущений", parse_mode="Markdown")
        except Exception as e:
            print(f"Старт error: {e}")

# Функція під час завершення
async def shutdown(dp):
    if STATUS == 'True':
        try:
            await dp.bot.send_message(CHANNEL, f"⛔️ Бот зупинений", parse_mode="Markdown")
        except Exception as e:
            print(f"Стоп error: {e}")


# Перевірка налаштувань
async def check_settings(chat_id: int, setting: str) -> bool:
    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute(f'SELECT {setting} FROM chats WHERE chat_id = ?', (chat_id,)) as cursor:
            result = await cursor.fetchone()
            return result is None or result[0] is None or result[0]

# Перевірка на канал, пп та ботів
async def check_type(message: types.Message):
    if (message.from_user.is_bot or message.chat.type in ['channel', 'private'] or (message.reply_to_message and message.reply_to_message.from_user.id == 777000)):
        
        reply_message = await message.reply("ℹ️ Команда недоступна для каналів, ботів і в особистих повідомленнях")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return True
    return False
