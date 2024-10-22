import asyncio

from aiogram import Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject, or_f
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import Text, Code, TextMention, TextLink
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import config
from src.database import Database
from src.filters import IsChat, IsAdmin, IsSupport
from src.types import LeaveCallback
from src.utils import TextBuilder, reply_and_delete, get_mentioned_user
from src.config import config

admin_commands_router = Router(name="Admin commands router")


@admin_commands_router.message(Command("chatlist"), IsAdmin())
async def chatlist_command(message: types.Message, db: Database):
    chats = await db.chat.get_chats()
    tb = TextBuilder()
    if not chats:
        tb.add("😬 Бота не було додано до жодного чату")
    else:
        chat_list_lines = []
        removed_chats_info = []
        total_chats_count = 0
        removed_chats_count = 0

        for (chat_id, _, _) in chats:
            total_chats_count += 1
            try:
                chat_info = await message.bot.get_chat(chat_id)
                chat_username = f"@{chat_info.username}" if chat_info.username else ""
                chat_list_lines.append(f"🔹 {chat_id}, {chat_info.type}, {chat_info.title} {chat_username}")
            except TelegramBadRequest as e:
                removed_chats_count += 1
                removed_chats_info.append(f"🔹 {chat_id} - вилучено ({e.message})")
                await db.chat.remove_chat(chat_id)

        tb.add("💬 Список чатів бота ({chats_count}):", chats_count=total_chats_count)
        tb.add('\n'.join(chat_list_lines), new_line=True)
        if removed_chats_info:
            tb.add("\n\n\n💢 Список вилучених чатів ({removed_chats_count}):", removed_chats_count=removed_chats_count)
            tb.add('\n'.join(removed_chats_info), new_line=True)

    await reply_and_delete(message, tb.render())


@admin_commands_router.message(Command("message"), IsAdmin())
async def message_command(message: types.Message, command: CommandObject, db: Database):
    tb = TextBuilder()
    if not command.args:
        tb.add("ℹ️ Розсилка повідомлень\n\n"
               "{example1} - в усі чати\n"
               "{example2} - в один чат",
               example1=Code("/message [text]"),
               example2=Code("/message [ID/alias] [text]"))
        await reply_and_delete(message, tb.render())
        return

    parts = command.args.split(maxsplit=1)
    chat_id = None

    if len(parts) == 2 and (parts[0].startswith('-100') or parts[0].lower() in config.ALIASES):
        chat_id = int(parts[0]) if parts[0].startswith('-100') else config.ALIASES[parts[0].lower()]
        text = parts[1]
    else:
        text = " ".join(parts)

    if not text.strip():
        tb.add("ℹ️ Текст повідомлення не може бути пустим")
        await reply_and_delete(message, tb.render())
        return

    successful_sends = 0
    error_messages = ""

    chat_ids = await db.chat.get_chats_ids() if not chat_id else [(chat_id,)]
    tb_chat = TextBuilder()
    tb_chat.add(text)
    text = tb_chat.render()

    for chat in chat_ids:
        try:
            await message.bot.send_message(chat[0], text)
            successful_sends += 1
        except TelegramBadRequest as e:
            error_messages += f"{chat[0]}: {e.message}\n"

    tb.add("🆒 Повідомлення надіслано. Кількість чатів: `{successful_sends}`", successful_sends=successful_sends)
    if error_messages:
        tb.add("\nℹ️ Помилки:\n{error_messages}", error_messages=error_messages, new_line=True)

    await reply_and_delete(message, tb.render())


@admin_commands_router.message(Command("edit"), IsAdmin())
async def edit_command(message: types.Message, db: Database, command: CommandObject):
    tb = TextBuilder()
    if not command.args:
        parts = []
    else:
        parts = command.args.split()

    user = get_mentioned_user(message)

    if not user:
        await reply_and_delete(message, "ℹ️ Вкажіть користувача")
        return

    if user.is_bot or message.chat.type in ("private", "channel"):
        await reply_and_delete(message, "ℹ️ Команда недоступна для каналів, ботів і в особистих повідомленнях")
        return

    user_id = user.id
    chat_id = message.chat.id
    mention = TextMention(user.first_name, user=user)
    user_balance = (await db.chat_user.get_chat_user(chat_id, user_id))[3]
    index = 0 if len(parts) == 1 else 1
    value = int(parts[index]) if parts and parts[index].isdecimal() else None

    if value is None:
        if user_balance:
            tb.add("📊 {user} має {balance} кг русофобії", user=mention, balance=Code(user_balance))
        else:
            tb.add("😬 {user} ще не має русофобії", user=mention)
    else:
        await db.chat_user.update_user_russophobia(chat_id, user_id, value)
        tb.add("📊 {user} тепер має {balance} кг русофобії", user=mention, balance=Code(value))

    await reply_and_delete(message, tb.render())


@admin_commands_router.message(Command("add"), or_f(IsSupport(), IsAdmin()))
async def add_command(message: types.Message, db: Database, command: CommandObject):
    tb = TextBuilder()
    parts = []
    if command.args:
        parts = command.args.split()
    if not command.args or len(parts) < 3:
        tb.add("ℹ️ Неправильний формат. Використовуй {example}",
               example=Code("/add chat_id user_id value"))
        await reply_and_delete(message, tb.render())
        return

    chat_id = None

    try:
        chat_id = int(parts[0]) if parts[0].startswith('-100') else config.ALIASES[parts[0].lower()]
        user_id = int(parts[1])
        value = int(parts[2])
    except (ValueError, KeyError):
        tb.add("ℹ️ Неправильний формат. Використовуй {example}",
               example=Code("/add chat_id user_id value"))
        await reply_and_delete(message, tb.render())
        return

    current_value = (await db.chat_user.get_chat_user(chat_id, user_id))
    if current_value is None:
        await reply_and_delete(message, "😬 Користувача або чат не знайдено")
        return
    current_value = current_value[3]
    updated_value = current_value + value

    if updated_value < 0:
        await reply_and_delete(message, "ℹ️ Результат не може бути від'ємним числом")
        return

    try:
        await db.chat_user.update_user_russophobia(chat_id, user_id, updated_value)
    except OverflowError:
        await reply_and_delete(message, "ℹ️ Занадто велике значення\. Спробуй менше число")
        return

    tb.add("🆒 Значення користувача {user_id} було змінено на {updated_value} кг",
           user_id=Code(user_id),
           updated_value=Code(updated_value))
    await reply_and_delete(message, tb.render())
