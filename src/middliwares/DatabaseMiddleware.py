from typing import Dict, Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram import types

from src import config
from src.database import DatabaseWrapper, Database


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], event: types.Message,
                       data: Dict[str, Any]
                       ):
        async with DatabaseWrapper(config.DBFILE) as db_conn:
            DB = Database(db_conn)
            data["db"] = DB
            await handler(event, data)
