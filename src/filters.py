from datetime import datetime, date

from aiogram import F, types
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.utils.formatting import Code

from src import config
from src.database import Database
from src.functions import get_time_until_midnight
from src.types import Games
from src.utils import TextBuilder


class CooldownFilter(BaseFilter):
    def __init__(self, game_type: str | Games, send_answer: bool = False):
        if isinstance(game_type, Games):
            game_type = str(game_type)
        self.game_type = game_type
        self.send_answer = send_answer

    async def __call__(self, message: Message, db: Database):
        if config.TEST:
            return True
        cooldown = await db.cooldown.get_user_cooldown(message.chat.id, message.from_user.id, self.game_type)
        if cooldown is None:
            return True
        last_game_date: date = date.fromtimestamp(cooldown[0])
        message_date = date.fromtimestamp(message.date.timestamp())
        result = last_game_date < message_date
        if not result and self.send_answer:
            time = get_time_until_midnight(message.date.timestamp())
            text = TextBuilder("ℹ️ Ти можеш грати тільки один раз на день.\nСпробуй через {ttp}", ttp=Code(time))
            await message.reply(text.render(ParseMode.MARKDOWN_V2))
        return result


class IsChat(BaseFilter):
    async def __call__(self, message: Message):
        return message.chat.type in [ChatType.SUPERGROUP, ChatType.GROUP]


class IsCurrentUser(BaseFilter):
    def __init__(self, send_callback: bool = False):
        self.send_callback = send_callback

    async def __call__(self, callback: types.CallbackQuery, callback_data):
        result = callback.from_user.id == callback_data.user_id
        if not result and self.send_callback:
            await callback.bot.answer_callback_query(callback.id, "❌ Ці кнопочки не для тебе!", show_alert=True)
        return result

