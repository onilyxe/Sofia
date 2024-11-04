import asyncio
import configparser
import logging
from datetime import datetime, timedelta

import aiocache
import aiosqlite
from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import MessageCantBeDeleted, MessageToDeleteNotFound

from src.functions import reply_and_delete, check_type, edit_and_delete, check_settings

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
    dp.register_message_handler(give, commands=['give'])
    dp.register_callback_query_handler(give_inline, lambda c: c.data and c.data.startswith('give_'))
