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

# /ping
bot_start_time = datetime.now()

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
    dp.register_message_handler(settings, commands=['settings'])
    dp.register_callback_query_handler(handle_settings_callback, lambda c: c.data.startswith('toggle_'))
    dp.register_message_handler(shop, commands=['shop'])
    dp.register_callback_query_handler(shop_selected, lambda c: c.data == 'main_shop' or c.data.startswith('shop_'))
    dp.register_callback_query_handler(back_to_shop, lambda c: c.data == 'back_to_shop')
    dp.register_message_handler(help, commands=['help'])
    dp.register_callback_query_handler(game_selected, lambda c: c.data == 'main_game' or c.data.startswith('game_'))
    dp.register_callback_query_handler(back_to_games, lambda c: c.data == 'back_to_games')
    dp.register_message_handler(give, commands=['give'])
    dp.register_callback_query_handler(give_inline, lambda c: c.data and c.data.startswith('give_'))
