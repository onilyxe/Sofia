import configparser
import aiosqlite
import aiocache
import aiogram
import logging
import asyncio
import psutil

from src.functions import reply_and_delete, show_globaltop, show_top, check_type, edit_and_delete, check_settings
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from datetime import datetime, timedelta
from aiogram import Bot, types

# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    ADMIN = int(config['ID']['ADMIN'])
    TEST = (config['SETTINGS']['TEST'])
    VERSION = (config['SETTINGS']['VERSION'])
    DELETE = int(config['SETTINGS']['DELETE'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в messages.py: {e}")
    exit()

# Ініціалізація бота та кеш-пам'яті
bot = Bot(token=TOKEN)
cache = aiocache.Cache()

# /start
async def start(message: types.Message):
    await reply_and_delete(message, "🫡 Привіт. Я бот для гри в русофобію. Додавай мене в чат і розважайся. Щоб дізнатися як мною користуватися, вивчай /help")

# /ping
bot_start_time = datetime.now()

def format_uptime(uptime):
    days, remainder = divmod(uptime.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        return f"{int(days)} д. {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

async def ping(message: types.Message):
    start_time = datetime.now()
    await bot.get_me()
    end_time = datetime.now()
    ping_time = (end_time - start_time).total_seconds() * 1000
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    now = datetime.now()
    uptime = now - bot_start_time
    formatted_uptime = format_uptime(uptime)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_today - timedelta(days=now.weekday())

    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute('SELECT count FROM queries WHERE datetime >= ? AND datetime < ? ORDER BY datetime DESC LIMIT 1', (start_time.replace(hour=0, minute=0, second=0, microsecond=0), start_time.replace(hour=23, minute=59, second=59, microsecond=999999))) as cursor:
            today_record = await cursor.fetchone()
            today_queries = today_record[0] if today_record else 0

        period_start = start_of_today if now.weekday() == 0 else start_of_week
        async with db.execute('SELECT SUM(count) FROM queries WHERE datetime >= ?', (period_start,)) as cursor:
            week_record = await cursor.fetchone()
            week_queries = week_record[0] if week_record else 0

        async with db.execute('SELECT SUM(count) FROM queries') as cursor:
            all_time_record = await cursor.fetchone()
            all_time_queries = all_time_record[0] if all_time_record else 0

    ping_text = (
        f"📡 Ping: `{ping_time:.2f}` ms\n\n"
        f"🔥 CPU: `{cpu_usage}%`\n"
        f"💾 RAM: `{ram_usage}%`\n"
        f"⏱️ Uptime: `{formatted_uptime}`\n\n"
        f"📊 Кількість запитів:\n"
        f"_За сьогодні:_ `{today_queries}`\n"
        f"_За тиждень:_ `{week_queries}`\n"
        f"_За весь час:_ `{all_time_queries}`")

    await reply_and_delete(message, ping_text)

# /about
async def about(message: types.Message):
    about_text = (
        f"📡 Sofia `{VERSION}`\n\n"
        f"[News Channel](t.me/SofiaBotRol)\n"
        f"[Source](https://github.com/onilyxe/Sofia)\n\n"
        f"Made [onilyxe](https://t.me/onilyxe). Idea [den](https://t.me/itsokt0cry)")

    await reply_and_delete(message, about_text)

# /globaltop
async def globaltop(message: types.Message):
    await show_globaltop(message, limit=101, title='🌏 Глобальний топ русофобій')

# /globaltop10
async def globaltop10(message: types.Message):
    await show_globaltop(message, limit=10, title='🌏 Глобальний топ 10 русофобій')

# /top
async def top(message: types.Message):
    await show_top(message, limit=101, title='📊 Топ русофобій чату')

# /top10
async def top10(message: types.Message):
    await show_top(message, limit=10, title='📊 Топ 10 русофобій чату')

# /my
async def my(message: types.Message):
    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        result = await cursor.fetchone()

    if message.from_user.username:
        mention = f"[{message.from_user.username}](https://t.me/{message.from_user.username})"
    else:
        mention = message.from_user.first_name

    if result is None:
        await reply_and_delete(message, f'😠 {mention}, у тебе немає русофобії, губися')
    else:
        rusophobia = result[0]
        await reply_and_delete(message, f"😡 {mention}, твоя русофобія: `{rusophobia}` кг")

# /settings
async def settings(message: types.Message):
    chat_id = message.chat.id

    user = await bot.get_chat_member(chat_id, message.from_user.id)
    if not user.status in ['administrator', 'creator']:
        return

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute('SELECT minigame, give FROM chats WHERE chat_id = ?', (chat_id,))
        settings = await cursor.fetchone()
        minigame_enabled = True if settings is None or settings[0] is None else settings[0]
        give_enabled = True if settings is None or settings[1] is None else settings[1]

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(f"Міні-ігри: {'✅' if minigame_enabled else '❌'}", callback_data=f"toggle_minigame_{chat_id}"))
    keyboard.add(InlineKeyboardButton(f"Передача кг: {'✅' if give_enabled else '❌'}", callback_data=f"toggle_give_{chat_id}"))

    await message.reply("⚙️ Налаштування чату:", reply_markup=keyboard)

async def handle_settings_callback(callback_query: types.CallbackQuery):
    chat_id = int(callback_query.data.split('_')[2])
    setting = callback_query.data.split('_')[1]

    if setting not in ['minigame', 'give']:
        await callback_query.answer("❌ Невідома настройка", show_alert=True)
        return

    user = await bot.get_chat_member(chat_id, callback_query.from_user.id)
    if not user.status in ['administrator', 'creator']:
        await callback_query.answer("❌ Тільки адміністратори можуть змінювати налаштування", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        await db.execute(f'UPDATE chats SET {setting} = NOT COALESCE({setting}, 1) WHERE chat_id = ?', (chat_id,))
        await db.commit()

        cursor = await db.execute('SELECT minigame, give FROM chats WHERE chat_id = ?', (chat_id,))
        updated_settings = await cursor.fetchone()
        minigame_enabled = True if updated_settings[0] is None else updated_settings[0]
        give_enabled = True if updated_settings[1] is None else updated_settings[1]

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(f"Міні-ігри: {'✅' if minigame_enabled else '❌'}", callback_data=f"toggle_minigame_{chat_id}"))
    keyboard.add(InlineKeyboardButton(f"Передача кг: {'✅' if give_enabled else '❌'}", callback_data=f"toggle_give_{chat_id}"))

    await bot.edit_message_text(chat_id=chat_id, message_id=callback_query.message.message_id, text="⚙️ Налаштування чату:", reply_markup=keyboard)
    await callback_query.answer("ℹ️ Змінено")

# /shop
async def shop(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=1)
    main_shop_button = InlineKeyboardButton(text="❔ Як купити кг?", callback_data="main_shop")
    main_shop_button2 = InlineKeyboardButton(text="💲 Яка ціна?", callback_data="shop_two")
    main_shop_button3 = InlineKeyboardButton(text="🛸 Куди підуть гроші?", callback_data="shop_three")
    keyboard.add(main_shop_button)
    keyboard.add(main_shop_button2)
    keyboard.add(main_shop_button3)

    text = await message.reply("💳 Хочеш більше русофобії?\nТут ти зможеш дізнатися як її купити", reply_markup=keyboard)
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=text.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass
    return

async def shop_selected(callback_query: types.CallbackQuery):
    shop_text = {
        "main_shop": "Посилання на банку: [send.monobank.ua](https://send.monobank.ua/jar/5T9BXGpL83)\nРобите донат на потрібну вам суму, і відправляєте скріншот оплати в @OnilyxeBot\nГоловна умова, вказати ID чату де ви хочете поповнення балансу. Якщо ти не знаєш що це таке, то просто напиши назву свого чату\nПісля чекай поки адміни оброблять твій запит",
        "shop_two": "Курс гривні до русофобії 1:10\n1 грн = 10 кг\n100 кг - 10 грн\n1000 кг - 100 грн\nБеремо потрібну кількість русофобії і ділимо на 10\n500 кг / 10 = 50 грн",
        "shop_three": "Розробник бота зараз служить в артилерії. Їбашить кацапів щодня (Його канал [5011](https://t.me/ua5011))\nЗібрані гроші підуть на поновлення екіпірування"
    }
    selected_shop = shop_text[callback_query.data]    
    keyboard = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_shop")
    keyboard.add(back_button)
    await bot.answer_callback_query(callback_query.id, "ℹ️ Готово")
    await callback_query.message.edit_text(f"{selected_shop}", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

async def back_to_shop(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    main_shop_button = InlineKeyboardButton(text="❔ Як купити кг?", callback_data="main_shop")
    main_shop_button2 = InlineKeyboardButton(text="💲 Яка ціна?", callback_data="shop_two")
    main_shop_button3 = InlineKeyboardButton(text="🛸 Куди підуть гроші?", callback_data="shop_three")
    keyboard.add(main_shop_button)
    keyboard.add(main_shop_button2)
    keyboard.add(main_shop_button3)
    await bot.answer_callback_query(callback_query.id, "ℹ️ Гаразд")
    await callback_query.message.edit_text("💳 Хочеш поповнити свою русофобію і обігнати суперників?\nТут ти зможеш дізнатися як купити кг", reply_markup=keyboard)

# /help
async def help(message: types.Message):
    keyboard = InlineKeyboardMarkup(row_width=4)
    main_game_button = InlineKeyboardButton(text="Основна гра - /killru", callback_data="main_game")
    keyboard.add(main_game_button)
    games_buttons = [
        InlineKeyboardButton(text="🧌", callback_data="game_club"),
        InlineKeyboardButton(text="🎲", callback_data="game_dice"),
        InlineKeyboardButton(text="🎯", callback_data="game_darts"),
        InlineKeyboardButton(text="🏀", callback_data="game_basketball"),
        InlineKeyboardButton(text="⚽️", callback_data="game_football"),
        InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
        InlineKeyboardButton(text="🎰", callback_data="game_casino")
    ]
    keyboard.add(*games_buttons)
    text = await message.reply("⚙️ Тут ти зможеш дізнатися\nпро мене все", reply_markup=keyboard)
    await asyncio.sleep(DELETE)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=text.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    except (MessageCantBeDeleted, MessageToDeleteNotFound):
        pass
    return

async def game_selected(callback_query: types.CallbackQuery):
    game_emojis = {
        "main_game": 
        f"Гра в русофобію"
        "\nУ гру можна зіграти кожен день один раз, виконавши /killru"
        "\nПри цьому кількість русофобії випадковим чином збільшиться(до +25) або зменшиться(до -5)"
        "\nРейтин можна подивитися виконавши /top. Є маленький варіант /top10, і глобальний топ, показує топ серед усіх учасників /globaltop10 і маленький варіант /globaltop10 "
        "\nВиконавши /my можна дізнатися свою кількість русофобії"
        "\nПередати свою русофобію іншому користувачу, можна відповівши йому командою /give, вказавши кількість русофобії"
        "\nІнформацію про бота можна подивитися, виконавши /about"
        "\nСлужбова інформація: /ping"
        "\nВаріанти міні-ігор можна переглянути за командою /help, вибравши знизу емодзі, що вказує на гру"
        "\nЗа командою /settings можна вимкнути в чаті міні-ігри та передачу русофобії. Налаштування доступні тільки адмінам чату"
        "\nВийти з гри (прогрес видаляється): /leave"
        "\n\n\nЯкщо мені видати права адміна (видалення повідомлень), то я через годину буду видаляти повідомлення від мене і які мене викликали. Залишаючи тільки про зміни в русофобії"
        "\n\n\nKillru. Смерть всьому російському. 🫡",

        "game_club": 
        f"🧌 Знайди і вбий москаля. Суть гри вгадати де знаходиться москаль на сітці 3х3"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /game",

        "game_dice": 
        f"🎲 Гра у кості. Суть гри вгадати яке випаде число, парне чи непарне"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 15. Буде 65"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /dice",

        "game_darts": 
        f"🎯 Гра в дартс. Суть гри потрапити в центр"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 2. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /darts",

        "game_basketball": 
        f"🏀 Гра в баскетбол. Суть гри потрапити в кошик м'ячем"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 15. Буде 65"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /basketball",

        "game_football": 
        f"⚽️ Гра у футбол. Суть гри потрапити м'ячем у ворота"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 15. Буде 65"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /football",

        "game_bowling": 
        f"🎳 Гра в боулінг. Суть гри вибити страйк"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 2. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /bowling",
        
        "game_casino": 
        f"🎰 Гра в казино. Суть гри вибити джекпот"
        "\n⏱️ Можна зіграти раз на 2 години"
        "\n🔀 Приз: ставка множиться на 2. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70. Якщо вибити джекпот (777), то ставка множиться на 10"
        "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
        "\n🚀 Команда гри: /casino",
   }
    selected_game = game_emojis[callback_query.data]    
    keyboard = InlineKeyboardMarkup()
    back_button = InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_games")
    keyboard.add(back_button)
    await bot.answer_callback_query(callback_query.id, "ℹ️ Готово")
    await callback_query.message.edit_text(f"{selected_game}", reply_markup=keyboard, parse_mode="Markdown")

async def back_to_games(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=4)
    main_game_button = InlineKeyboardButton(text="Основна гра - /killru", callback_data="main_game")
    keyboard.add(main_game_button)
    games_buttons = [
        InlineKeyboardButton(text="🧌", callback_data="game_club"),
        InlineKeyboardButton(text="🎲", callback_data="game_dice"),
        InlineKeyboardButton(text="🎯", callback_data="game_darts"),
        InlineKeyboardButton(text="🏀", callback_data="game_basketball"),
        InlineKeyboardButton(text="⚽️", callback_data="game_football"),
        InlineKeyboardButton(text="🎳", callback_data="game_bowling"),
        InlineKeyboardButton(text="🎰", callback_data="game_casino")
    ]
    keyboard.add(*games_buttons)
    await bot.answer_callback_query(callback_query.id, "ℹ️ Гаразд")
    await callback_query.message.edit_text("⚙️ Тут ти зможеш дізнатися\nпро мене все", reply_markup=keyboard)

# /leave
async def leave(message: types.Message):
    if await check_type(message):
        return

    inline = InlineKeyboardMarkup(row_width=2)
    inline.add(InlineKeyboardButton("✅ Так", callback_data="confirm_leave"), InlineKeyboardButton("❌ Ні", callback_data="cancel_leave"))
    
    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = f"[{message.from_user.username}](https://t.me/{message.from_user.username})" if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute('SELECT * FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)) as cursor:
            user_exists = await cursor.fetchone()

    if not user_exists:
        await reply_and_delete(message, f"😯 {mention}, у тебе і так немає русофобії, губися")

    else:
        msg = await bot.send_message(chat_id, f"😡 {mention}, ти впевнений, що хочеш проїбати свою русофобію? Твої дані буде видалено з бази даних. Цю дію не можна буде скасувати", reply_markup=inline, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"leavers_{msg.message_id}", user_id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass

async def leave_inline(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    
    leaver_id = await cache.get(f"leavers_{callback_query.message.message_id}")

    if leaver_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    mention = f"[{callback_query.from_user.username}](https://t.me/{callback_query.from_user.username})" if callback_query.from_user.username else callback_query.from_user.first_name

    if callback_query.data == 'confirm_leave':
        async with aiosqlite.connect('src/database.db') as db:
            await db.execute('DELETE FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            if TEST == 'True':
                await db.execute('UPDATE cooldowns SET killru = NULL, give = NULL, game = NULL, dice = NULL, darts = NULL, basketball = NULL, football = NULL, bowling = NULL, casino = NULL WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            await db.commit()

        await bot.answer_callback_query(callback_query.id, "👹 Ох братику, даремно ти це зробив...")
        await bot.edit_message_text(f"🤬 {mention}, ти покинув гру, і тебе було видалено з бази даних", chat_id, callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await bot.answer_callback_query(callback_query.id, "ℹ️ Cкасовуємо..")
        await bot.edit_message_text(f"🫡 {mention} красунчик, ти залишився у грі", chat_id, callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id=chat_id, message_id=callback_query.message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass  

# /give
async def give(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'give'):
        return

    if await check_type(message):
        return

    if not message.reply_to_message:
        await reply_and_delete(message, "ℹ️ Використовуй `/give N` у відповідь на повідомлення")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_is_bot = message.reply_to_message.from_user.is_bot

    if receiver_is_bot:
        await reply_and_delete(message, "ℹ️ Боти не можуть грати")
        return

    global givers
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        parts = message.text.split()
        if len(parts) != 2:
            await reply_and_delete(message, "ℹ️ Використовуй `/give N` у відповідь на повідомлення")
            return

        try:
            value = int(parts[1])
            if value <= 0:
                raise ValueError

        except ValueError:
            await reply_and_delete(message, "🤨 Типу розумний, так? Введи плюсове і ціле число. Наприклад: `/give 5` у відповідь на повідомлення")
            return

        giver_id = message.from_user.id
        chat_id = message.chat.id
        now = datetime.now()

        async with aiosqlite.connect('src/database.db') as db:
            async with db.cursor() as cursor:   
                await cursor.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL', (giver_id, chat_id))
                last_given = await cursor.fetchone()

        if last_given and last_given[0]:
            last_given = datetime.strptime(last_given[0], '%Y-%m-%d %H:%M:%S') 
            if last_given + timedelta(hours=5) > now:
                cooldown_time = (last_given + timedelta(hours=5)) - now
                cooldown_time = str(cooldown_time).split('.')[0]
                await reply_and_delete(message,f"ℹ️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`")
                return
        else:
            last_given = None

        async with aiosqlite.connect('src/database.db') as db:
            async with db.cursor() as cursor: 
                await cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
                result = await cursor.fetchone()
                if not result or result[0] < value:
                    await reply_and_delete(message, f"ℹ️ У тебе `{result[0] if result else 0}` кг. Цього недостатньо")
                    return


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
        await reply_and_delete(message, "ℹ️ Використовуй `/give N` у відповідь на повідомлення")

async def give_inline(callback_query: types.CallbackQuery):
    _, value, answer, receiver_id = callback_query.data.split('_')
    value = int(value)
    receiver_id = int(receiver_id)
    giver_id = await cache.get(f"givers_{callback_query.message.message_id}")

    receiver = await bot.get_chat_member(callback_query.message.chat.id, receiver_id)
    mention = ('[' + receiver.user.username + ']' + '(https://t.me/' + receiver.user.username + ')') if receiver.user.username else receiver.user.first_name

    now = datetime.now()
    
    async with aiosqlite.connect('src/database.db') as db:
        async with db.execute('SELECT give FROM cooldowns WHERE user_id = ? AND chat_id = ? AND give IS NOT NULL', (giver_id, callback_query.message.chat.id)) as cursor:
            last_given_row = await cursor.fetchone()

        if last_given_row and last_given_row[0]:
            last_given = datetime.strptime(last_given_row[0], '%Y-%m-%d %H:%M:%S')
            if last_given + timedelta(hours=5) > now:
                cooldown_time = (last_given + timedelta(hours=5)) - now
                cooldown_time = str(cooldown_time).split('.')[0]
                await edit_and_delete(bot, callback_query.message.chat.id, callback_query.message.message_id, f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`")
                return

        if giver_id != callback_query.from_user.id:
            await bot.answer_callback_query(callback_query.id, text="❌ Ці кнопочки не для тебе!", show_alert=True)
            return

        if answer == 'yes':
            await db.execute('UPDATE user_values SET value = value - ? WHERE user_id = ? AND chat_id = ?', (value, giver_id, callback_query.message.chat.id))
            await db.execute(
                'INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?) '
                'ON CONFLICT(user_id, chat_id) DO UPDATE SET value = value + ?', (receiver_id, callback_query.message.chat.id, value, value))
            if TEST == 'False':
                await db.execute(
                    'UPDATE cooldowns SET give = ? WHERE user_id = ? AND chat_id = ?', (now.strftime("%Y-%m-%d %H:%M:%S"), giver_id, callback_query.message.chat.id))
            await db.commit()

            async with db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, callback_query.message.chat.id)) as cursor:
                updated_value = await cursor.fetchone()

            if callback_query.from_user.username:
                giver_mention = f"[{callback_query.from_user.username}](https://t.me/{callback_query.from_user.username})"
            else:
                giver_mention = callback_query.from_user.first_name

            await bot.answer_callback_query(callback_query.id, "ℹ️ Переказую кг..")
            await bot.edit_message_text(
                text=f"✅ {giver_mention} передав `{value}` кг русофобії {mention}\n🏷️ Тепер в тебе: `{updated_value[0] if updated_value else 0}` кг",
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую..")
            await edit_and_delete(bot, callback_query.message.chat.id, callback_query.message.message_id, "ℹ️ Передача русофобії скасована")
            return

# Ініціалізація обробника
def messages_handlers(dp, bot):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(ping, commands=['ping'])
    dp.register_message_handler(about, commands=['about'])
    dp.register_message_handler(globaltop, commands=['globaltop'])
    dp.register_message_handler(globaltop10, commands=['globaltop10'])
    dp.register_message_handler(top10, commands=['top10'])
    dp.register_message_handler(top, commands=['top'])
    dp.register_message_handler(settings, commands=['settings'])
    dp.register_callback_query_handler(handle_settings_callback, lambda c: c.data.startswith('toggle_'))
    dp.register_message_handler(shop, commands=['shop'])
    dp.register_callback_query_handler(shop_selected, lambda c: c.data == 'main_shop' or c.data.startswith('shop_'))
    dp.register_callback_query_handler(back_to_shop, lambda c: c.data == 'back_to_shop')
    dp.register_message_handler(my, commands=['my'])
    dp.register_message_handler(help, commands=['help'])
    dp.register_callback_query_handler(game_selected, lambda c: c.data == 'main_game' or c.data.startswith('game_'))
    dp.register_callback_query_handler(back_to_games, lambda c: c.data == 'back_to_games')
    dp.register_message_handler(leave, commands=['leave'])
    dp.register_callback_query_handler(leave_inline, lambda c: c.data in ['confirm_leave', 'cancel_leave'])
    dp.register_message_handler(give, commands=['give'])
    dp.register_callback_query_handler(give_inline, lambda c: c.data and c.data.startswith('give_'))
