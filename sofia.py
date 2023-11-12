# Імпорти
import configparser
import aiosqlite
import datetime
import aiocache
import aiogram
import logging
import asyncio
import random
import math
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.executor import start_polling
from datetime import datetime, timedelta, time
from aiogram import Bot, Dispatcher, types


# Імпортуємо інші частини коду
from src.functions import startup, shutdown, add_chat, check_type, reply_and_delete, send_and_delete, edit_and_delete
from src.middlewares import Logging, Database, RateLimit
from src.messages import messages_handlers
from src.admins import admins_handlers
from src.logger import logger


# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    ADMIN = int(config['ID']['ADMIN'])
    TEST = (config['SETTINGS']['TEST'])
    RANDOMGAMES = float(config['SETTINGS']['RANDOMGAMES'])
    SKIPUPDATES = config['SETTINGS']['SKIPUPDATES'] == 'True'
    DELETE = int(config['SETTINGS']['DELETE'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в sofia.py: {e}")
    exit()


# Ініціалізація бота і диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


# Ініціалізація кеш-пам'яті
cache = aiocache.Cache()


# Ініціалізація проміжного ПЗ
dp.middleware.setup(Logging())
dp.middleware.setup(Database())
dp.middleware.setup(RateLimit())


# Ініціалізація обробників
messages_handlers(dp, bot)
admins_handlers(dp, bot)


#/killru-----
@dp.message_handler(commands=['killru'])
async def killru(message: types.Message):
    if await check_type(message):
        return

    await add_chat(message.chat.id)

    user_id = message.from_user.id
    chat_id = message.chat.id
    now = datetime.now()
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        value_killru = await cursor.fetchone()

        newuser = False
        if not value_killru:
            newuser = True
            welcome = f"🎉 {mention}, вітаю! Ти тепер зареєстрований у грі русофобії!"
            asyncio.create_task(reply_and_delete(message, welcome))
            await db.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, 0))
            await db.commit()


        cursor = await db.execute('SELECT killru FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        cooldown = await cursor.fetchone()
        cooldown_killru_date = None
        if cooldown and cooldown[0]:
            cooldown_killru_date = datetime.strptime(cooldown[0], '%Y-%m-%d %H:%M:%S').date()

        if cooldown_killru_date and now.date() == cooldown_killru_date:
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
                await db.execute('UPDATE user_values SET value = value + 5 WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
                await db.commit()

            await reply_and_delete(message, f"⚠️ Ти можеш використати цю команду тільки один раз на день. Спробуй через `{cooldown_time_str}`{bonus}")
            return

        else:
            cursor = await db.execute('SELECT * FROM cooldowns WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            if await cursor.fetchone():
                await db.execute('UPDATE cooldowns SET killru = ? WHERE user_id = ? AND chat_id = ?', (now.strftime('%Y-%m-%d %H:%M:%S'), user_id, chat_id))
            else:
                await db.execute('INSERT INTO cooldowns (user_id, chat_id, killru) VALUES (?, ?, ?)', (user_id, chat_id, now.strftime('%Y-%m-%d %H:%M:%S')))
            await db.commit()

        if TEST == 'True':
            rusophobia = random.choice([1000, 1488])
        else:
            rusophobia = random.choice([-4, -3, -2, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15])

        if newuser:
            rusophobia = abs(rusophobia)

        cursor = await db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        result = await cursor.fetchone()
        new_rusophobia = result[0] + rusophobia if result else rusophobia

        await db.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?', (new_rusophobia, user_id, chat_id))
        await db.commit()

        if rusophobia >= 0:
            message_text = f"📈 {mention}, твоя русофобія збільшилась на `{rusophobia}` кг"
        else:
            message_text = f"📉 {mention}, твоя русофобія зменшилась на `{abs(rusophobia)}` кг"

        message_text += f"\n🏷️ Тепер в тебе: `{new_rusophobia}` кг"
        await send_and_delete(message, chat_id=message.chat.id, reply_text=message_text)


#/my-----
@dp.message_handler(commands=['my'])
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
        await reply_and_delete(message, f'😯 {mention}, ти ще не грав')
    else:
        rusophobia = result[0]
        await reply_and_delete(message, f"😡 {mention}, твоя русофобія: `{rusophobia}` кг")


#/game-----
@dp.message_handler(commands=['game'])
async def start_game(message: types.Message):
    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=3)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return 

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        if balance:
            balance = balance[0]
        else:
            balance = 0

        if balance <= 0:
            await reply_and_delete(message,f"⚠️ У тебе недостатньо русофобії для гри")
            return
        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=3)
        bet_buttons = [InlineKeyboardButton(f"🏷️ {bet} кг", callback_data=f"bet_{bet}") for bet in [1, 3, 5, 10, 20, 30, 40, 50, 60]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancel"))
        keyboard.add(*bet_buttons)
        game_message = await bot.send_message(chat_id, f"🧌 {mention}, знайди і вбий москаля\n\n🏷️ У тебе: `{balance}` кг\n🎰 Вибери ставку\n🔀 Приз: ставка x2", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
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

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancel':
            await bot.answer_callback_query(callback_query.id, "✅")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "⚠️ Гру скасовано")
            return


        elif callback_query.data.startswith('bet_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)

            cursor = await db.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=3)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "✅")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "⚠️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

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
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('cancel_cell'):
            bet = await cache.get(f"bet_{user_id}_{chat_id}")
            bet = int(bet)
            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            current_balance = await cursor.fetchone()
            current_balance = current_balance[0] if current_balance else 0
            new_balance = current_balance + bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "✅")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"⚠️ Гру скасовано. Твоя ставка в `{bet} кг` повернута")
            return

        elif callback_query.data.startswith('cell_'):
            _, cell = callback_query.data.split('_')
            cell = int(cell)

            cursor = await db.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=3)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "✅")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet = await cursor.fetchone()
            balance_after_bet = balance_after_bet[0] if balance_after_bet else 0
            bet = await cache.get(f"bet_{user_id}_{chat_id}")
            bet = int(bet)
            win = random.random() < RANDOMGAMES

            if win:
                bet_won = bet * 2 
                new_balance = balance_after_bet + bet_won + bet
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
                message = f"🥇 {mention}, вітаю! Ти знайшов і вбив москаля, і з нього випало `{bet_won}` кг\n🏷️ Тепер у тебе: `{new_balance}` кг"
            else:
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (balance_after_bet, user_id, chat_id))
                message = f"😔 {mention}, на жаль, ти програв `{bet}` кг\n🏷️ У тебе залишилося: `{balance_after_bet}` кг"

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("UPDATE cooldowns SET game = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "✅")
            await bot.edit_message_text(message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

#/dice-----
@dp.message_handler(commands=['dice'])
async def start_dice(message: types.Message):
    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT dice FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=1)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"⚠️ У тебе недостатньо русофобії для гри")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=3)
        bet_buttons = [InlineKeyboardButton(f"🖱️ {bet} кг", callback_data=f"bett_{bet}") for bet in [1, 3, 5, 10, 20, 30, 40, 50, 60]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancell"))
        keyboard.add(*bet_buttons)
        dice_message = await bot.send_message(chat_id, f"🎲 {mention}, зіграй у кості\n\n🏷️ У тебе: `{balance}` кг\n🎰 Вибери ставку\n🔀 Приз: ставка x0.5", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"dice_player_{dice_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


@dp.callback_query_handler(lambda c: c.data.startswith('bett_') or c.data == 'cancell' or c.data == 'cancelll_cell' or c.data.startswith('even_') or c.data.startswith('odd_'))
async def handle_dice_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    dice_player_id = await cache.get(f"dice_player_{callback_query.message.message_id}")

    if dice_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancell':
            await bot.answer_callback_query(callback_query.id, "✅")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "⚠️ Гру скасовано")
            return

        elif callback_query.data.startswith('bett_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT dice FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=1)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "✅")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "⚠️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"bett_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 0.5)

            keyboard = InlineKeyboardMarkup()
            button_even = InlineKeyboardButton("➗Парне", callback_data=f"even_{bet}")
            button_odd = InlineKeyboardButton("✖️Непарне", callback_data=f"odd_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="cancelll_cell")
            keyboard.row(button_even, button_odd)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "✅")
            await bot.edit_message_text(
                f"🎲 {mention}, зроби свій вибір:\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('cancelll_cell'):
            bet = await cache.get(f"bett_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "✅")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"⚠️ Гру скасовано. Твоя ставка в `{bet} кг` повернута")
            return

        elif callback_query.data.startswith('even_') or callback_query.data.startswith('odd_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT dice FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=1)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "✅")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"⚠️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("UPDATE cooldowns SET dice = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
            await db.commit()

            dice_message = await bot.send_dice(chat_id=chat_id)
            result_dice = dice_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"bett_{user_id}_{chat_id}")
            bet = int(bet)
            
            if (result_dice % 2 == 0 and bet_type == 'even') or (result_dice % 2 != 0 and bet_type == 'odd'):
                bet_won = math.ceil(bet * 0.5)
                new_balance = balance_after_bet + bet_won + bet
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
                win_message = f"🥇 {mention}, ти виграв! \n🎲 Випало `{result_dice}`, {'парне' if result_dice % 2 == 0 else 'непарне'} \n💰 Твій виграш: `{bet_won}` кг\n\n🏷️ Тепер у тебе: `{new_balance}` кг"
            else:
                win_message = f"😔 {mention}, ти програв \n🎲 Випало `{result_dice}`, {'непарне' if result_dice % 2 != 0 else 'парне'} \n🤜 Втрата: `{bet}` кг\n\n🏷️ Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "✅")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


#/give-----
@dp.message_handler(commands=['give'])
async def give(message: types.Message):
    if await check_type(message):
        return

    if not message.reply_to_message:
        await reply_and_delete(message, "⚙️ Використовуй `/give N` у відповідь на повідомлення")
        return

    receiver_id = message.reply_to_message.from_user.id
    receiver_is_bot = message.reply_to_message.from_user.is_bot

    if receiver_is_bot:
        await reply_and_delete(message, "⚠️ Боти не можуть грати")
        return

    global givers
    if message.reply_to_message and message.from_user.id != message.reply_to_message.from_user.id:
        parts = message.text.split()
        if len(parts) != 2:
            await reply_and_delete(message, "⚙️ Використовуй `/give N` у відповідь на повідомлення")
            return

        try:
            value = int(parts[1])
            if value <= 0:
                raise ValueError

        except ValueError:
            await reply_and_delete(message, "🤨 Типо розумний? Введи плюсове і ціле число. Наприклад: /give `5` у відповідь на повідомлення")
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
                await reply_and_delete(message,f"⚠️ Ти ще не можеш передати русофобію. Спробуй через `{cooldown_time}`")
                return
        else:
            last_given = None

        async with aiosqlite.connect('src/database.db') as db:
            async with db.cursor() as cursor: 
                await cursor.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, chat_id))
                result = await cursor.fetchone()
                if not result or result[0] < value:
                    await reply_and_delete(message, f"⚠️ У тебе `{result[0] if result else 0}` кг. Цього недостатньо")
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
        await reply_and_delete(message, "⚙️ Використовуй `/give N` у відповідь на повідомлення")


@dp.callback_query_handler(lambda c: c.data and c.data.startswith('give_'))
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
            await db.execute(
                'UPDATE user_values SET value = value - ? WHERE user_id = ? AND chat_id = ?', (value, giver_id, callback_query.message.chat.id))
            await db.execute(
                'INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?) '
                'ON CONFLICT(user_id, chat_id) DO UPDATE SET value = value + ?', (receiver_id, callback_query.message.chat.id, value, value))
            await db.execute(
                'UPDATE cooldowns SET give = ? WHERE user_id = ? AND chat_id = ?', (now.strftime("%Y-%m-%d %H:%M:%S"), giver_id, callback_query.message.chat.id))
            await db.commit()

            async with db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (giver_id, callback_query.message.chat.id)) as cursor:
                updated_value = await cursor.fetchone()

            if callback_query.from_user.username:
                giver_mention = f"[{callback_query.from_user.username}](https://t.me/{callback_query.from_user.username})"
            else:
                giver_mention = callback_query.from_user.first_name

            await bot.answer_callback_query(callback_query.id, "✅ Успішно")
            await bot.edit_message_text(
                text=f"✅ {giver_mention} передав `{value}` кг русофобії {mention}\n🏷️ Тепер в тебе: `{updated_value[0] if updated_value else 0}` кг",
                chat_id=callback_query.message.chat.id,
                message_id=callback_query.message.message_id,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
        else:
            await bot.answer_callback_query(callback_query.id, "❌ Скасовано")
            await edit_and_delete(bot, callback_query.message.chat.id, callback_query.message.message_id, "❌ Передача русофобії скасована")
            return


#/-----leave
@dp.message_handler(commands=['leave'])
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
        await reply_and_delete(message, f"😯 {mention}, ти й так не граєш")

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

    mention = f"[{callback_query.from_user.username}](https://t.me/{callback_query.from_user.username})" if callback_query.from_user.username else callback_query.from_user.first_name

    if callback_query.data == 'confirm_leave':
        async with aiosqlite.connect('src/database.db') as db:
            await db.execute('DELETE FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            if TEST == 'True':
                await db.execute('UPDATE cooldowns SET killru = NULL, give = NULL, game = NULL, dice = NULL WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
            await db.commit()

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


@dp.message_handler(commands=['hapai'])
async def hapai(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(text="ХАПАНУТИ", callback_data="button_clicked")
    keyboard.add(button)
    await message.answer("🌿", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'button_clicked')
async def handle_button_click(callback_query: types.CallbackQuery):
    await callback_query.answer("Ухх дурман. Розкумарчик що треба")       


if __name__ == '__main__':
    start_polling(dp, skip_updates=SKIPUPDATES, on_startup=startup, on_shutdown=shutdown)