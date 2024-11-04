from datetime import date

from aiogram import types
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.utils.formatting import Code

from src import config
from src.database import Database
from src.types import Games
from src.utils import TextBuilder, get_time_until_midnight


class CooldownFilter(BaseFilter):
    def __init__(self, cooldown_type: str | Games, send_answer: bool = False):
        if isinstance(cooldown_type, Games):
            cooldown_type = str(cooldown_type)
            self.is_game = True
        else:
            self.is_game = False
        self.cooldown_type = cooldown_type
        self.send_answer = send_answer

    async def __call__(self, message: Message, db: Database):
        if config.TEST:
            return True
        cooldown = await db.cooldown.get_user_cooldown(message.chat.id, message.from_user.id, self.cooldown_type)
        if cooldown is None:
            return True
        last_game_date: date = date.fromtimestamp(cooldown[0])
        message_date = date.fromtimestamp(message.date.timestamp())
        result = last_game_date < message_date
        if not result and self.send_answer:
            time = get_time_until_midnight(message.date.timestamp())
            text = "ℹ️ Ти можеш грати тільки один раз на день.\nСпробуй через {ttp}" \
                if self.is_game \
                else "ℹ️ Ти ще не можеш передати русофобію.\nСпробуй через {ttp}"
            text = TextBuilder(text, ttp=Code(time))
            await message.reply(text.render(ParseMode.MARKDOWN_V2))
        return result


class GamesFilter(BaseFilter):
    async def __call__(self, message: Message, db: Database):
        chat = await db.chat.get_chat(message.chat.id)
        return bool(chat[1])


class GiveFilter(BaseFilter):
    async def __call__(self, message: Message, db: Database):
        chat = await db.chat.get_chat(message.chat.id)
        return bool(chat[2])


class IsChat(BaseFilter):
    async def __call__(self, message: Message):
        return message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message):
        return message.from_user.id in config.ADMIN


class IsSupport(BaseFilter):
    async def __call__(self, message: Message):
        return message.from_user.id in config.SUPPORT


class IsChatAdmin(BaseFilter):
    async def __call__(self, message: Message):
        chat = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        return chat.status in ["administrator", "creator"]


class IsCurrentUser(BaseFilter):
    def __init__(self, send_callback: bool = False):
        self.send_callback = send_callback

    async def __call__(self, callback: types.CallbackQuery, callback_data):
        result = callback.from_user.id == callback_data.user_id
        if not result and self.send_callback:
            await callback.bot.answer_callback_query(callback.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return result

