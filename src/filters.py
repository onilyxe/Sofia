from datetime import datetime, date

from aiogram.filters import BaseFilter
from aiogram.types import Message

from src import config
from src.database import Database
from src.types import Games


class CooldownFilter(BaseFilter):
    def __init__(self, game_type: str | Games):
        if isinstance(game_type, Games):
            game_type = str(game_type)
        self.game_type = game_type

    async def __call__(self, message: Message, db: Database):
        cooldown = await db.cooldown.get_user_cooldown(message.chat.id, message.from_user.id, self.game_type)
        if cooldown is None:
            return True
        last_game_date: date = datetime.fromtimestamp(cooldown[0]).date()
        message_date = message.date.astimezone(config.LOCAlTIMEZONE).date()
        return last_game_date < message_date
