from sqlite3 import Row
from typing import Iterable

from aiosqlite import Connection, Cursor


class ChatUserRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def get_by_id(self, row_id: int) -> list | None:
        data: Cursor = await self.connection.execute("SELECT * FROM chat_users WHERE id = ?",
                                                     (row_id,))
        return await data.fetchone()

    async def get_chat_user(self, chat_id: int, user_id: int) -> list | None:
        data: Cursor = await self.connection.execute("SELECT * FROM chat_users WHERE chat_id = ? AND user_id = ?",
                                                     (chat_id, user_id,))
        return await data.fetchone()

    async def add_chat_user(self, chat_id: int, user_id: int) -> Row | None:
        data: Row = await self.connection.execute_insert("INSERT OR IGNORE INTO chat_users (chat_id, user_id) "
                                                         "VALUES (?, ?)", (chat_id, user_id))
        await self.connection.commit()
        return data

    async def update_user_russophobia(self, chat_id: int, user_id: int, russophobia: int) -> None:
        data: Row = await self.connection.execute(
            "UPDATE chat_users SET russophobia = ? WHERE chat_id = ? AND user_id = ?",
            (russophobia, chat_id, user_id))
        await self.connection.commit()

    async def get_chat_top(self, chat_id: int, limit: int = 101) -> Iterable[Row]:
        data: Cursor = await self.connection.execute(
            'SELECT user_id, russophobia FROM chat_users WHERE chat_id = ? AND russophobia != 0 ORDER BY russophobia '
            'DESC LIMIT ?',
            (chat_id, limit)
        )
        return await data.fetchall()

    async def get_global_top(self, limit: int = 101) -> Iterable[Row]:
        data: Cursor = await self.connection.execute(
            'SELECT user_id, SUM(russophobia) AS russophobia FROM chat_users WHERE russophobia != 0 '
            'GROUP BY user_id ORDER BY russophobia DESC LIMIT ?',
            (limit,)
        )
        return await data.fetchall()
