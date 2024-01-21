import configparser
import aiosqlite
import datetime
import aiocache
import aiogram
import logging
import asyncio
import random
import math

from src.functions import add_chat, check_type, reply_and_delete, send_and_delete, edit_and_delete, check_settings
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound
from datetime import datetime, timedelta, time
from aiogram import Bot, types

# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    TEST = (config['SETTINGS']['TEST'])
    RANDOMGAMES = float(config['SETTINGS']['RANDOMGAMES'])
    DELETE = int(config['SETTINGS']['DELETE'])
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в games.py: {e}")
    exit()

# Ініціалізація бота та кеш-пам'яті
bot = Bot(token=TOKEN)
cache = aiocache.Cache()


# /game
async def game(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'minigame'):
        return

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
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return 

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        if balance:
            balance = balance[0]
        else:
            balance = 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return
        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"bet_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancel"))
        keyboard.add(*bet_buttons)
        game_message = await bot.send_message(chat_id, f"🧌 {mention}, знайди і вбий москаля\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"game_player_{game_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass

async def handle_game_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    game_player_id = await cache.get(f"game_player_{callback_query.message.message_id}")

    if game_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancel':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return


        elif callback_query.data.startswith('bet_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)

            cursor = await db.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "❌ Недостатньо русофобії")
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
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
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

            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('cell_'):
            _, cell = callback_query.data.split('_')
            cell = int(cell)

            cursor = await db.execute("SELECT game FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet = await cursor.fetchone()
            balance_after_bet = balance_after_bet[0] if balance_after_bet else 0
            bet = await cache.get(f"bet_{user_id}_{chat_id}")
            bet = int(bet)
            win = random.random() < RANDOMGAMES

            if win:
                bet_won = math.ceil(bet * 1.5)
                new_balance = balance_after_bet + bet_won + bet
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
                message = f"🏆 {mention}, ти виграв(ла)! Ти знайшов і вбив москаля, з нього випало `{bet_won}` кг 🧌\n🏷️ Тепер у тебе: `{new_balance}` кг"
            else:
                message = f"😔 {mention}, ти програв(ла) `{bet}` кг 🧌\n🏷️ Тепер у тебе: `{balance_after_bet}` кг"

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET game = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
            
            await db.commit()
            wait = "🧌 Тикаємо палицею в труп, здох чи не.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# /dice
async def dice(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'minigame'):
        return

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
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"betdice_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="canceldice"))
        keyboard.add(*bet_buttons)
        dice_message = await bot.send_message(chat_id, f"🎲 {mention}, зіграй у кості\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг\n", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"dice_player_{dice_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


async def handle_dice_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    dice_player_id = await cache.get(f"dice_player_{callback_query.message.message_id}")

    if dice_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'canceldice':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return

        elif callback_query.data.startswith('betdice_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT dice FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "ℹ️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"betdice_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 1.5)

            keyboard = InlineKeyboardMarkup()
            button_even = InlineKeyboardButton("➗ Парне", callback_data=f"even_{bet}")
            button_odd = InlineKeyboardButton("✖️ Непарне", callback_data=f"odd_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="canceldice_cell")
            keyboard.row(button_even, button_odd)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
            await bot.edit_message_text(
                f"🎲 {mention}, зроби свій вибір:\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('canceldice_cell'):
            bet = await cache.get(f"betdice_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('even_') or callback_query.data.startswith('odd_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT dice FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET dice = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
                await db.commit()

            wait = "🎲 Кидаємо кубик.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

            dice_message = await bot.send_dice(chat_id=chat_id)
            result_dice = dice_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"betdice_{user_id}_{chat_id}")
            bet = int(bet)
            
            if (result_dice % 2 == 0 and bet_type == 'even') or (result_dice % 2 != 0 and bet_type == 'odd'):
                bet_won = math.ceil(bet * 1.5)
                new_balance = balance_after_bet + bet_won + bet
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
                win_message = f"🏆 {mention}, ти виграв(ла)! Випало `{result_dice}`, {'парне' if result_dice % 2 == 0 else 'непарне'} \n🎲 Твій виграш: `{bet_won}` кг \n\n🏷️ Тепер у тебе: `{new_balance}` кг"
            else:
                win_message = f"😔 {mention}, ти програв(ла). Випало `{result_dice}`, {'непарне' if result_dice % 2 != 0 else 'парне'} \n🎲 Втрата: `{bet}` кг \n\n🏷️ Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# /darts
async def darts(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'minigame'):
        return

    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT darts FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"betdarts_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="canceldarts"))
        keyboard.add(*bet_buttons)
        darts_message = await bot.send_message(chat_id, f"🎯 {mention}, зіграй у дартс\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг\n", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"darts_player_{darts_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


async def handle_darts_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    darts_player_id = await cache.get(f"darts_player_{callback_query.message.message_id}")

    if darts_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'canceldarts':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return

        elif callback_query.data.startswith('betdarts_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT darts FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "ℹ️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"betdarts_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 2)

            keyboard = InlineKeyboardMarkup()
            button_go = InlineKeyboardButton("▶️ Грати", callback_data=f"godarts_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="canceldarts_cell")
            keyboard.row(button_go)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
            await bot.edit_message_text(
                f"🎯 {mention}, готовий(а)?\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('canceldarts_cell'):
            bet = await cache.get(f"betdarts_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('godarts_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT darts FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET darts = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
                await db.commit()

            wait = "🎯 Прицілюємося.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

            darts_message = await bot.send_dice(chat_id=chat_id, emoji='🎯')
            result_darts = darts_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"betdarts_{user_id}_{chat_id}")
            bet = int(bet)
            

            if result_darts == 6:
                bet_won = math.ceil(bet * 2)
                new_balance = balance_after_bet + bet_won + bet
                win_message = f"🏆 {mention}, точне попадання! Ти виграв(ла) `{bet_won}` кг \n🎯 Тепер у тебе: `{new_balance}` кг"
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            else:
                win_message = f"😔 {mention}, ти не влучив(ла). Втрата: `{bet}` кг \n🎯 Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# /basketball
async def basketball(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'minigame'):
        return

    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT basketball FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"betbasketball_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancelbasketball"))
        keyboard.add(*bet_buttons)
        basketball_message = await bot.send_message(chat_id, f"🏀 {mention}, зіграй у баскетбол\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг\n", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"basketball_player_{basketball_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


async def handle_basketball_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    basketball_player_id = await cache.get(f"basketball_player_{callback_query.message.message_id}")

    if basketball_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancelbasketball':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return

        elif callback_query.data.startswith('betbasketball_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT basketball FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "ℹ️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"betbasketball_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 1.5)

            keyboard = InlineKeyboardMarkup()
            button_go = InlineKeyboardButton("▶️ Грати", callback_data=f"gobasketball_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="cancelbasketball_cell")
            keyboard.row(button_go)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
            await bot.edit_message_text(
                f"🏀 {mention}, готовий(а)?\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('cancelbasketball_cell'):
            bet = await cache.get(f"betbasketball_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('gobasketball_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT basketball FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET basketball = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
                await db.commit()

            wait = "🏀 Прикидаємося Леброном Джеймсом.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

            basketball_message = await bot.send_dice(chat_id=chat_id, emoji='🏀')
            result_basketball = basketball_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"betbasketball_{user_id}_{chat_id}")
            bet = int(bet)

            if result_basketball >= 4:
                bet_won = math.ceil(bet * 1.5)
                new_balance = balance_after_bet + bet_won + bet
                win_message = f"🏆 {mention}, точне попадання! Ти виграв(ла) `{bet_won}` кг \n🏀 Тепер у тебе: `{new_balance}` кг"
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            else:
                win_message = f"😔 {mention}, ти не влучив(ла). Втрата: `{bet}` кг \n🏀 Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# /football
async def football(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'minigame'):
        return

    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT football FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"betfootball_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancelfootball"))
        keyboard.add(*bet_buttons)
        football_message = await bot.send_message(chat_id, f"⚽️ {mention}, зіграй у футбол\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг\n", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"football_player_{football_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


async def handle_football_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    football_player_id = await cache.get(f"football_player_{callback_query.message.message_id}")

    if football_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancelfootball':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return

        elif callback_query.data.startswith('betfootball_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT football FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "ℹ️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"betfootball_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 1.5)

            keyboard = InlineKeyboardMarkup()
            button_go = InlineKeyboardButton("▶️ Грати", callback_data=f"gofootball_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="cancelfootball_cell")
            keyboard.row(button_go)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
            await bot.edit_message_text(
                f"⚽️ {mention}, готовий(а)?\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('cancelfootball_cell'):
            bet = await cache.get(f"betfootball_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('gofootball_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT football FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET football = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
                await db.commit()

            wait = "⚽️ Майже дев'ятка йоу.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

            football_message = await bot.send_dice(chat_id=chat_id, emoji='⚽️')
            result_football = football_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"betfootball_{user_id}_{chat_id}")
            bet = int(bet)
            

            if result_football in [3, 4, 5]:
                bet_won = math.ceil(bet * 1.5)
                new_balance = balance_after_bet + bet_won + bet
                win_message = f"🏆 {mention}, точне попадання! Ти виграв(ла) `{bet_won}` кг \n⚽️ Тепер у тебе: `{new_balance}` кг"
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            else:
                win_message = f"😔 {mention}, ти не влучив(ла). Втрата: `{bet}` кг \n⚽️ Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# /bowling
async def bowling(message: types.Message):
    chat_id = message.chat.id

    if not await check_settings(chat_id, 'minigame'):
        return

    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT bowling FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"betbowling_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancelbowling"))
        keyboard.add(*bet_buttons)
        bowling_message = await bot.send_message(chat_id, f"🎳 {mention}, зіграй у боулінг\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг\n", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"bowling_player_{bowling_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


async def handle_bowling_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    bowling_player_id = await cache.get(f"bowling_player_{callback_query.message.message_id}")

    if bowling_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancelbowling':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return

        elif callback_query.data.startswith('betbowling_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT bowling FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "ℹ️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"betbowling_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 2)

            keyboard = InlineKeyboardMarkup()
            button_go = InlineKeyboardButton("▶️ Грати", callback_data=f"gobowling_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="cancelbowling_cell")
            keyboard.row(button_go)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
            await bot.edit_message_text(
                f"🎳 {mention}, готовий(а)?\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('cancelbowling_cell'):
            bet = await cache.get(f"betbowling_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "ℹ️")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('gobowling_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT bowling FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET bowling = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
                await db.commit()

            wait = "🎳 Ловимо рівновагу.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

            bowling_message = await bot.send_dice(chat_id=chat_id, emoji='🎳')
            result_bowling = bowling_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"betbowling_{user_id}_{chat_id}")
            bet = int(bet)
            

            if result_bowling == 6:
                bet_won = math.ceil(bet * 2)
                new_balance = balance_after_bet + bet_won + bet
                win_message = f"🏆 {mention}, точне попадання! Ти виграв(ла) `{bet_won}` кг \n🎳 Тепер у тебе: `{new_balance}` кг"
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            else:
                win_message = f"😔 {mention}, ти не влучив(ла). Втрата: `{bet}` кг \n🎳 Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(4)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# /casino
async def casino(message: types.Message):
    chat_id = message.chat.id
    
    if not await check_settings(chat_id, 'minigame'):
        return
        
    if await check_type(message):
        return

    user_id = message.from_user.id
    chat_id = message.chat.id
    mention = ('[' + message.from_user.username + ']' + '(https://t.me/' + message.from_user.username + ')') if message.from_user.username else message.from_user.first_name

    async with aiosqlite.connect('src/database.db') as db:
        cursor = await db.execute("SELECT casino FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        last_played = await cursor.fetchone()

        if last_played and last_played[0]:
            last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
            cooldown = timedelta(hours=2)
            if datetime.now() < last_played + cooldown:
                time_left = last_played + cooldown - datetime.now()
                cooldown_time = str(time_left).split(".")[0]
                await reply_and_delete(message, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                return

        cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
        balance = await cursor.fetchone()
        balance = balance[0] if balance else 0

        if balance <= 0:
            await reply_and_delete(message,f"ℹ️ У тебе `{balance}` кг. Цього недостатньо")
            return

        await cache.set(f"initial_balance_{user_id}_{chat_id}", balance)

        keyboard = InlineKeyboardMarkup(row_width=2)
        bet_buttons = [InlineKeyboardButton(f"{bet} кг", callback_data=f"betcasino_{bet}") for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
        bet_buttons.append(InlineKeyboardButton("❌ Вийти", callback_data="cancelcasino"))
        keyboard.add(*bet_buttons)
        casino_message = await bot.send_message(chat_id, f"🎰 {mention}, зіграй у казіно\nВибери ставку\n\n🏷️ У тебе: `{balance}` кг\n", reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)
        await cache.set(f"casino_player_{casino_message.message_id}", message.from_user.id)
        await asyncio.sleep(DELETE)
        try:
            await bot.delete_message(chat_id, message.message_id)
        except (MessageCantBeDeleted, MessageToDeleteNotFound):
            pass


async def handle_casino_buttons(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    casino_player_id = await cache.get(f"casino_player_{callback_query.message.message_id}")

    if casino_player_id != user_id:
        await bot.answer_callback_query(callback_query.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return

    async with aiosqlite.connect('src/database.db') as db:
        if callback_query.data == 'cancelcasino':
            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, "ℹ️ Гру скасовано")
            return

        elif callback_query.data.startswith('betcasino_'):
            _, bet = callback_query.data.split('_')
            bet = int(bet)
            cursor = await db.execute("SELECT casino FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            initial_balance = await cache.get(f"initial_balance_{user_id}_{chat_id}")
            if initial_balance is None or int(initial_balance) < bet:
                await bot.answer_callback_query(callback_query.id, "ℹ️ Недостатньо русофобії")
                return

            new_balance = int(initial_balance) - bet
            await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            await db.commit()

            await cache.set(f"betcasino_{user_id}_{chat_id}", str(bet))
            potential_win = math.ceil(bet * 2)
            potential_win2 = math.ceil(bet * 10)

            keyboard = InlineKeyboardMarkup()
            button_go = InlineKeyboardButton("▶️ Грати", callback_data=f"gocasino_{bet}")
            button_cancel = InlineKeyboardButton("❌ Відміна", callback_data="cancelcasino_cell")
            keyboard.row(button_go)
            keyboard.add(button_cancel)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name
            await bot.answer_callback_query(callback_query.id, "ℹ️ Ставка прийнята")
            await bot.edit_message_text(
                f"🎰 {mention}, готовий(а)?\n\n"
                f"🏷️ Твоя ставка: `{bet} кг`\n"
                f"💰 Можливий виграш: `{potential_win} кг `\n🎰 Або `{potential_win2} кг якщо джекпот`", chat_id=chat_id, message_id=callback_query.message.message_id, reply_markup=keyboard, parse_mode="Markdown", disable_web_page_preview=True)

        elif callback_query.data.startswith('cancelcasino_cell'):
            bet = await cache.get(f"betcasino_{user_id}_{chat_id}")
            bet = int(bet)
            await db.execute("UPDATE user_values SET value = value + ? WHERE user_id = ? AND chat_id = ?", (bet, user_id, chat_id))
            await db.commit()

            await bot.answer_callback_query(callback_query.id, "ℹ️ Скасовую гру..")
            await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Гру скасовано. Твої `{bet} кг` повернуто")
            return

        elif callback_query.data.startswith('gocasino_'):
            bet_type, bet_amount = callback_query.data.split('_')
            bet_amount = int(bet_amount)
            mention = ('[' + callback_query.from_user.username + ']' + '(https://t.me/' + callback_query.from_user.username + ')') if callback_query.from_user.username else callback_query.from_user.first_name

            cursor = await db.execute("SELECT casino FROM cooldowns WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            last_played = await cursor.fetchone()
            if last_played and last_played[0]:
                last_played = datetime.strptime(last_played[0], "%Y-%m-%d %H:%M:%S")
                cooldown = timedelta(hours=2)
                if datetime.now() < last_played + cooldown:
                    time_left = last_played + cooldown - datetime.now()
                    cooldown_time = str(time_left).split(".")[0]
                    await bot.answer_callback_query(callback_query.id, "ℹ️ Спробуй пізніше")
                    await edit_and_delete(bot, chat_id, callback_query.message.message_id, f"ℹ️ Ти ще не можеш грати. Спробуй через `{cooldown_time}`")
                    return

            if TEST == 'False':
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("UPDATE cooldowns SET casino = ? WHERE user_id = ? AND chat_id = ?", (now, user_id, chat_id))
                await db.commit()

            wait = "🎰 Довбаний рот цього казино, блядь! Ти хто такий, сука, щоб це зробити?.."
            await bot.edit_message_text(wait, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)

            casino_message = await bot.send_dice(chat_id=chat_id, emoji='🎰')
            result_casino = casino_message.dice.value

            cursor = await db.execute("SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
            balance_after_bet_tuple = await cursor.fetchone()
            if balance_after_bet_tuple is not None:
                balance_after_bet = balance_after_bet_tuple[0]
            else:
                balance_after_bet = 0

            bet = await cache.get(f"betcasino_{user_id}_{chat_id}")
            bet = int(bet)
            
            if result_casino == 64:
                bet_won = math.ceil(bet * 10)
                new_balance = balance_after_bet + bet_won + bet
                win_message = f"🏆 {mention}, джекпот! Ти виграв(ла) `{bet_won}` кг \n🎰 Тепер у тебе: `{new_balance}` кг"
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            elif result_casino in [1, 22, 43]:
                bet_won = math.ceil(bet * 2)
                new_balance = balance_after_bet + bet_won + bet
                win_message = f"🎉 {mention}, вітаю! Ти виграв(ла) `{bet_won}` кг \n🎰 Тепер у тебе: `{new_balance}` кг"
                await db.execute("UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?", (new_balance, user_id, chat_id))
            else:
                win_message = f"😔 {mention}, ти програв(ла). Втрата: `{bet}` кг \n🎰 Тепер у тебе: `{balance_after_bet}` кг"

            await db.commit()
            await asyncio.sleep(3)
            await bot.answer_callback_query(callback_query.id, "ℹ️ Гру завершено")
            await bot.edit_message_text(win_message, chat_id=chat_id, message_id=callback_query.message.message_id, parse_mode="Markdown", disable_web_page_preview=True)


# Ініціалізація обробника
def games_handlers(dp, bot):
    dp.register_message_handler(killru, commands=['killru'])
    dp.register_message_handler(game, commands=['game'])
    dp.register_callback_query_handler(handle_game_buttons, lambda c: c.data.startswith('bet_') or c.data.startswith('cell_') or c.data == 'cancel' or c.data == 'cancel_cell')
    dp.register_message_handler(dice, commands=['dice'])
    dp.register_callback_query_handler(handle_dice_buttons, lambda c: c.data.startswith('betdice_') or c.data == 'canceldice' or c.data == 'canceldice_cell' or c.data.startswith('even_') or c.data.startswith('odd_'))
    dp.register_message_handler(darts, commands=['darts'])
    dp.register_callback_query_handler(handle_darts_buttons, lambda c: c.data.startswith('betdarts_') or c.data == 'canceldarts' or c.data == 'canceldarts_cell' or c.data.startswith('godarts_'))
    dp.register_message_handler(basketball, commands=['basketball'])
    dp.register_callback_query_handler(handle_basketball_buttons, lambda c: c.data.startswith('betbasketball_') or c.data == 'cancelbasketball' or c.data == 'cancelbasketball_cell' or c.data.startswith('gobasketball_'))
    dp.register_message_handler(football, commands=['football'])
    dp.register_callback_query_handler(handle_football_buttons, lambda c: c.data.startswith('betfootball_') or c.data == 'cancelfootball' or c.data == 'cancelfootball_cell' or c.data.startswith('gofootball_'))
    dp.register_message_handler(bowling, commands=['bowling'])
    dp.register_callback_query_handler(handle_bowling_buttons, lambda c: c.data.startswith('betbowling_') or c.data == 'cancelbowling' or c.data == 'cancelbowling_cell' or c.data.startswith('gobowling_'))
    dp.register_message_handler(casino, commands=['casino'])
    dp.register_callback_query_handler(handle_casino_buttons, lambda c: c.data.startswith('betcasino_') or c.data == 'cancelcasino' or c.data == 'cancelcasino_cell' or c.data.startswith('gocasino_'))