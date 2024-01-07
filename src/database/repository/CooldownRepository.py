from aiosqlite import Connection

from src.types import Games


class CooldownRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def get_user_cooldown(self, chat_id: int, user_id: int, cooldown: str | Games | None = None) -> list | None:
        if not cooldown:
            cooldown = "*"
        data = await self.connection.execute(f"SELECT cooldowns.{cooldown} FROM cooldowns, chat_users AS cu "
                                             f"INNER JOIN cooldowns c on cu.id = c.chat_user "
                                             f"WHERE cu.chat_id = ? AND cu.user_id = ?",
                                             (chat_id, user_id,))
        return await data.fetchone()

    async def add_user_cooldown(self, chat_id: int, user_id: int) -> None:
        await self.connection.execute_insert("INSERT OR IGNORE INTO cooldowns (chat_user) SELECT id AS chat_user "
                                             "FROM chat_users WHERE chat_id = ? AND user_id = ?",
                                             (chat_id, user_id))
        await self.connection.commit()

    async def update_user_cooldown(self, chat_id: int, user_id: int, cooldown: str, new_cooldown: int) -> None:
        await self.connection.execute(f"UPDATE cooldowns SET {cooldown} = ? WHERE chat_user = "
                                      f"(SELECT id FROM chat_users WHERE chat_id = ? AND user_id = ?)",
                                      (new_cooldown, chat_id, user_id))
