# Імпорти
import configparser
import aiosqlite
import asyncio
import aiogram
import logging
from aiogram.utils.exceptions import MessageCantBeDeleted, BotKicked, ChatNotFound, MessageToDeleteNotFound, Unauthorized
from src.functions import remove_chat, admin, reply_and_delete, send_and_delete
from aiogram import types
from aiogram import Bot


# Імпортуємо конфігураційний файл
config = configparser.ConfigParser()
try:
    config.read('config.ini')
    TOKEN = config['TOKEN']['BOT']
    ADMIN = int(config['ID']['ADMIN'])
    DELETE = int(config['SETTINGS']['DELETE'])
    ALIASES = {k: int(v) for k, v in config['ALIASES'].items()}
except (FileNotFoundError, KeyError) as e:
    logging.error(f"Помилка завантаження конфігураційного файлу в admins.py: {e}")
    exit()


# Ініціалізація бота
bot = Bot(token=TOKEN)


#-----/chatlist
async def chatlist(message: types.Message):
    if not await admin(message):
        return

    async with aiosqlite.connect('src/database.db') as db:
        chats = await db.execute_fetchall('SELECT chat_id FROM chats')

    if not chats:
        chat_list = "😬 Бота не було додано до жодного чату"
    else:
        chat_list_lines = []
        removed_chats_info = []

        for (chat_id,) in chats:
            try:
                chat_info = await bot.get_chat(chat_id)
                chat_username = f"@{chat_info.username}" if chat_info.username else ""
                chat_list_lines.append(f"🔹 {chat_id}, {chat_info.type}, {chat_info.title} {chat_username}")
            except (BotKicked, ChatNotFound, Unauthorized) as e:
                removed_chats_info.append(f"🔹 {chat_id} - вилучено ({type(e).__name__})")
                await remove_chat(chat_id)

        chat_list = "💬 Список чатів бота:\n\n" + '\n'.join(chat_list_lines)
        if removed_chats_info:
            chat_list += f"\n\n\n💢 Список вилучених чатів:\n\n" + '\n'.join(removed_chats_info)

    await reply_and_delete(message, chat_list)


#-----/message
async def message(message: types.Message):
    if not await admin(message):
        return

    parts = message.text.split(" ", 2)

    if len(parts) < 2:
        await reply_and_delete(message, "ℹ️ Розсилка повідомлень\n\n`/message [text]` - в усі чати\n`/message [ID/alias] [text]` - в один чат")
        return

    chat_id_to_send = None
    text_to_send = None

    # Determine the chat_id and text to send
    if len(parts) == 3:
        if parts[1].startswith('-100') or parts[1].lower() in ALIASES:
            chat_id_to_send = int(parts[1]) if parts[1].startswith('-100') else ALIASES[parts[1].lower()]
            text_to_send = parts[2]
        else:
            text_to_send = " ".join(parts[1:])
    else:
        text_to_send = parts[1]

    if not text_to_send.strip():
        await reply_and_delete(message, "⚠️ Текст повідомлення не може бути пустим")
        return

    successful_sends = 0
    error_messages = ""

    async with aiosqlite.connect('src/database.db') as db:
        if chat_id_to_send:
            try:
                await bot.send_message(chat_id_to_send, text_to_send)
                successful_sends += 1
            except Exception as e:
                error_messages += f"`{chat_id_to_send}`: _{e}_\n"
        else:
            async with db.execute('SELECT chat_id FROM chats') as cursor:
                chat_ids = await cursor.fetchall()
                for chat_id in chat_ids:
                    try:
                        await bot.send_message(chat_id[0], text_to_send)
                        successful_sends += 1
                    except Exception as e:
                        error_messages += f"`{chat_id[0]}`: _{e}_\n"

    reply_text = f"🆒 Повідомлення надіслано. Кількість чатів: `{successful_sends}`"
    if error_messages:
        reply_text += f"\n\n⚠️ Помилки:\n{error_messages}"

    await reply_and_delete(message, reply_text)


#-----/edit
async def edit(message: types.Message):
    if not await admin(message):
        return
    try:
        parts = message.text.split()
        user_id = None
        chat_id = message.chat.id
        mention = None

        async with aiosqlite.connect('src/database.db') as db:
            if message.reply_to_message:
                user_id = message.reply_to_message.from_user.id
                if message.reply_to_message.from_user.username:
                    mention = f"[{message.reply_to_message.from_user.username}](https://t.me/{message.reply_to_message.from_user.username})"
                else:
                    mention = message.reply_to_message.from_user.first_name

                if len(parts) == 1:
                    async with db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)) as cursor:
                        current_value = await cursor.fetchone()
                        if current_value:
                            await reply_and_delete(message, f"📊 {mention} має `{current_value[0]}` кг русофобії")
                        else:
                            await reply_and_delete(message, f"😬 {mention} ще не має русофобії")
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
                    async with db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)) as cursor:
                        current_value = await cursor.fetchone()
                        if current_value:
                            await reply_and_delete(message, f"📊 {mention} має `{current_value[0]}` кг русофобії")
                        else:
                            await reply_and_delete(message, f"😬 {mention} ще не має русофобії")
                    return

                value = parts[2]

            if ',' in value or '.' in value:
                raise ValueError("⚠️ Введене значення не є цілим числом")

            async with db.execute('SELECT value FROM user_values WHERE user_id = ? AND chat_id = ?', (user_id, chat_id)) as cursor:
                current_value = await cursor.fetchone()

            if current_value is None:
                current_value = 0
            else:
                current_value = current_value[0]

            if value.startswith('+') or value.startswith('-'):
                updated_value = current_value + int(value)
            else:
                updated_value = int(value)

            if current_value is None:
                await db.execute('INSERT INTO user_values (user_id, chat_id, value) VALUES (?, ?, ?)', (user_id, chat_id, updated_value))
            else:
                await db.execute('UPDATE user_values SET value = ? WHERE user_id = ? AND chat_id = ?', (updated_value, user_id, chat_id))

            await db.commit()
            await send_and_delete(message, chat_id, f"🆒 Значення {mention} було змінено на `{updated_value}` кг")

    except ValueError as e:
        await reply_and_delete(message, str(e))
    except OverflowError:
        await reply_and_delete(message, "⚠️ Занадто велике значення. Спробуй менше число")


# Ініціалізація обробника
def admins_handlers(dp, bot):
    dp.register_message_handler(chatlist, commands=['chatlist'])
    dp.register_message_handler(message, commands=['message'])
    dp.register_message_handler(edit, commands=['edit'])