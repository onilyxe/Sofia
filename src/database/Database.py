from aiosqlite import Connection

from src.database.repository import UserRepository, ChatRepository, ChatUserRepository, CooldownRepository


class Database:
    def __init__(self, db_connection: Connection):
        self.user = UserRepository(db_connection)
        self.chat = ChatRepository(db_connection)
        self.chat_user = ChatUserRepository(db_connection)
        self.cooldown = CooldownRepository(db_connection)
