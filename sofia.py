import aiogram
import logging
import sqlite3
import asyncio
import random
import json
from aiogram.utils.exceptions import BadRequest
from aiogram.dispatcher import filters
from aiogram.types import CallbackQuery, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types

try:
    with open('config.json', 'r') as file:
        config = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error loading config file: {e}")
    exit()

TOKEN = config['TOKEN']
ADMIN = config['ADMIN_ID']
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

conn = sqlite3.connect('sofia.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS user_values 
                 (user_id INTEGER, 
                  chat_id INTEGER, 
                  value INTEGER, 
                  PRIMARY KEY(user_id, chat_id))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS cooldowns (
                  user_id INTEGER,
                  chat_id INTEGER,
                  give TEXT,
                  killru TIMESTAMP,
                  PRIMARY KEY(user_id, chat_id, give))''')

cursor.execute('CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY)')

def add_chat(chat_id):
    cursor.execute('INSERT OR IGNORE INTO chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()

#/start-----
@dp.message_handler(commands=['start'])
async def send_message(message: types.Message):
    add_chat(message.chat.id)
    await message.reply("🫡 Привіт. Я бот для розваг\nВивчай /help")

#/help-----
@dp.message_handler(commands=['help'])
async def send_message(message: types.Message):
    await message.reply("🎮 *Розвивай свою русофобію. Зростай її щодня, і змагайся з друзями*"+
        "\n\n*/killru* — _Спробувати підвищити свою русофобію_"+
        "\n*/my* — _Моя русофобія_"+
        "\n*/give* — _Поділиться русофобією_"+
        "\n*/globaltop* — _Топ всіх гравців_"+
        "\n*/top10* — _Топ 10 гравців_"+
        "\n*/top* — _Топ гравців_"+
        "\n*/statareset* — _Скинути мою статистику_", parse_mode="Markdown")

#/message-----
@dp.message_handler(commands=['message'])
async def broadcast_message(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    text_to_send = message.text.split(" ", 1)[1]
    cursor.execute('SELECT chat_id FROM chats')
    chat_ids = cursor.fetchall()

    successful_sends = 0
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id[0], text_to_send)
            successful_sends += 1
        except Exception as e:
            print(f"Помилка під час розсилки в чат {chat_id[0]}: {e}")

    await message.reply(f"🆒 Повідомлення надіслано. Кількість чатів: `{successful_sends}`", parse_mode="Markdown")

#/statareset-----
@dp.message_handler(commands=['statareset'])
async def reset_user_value(message: types.Message):
    admin = ADMIN

    if message.from_user.id == admin and message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        cursor.execute('UPDATE user_values SET value = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        await message.reply(f"📡 Статистика `{user_id}` обнулена", parse_mode="Markdown")
    elif message.from_user.id != admin and not message.reply_to_message:
        user_id = message.from_user.id
        cursor.execute('UPDATE user_values SET value = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        await message.reply("📡 Твою статистику обнулено")
    else:
        await message.reply("📡 Кого караємо?")

#/killru-----
@dp.message_handler(commands=['killru'])
async def get_benis(message: types.Message):
    add_chat(message.chat.id)
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = datetime.now()

    cursor.execute('SELECT killru FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if result:
        killru = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
        if killru + timedelta(hours=24) > now:
            cooldown_time = (killru + timedelta(hours=24)) - now
            cooldown_time = str(cooldown_time).split('.')[0]
            await message.reply(f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`", parse_mode="Markdown")
            return
    else:
        cursor.execute('INSERT INTO cooldowns (user_id, chat_id, killru) VALUES (?, ?, ?)', (user_id, chat_id, str(now)))
        conn.commit()

    benis = random.randint(-4, 15)
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if result is None and benis < 0:
       benis = abs(benis)

    new_benis = 0
    if result is None:
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, benis))
        conn.commit()
        new_benis = benis
    else:
        new_benis = result[0] + benis
        cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?', (new_benis, user_id, chat_id))
        conn.commit()

    cursor.execute('UPDATE cooldowns SET killru = ? WHERE user_id = ? AND chat_id = ?', (str(now), user_id, chat_id))
    conn.commit()

    if benis >= 0:
        message_text = f"📈 Твоя русофобія збільшилась на `{benis}` кг"
    else:
        message_text = f"📉 Твоя русофобія зменшилась на `{abs(benis)}` кг"

    message_text += f" \n🏷️ Тепер в тебе: `{new_benis}` кг"
    await message.reply(message_text, parse_mode="Markdown")

#/my-----
@dp.message_handler(commands=['my'])
async def show_my_benis(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if result is None:
        await message.reply('😯 Ти ще не грав')
    else:
        benis = result[0]
        await message.reply(f"😡 Твоя русофобія: `{benis}` кг", parse_mode="Markdown")

#/top-----
async def show_top(message: types.Message, limit: int, title: str):
    chat_id = message.chat.id
    cursor.execute(f'SELECT user_id, value FROM user_values WHERE chat_id = ? AND value != 0 ORDER BY value DESC LIMIT {limit}', (chat_id,))
    results = cursor.fetchall()

    if len(results) == 0:
        await message.reply('😯 Ще ніхто не грав')
        return

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

    await message.reply(message_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message_handler(commands=['top10'])
async def top10_handler(message: types.Message):
    await show_top(message, limit=10, title='📊 Топ 10 русофобій')

@dp.message_handler(commands=['top'])
async def top_handler(message: types.Message):
    await show_top(message, limit=101, title='📊 Топ русофобій')

#/globaltop-----
async def show_global_top(message: types.Message, limit: int, title: str):
    cursor.execute(f'SELECT user_id, MAX(value) as max_value FROM user_values WHERE value != 0 GROUP BY user_id ORDER BY max_value DESC LIMIT {limit}')
    results = cursor.fetchall()

    if len(results) == 0:
        await message.reply('😯 Ще ніхто не грав')
        return

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

    await message.reply(message_text, parse_mode="Markdown", disable_web_page_preview=True)

@dp.message_handler(commands=['globaltop'])
async def global_top_handler(message: types.Message):
    await show_global_top(message, limit=201, title='📊 Глобальний топ русофобій')

#/edit-----
@dp.message_handler(commands=['edit'])
async def edit_benis(message: types.Message):
    if message.from_user.id != ADMIN:
        return

    try:
        parts = message.text.split()
        user_id = None
        chat_id = message.chat.id
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if len(parts) != 2:
                raise ValueError("⚙️ Неправильний формат. Використовуй `/edit N` у відповідь на повідомлення", parse_mode="Markdown")
            value = int(parts[1])
        else:
            if len(parts) != 3:
                raise ValueError("⚙️ Неправильний формат. Використовуй `/edit ID N`", parse_mode="Markdown")
            user_id = int(parts[1])
            value = int(parts[2])

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        result = cursor.fetchone()

        if result is None:
            cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, value))
        else:
            cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?', (value, user_id, chat_id))

        conn.commit()
        await message.reply(f"🆒 Значення `{user_id}` було змінено на `{value}` кг", parse_mode="Markdown")
    except ValueError as e:
        await message.reply(str(e))
    except OverflowError:
        await message.reply("⚠️ Занадто велике значення. Спробуй менше число", parse_mode="Markdown")
        
#/give-----
givers = {}
@dp.message_handler(commands=['give'])
async def give_benis(message: types.Message):
    global givers
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("⚙️ Використовуй `/give N` у відповідь на повідомлення", parse_mode="Markdown")
            return

        try:
            value = int(parts[1])
            if value <= 0:
                raise ValueError
            
        except ValueError:
            await message.reply("🤨 Типо розумний? Введи плюсове і ціле число. Наприклад: `/give 5`", parse_mode="Markdown")
            return

        giver_id = message.from_user.id
        chat_id = message.chat.id
        now = datetime.now()

        cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL', 
                       (giver_id, chat_id))
        last_given = cursor.fetchone()

        if last_given:
            last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f')
            if last_given + timedelta(hours=12) > now:
                cooldown_time = (last_given + timedelta(hours=12)) - now
                cooldown_time = str(cooldown_time).split('.')[0]
                await message.reply(f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`", parse_mode="Markdown")
                return

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
        result = cursor.fetchone()
        if not result or result[0] < value:
            await message.reply(f"⚠️ У тебе `{result[0] if result else 0}` кг. Цього недостатньо", parse_mode="Markdown")
            return

        inline_kb = InlineKeyboardMarkup(row_width=2)
        btn1 = InlineKeyboardButton('✅ Так', callback_data=f'give_{value}_yes_{message.reply_to_message.from_user.id}')
        btn2 = InlineKeyboardButton('❌ Ні', callback_data=f'give_{value}_no_{message.reply_to_message.from_user.id}')
        inline_kb.add(btn1, btn2)
        
        current_balance = result[0] if result else 0

        receiver_mention = ('[' + message.reply_to_message.from_user.username + ']' + '(https://t.me/' + message.reply_to_message.from_user.username + ')') if message.reply_to_message.from_user.username else message.reply_to_message.from_user.first_name  # Получение упоминания получателя

        sent_message = await message.reply(f"🔄 Ти збираєшся передати `{value}` кг русофобії {receiver_mention}\n🏷️ В тебе: `{current_balance}` кг. Підтверджуєш?", 
                                   reply_markup=inline_kb, parse_mode="Markdown", disable_web_page_preview=True)

        givers[sent_message.message_id] = message.from_user.id
    else:
        await message.reply("⚙️ Використовуй `/give N` у відповідь на повідомлення", parse_mode="Markdown")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('give_'))
async def process_give_callback(callback_query: CallbackQuery):
    global givers  
    _, value, answer, receiver_id = callback_query.data.split('_')
    value = int(value)
    receiver_id = int(receiver_id)
    giver_id = givers.get(callback_query.message.message_id)

    receiver = await bot.get_chat_member(callback_query.message.chat.id, receiver_id)
    receiver_mention = ('[' + receiver.user.username + ']' + '(https://t.me/' + receiver.user.username + ')') if receiver.user.username else receiver.user.first_name

    now = datetime.now()
    cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL', 
                   (giver_id, callback_query.message.chat.id))
    last_given = cursor.fetchone()
    if last_given:
        last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f')
        if last_given + timedelta(hours=12) > now:
            cooldown_time = (last_given + timedelta(hours=12)) - now
            cooldown_time = str(cooldown_time).split('.')[0]
            await bot.edit_message_text(
                text=f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`", 
                chat_id=callback_query.message.chat.id, 
                message_id=callback_query.message.message_id,
                parse_mode="Markdown")
            return

    if giver_id != callback_query.from_user.id:
        try:
            await bot.answer_callback_query(callback_query.id, text="❌ Ці кнопочки не для тебе!", show_alert=True)
        except Exception as e:
            logging.exception(e)
        return

    if answer == 'yes':
        cursor.execute('UPDATE user_values SET value = value - ? WHERE user_id = ? AND chat_id = ?', 
                       (value, giver_id, callback_query.message.chat.id))
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?) ON CONFLICT(user_id, chat_id) DO UPDATE SET value = value + ?', 
                       (receiver_id, callback_query.message.chat.id, value, value))
        conn.commit()

        cursor.execute('UPDATE cooldowns SET give = ? WHERE user_id = ? AND chat_id = ?', 
                       (str(datetime.now()), giver_id, callback_query.message.chat.id))
        conn.commit()

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, callback_query.message.chat.id))
        updated_benis = cursor.fetchone()[0]

        await bot.edit_message_text(
            text=f"✅ Ти передав `{value}` кг русофобії {receiver_mention}\n🏷️ Тепер в тебе: `{updated_benis}` кг", 
            chat_id=callback_query.message.chat.id, 
            message_id=callback_query.message.message_id, 
            parse_mode="Markdown", 
            disable_web_page_preview=True
        )
    else:
        await bot.edit_message_text(text="❌ Передача русофобії скасована", 
                                    chat_id=callback_query.message.chat.id, 
                                    message_id=callback_query.message.message_id)

if __name__ == '__main__':
    executor.start_polling(dp)