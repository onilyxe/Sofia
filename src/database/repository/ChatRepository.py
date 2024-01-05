from aiosqlite import Connection


class ChatRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def get_chat(self, chat_id: int) -> list | None:
        data = await self.connection.execute("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
        return await data.fetchone()

    async def add_chat(self, chat_id: int) -> None:
        await self.connection.execute_insert("INSERT OR IGNORE INTO chats (chat_id) VALUES (?)", (chat_id,))
        await self.connection.commit()
