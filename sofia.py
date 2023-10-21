# Імпорти
import configparser
import logging
import sqlite3
import asyncio
import random
import aiocache
import aiogram
import psutil
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import BadRequest, MessageCantBeDeleted, BotKicked, ChatNotFound, MessageToDeleteNotFound
from datetime import datetime, timedelta, time

# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['SOFIA']
    ADMIN = int(config['ID']['ADMIN'])
    ALIASES = {k: int(v) for k, v in config['ALIASES'].items()}
    DELETE = int(config['SETTINGS']['DELETE'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу: {e}")
    exit()

# Ініціалізація бота й обробника
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
cache = aiocache.Cache()

# Логування кожного повідомлення
class LoggingMiddleware(aiogram.dispatcher.middlewares.BaseMiddleware):
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

dp.middleware.setup(LoggingMiddleware())

# Створюємо папку logs якщо її немає
if not os.path.exists('logs'):
    os.makedirs('logs')

# Отримуємо поточну дату для використання в імені файлу лога
current_date = datetime.now().strftime("%Y-%m-%d")

# Створюємо логгер
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Створюємо обробник для запису логів у файл
file_handler = logging.FileHandler(f'logs/log_{current_date}.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(file_handler)

# Створюємо обробник для виведення логів у консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(console_handler)

# Запис у базу даних кількість запитів до бота для команди /ping
class DatabaseMiddleware(aiogram.dispatcher.middlewares.BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if message.text and message.text.startswith('/'):
            nowtime = datetime.now()
            cursor.execute('SELECT id, count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1', 
                        (nowtime.replace(hour=0, minute=0, second=0, microsecond=0), 
                        nowtime.replace(hour=23, minute=59, second=59, microsecond=999999)))

            row = cursor.fetchone()
            if row:
                cursor.execute('UPDATE queries SET count = count + 1 WHERE id = ?', (row[0],))
            else:
                cursor.execute('INSERT INTO queries (datetime, count) VALUES (?, 1)', (nowtime,))
        
            conn.commit()

dp.middleware.setup(DatabaseMiddleware())

# Підключення до бази даних SQLite і створення таблиць
conn = sqlite3.connect('sofia.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS user_values (user_id INTEGER, chat_id INTEGER, value INTEGER, PRIMARY KEY(user_id, chat_id))''')
cursor.execute('''CREATE TABLE IF NOT EXISTS cooldowns (user_id INTEGER, chat_id INTEGER, killru DATE, give TIMESTAMP, game TIMESTAMP, PRIMARY KEY(user_id, chat_id))''')
cursor.execute('CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY)')
cursor.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, datetime TIMESTAMP NOT NULL, count INTEGER NOT NULL DEFAULT 0)''')

# Додає chat_id у базу даних для розсилки
def add_chat(chat_id):
    cursor.execute('INSERT OR IGNORE INTO chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()

#/start-----
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    reply = await message.reply("🫡 Привіт. Я бот для розваг\nВивчай /help")

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, reply.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass

#/help-----
@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    reply = await message.reply(
        "🎮 *Розвивай свою русофобію. Зростай її щодня, і змагайся з друзями*" +
        "\n\n*/killru* — _Спробувати підвищити свою русофобію_" +
        "\n*/my* — _Моя русофобія_" +
        "\n*/game* — _Знайди і вбий москаля_" +
        "\n*/give* — _Поділиться русофобією_" +
        "\n*/globaltop* — _Топ всіх гравців_" +
        "\n*/top10* — _Топ 10 гравців_" +
        "\n*/top* — _Топ гравців_" +
        "\n*/leave* — _Покинути гру_"+
        "\n*/ping* — _статус бота_", parse_mode="Markdown")

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, reply.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass

#/killru-----
@dp.message_handler(commands=['killru'])
async def killru(message: types.Message):
    add_chat(message.chat.id)
    if message.from_user.is_bot or message.chat.type == 'channel':
        reply_message = await message.reply("⚠️ Команда не доступна для каналів і ботів")

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, BadRequest):
            pass
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    now = datetime.now()
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    value_killru = cursor.fetchone()

    newuser = False

    if not value_killru:
        newuser = True
        welcome = await message.reply(f"🎉 {mention}, вітаю! Ти тепер зареєстрований у грі русофобії!", parse_mode="Markdown", disable_web_page_preview=True)
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, 0))
        conn.commit()

    cursor.execute('SELECT killru FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    cooldown = cursor.fetchone()
    cooldown_killru = None

    if cooldown and cooldown[0]:
        cooldown_killru = datetime.strptime(cooldown[0], '%Y-%m-%d').date()
    if cooldown_killru and now.date() <= cooldown_killru:
        next_day = now + timedelta(days=1)
        midnight = datetime.combine(next_day, datetime.min.time())
        remaining_time = midnight - now

        hours, remainder = divmod(remaining_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        cooldown_time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

        bonus = ""
        bonus_times = ['00:00:00', '00:13:37', '01:00:00', '01:11:11', '02:00:00', '02:22:22', '22:22:22', '03:00:00', '03:33:33', '04:00:00', '04:20:00', '04:44:44', '05:00:00', '05:55:55', '06:00:00', '07:00:00', '08:00:00', '09:00:00', '10:00:00', '11:00:00', '11:11:11', '12:00:00', '13:00:00', '13:33:37', '14:00:00', '15:00:00', '16:00:00', '17:00:00', '18:00:00', '19:00:00', '20:00:00', '21:00:00', '22:00:00', '23:00:00']
        if cooldown_time_str in bonus_times:
            bonus = "\n\n🎉 Гарний час! Тримай за удачу `5` кг!"
            cursor.execute('UPDATE user_values SET value = value + 5 WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            conn.commit()

        cooldown_message = await message.reply(
            f"⚠️ Ти можеш використати цю команду тільки один раз на день. Спробуй через `{cooldown_time_str}`{bonus}", 
            parse_mode="Markdown"
        )

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
            await bot.delete_message(chat_id, cooldown_message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return

    else:
        cursor.execute('SELECT * FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        if cursor.fetchone():
            cursor.execute('UPDATE cooldowns SET killru = ? WHERE user_id = ? AND chat_id = ?', (now.strftime('%Y-%m-%d'), user_id, chat_id))
        else:
            cursor.execute('INSERT INTO cooldowns (user_id, chat_id, killru) VALUES (?, ?, ?)', (user_id, chat_id, now.strftime('%Y-%m-%d')))
        conn.commit()



    rusophobia = random.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

    if newuser:
        rusophobia = abs(rusophobia)

    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()
    new_rusophobia = result[0] + rusophobia if result else rusophobia

    cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?', (new_rusophobia, user_id, chat_id))
    conn.commit()

    if rusophobia >= 0:
        message_text = f"📈 {mention}, твоя русофобія збільшилась на `{rusophobia}` кг"
    else:
        message_text = f"📉 {mention}, твоя русофобія зменшилась на `{abs(rusophobia)}` кг"

    message_text += f"\n🏷️ Тепер в тебе: `{new_rusophobia}` кг"
    reply = await bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        if newuser:
            await bot.delete_message(chat_id=message.chat.id, message_id=welcome.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=reply.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass

#/my-----
@dp.message_handler(commands=['my'])
async def my(message: types.Message):
    if message.from_user.is_bot or message.chat.type == 'channel':
        reply_message = await message.reply("⚠️ Команда не доступна для каналів і ботів")

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, BadRequest):
            pass
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if message.from_user.username:
        mention = f"[{message.from_user.username}](https://t.me/{message.from_user.username})"
    else:
        mention = message.from_user.first_name

    if result is None:
        response = await message.reply(f'😯 {mention}, ти ще не грав', parse_mode="Markdown", disable_web_page_preview=True)
    else:
        rusophobia = result[0]
        response = await message.reply(f"😡 {mention}, твоя русофобія: `{rusophobia}` кг", parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=response.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass

#/game-----
@dp.message_handler(commands=['game'])
async def start_game(message: types.Message):
    if message.from_user.is_bot or message.chat.type == 'channel':
        reply_message = await message.reply("⚠️ Команда не доступна для каналів і ботів")

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, BadRequest):
            pass
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    cursor.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    last_played = cursor.fetchone()
    
    if last_played and last_played[0]:
        last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
        cooldown = timedelta(hours=3)
        if datetime.now() < last_played + cooldown:
            time_left = last_played + cooldown - datetime.now()
            cooldown_time = str(time_left).split(".")[0]
            cooldown_message = await bot.send_message(chat_id, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`", parse_mode="Markdown")
            await asyncio.sleep(DELETE)
            try:
                await bot.delete_message(chat_id, message.message_id)
                await bot.delete_message(chat_id, cooldown_message.message_id)
            except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass
            return

    cursor.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    balance = cursor.fetchone()
    if balance:
        balance = balance[0]
    else:
        balance = 0

    if balance <= 0:
        no_balance_message = await bot.send_message(chat_id, f"⚠️ У тебе недостатньо русофобії для гри")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
            await bot.delete_message(chat_id, no_balance_message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return

    await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

    keyboard = InlineKeyboardMarkup(row_width=3)
    bet_buttons = [InlineKeyboardButton(f"🏷️ {bet} кг", callback_data=f"bet_{bet}") for bet in [1, 3, 5, 10, 20, 30, 40, 50, 60]]
    bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancel"))
    keyboard.add(*bet_buttons)
    game_message = await bot.send_message(chat_id, f"🧌 {mention}, знайди і вбий москаля\n\n🏷️ У тебе: `{balance}` кг\n🎰 Вибери ставку", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
    await cache.set(f"game_player_{game_message.message_id}", message.from_user.id)
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id, message.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass


@dp.callback_query_handler(lambda c: c.data.startswith('bet_') or c.data.startswith('cell_') or c.data == 'cancel' or c.data == 'cancel_cell')
async def handle_game_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    game_player_id = await cache.get(f"game_player_{callback_query.message.message_id}")

    if game_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    if callback_query.data == 'cancel':
        await bot.answer_callback_query(callback_query.id, "✅")
        await bot.edit_message_text("⚠️ Гру скасовано", chat_id=chat_id, message_id=callback_query.message.message_id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, callback_query.message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return

    elif callback_query.data.startswith('bet_'):
        _, bet = callback_query.data.split('_')
        bet = int(bet)

        cursor.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = cursor.fetchone()
        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=3)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await bot.answer_callback_query(callback_query.id, "✅")
                await bot.edit_message_text(f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`", 
                                            chat_id=chat_id, 
                                            message_id=callback_query.message.message_id, parse_mode="Markdown")
                await asyncio.sleep(DELETE)
                try:
                    await bot.delete_message(chat_id, callback_query.message.message_id)
                except (MessageCantBeDeleted, MessageToDeleteNotFound):
                    pass

        initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
        if initial_balance is None or int(initial_balance) < bet:
            await bot.answer_callback_query(callback_query.id, "⚠️ Недостатньо русофобії")
            return

        new_balance = int(initial_balance) - bet
        cursor.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
        conn.commit()

        await cache.set(f"bet_{user_id}_{chat_id}", str(bet))


        potential_win = bet * 2

        keyboard = InlineKeyboardMarkup(row_width=3)
        cell_buttons = [InlineKeyboardButton("🧌", callback_data=f"cell_{i}") for i in range(1, 10)]
        cell_buttons.append(InlineKeyboardButton("❌ Відміна", callback_data="cancel_cell"))
        keyboard.add(*cell_buttons)
        mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
        await bot.answer_callback_query(callback_query.id, "✅")
        await bot.edit_message_text(
            f"🧌 {mention}, знайди москаля:\n\n"
            f"🏷️ Твоя ставка: `{bet} кг`\n"
            f"💰 Можливий виграш: `{potential_win} кг`", 
            chat_id=chat_id, 
            message_id=callback_query.message.message_id, 
            reply_markup=keyboard, 
            parse_mode="Markdown", 
            disable_web_page_preview=True
        )

    elif callback_query.data.startswith('cancel_cell'):
        bet = await cache.get(f"bet_{user_id}_{chat_id}")
        bet = int(bet)
        cursor.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        current_balance = cursor.fetchone()[0]
        new_balance = current_balance + bet
        cursor.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
        conn.commit()

        await bot.answer_callback_query(callback_query.id, "✅")
        await bot.edit_message_text(f"⚠️ Гру скасовано. Твоя ставка в `{bet} кг` повернута", chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, callback_query.message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return

    elif callback_query.data.startswith('cell_'):
        _, cell = callback_query.data.split('_')
        cell = int(cell)

        mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

        cursor.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance_after_bet = cursor.fetchone()[0]
        bet = await cache.get(f"bet_{user_id}_{chat_id}")
        bet = int(bet)
        win = random.random() < 0.4

        if win:
            bet_won = bet * 2 
            new_balance = balance_after_bet + bet_won + bet
            cursor.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            conn.commit()
            message = f"🥇 {mention}, вітаю! Ти знайшов і вбив москаля, і з нього випало `{bet_won}` кг\n🏷️ Тепер у тебе: `{new_balance}` кг"
        else:
            message = f"😔 {mention}, на жаль, ти програв `{bet}` кг\n🏷️ У тебе залишилося: `{balance_after_bet}` кг"

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT OR REPLACE INTO cooldowns (user_id, chat_id, game) VALUES (?, ?, ?)", (user_id, chat_id, now))
        conn.commit()

        await bot.answer_callback_query(callback_query.id, "✅")
        await bot.edit_message_text(message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

#/give-----
@dp.message_handler(commands=['give'])
async def give(message: types.Message):
    if message.from_user.is_bot or message.chat.type == 'channel':
        reply_message = await message.reply("⚠️ Команда не доступна для каналів і ботів")

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, BadRequest):
            pass
        return

    global givers
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        parts = message.text.split()
        if len(parts) != 2:
            reply = await bot.send_message(message.chat.id, "⚙️ Використовуй `/give N` у відповідь на повідомлення", parse_mode="Markdown")
            await asyncio.sleep(DELETE)
            try:
                await bot.delete_message(message.chat.id, message.message_id)
                await bot.delete_message(message.chat.id, reply.message_id)
            except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass

        try:
            value = int(parts[1])
            if value <= 0:
                raise ValueError

        except ValueError:
            reply = await bot.send_message(message.chat.id, "🤨 Типо розумний? Введи плюсове і ціле число. Наприклад: `/give 5` у відповідь на повідомлення", parse_mode="Markdown")
            await asyncio.sleep(DELETE)
            try:
                await bot.delete_message(message.chat.id, message.message_id)
                await bot.delete_message(message.chat.id, reply.message_id)
            except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass

        giver_id = message.from_user.id
        chat_id = message.chat.id
        now = datetime.now()

        cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL', (giver_id, chat_id))
        last_given = cursor.fetchone()

        if last_given and last_given[0]:
            last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f') 
            if last_given + timedelta(hours=12) > now:
                cooldown_time = (last_given + timedelta(hours=12)) - now
                cooldown_time = str(cooldown_time).split('.')[0]
                reply = await bot.send_message(message.chat.id, f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`", parse_mode="Markdown")
                await asyncio.sleep(DELETE)
                try:
                    await bot.delete_message(message.chat.id, message.message_id)
                    await bot.delete_message(message.chat.id, reply.message_id)
                except (MessageCantBeDeleted, MessageToDeleteNotFound):
                    pass
        else:
            last_given = None


        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
        result = cursor.fetchone()
        if not result or result[0] < value:
            reply = await bot.send_message(message.chat.id, f"⚠️ У тебе `{result[0] if result else 0}` кг. Цього недостатньо", parse_mode="Markdown")
            await asyncio.sleep(DELETE)
            try:
                await bot.delete_message(message.chat.id, message.message_id)
                await bot.delete_message(message.chat.id, reply.message_id)
            except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass

        inline = InlineKeyboardMarkup(row_width=2)
        inline_yes = InlineKeyboardButton('✅ Так', callback_data=f'give_{value}_yes_{message.reply_to_message.from_user.id}')
        inline_no = InlineKeyboardButton('❌ Ні', callback_data=f'give_{value}_no_{message.reply_to_message.from_user.id}')
        inline.add(inline_yes, inline_no)

        current_rusophobia = result[0] if result else 0
        mention = ('[' + message.reply_to_message.from_user.username + ']' + '(https://t.me/' + message.reply_to_message.from_user.username + ')') if message.reply_to_message.from_user.username else message.reply_to_message.from_user.first_name
        giver_mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name
        sent_message = await bot.send_message(chat_id=message.chat.id, text=f"🔄 {giver_mention} збирається передати `{value}` кг русофобії {mention}\n🏷️ В тебе: `{current_rusophobia}` кг. Підтверджуєш?", reply_markup=inline, parse_mode="Markdown", disable_web_page_preview=True)

        await cache.set(f"givers_{sent_message.message_id}", message.from_user.id)

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(message.chat.id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass
    else:
        reply = await bot.send_message(message.chat.id, "⚙️ Використовуй `/give N` у відповідь на повідомлення", parse_mode="Markdown")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.delete_message(message.chat.id, reply.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('give_'))
async def give_inline(callback_query: CallbackQuery):
    global givers
    _, value, answer, receiver_id = callback_query.data.split('_')
    value = int(value)
    receiver_id = int(receiver_id)
    giver_id = await cache.get(f"givers_{callback_query.message.message_id}")

    receiver = await bot.get_chat_member(callback_query.message.chat.id, receiver_id)
    mention = ('[' + receiver.user.username + ']' + '(https://t.me/' + receiver.user.username + ')') if receiver.user.username else receiver.user.first_name

    now = datetime.now()
    cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL', (giver_id, callback_query.message.chat.id))
    last_given = cursor.fetchone()
    if last_given and last_given[0]:
        last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f')
        if last_given + timedelta(hours=12) > now:
            cooldown_time = (last_given + timedelta(hours=12)) - now
            cooldown_time = str(cooldown_time).split('.')[0]
            reply = await bot.edit_message_text(
                text=f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`", chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, parse_mode="Markdown")
            await asyncio.sleep(DELETE)
            try:
                await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            except (MessageCantBeDeleted, MessageToDeleteNotFound):
                pass
            return
        else:
            last_given = None

    if giver_id != callback_query.from_user.id:
        try:
            await bot.answer_callback_query(callback_query.id, text="❌ Ці кнопочки не для тебе!", show_alert=True)
        except Exception as e:
            logging.exception(e)
        return

    if answer == 'yes':
        cursor.execute('UPDATE user_values SET value = value - ? WHERE user_id = ? AND chat_id = ?', (value, giver_id, callback_query.message.chat.id))
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?) ON CONFLICT(user_id, chat_id) DO UPDATE SET value = value + ?', (receiver_id, callback_query.message.chat.id, value, value))
        conn.commit()

        cursor.execute('UPDATE cooldowns SET give = ? WHERE user_id = ? AND chat_id = ?', (datetime.now(), giver_id, callback_query.message.chat.id))
        conn.commit()

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, callback_query.message.chat.id))
        updated_benis = cursor.fetchone()[0]

        if callback_query.from_user.username:
            giver_mention = f"[{callback_query.from_user.username}](https://t.me/{callback_query.from_user.username})"
        else:
            giver_mention = callback_query.from_user.first_name

        await bot.answer_callback_query(callback_query.id, "✅ Успішно")
        await bot.edit_message_text(text=f"✅ {giver_mention} передав `{value}` кг русофобії {mention}\n🏷️ Тепер в тебе: `{updated_benis}` кг", chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

    else:
        await bot.answer_callback_query(callback_query.id, "❌ Скасовано")
        await bot.edit_message_text(text="❌ Передача русофобії скасована", chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass

#/globaltop-----
async def show_globaltop(message: types.Message, limit: int, title: str):
    cursor.execute(
        f'SELECT user_id, MAX(value) as max_value FROM user_values WHERE value != 0 GROUP BY user_id ORDER BY max_value DESC LIMIT {limit}')
    results = cursor.fetchall()

    if len(results) == 0:
        response = await message.reply('😯 Ще ніхто не грав')
    else:
        async def username(user_id):
            try:
                user_info = await bot.get_chat(user_id)
                if user_info.username:
                    return f'[{user_info.username}](https://t.me/{user_info.username})'
                else:
                    return user_info.first_name
            except BadRequest:
                return None

        tasks = [username(user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        message_text = f'{title}:\n'
        medals = ["🥇", "🥈", "🥉"]
        count = 0
        for user_name, (_, rusophobia) in zip(user_names, results):
            if user_name:
                medal = medals[count] if count < 3 else f"{count + 1}."
                message_text += f'{medal} {user_name}: {rusophobia} кг\n'
                count += 1

        response = await message.reply(message_text, parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=response.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass


@dp.message_handler(commands=['globaltop'])
async def globaltop(message: types.Message):
    await show_globaltop(message, limit=201, title='🌏 Глобальний топ русофобій')

#/top-----
async def show_top(message: types.Message, limit: int, title: str):
    chat_id = message.chat.id
    cursor.execute(
        f'SELECT user_id, value FROM user_values WHERE chat_id = ? AND value != 0 ORDER BY value DESC LIMIT {limit}', (chat_id,))
    results = cursor.fetchall()

    if len(results) == 0:
        response = await message.reply('😯 Ще ніхто не грав')
    else:
        async def username(user_id):
            try:
                user_info = await bot.get_chat_member(chat_id, user_id)
                if user_info.user.username:
                    return f'[{user_info.user.username}](https://t.me/{user_info.user.username})'
                else:
                    return user_info.user.full_name
            except BadRequest:
                return None

        tasks = [username(user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        message_text = f'{title}:\n'
        medals = ["🥇", "🥈", "🥉"]
        count = 0
        for user_name, (_, rusophobia) in zip(user_names, results):
            if user_name:
                medal = medals[count] if count < 3 else f"{count + 1}."
                message_text += f'{medal} {user_name}: {rusophobia} кг\n'
                count += 1

        response = await message.reply(message_text, parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=response.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass



@dp.message_handler(commands=['top10'])
async def top10(message: types.Message):
    await show_top(message, limit=10, title='📊 Топ 10 русофобій')


@dp.message_handler(commands=['top'])
async def top(message: types.Message):
    await show_top(message, limit=101, title='📊 Топ русофобій')

#/leave-----
@dp.message_handler(commands=['leave'])
async def leave(message: types.Message):
    if message.from_user.is_bot or message.chat.type == 'channel':
        reply_message = await message.reply("⚠️ Команда не доступна для каналів і ботів")

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=reply_message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, BadRequest):
            pass
        return

    inline = InlineKeyboardMarkup(row_width=2)
    inline.add(InlineKeyboardButton("✅ Так", callback_data="confirm_leave"), InlineKeyboardButton("❌ Ні", callback_data="cancel_leave"))
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    cursor.execute('SELECT * FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    user_exists = cursor.fetchone()

    if not user_exists:
        msg = await bot.send_message(chat_id, f"😯 {mention}, ти й так не граєш", parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
    else:
        msg = await bot.send_message(chat_id, f"😡 {mention}, ти впевнений, що хочеш ливнути з гри? Твої дані буде видалено з бази даних", reply_markup=inline, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"leavers_{msg.message_id}", user_id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


@dp.callback_query_handler(lambda c: c.data in ['confirm_leave', 'cancel_leave'])
async def leave_inline(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    
    leaver_id = await cache.get(f"leavers_{callback_query.message.message_id}")

    if leaver_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    mention = (
        '[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')'
    ) if callback_query.from_user.username else callback_query.from_user.first_name

    if callback_query.data == 'confirm_leave':
        cursor.execute('DELETE FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        # cursor.execute('UPDATE cooldowns SET killru = NULL, give = NULL, game = NULL WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)) # Для тестування
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "✅ Успішно")
        await bot.edit_message_text(f"🤬 {mention}, ти покинув гру, і тебе було видалено з бази даних", chat_id, callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await bot.answer_callback_query(callback_query.id, "❌ Скасовано")
        await bot.edit_message_text(f"🫡 {mention}, ти залишився у грі", chat_id, callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass

#/ping-----
@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
    start_time = datetime.now()
    await bot.get_me()
    end_time = datetime.now()

    ping = (end_time - start_time).total_seconds() * 1000
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()

    cursor.execute('SELECT count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1', (start_time.replace(hour=0, minute=0, second=0, microsecond=0), start_time.replace(hour=23, minute=59, second=59, microsecond=999999)))
    today = cursor.fetchone()[0] or 0
    cursor.execute('SELECT SUM(count) FROM queries WHERE datetime >= ?', (start_time - timedelta(days=7),))
    last_week = cursor.fetchone()[0] or 0
    cursor.execute('SELECT SUM(count) FROM queries')
    all_time = cursor.fetchone()[0] or 0

    text = await message.reply(
        f"📡 Ping: `{ping:.2f}` ms\n\n"
        f"🔥 CPU: `{cpu}%`\n"
        f"💾 RAM: `{ram.percent}%`\n\n"
        f"📊 Кількість запитів\n"
        f"_За сьогодні:_ `{today}`\n"
        f"_За тиждень:_ `{last_week}`\n"
        f"_За весь час:_ `{all_time}`\n\n"
        f"`v1.8`", parse_mode="Markdown")

    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(text.chat.id, text.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass
    return

#/chatlist-----
@dp.message_handler(commands=['chatlist'])  
async def chatlist(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    cursor.execute('SELECT chat_id FROM chats')
    chats = cursor.fetchall()

    if not chats:
        reply = await message.reply("😬 Бота не було додано до жодного чату")
    else:
        chat_list = "💬 Список чатів бота:\n\n"
        for chat in chats:
            try:
                chat_info = await bot.get_chat(chat[0])
                chat_title = chat_info.title
                chat_type = chat_info.type
                chat_username = chat_info.username

                if chat_username:
                    chat_link = f"@{chat_username}"
                    chat_list += f"🔹 {chat[0]}, {chat_type}\n{chat_title} - {chat_link}\n"
                else:
                    chat_list += f"🔹 {chat[0]}, {chat_type}, {chat_title}\n"
            except BotKicked:
                chat_list += f"🔹 {chat[0]} - вилучено\n"
            except ChatNotFound:
                chat_list += f"🔹 {chat[0]} - не знайдено\n"

        reply = await message.reply(chat_list, disable_web_page_preview=True)
    
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=reply.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass

#/message-----
@dp.message_handler(commands=['message'])
async def message(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    parts = message.text.split(" ", 2)

    if len(parts) < 2:
        info_message = await message.reply(
            "ℹ️ Розсилка повідомлень\n\n/message `text` - в усі чати\n/message `ID/alias text` - в один чат", parse_mode="Markdown")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=info_message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return

    chat_id_to_send = None
    text_to_send = None
    if len(parts) == 3:
        if parts[1].startswith('-100') or parts[1].lower() in ALIASES:
            chat_id_to_send = int(parts[1]) if parts[1].startswith('-100') else ALIASES[parts[1].lower()]
            text_to_send = parts[2]
        else:
            text_to_send = " ".join(parts[1:])
    else:
        text_to_send = parts[1]

    if not text_to_send.strip():
        error_message = await message.reply("⚠️ Текст повідомлення не може бути пустим")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
        return

    successful_sends = 0
    error_messages = ""
    if chat_id_to_send:
        try:
            await bot.send_message(chat_id_to_send, text_to_send)
            successful_sends += 1
        except Exception as e:
            error_message = f"`{chat_id_to_send}`: _{e}_"
            error_messages += error_message + "\n"
    else:
        cursor.execute('SELECT chat_id FROM chats')
        chat_ids = cursor.fetchall()
        for chat_id in chat_ids:
            try:
                await bot.send_message(chat_id[0], text_to_send)
                successful_sends += 1
            except Exception as e:
                error_message = f"`{chat_id[0]}`: _{e}_"
                error_messages += error_message + "\n"

    reply_text = f"🆒 Повідомлення надіслано. Кількість чатів: `{successful_sends}`"
    if error_messages:
        reply_text += "\n\n⚠️ Помилки:\n" + error_messages

    await message.reply(reply_text, parse_mode="Markdown")
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass

#/edit-----
@dp.message_handler(commands=['edit'])
async def edit(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    try:
        parts = message.text.split()
        user_id = None
        chat_id = message.chat.id
        mention = None

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if message.reply_to_message.from_user.username:
                mention = f"[{message.reply_to_message.from_user.username}](https://t.me/{message.reply_to_message.from_user.username})"
            else:
                mention = message.reply_to_message.from_user.first_name

            if len(parts) == 1:
                cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
                current_value = cursor.fetchone()
                if current_value:
                    await message.reply(f"📊 {mention} має `{current_value[0]}` кг русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await message.reply(f"😬 {mention} ще не має русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                return

            elif len(parts) != 2:
                raise ValueError("⚙️ Неправильний формат. Використовуй `/edit N` у відповідь на повідомлення")
            value = parts[1]
        else:
            if len(parts) < 2:
                raise ValueError("⚙️ Неправильний формат. Використовуй `/edit ID N` або `/edit ID`")
            user_id = int(parts[1])

            user_info = await bot.get_chat_member(chat_id, user_id)
            if user_info.user.username:
                mention = f"[{user_info.user.username}](https://t.me/{user_info.user.username})"
            else:
                mention = user_info.user.first_name

            if len(parts) == 2:
                cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
                current_value = cursor.fetchone()
                if current_value:
                    await message.reply(f"📊 {mention} має `{current_value[0]}` кг русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await message.reply(f"😬 {mention} ще не має русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                return

            value = parts[2]

            user_info = await bot.get_chat_member(chat_id, user_id)
            if user_info.user.username:
                mention = f"[{user_info.user.username}](https://t.me/{user_info.user.username})"
            else:
                mention = user_info.user.first_name

        if ',' in value or '.' in value:
            raise ValueError("⚠️ Введене значення не є цілим числом")

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        current_value = cursor.fetchone()

        if current_value is None:
            current_value = 0
        else:
            current_value = current_value[0]

        if value.startswith('+') or value.startswith('-'):
            updated_value = current_value + int(value)
        else:
            updated_value = int(value)

        if current_value is None:
            cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)',
                           (user_id, chat_id, updated_value))
        else:
            cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?',
                           (updated_value, user_id, chat_id))

        conn.commit()
        await bot.send_message(chat_id=message.chat.id,
                               text=f"🆒 Значення {mention} було змінено на `{updated_value}` кг", parse_mode="Markdown", disable_web_page_preview=True)

        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
    except ValueError as e:
        error_message = await message.reply(str(e))
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
    except OverflowError:
        error_message = await message.reply("⚠️ Занадто велике значення. Спробуй менше число", parse_mode="Markdown")
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass
            

if __name__ == '__main__':
    aiogram.utils.executor.start_polling(dp)
