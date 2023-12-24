# Імпорти
import configparser
import aiosqlite
import datetime
import asyncio
import aiogram
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted, BadRequest
from aiogram import Bot, Dispatcher, types
from datetime import datetime


# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    ADMIN = int(config['ID']['ADMIN'])
    support_str = config['ID']['SUPPORT']
    CHANNEL= int(config['ID']['CHANNEL'])
    TEST = (config['SETTINGS']['TEST'])
    STATUS = (config['SETTINGS']['STATUS'])
    DELETE = int(config['SETTINGS']['DELETE'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в functions.py: {e}")
    exit()


# Ініціалізація бота і обробника
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


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
        types.BotCommand(command="/give", description="Поділиться русофобією"),
        types.BotCommand(command="/top10", description="Топ 10 гравців"),
        types.BotCommand(command="/top", description="Топ гравців"),
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


# Додає chat_id у базу даних для розсилки
async def add_chat(chat_id):
    async with aiosqlite.connect('src/database.db') as db:
        await db.execute('INSERT OR IGNORE INTO chats (chat_id) VALUES (?)', (chat_id,))
        await db.commit()


# Видаляє chat_id із бази даних для розсилки
async def remove_chat(chat_id):
    async with aiosqlite.connect('src/database.db') as db:
        await db.execute('DELETE FROM chats WHERE chat_id = ?', (chat_id,))
        await db.commit()


# Перевірка на адміна
async def admin(message: types.Message):
    if message.from_user.id != ADMIN:
        return False
    return True


# Перевірка на адміна підтримки
async def supportusers(message: types.Message):
    SUPPORT = [int(id.strip()) for id in support_str.split(',')]
    if message.from_user.id not in SUPPORT:
        return False
    return True


# Перевірка налаштувань
async def check_settings(chat_id: int, setting: str) -> bool:
    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute(f'SELECT {setting} FROM chats WHERE chat_id = ?', (chat_id,)) as cursor:
            result = await cursor.fetchone()
            return result is None or result[0] is None or result[0]

# Перевірка на канал і пп
async def check_type(message: types.Message):
    if (message.from_user.is_bot or message.chat.type in ['channel', 'private'] or (message.reply_to_message and message.reply_to_message.from_user.id == 777000)):
        
        reply_message = await message.reply("⚠️ Команда недоступна для каналів, ботів і в особистих повідомленнях")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return True
    return False


# Виведення топа
async def show_top(message: types.Message, limit: int, title: str):
    chat_id = message.chat.id
    total_kg = 0

    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute(
            'SELECT user_id, value FROM user_values WHERE chat_id = ? AND value != 0 ORDER BY value DESC LIMIT ?',
            (chat_id, limit)
        ) as cursor:
            results = await cursor.fetchall()

        if results:
            total_kg = sum([value for _, value in results])

    if not results:
        await reply_and_delete(message, '😯 Ще ніхто не грав')
    else:
        async def username(chat_id, user_id):
            try:
                user_info = await bot.get_chat_member(chat_id, user_id)
                if user_info.user.username:
                    return f'[{user_info.user.username}](https://t.me/{user_info.user.username})'
                else:
                    return user_info.user.full_name
            except BadRequest:
                return None

        tasks = [username(chat_id, user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        message_text = f'{title}:\n🟰 Усього: {total_kg} кг\n\n'
        count = 0
        for user_name, (_, rusophobia) in zip(user_names, results):
            if user_name:
                count += 1
                message_text += f'{count}. {user_name}: {rusophobia} кг\n'

        await reply_and_delete(message, message_text)


# Виведення глобального топа
async def show_globaltop(message: types.Message, limit: int, title: str):
    total_kg = 0

    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute(
            'SELECT user_id, MAX(value) as max_value FROM user_values WHERE value != 0 GROUP BY user_id ORDER BY max_value DESC LIMIT ?',
            (limit,)
        ) as cursor:
            results = await cursor.fetchall()

        if results:
            total_kg = sum([value for _, value in results])

    if not results:
        await reply_and_delete(message, '😯 Ще ніхто не грав')
    else:
        async def get_username(user_id):
            try:
                user_info = await bot.get_chat(user_id)
                if user_info.username:
                    return f'[{user_info.username}](https://t.me/{user_info.username})'
                else:
                    return user_info.first_name
            except BadRequest:
                return None

        tasks = [get_username(user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        message_text = f'{title}:\n🟰 Усього: {total_kg} кг\n\n'
        count = 0
        for user_name, (_, rusophobia) in zip(user_names, results):
            if user_name:
                count += 1
                message_text += f'{count}. {user_name}: {rusophobia} кг\n'

        await reply_and_delete(message, message_text)


# Відповідь на повідомлення та видалення
async def reply_and_delete(message: types.Message, reply_text):
    text = await message.reply(reply_text, parse_mode="Markdown", disable_web_page_preview=True)
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=text.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass
    return


# Надсилання повідомлення та видалення ісходного повідомлення
async def send_and_delete(message: types.Message, chat_id, reply_text):
    text = await bot.send_message(chat_id=message.chat.id, text=reply_text, parse_mode="Markdown", disable_web_page_preview=True)
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass
    return


# Редагування та видалення повідомлення
async def edit_and_delete(message: types.Message, chat_id, message_id, reply_text):
    await bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=reply_text, parse_mode="Markdown", disable_web_page_preview=True)
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id, message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass
    return