# Імпорти
import configparser
import aiosqlite
import aiogram
import logging
import psutil

from src.functions import reply_and_delete, show_globaltop, show_top
from datetime import datetime, timedelta
from aiogram import Bot, types


# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    ADMIN = int(config['ID']['ADMIN'])
    DELETE = int(config['SETTINGS']['DELETE'])
    VERSION = (config['SETTINGS']['VERSION'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в messages.py: {e}")
    exit()


# Ініціалізація бота
bot = Bot(token=TOKEN)


#/-----start
async def start(message: types.Message):
    await reply_and_delete(message, "🫡 Привіт. Я бот для гри в русофобію. Додавай мене в чат і розважайся. Щоб дізнатися як мною користуватися, вивчай /help")


#-----/help
async def help(message: types.Message):
    help_text = (
        "🎮 *Розвивай свою русофобію. Зростай її щодня, і змагайся з друзями*" +
        "\n\n*📈 /killru* — _Спробувати підвищити свою русофобію_" +
        "\n*😡 /my* — _Моя русофобія_" +
        "\n*🎮 /game* — _Знайди і вбий москаля_" +
        "\n*🎲 /dice* — _Міні гра, кинь кістки_" +
        "\n*🔄 /give* — _Передати русофобію_" +
        "\n*🌏 /globaltop* — _Топ всіх гравців_" +
        "\n*📊 /top10* — _Топ 10 гравців чату_" +
        "\n*📊 /top* — _Топ гравців чату_" +
        "\n*🫡 /leave* — _Покинути гру (прогрес видаляється):_" +
        "\n*📡 /about* — _Про бота_" +
        "\n\n_Якщо мені видати права адміністратора на видалення повідомлень, я буду прибирати за собою_")
    
    await reply_and_delete(message, help_text)


#-----/ping
async def ping(message: types.Message):
    start_time = datetime.now()
    await bot.get_me()
    end_time = datetime.now()
    ping_time = (end_time - start_time).total_seconds() * 1000
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent

    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute('SELECT count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1', (start_time.replace(hour=0, minute=0, second=0, microsecond=0), start_time.replace(hour=23, minute=59, second=59, microsecond=999999))) as cursor:
            today_record = await cursor.fetchone()
            today_queries = today_record[0] if today_record else 0

        async with db.execute('SELECT SUM(count) FROM queries WHERE datetime >= ?', (start_time - timedelta(days=7),)) as cursor:
            last_week_record = await cursor.fetchone()
            last_week_queries = last_week_record[0] if last_week_record else 0

        async with db.execute('SELECT SUM(count) FROM queries') as cursor:
            all_time_record = await cursor.fetchone()
            all_time_queries = all_time_record[0] if all_time_record else 0

    ping_text = (
        f"📡 Ping: `{ping_time:.2f}` ms\n\n"
        f"🔥 CPU: `{cpu_usage}%`\n"
        f"💾 RAM: `{ram_usage}%`\n\n"
        f"📊 Кількість запитів:\n"
        f"_За сьогодні:_ `{today_queries}`\n"
        f"_За тиждень:_ `{last_week_queries}`\n"
        f"_За весь час:_ `{all_time_queries}`")

    await reply_and_delete(message, ping_text)


#-----/about
async def about(message: types.Message):
    about_text = (
        f"📡 Sofia `{VERSION}`\n\n"
        f"[News Channel](t.me/SofiaBotRol)\n"
        f"[Source](https://github.com/onilyxe/Sofia)\n\n"
        f"Made [onilyxe](https://t.me/itsokt0cry). Idea [den](https://t.me/itsokt0cry)")

    await reply_and_delete(message, about_text)


# Виведення глобального топа
async def globaltop(message: types.Message):
    await show_globaltop(message, limit=101, title='🌏 Глобальний топ русофобій')


# Виведення топ 10
async def top10(message: types.Message):
    await show_top(message, limit=10, title='📊 Топ 10 русофобій')


# Виведення топа
async def top(message: types.Message):
    await show_top(message, limit=101, title='📊 Топ русофобій')


# Ініціалізація обробника
def messages_handlers(dp, bot):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(help, commands=['help'])
    dp.register_message_handler(ping, commands=['ping'])
    dp.register_message_handler(about, commands=['about'])
    dp.register_message_handler(globaltop, commands=['globaltop'])
    dp.register_message_handler(top10, commands=['top10'])
    dp.register_message_handler(top, commands=['top'])