import json
import random
import aiogram
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from aiogram.utils.exceptions import BadRequest
import asyncio

with open('config.json', 'r') as file:
    config = json.load(file)

TOKEN = config['TOKEN']
ADMIN_ID = config['ADMIN_ID']
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect('sofia.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS user_values 
                 (user_id INTEGER, 
                  chat_id INTEGER, 
                  value INTEGER, 
                  PRIMARY KEY(user_id, chat_id))''')

cursor.execute('''CREATE TABLE IF NOT EXISTS user_cooldowns (
                  user_id INTEGER,
                  chat_id INTEGER,
                  command TEXT,
                  last_used TIMESTAMP,
                  PRIMARY KEY(user_id, chat_id, command))''')


cursor.execute('CREATE TABLE IF NOT EXISTS chats (chat_id INTEGER PRIMARY KEY)')

cooldowns = {}

def add_chat(chat_id):
    cursor.execute('INSERT OR IGNORE INTO chats (chat_id) VALUES (?)', (chat_id,))
    conn.commit()

#/message-----
@dp.message_handler(commands=['message'])
async def broadcast_message(message: types.Message):
    if message.from_user.id != ADMIN_ID:
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

    await message.reply(f"Повідомлення надіслано в {successful_sends} чатів.")
    
#/killru-----
@dp.message_handler(commands=['killru'])
async def get_benis(message: types.Message):
    add_chat(message.chat.id)
    user_id = message.from_user.id
    chat_id = message.chat.id
    now = datetime.now()

    cursor.execute('SELECT last_used FROM user_cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if result:
        last_used = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S.%f')
        if last_used + timedelta(hours=24) > now:
            cooldown_time = (last_used + timedelta(hours=24)) - now
            cooldown_time = str(cooldown_time).split('.')[0]
            await message.reply(f"ℹ️Ти ще не можеш грати. Спробуй через {cooldown_time}")
            return
    else:
        cursor.execute('INSERT INTO user_cooldowns (user_id, chat_id, last_used) VALUES (?, ?, ?)', (user_id, chat_id, str(now)))
        conn.commit()

    benis = random.randint(-4, 15)
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if result is None:
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, benis))
        conn.commit()
    else:
        new_benis = result[0] + benis
        cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?', (new_benis, user_id, chat_id))
        conn.commit()

    cursor.execute('UPDATE user_cooldowns SET last_used = ? WHERE user_id = ? AND chat_id = ?', (str(now), user_id, chat_id))
    conn.commit()

    if benis >= 0:
        message_text = f"📈Твоя русофобія збільшилась на {benis} кг"
    else:
        message_text = f"📉Твоя русофобія зменшилась на {abs(benis)} кг"
    await message.reply(message_text)

#/my-----
@dp.message_handler(commands=['my'])
async def show_my_benis(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
    result = cursor.fetchone()

    if result is None:
        await message.reply('😯Ти ще не грав')
    else:
        benis = result[0]
        await message.reply(f"😡Твоя русофобія: {benis} кг")

async def get_user_info(chat_id, user_id):
    try:
        user = await bot.get_chat_member(chat_id, user_id)
        return user.user.username
    except Exception as e:
        print(f"Помилка отримання користувача: {e}")
        return None

#/give-----
@dp.message_handler(commands=['give'])
async def give_benis(message: types.Message):
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        parts = message.text.split()
        if len(parts) != 2:
            await message.reply("⚙️ Неправильний формат. Використовуй /give <значення> у відповідь на повідомлення")
            return

        try:
            value = int(parts[1])
            if value <= 0:
                raise ValueError
            
        except ValueError:
            await message.reply("🤨 Типо розумний? Введи позитивне число")
            return

        giver_id = message.from_user.id
        receiver_id = message.reply_to_message.from_user.id
        chat_id = message.chat.id
        now = datetime.now()

        cursor.execute('SELECT command FROM user_cooldowns WHERE user_id = ? AND chat_id = ? AND command IS NOT NULL', 
                       (giver_id, chat_id))
        last_given = cursor.fetchone()

        if last_given:
            last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S.%f')
            if last_given + timedelta(hours=12) > now:
                cooldown_time = (last_given + timedelta(hours=12)) - now
                cooldown_time = str(cooldown_time).split('.')[0]
                await message.reply(f"ℹ️ Ти ще не можеш передати русофобію. Спробуй через {cooldown_time}")
                return

        cursor.execute('UPDATE user_cooldowns SET command = ? WHERE user_id = ? AND chat_id = ?', 
                       (str(now), giver_id, chat_id))
        conn.commit()

        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
        result = cursor.fetchone()
        if not result or result[0] < value:
            await message.reply(f"😯 У тебе {result[0] if result else 0} кг. Цього недостатньо")
            return

        cursor.execute('UPDATE user_values SET value = value - ? WHERE user_id = ? AND chat_id = ?', 
                       (value, giver_id, chat_id))
        cursor.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?) ON CONFLICT(user_id, chat_id) DO UPDATE SET value = value + ?', 
                       (receiver_id, chat_id, value, value))
        conn.commit()

        # Получаем обновленное значение русофобии дарителя
        cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
        updated_benis = cursor.fetchone()[0]

        await message.reply(f"✅ Ти передав {value} кг русофобії @{message.reply_to_message.from_user.username if message.reply_to_message.from_user.username else message.reply_to_message.from_user.first_name}. Залишок: {updated_benis} кг.")
    else:
        await message.reply("⚙️ Ділитися русофобією потрібно у відповідь на повідомлення")

#/top10-----
@dp.message_handler(commands=['top10'])
async def show_top_benis(message: types.Message):
    chat_id = message.chat.id
    cursor.execute('SELECT user_id, value FROM user_values WHERE chat_id = ? ORDER BY value DESC LIMIT 10', (chat_id,))
    results = cursor.fetchall()

    if len(results) == 0:
        await message.reply('😯Ще ніхто не грав')
        return

    async def fetch_username(user_id):
        return await get_user_info(message.chat.id, user_id)

    tasks = [fetch_username(user_id) for user_id, _ in results]
    user_names = await asyncio.gather(*tasks)

    message_text = '📊Топ русофобій:\n'
    for i, (user_name, (user_id, benis)) in enumerate(zip(user_names, results)):
        if user_name:
            message_text += f'{i+1}. <a href="https://t.me/{user_name}">{user_name}</a>: {benis} кг\n'

    await message.reply(message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

#/top-----
@dp.message_handler(commands=['top'])
async def show_top_benis(message: types.Message):
    chat_id = message.chat.id
    cursor.execute('SELECT user_id, value FROM user_values WHERE chat_id = ? ORDER BY value DESC LIMIT 100', (chat_id,))
    results = cursor.fetchall()

    if len(results) == 0:
        await message.reply('😯Ще ніхто не грав')
        return

    async def fetch_username(user_id):
        return await get_user_info(message.chat.id, user_id)

    tasks = [fetch_username(user_id) for user_id, _ in results]
    user_names = await asyncio.gather(*tasks)

    message_text = '📊Топ русофобій:\n'
    for i, (user_name, (user_id, benis)) in enumerate(zip(user_names, results)):
        if user_name:
            message_text += f'{i+1}. <a href="https://t.me/{user_name}">{user_name}</a>: {benis} кг\n'

    await message.reply(message_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

#/edit-----
@dp.message_handler(commands=['edit'])
async def edit_benis(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()
        user_id = None
        
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            if len(parts) != 2:
                raise ValueError("Неправильний формат. Використовуй /edit <value>")
            value = int(parts[1])
        else:
            if len(parts) != 3:
                raise ValueError("Неправильний формат. Використовуй /edit <user_id> <value>")
            user_id = int(parts[1])
            value = int(parts[2])

        cursor.execute('SELECT value FROM user_values WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute('INSERT INTO user_values VALUES (?, ?)', (user_id, value))
        else:
            cursor.execute('UPDATE user_values SET value = ? WHERE user_id = ?', (value, user_id))

        conn.commit()
        await message.reply(f"🚨Значення {user_id} було змінено на {value} кг")
    except ValueError as e:
        await message.reply(str(e))

#/statareset-----
@dp.message_handler(commands=['statareset'])
async def reset_user_value(message: types.Message):
    admin_id = ADMIN_ID

    if message.from_user.id == admin_id and message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        cursor.execute('UPDATE user_values SET value = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        await message.reply(f"📡Статистика {user_id} обнулена")
    elif message.from_user.id != admin_id and not message.reply_to_message:
        user_id = message.from_user.id
        cursor.execute('UPDATE user_values SET value = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        await message.reply("📡Твою статистику обнулено")
    else:
        await message.reply("📡Кого караємо?")

#/start-----
@dp.message_handler(commands=['start'])
async def send_message(message: types.Message):
    add_chat(message.chat.id)
    await message.reply("🫡Привіт. Я бот для розваг\nВивчай /help")

#/game-----
@dp.message_handler(commands=['game'])
async def send_message(message: types.Message):
    await message.reply("🎮*Розвивай свою русофобію. Зростай її щодня, і змагайся з друзями*"+
        "\n\n*/killru* — _Спробувати підвищити свою русофобію._"+
        "\n*/my* — _Моя русофобія._"+
        "\n*/give* — _Поділиться русофобією._"+
        "\n*/top10* — _Топ 10 гравців._"+
        "\n*/top* — _Топ гравців._"+
        "\n*/statareset* — _Скинути мою статистику._", parse_mode="Markdown")

#/secret-----
@dp.message_handler(commands=['secret'])
async def send_message(message: types.Message):
    add_chat(message.chat.id)
    await message.reply("Бот створювався спочатку для байта юзерів у чаті. Ноунейми заходили в чат і тикали відразу команду, після цього в чаті ніколи не з'являлися. Вирішив зробити байт команди, які кикають таких \"індивідуумів\". Все що в /bluetext і /roulet просто кикає учасників. Ще є /kekmi яка теж кикає з чату", parse_mode="Markdown")

#/help-----
@dp.message_handler(commands=['help'])
async def send_message(message: types.Message):
    await message.reply("⚙️*Список команд:*"+
    "\n\n*/start* — _запустити бота._"+
    "\n*/help* — _це повідомлення._"+
    "\n*/bluetext* — _синій текст._"+
    "\n*/secret* — _не розповідай нікому._"+
    "\n*/id* — _Показує твій ID, якщо відповідь на користувача, то його. Допиши_ `chat`_, і покаже ID чату._"+
    "\n\n🎮Гра виключно для українців. Зомбі з боліт теж можна, але зворотного шляху не буде"+
    "\n*/game* — _про гру._"+
    "\n\n🤭*І те, заради чого створювався бот.*"+
    "\n*/roulet* — _список розіграшів._", parse_mode="Markdown")

#/id-----
@dp.message_handler(commands=['id'])
async def command_id(message: types.Message):
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        await message.reply(f"ID користувача: `{user_id}`", parse_mode="Markdown")
    elif "chat" in message.text:
        chat_id = message.chat.id
        await message.reply(f"ID чату: `{chat_id}`", parse_mode="Markdown")
    else:
        user_id = message.from_user.id
        await message.reply(f"Твій ID: `{user_id}`", parse_mode="Markdown")

#/kickme-----
@dp.message_handler(commands=['kickme'])
async def send_message(message: types.Message):
    await message.reply("Rose, твоя черга😁")

#/roulet-----
@dp.message_handler(commands=['roulet'])
async def send_message(message: types.Message):
    await message.reply("🚀*Про розіграші:*"+
    "\n_Введи команду та отримай шанс виграти приз. У кожної команди свій приз і свої шанси. Не забудь додати мене в груповий чат (розіграші працюють тільки там) і видати права адміністратора, інакше я не зможу працювати😢_"+
    "\n\n🥳️*Список розіграшів:*"+
    "\n*/yadebil*"+
    "\n*Приз:* _можливість закріплювати повідомлення._"+
    "\n*Шанс:* _10%_"+
    "\n*/yagandone*"+
    "\n*Приз:* _можливість отримати адміністратора._"+
    "\n*Шанс:* _5%_"+
    "\n*/yapedarasik*"+
    "\n*Приз:* _можливість отримати творця._"+
    "\n*Шанс:* _1%_", parse_mode="Markdown")

async def kick_roulet_words(message: types.Message) -> bool:
    roulet_word = ["/yadebil","/yagandone", "/yapedarasik"]
    return any(keyword in message.text.lower() for keyword in roulet_word)

@dp.message_handler(kick_roulet_words)
async def kick_user(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        await bot.kick_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id)
        await message.reply("😢*На жаль, ти не виграв.*\n_Спробуй ще раз_", parse_mode="Markdown")
    except aiogram.exceptions.BadRequest:
        await message.reply("🚀*Ти вже отримав цей приз!*", parse_mode="Markdown")

#/kicktext-----
@dp.message_handler(commands=['bluetext'])
async def send_message(message: types.Message):
    await message.reply("/BLUE /TEXT\n/MUST /CLICK\n/I /AM /A /STUPID /ANIMAL /THAT /ISS /ATTRACTED /TO /COLORS")

async def kick_words(message: types.Message) -> bool:
    words = ["слава россии", "/kekmi","/blue", "/text", "/must", "/click", "/i", "/am", "/stupid", "/animal", "/that", "/iss", "/attracted", "/to", "/colors"]
    return any(keyword in message.text.lower() for keyword in words)

@dp.message_handler(kick_words)
async def kick_user(message: types.Message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        await bot.kick_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id)
        await message.reply("🫵😂")
    except aiogram.exceptions.BadRequest:
        await None

if __name__ == '__main__':
    executor.start_polling(dp)
