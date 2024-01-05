from aiosqlite import Connection

from src.database.repository import UserRepository, ChatRepository


class Database:
    def __init__(self, db_connection: Connection):
        self.user_repository = UserRepository(db_connection)
        self.chat_repository = ChatRepository(db_connection)
