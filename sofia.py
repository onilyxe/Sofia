import asyncio
import json
import logging
import random
import sqlite3
import psutil
import aiogram
import configparser
from asyncio import sleep
from datetime import datetime, timedelta, time
from aiogram import Bot, Dispatcher, types
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.utils.exceptions import BadRequest, MessageCantBeDeleted, BotKicked, ChatNotFound
from aiogram.dispatcher.middlewares import BaseMiddleware

config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['SOFIA']
    ADMIN = int(config['ID']['ADMIN'])
    ALIASES = {k: int(v) for k, v in config['ALIASES'].items()}
except (FileNotFoundError, KeyError) as e:
    print(f"Помилка завантаження конфігураційного файлу: {e}")
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

class DatabaseMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if message.text and message.text.startswith('/'):
            current_time = datetime.now()
            cursor.execute('SELECT id, count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1', 
                        (current_time.replace(hour=0, minute=0, second=0, microsecond=0), 
                        current_time.replace(hour=23, minute=59, second=59, microsecond=999999)))

            row = cursor.fetchone()
            if row:
                cursor.execute('UPDATE queries SET count = count + 1 WHERE id = ?', (row[0],))
            else:
                cursor.execute('INSERT INTO queries (datetime, count) VALUES (?, 1)', (current_time,))
        
            conn.commit()

dp.middleware.setup(DatabaseMiddleware())

conn = sqlite3.connect('sofia.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS user_values (user_id INTEGER, chat_id INTEGER, value INTEGER, PRIMARY KEY(user_id, chat_id))''')
cursor.execute('''CREATE TABLE IF NOT EXISTS cooldowns (user_id INTEGER, chat_id INTEGER, give TEXT, killru TIMESTAMP, PRIMARY KEY(user_id, chat_id, give))''')
cursor.execute('CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY)')
cursor.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, datetime TIMESTAMP NOT NULL, count INTEGER NOT NULL DEFAULT 0)''')

def add_chat(chat_id):
    cursor.execute('INSERT OR IGNORE INTO chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()

#/start-----
@dp.message_handler(commands=['start'])
async def send_message(message: types.Message):
    add_chat(message.chat.id)
    reply = await message.reply("🫡 Привіт. Я бот для розваг\nВивчай /help")

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, reply.message_id)
    except MessageCantBeDeleted:
        pass

#/help-----
@dp.message_handler(commands=['help'])
async def send_message(message: types.Message):
    reply = await message.reply(
        "🎮 *Розвивай свою русофобію. Зростай її щодня, і змагайся з друзями*" +
        "\n\n*/killru* — _Спробувати підвищити свою русофобію_" +
        "\n*/my* — _Моя русофобія_" +
        "\n*/give* — _Поділиться русофобією_" +
        "\n*/globaltop* — _Топ всіх гравців_" +
        "\n*/top10* — _Топ 10 гравців_" +
        "\n*/top* — _Топ гравців_" +
        "\n*/leave* — _Покинути гру_"+
        "\n*/ping* — _статус бота_", parse_mode="Markdown")

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, reply.message_id)
    except MessageCantBeDeleted:
        pass

#/killru-----
@dp.message_handler(commands=['killru'])
async def get_benis(message: types.Message):
    add_chat(message.chat.id)
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = datetime.now()

    username_or_name = (
        '[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')'
    ) if message.from_user.username else message.from_user.first_name

    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    user_value_result = cursor.fetchone()

    isNewUser = False

    if not user_value_result:
        isNewUser = True
        welcome_message = await message.reply(f"🎉 {username_or_name}, вітаю! Ти тепер зареєстрований у грі русофобії!", parse_mode="Markdown",
                                   disable_web_page_preview=True)
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, 0))
        conn.commit()

    cursor.execute('SELECT killru FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    cooldown_result = cursor.fetchone()
    killru = None

    if cooldown_result and cooldown_result[0]:
        killru = datetime.strptime(cooldown_result[0], '%Y-%m-%d %H:%M:%S.%f')
    if not killru or isNewUser:
        cursor.execute('UPDATE cooldowns SET killru = ? WHERE user_id = ? AND chat_id = ?', (str(now), user_id, chat_id))
        conn.commit()
    if killru and killru + timedelta(hours=24) > now:
        remaining_time = (killru + timedelta(hours=24)) - now
        hours, remainder = divmod(remaining_time.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        cooldown_time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

        bonus_message = ""
        special_times = ['00:00:00', '00:13:37', '01:00:00', '01:11:11', '02:00:00', '02:22:22', '22:22:22', '03:00:00', '04:00:00', '04:20:00', '05:00:00', '06:00:00', '07:00:00', '08:00:00', '09:00:00', '10:00:00', '11:00:00', '12:00:00', '13:00:00', '14:00:00', '15:00:00', '16:00:00', '17:00:00', '18:00:00', '19:00:00', '20:00:00', '21:00:00', '22:00:00', '23:00:00']

        if cooldown_time_str in special_times:
            bonus_message = "\n🎉 Гарний час. Бонус + `5` кг!"
            cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            result = cursor.fetchone()
            new_benis = result[0] + 5 if result else 5
            cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?',
                   (new_benis, user_id, chat_id))
            conn.commit()

        cooldown_time = str(remaining_time).split('.')[0]
        cooldown_message = await message.reply(
            f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`{bonus_message}", 
            parse_mode="Markdown")

        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=cooldown_message.message_id)
        except MessageCantBeDeleted:
            pass
        return

    else:
        cursor.execute('SELECT * FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        if cursor.fetchone():
            cursor.execute('UPDATE cooldowns SET killru = ? WHERE user_id = ? AND chat_id = ?', (str(now), user_id, chat_id))
        else:
            cursor.execute('INSERT INTO cooldowns (user_id, chat_id, killru) VALUES (?, ?, ?)', (user_id, chat_id, str(now)))
        conn.commit()

    benis = random.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

    if isNewUser:
        benis = abs(benis)

    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    new_benis = 0
    if result is None:
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, benis))
        conn.commit()
        new_benis = benis
    else:
        new_benis = result[0] + benis
        cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?',
                       (new_benis, user_id, chat_id))
        conn.commit()

    cursor.execute('UPDATE cooldowns SET killru = ? WHERE user_id = ? AND chat_id = ?', (str(now), user_id, chat_id))
    conn.commit()

    if benis >= 0:
        message_text = f"📈 {username_or_name}, твоя русофобія збільшилась на `{benis}` кг"
    else:
        message_text = f"📉 {username_or_name}, твоя русофобія зменшилась на `{abs(benis)}` кг"

    message_text += f" \n🏷️ Тепер в тебе: `{new_benis}` кг"
    reply = await bot.send_message(chat_id=message.chat.id, text=message_text, parse_mode="Markdown",
                                   disable_web_page_preview=True)

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        if isNewUser:
            await bot.delete_message(chat_id=message.chat.id, message_id=welcome_message.message_id)
    except MessageCantBeDeleted:
        pass

#/my-----
@dp.message_handler(commands=['my'])
async def show_my_benis(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if message.from_user.username:
        mention = f"[{message.from_user.username}](https://t.me/{message.from_user.username})"
    else:
        mention = message.from_user.first_name

    if result is None:
        response = await message.reply(f'😯 {mention}, ти ще не грав', parse_mode="Markdown",
                                        disable_web_page_preview=True)
    else:
        benis = result[0]
        response = await message.reply(f"😡 {mention}, твоя русофобія: `{benis}` кг", parse_mode="Markdown",
                                       disable_web_page_preview=True)

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=response.message_id)
    except MessageCantBeDeleted:
        pass

#/give-----
givers = {}
original_messages = {}
@dp.message_handler(commands=['give'])
async def give_benis(message: types.Message):
    global givers
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        parts = message.text.split()
        if len(parts) != 2:
            reply = await bot.send_message(message.chat.id, "⚙️ Використовуй `/give N` у відповідь на повідомлення",
                                           parse_mode="Markdown")
            await asyncio.sleep(3600)
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.delete_message(message.chat.id, reply.message_id)
            return

        try:
            value = int(parts[1])
            if value <= 0:
                raise ValueError

        except ValueError:
            reply = await bot.send_message(message.chat.id,
                                           "🤨 Типо розумний? Введи плюсове і ціле число. Наприклад: `/give 5` у відповідь на повідомлення",
                                           parse_mode="Markdown")
            await asyncio.sleep(3600)
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.delete_message(message.chat.id, reply.message_id)
            return

        giver_id = message.from_user.id
        chat_id = message.chat.id
        now = datetime.now()

        cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL',
                       (giver_id, chat_id))
        last_given = cursor.fetchone()

        if last_given and last_given[0]:
            last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f')
            if last_given + timedelta(hours=12) > now:
                cooldown_time = (last_given + timedelta(hours=12)) - now
                cooldown_time = str(cooldown_time).split('.')[0]
                reply = await bot.send_message(message.chat.id,
                                               f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`",
                                               parse_mode="Markdown")
                await asyncio.sleep(3600)
                await bot.delete_message(message.chat.id, message.message_id)
                await bot.delete_message(message.chat.id, reply.message_id)
                return
        else:
            last_given = None

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
        result = cursor.fetchone()
        if not result or result[0] < value:
            reply = await bot.send_message(message.chat.id,
                                           f"⚠️ У тебе `{result[0] if result else 0}` кг. Цього недостатньо",
                                           parse_mode="Markdown")
            await asyncio.sleep(3600)
            await bot.delete_message(message.chat.id, message.message_id)
            await bot.delete_message(message.chat.id, reply.message_id)
            return

        inline_kb = InlineKeyboardMarkup(row_width=2)
        btn1 = InlineKeyboardButton('✅ Так', callback_data=f'give_{value}_yes_{message.reply_to_message.from_user.id}')
        btn2 = InlineKeyboardButton('❌ Ні', callback_data=f'give_{value}_no_{message.reply_to_message.from_user.id}')
        inline_kb.add(btn1, btn2)

        current_balance = result[0] if result else 0

        receiver_mention = (
                    '[' + message.reply_to_message.from_user.username + ']' + '(https://t.me/' + message.reply_to_message.from_user.username + ')') if message.reply_to_message.from_user.username else message.reply_to_message.from_user.first_name

        giver_mention = (
                    '[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

        sent_message = await bot.send_message(chat_id=message.chat.id,
                                              text=f"🔄 {giver_mention} збирається передати `{value}` кг русофобії {receiver_mention}\n🏷️ В тебе: `{current_balance}` кг. Підтверджуєш?",
                                              reply_markup=inline_kb, parse_mode="Markdown",
                                              disable_web_page_preview=True)

        givers[sent_message.message_id] = message.from_user.id
        original_messages[sent_message.message_id] = message.message_id

        await asyncio.sleep(3600)
        await bot.delete_message(message.chat.id, message.message_id)

    else:
        reply = await bot.send_message(message.chat.id, "⚙️ Використовуй `/give N` у відповідь на повідомлення",
                                       parse_mode="Markdown")
        await asyncio.sleep(3600)
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(message.chat.id, reply.message_id)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('give_'))
async def process_give_callback(callback_query: CallbackQuery):
    global givers, original_messages
    _, value, answer, receiver_id = callback_query.data.split('_')
    value = int(value)
    receiver_id = int(receiver_id)
    giver_id = givers.get(callback_query.message.message_id)

    receiver = await bot.get_chat_member(callback_query.message.chat.id, receiver_id)
    receiver_mention = (
                '[' + receiver.user.username + ']' + '(https://t.me/' + receiver.user.username + ')') if receiver.user.username else receiver.user.first_name

    now = datetime.now()
    cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL',
                   (giver_id, callback_query.message.chat.id))
    last_given = cursor.fetchone()
    if last_given and last_given[0]:
        last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f')
        if last_given + timedelta(hours=12) > now:
            cooldown_time = (last_given + timedelta(hours=12)) - now
            cooldown_time = str(cooldown_time).split('.')[0]
            reply = await bot.edit_message_text(
                text=f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`",
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                parse_mode="Markdown")
            await asyncio.sleep(3600)
            try:
                await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
            except MessageCantBeDeleted:
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
        cursor.execute('UPDATE user_values SET value = value - ? WHERE user_id = ? AND chat_id = ?',
                       (value, giver_id, callback_query.message.chat.id))
        cursor.execute(
            'INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?) ON CONFLICT(user_id, chat_id) DO UPDATE SET value = value + ?',
            (receiver_id, callback_query.message.chat.id, value, value))
        conn.commit()

        cursor.execute('UPDATE cooldowns SET give = ? WHERE user_id = ? AND chat_id = ?',
                       (str(datetime.now()), giver_id, callback_query.message.chat.id))
        conn.commit()

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?',
                       (giver_id, callback_query.message.chat.id))
        updated_benis = cursor.fetchone()[0]

        if callback_query.from_user.username:
            giver_mention = f"[{callback_query.from_user.username}](https://t.me/{callback_query.from_user.username})"
        else:
            giver_mention = callback_query.from_user.first_name

        await bot.answer_callback_query(callback_query.id, "✅ Успішно")
        await bot.edit_message_text(
            text=f"✅ {giver_mention} передав `{value}` кг русофобії {receiver_mention}\n🏷️ Тепер в тебе: `{updated_benis}` кг",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        await asyncio.sleep(3600)
        try:
            await bot.delete_message(callback_query.message.chat.id,
                                     original_messages.get(callback_query.message.message_id))
        except MessageCantBeDeleted:
            pass
    else:
        await bot.answer_callback_query(callback_query.id, "❌ Скасовано")
        await bot.edit_message_text(
            text="❌ Передача русофобії скасована",
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id
        )

        await asyncio.sleep(3600)
        try:
            await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
        except MessageCantBeDeleted:
            pass

#/globaltop-----
async def show_global_top(message: types.Message, limit: int, title: str):
    cursor.execute(
        f'SELECT user_id, MAX(value) as max_value FROM user_values WHERE value != 0 GROUP BY user_id ORDER BY max_value DESC LIMIT {limit}')
    results = cursor.fetchall()

    if len(results) == 0:
        response = await message.reply('😯 Ще ніхто не грав')
    else:
        async def fetch_username(user_id):
            try:
                user_info = await bot.get_chat(user_id)
                if user_info.username:
                    return f'[{user_info.username}](https://t.me/{user_info.username})'
                else:
                    return user_info.first_name
            except aiogram.utils.exceptions.BadRequest:
                return None

        tasks = [fetch_username(user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        message_text = f'{title}:\n'
        count = 0
        for user_name, (_, benis) in zip(user_names, results):
            if user_name:
                count += 1
                message_text += f'{count}. {user_name}: {benis} кг\n'

        response = await message.reply(message_text, parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=response.message_id)
    except MessageCantBeDeleted:
        pass

@dp.message_handler(commands=['globaltop'])
async def global_top_handler(message: types.Message):
    await show_global_top(message, limit=201, title='🌏 Глобальний топ русофобій')

#/top-----
async def show_top(message: types.Message, limit: int, title: str):
    chat_id = message.chat.id
    cursor.execute(
        f'SELECT user_id, value FROM user_values WHERE chat_id = ? AND value != 0 ORDER BY value DESC LIMIT {limit}',
        (chat_id,))
    results = cursor.fetchall()

    if len(results) == 0:
        response = await message.reply('😯 Ще ніхто не грав')
    else:
        async def fetch_username(user_id):
            try:
                user_info = await bot.get_chat_member(chat_id, user_id)
                if user_info.user.username:
                    return f'[{user_info.user.username}](https://t.me/{user_info.user.username})'
                else:
                    return user_info.user.full_name
            except aiogram.utils.exceptions.BadRequest:
                return None

        tasks = [fetch_username(user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        message_text = f'{title}:\n'
        count = 0
        for user_name, (_, benis) in zip(user_names, results):
            if user_name:
                count += 1
                message_text += f'{count}. {user_name}: {benis} кг\n'

        response = await message.reply(message_text, parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=response.message_id)
    except MessageCantBeDeleted:
        pass

@dp.message_handler(commands=['top10'])
async def top10_handler(message: types.Message):
    await show_top(message, limit=10, title='📊 Топ 10 русофобій')

@dp.message_handler(commands=['top'])
async def top_handler(message: types.Message):
    await show_top(message, limit=101, title='📊 Топ русофобій')

#/leave-----
leavers = {}
@dp.message_handler(commands=['leave'])
async def leave_game(message: types.Message):
    confirmation_keyboard = InlineKeyboardMarkup(row_width=2)
    confirmation_keyboard.add(
        InlineKeyboardButton("✅ Так", callback_data="confirm_leave"),
        InlineKeyboardButton("❌ Ні", callback_data="cancel_leave")
    )
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    username_or_name = (
        '[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')'
    ) if message.from_user.username else message.from_user.first_name

    cursor.execute('SELECT * FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    user_exists = cursor.fetchone()

    if not user_exists:
        msg = await bot.send_message(chat_id, f"😯 {username_or_name}, ти й так не граєш", parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg.message_id)
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except MessageCantBeDeleted:
            pass
    else:
        msg = await bot.send_message(chat_id, f"😡 {username_or_name}, ти впевнений, що хочеш ливнути з гри? Твої дані буде видалено з бази даних", reply_markup=confirmation_keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        leavers[msg.message_id] = user_id
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except MessageCantBeDeleted:
            pass

@dp.callback_query_handler(lambda c: c.data in ['confirm_leave', 'cancel_leave'])
async def process_leave_confirmation(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id

    if leavers.get(callback_query.message.message_id) != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    username_or_name = (
        '[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')'
    ) if callback_query.from_user.username else callback_query.from_user.first_name

    if callback_query.data == 'confirm_leave':
        cursor.execute('DELETE FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        #cursor.execute('UPDATE cooldowns SET killru = NULL WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        conn.commit()
        await bot.answer_callback_query(callback_query.id, "✅ Успішно")
        await bot.edit_message_text(f"🤬 {username_or_name}, ти покинув гру, і тебе було видалено з бази даних", chat_id, callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await bot.answer_callback_query(callback_query.id, "❌ Скасовано")
        await bot.edit_message_text(f"🫡 {username_or_name}, ти залишився у грі", chat_id, callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)
        except MessageCantBeDeleted:
            pass

#/ping-----
@dp.message_handler(commands=['ping'])
async def ping(message: types.Message):
    start_time = datetime.now()
    await bot.get_me()
    end_time = datetime.now()
    ping_time = (end_time - start_time).total_seconds() * 1000

    cursor.execute('SELECT count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1',
                   (start_time.replace(hour=0, minute=0, second=0, microsecond=0),
                    start_time.replace(hour=23, minute=59, second=59, microsecond=999999)))

    requests_today = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(count) FROM queries WHERE datetime >= ?', (start_time - timedelta(days=7),))
    requests_last_week = cursor.fetchone()[0] or 0

    cursor.execute('SELECT SUM(count) FROM queries')
    requests_all_time = cursor.fetchone()[0] or 0

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()

    response = await message.reply(
        f"📡 Ping: `{ping_time:.2f}` ms\n\n"
        f"🔥 CPU: `{cpu_usage}%`\n"
        f"💾 RAM: `{memory_info.percent}%`\n\n"
        f"📊 Кількість запитів\n"
        f"_За сьогодні:_ `{requests_today}`\n"
        f"_За тиждень:_ `{requests_last_week}`\n"
        f"_За весь час:_ `{requests_all_time}`", parse_mode="Markdown"
    )

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        await bot.delete_message(response.chat.id, response.message_id)
    except MessageCantBeDeleted:
        pass
    return

#/chatlist-----
@dp.message_handler(commands=['chatlist'])  
async def list_chats(message: types.Message):
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
    
    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=reply.message_id)
    except MessageCantBeDeleted:
        pass

#/message-----
@dp.message_handler(commands=['message'])
async def broadcast_message(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    parts = message.text.split(" ", 2)

    if len(parts) < 2:
        info_message = await message.reply(
            "ℹ️ Ця команда дозволяє розсилати повідомлення у різні чати\n`/message <text>` - в усі чати\n`/message <ID>/<alias> <text>` - в один чат",
            parse_mode="Markdown")
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=info_message.message_id)
        except MessageCantBeDeleted:
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
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except MessageCantBeDeleted:
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
    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except MessageCantBeDeleted:
        pass

#/edit-----
@dp.message_handler(commands=['edit'])
async def edit_benis(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    try:
        parts = message.text.split()
        user_id = None
        chat_id = message.chat.id
        user_mention = None

        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if message.reply_to_message.from_user.username:
                user_mention = f"[{message.reply_to_message.from_user.username}](https://t.me/{message.reply_to_message.from_user.username})"
            else:
                user_mention = message.reply_to_message.from_user.first_name

            if len(parts) == 1:
                cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
                current_value = cursor.fetchone()
                if current_value:
                    await message.reply(f"📊 {user_mention} має `{current_value[0]}` кг русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await message.reply(f"😬 {user_mention} ще не має русофобії", parse_mode="Markdown", disable_web_page_preview=True)
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
                user_mention = f"[{user_info.user.username}](https://t.me/{user_info.user.username})"
            else:
                user_mention = user_info.user.first_name

            if len(parts) == 2:
                cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
                current_value = cursor.fetchone()
                if current_value:
                    await message.reply(f"📊 {user_mention} має `{current_value[0]}` кг русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await message.reply(f"😬 {user_mention} ще не має русофобії", parse_mode="Markdown", disable_web_page_preview=True)
                return

            value = parts[2]

            user_info = await bot.get_chat_member(chat_id, user_id)
            if user_info.user.username:
                user_mention = f"[{user_info.user.username}](https://t.me/{user_info.user.username})"
            else:
                user_mention = user_info.user.first_name

        if ',' in value or '.' in value:
            raise ValueError("🚫 Введене значення не є цілим числом.")

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
                               text=f"🆒 Значення {user_mention} було змінено на `{updated_value}` кг",
                               parse_mode="Markdown", disable_web_page_preview=True)

        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except MessageCantBeDeleted:
            pass
    except ValueError as e:
        error_message = await message.reply(str(e))
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except MessageCantBeDeleted:
            pass
    except OverflowError:
        error_message = await message.reply("⚠️ Занадто велике значення. Спробуй менше число", parse_mode="Markdown")
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except MessageCantBeDeleted:
            pass

#/statareset-----
@dp.message_handler(commands=['statareset'])
async def reset_user_value(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    if not message.reply_to_message and not (len(message.text.split()) > 1 and message.text.split()[1].isdigit()):
        error_message = await message.reply("📡 Кого караємо?")
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except MessageCantBeDeleted:
            pass
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        username = message.reply_to_message.from_user.username
        mention = f'[{username}](https://t.me/{username})' if username else message.reply_to_message.from_user.first_name
    else:
        user_id = int(message.text.split()[1])
        mention = f'{user_id}'

    cursor.execute('SELECT value FROM user_values WHERE user_id = ?', (user_id,))
    current_value = cursor.fetchone()

    if not current_value:
        error_message = await message.reply(f"⚙️ Користувач `{user_id}` не знайдений у базі даних", parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(3600)
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=error_message.message_id)
        except MessageCantBeDeleted:
            pass
        return

    cursor.execute('UPDATE user_values SET value = 0 WHERE user_id = ?', (user_id,))
    conn.commit()

    confirmation_message = await bot.send_message(chat_id=message.chat.id, text=f"📡 Статистика {mention} обнулена", parse_mode="Markdown", disable_web_page_preview=True)

    await asyncio.sleep(3600)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except MessageCantBeDeleted:
        pass
    return
            
if __name__ == '__main__':
    executor.start_polling(dp)
