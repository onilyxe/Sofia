from typing import Dict, Any, Awaitable, Callable
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram import types

from src import config
from src.database import DatabaseWrapper, Database


async def process_message(db: Database, msg: types.Message):
    if not (msg.text and msg.text.startswith("/")):
        return

    nowtime = datetime.now()
    row = await db.query.get_query(nowtime)
    if row:
        await db.query.add_count_by_id(row[0])
    else:
        await db.query.add_query(nowtime)


class DatabaseMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]], event: types.Message,
                       data: Dict[str, Any]
                       ):
        async with DatabaseWrapper(config.DBFILE) as db_conn:
            DB = Database(db_conn)
            data["db"] = DB
            await process_message(DB, event)
            await handler(event, data)
