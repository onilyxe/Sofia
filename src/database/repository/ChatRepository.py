from sqlite3 import Row

from aiosqlite import Connection, Cursor


class ChatRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def get_chat(self, chat_id: int) -> list | None:
        data: Cursor = await self.connection.execute("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
        return await data.fetchone()

    async def add_chat(self, chat_id: int) -> Row | None:
        data = await self.connection.execute_insert("INSERT OR IGNORE INTO chats (chat_id) VALUES (?)", (chat_id,))
        await self.connection.commit()
        return data
