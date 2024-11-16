from sqlite3 import Row

from aiosqlite import Connection


class UserRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def get_user(self, user_id: int) -> list | None:
        data = await self.connection.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await data.fetchone()

    async def add_user(self, user_id: int, username: str | None) -> Row | None:
        data = await self.connection.execute_insert("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                                             (user_id, username))
        await self.connection.commit()
        return data

    async def remove_user(self, user_id: int) -> None:
        await self.connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        chat_user_id = await self.connection.execute("DELETE FROM chat_users WHERE user_id = ? RETURNING id", (user_id,))
        chat_user_id = (await chat_user_id.fetchone())
        await self.connection.execute("DELETE FROM cooldowns WHERE chat_user = ?", chat_user_id)

        await self.connection.commit()
