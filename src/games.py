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


# Ініціалізація обробника
def games_handlers(dp, bot):
    dp.register_message_handler(game, commands=['game'])