from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import Database
from src.filters import IsChat, IsChatAdmin
from src.handlers.commands import commands_router
from src.types import (SettingsCallback, SettingsEnum)


def get_settings_keyboard(minigames_enabled: bool, give_enabled: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    minigames_btn = SettingsCallback(setting=SettingsEnum.MINIGAMES)
    give_btn = SettingsCallback(setting=SettingsEnum.GIVE)

    kb.row(InlineKeyboardButton(text=f"Міні-ігри: {'✅' if minigames_enabled else '❌'}",
                                callback_data=minigames_btn.pack()),
           InlineKeyboardButton(text=f"Передача кг: {'✅' if give_enabled else '❌'}",
                                callback_data=give_btn.pack()))
    return kb


@commands_router.message(Command("settings"), IsChat(), IsChatAdmin())
async def settings(message: types.Message, db: Database):
    chat = await db.chat.get_chat(message.chat.id)
    minigames_enabled = bool(chat[1])
    give_enabled = bool(chat[2])
    kb = get_settings_keyboard(minigames_enabled, give_enabled)

    await message.reply("🔧 Налаштування чату", reply_markup=kb.as_markup())


@commands_router.callback_query(SettingsCallback.filter(), IsChatAdmin())
async def settings_callback(query: CallbackQuery, callback_data: SettingsCallback, db: Database):
    chat = await db.chat.get_chat(query.message.chat.id)
    minigames_enabled = bool(chat[1])
    give_enabled = bool(chat[2])

    if callback_data.setting == SettingsEnum.MINIGAMES:
        minigames_enabled = not minigames_enabled
    elif callback_data.setting == SettingsEnum.GIVE:
        give_enabled = not give_enabled

    await db.chat.set_chat_setting(query.message.chat.id, minigames_enabled, give_enabled)
    kb = get_settings_keyboard(minigames_enabled, give_enabled)

    try:
        await query.message.edit_reply_markup(reply_markup=kb.as_markup())
    except TelegramBadRequest:
        pass
    await query.bot.answer_callback_query(query.id, "🔧 Налаштування змінено")
