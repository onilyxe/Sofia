from sqlite3 import Row

from aiosqlite import Connection

from src.types import Games


class CooldownRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def get_user_cooldown(self, chat_id: int, user_id: int, cooldown_type: str | Games | None = None) -> list | None:
        if not cooldown_type:
            cooldown = "*"

        data = await self.connection.execute(f"SELECT {cooldown_type} FROM cooldowns INNER JOIN chat_users ON"
                                             f" chat_users.id = cooldowns.chat_user WHERE chat_users.chat_id = ? "
                                             f"AND chat_users.user_id = ?",
                                             (chat_id, user_id,))
        return await data.fetchone()

    async def add_user_cooldown(self, chat_id: int, user_id: int) -> Row | None:
        data = await self.connection.execute_insert("INSERT OR IGNORE INTO cooldowns (chat_user) "
                                                    "SELECT id AS chat_user FROM chat_users "
                                                    "WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        await self.connection.commit()
        return data

    async def update_user_cooldown(self, chat_id: int, user_id: int, cooldown_type: str, new_cooldown: int) -> None:
        await self.connection.execute(f"UPDATE cooldowns SET {cooldown_type} = ? WHERE chat_user = "
                                      f"(SELECT id FROM chat_users WHERE chat_id = ? AND user_id = ?)",
                                      (new_cooldown, chat_id, user_id))
