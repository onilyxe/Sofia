from typing import Dict, Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram import types
from aiogram.enums import ChatType

from src import config
from src import Database


class RegisterMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], event: types.Message,
                       data: Dict[str, Any]
                       ):
        db: Database|None = data.get("db", None)
        if db is None:
            raise Exception("Database Not Found")
        if not event.from_user:
            return await handler(event, data)

        if not await db.user_repository.get_user(event.from_user.id):
            await db.user_repository.add_user(event.from_user.id, event.from_user.username)

        chat = await db.chat_repository.get_chat(event.chat.id)
        if event.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP] and not chat:
            await db.chat_repository.add_chat(event.chat.id)
        return await handler(event, data)
