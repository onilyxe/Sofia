from aiosqlite import Connection

from src.database.repository import UserRepository, ChatRepository, ChatUserRepository, CooldownRepository, \
    QueriesRepository


class Database:
    def __init__(self, db_connection: Connection):
        self.__db_connection = db_connection
        self.user = UserRepository(self.__db_connection)
        self.chat = ChatRepository(self.__db_connection)
        self.chat_user = ChatUserRepository(self.__db_connection)
        self.cooldown = CooldownRepository(self.__db_connection)
        self.query = QueriesRepository(self.__db_connection)

    async def init_database(self):
        await self.__db_connection.execute('''-- Table: chat_users
                CREATE TABLE IF NOT EXISTS chat_users 
                (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL, user_id NUMERIC REFERENCES users (user_id) 
                ON DELETE CASCADE NOT NULL, chat_id INTEGER REFERENCES chats (chat_id) NOT NULL, 
                russophobia INTEGER DEFAULT (0));
                ''')
        await self.__db_connection.execute('''-- Table: chats
                CREATE TABLE IF NOT EXISTS chats 
                (chat_id INTEGER PRIMARY KEY, minigames BOOLEAN DEFAULT (1), give BOOLEAN DEFAULT (1));
                ''')
        await self.__db_connection.execute('''-- Table: cooldowns
                CREATE TABLE IF NOT EXISTS cooldowns 
                (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE, chat_user INTEGER REFERENCES chat_users (id) 
                ON DELETE CASCADE UNIQUE NOT NULL, killru TIMESTAMP DEFAULT (0), give TIMESTAMP DEFAULT (0), 
                game TIMESTAMP DEFAULT (0), dice TIMESTAMP DEFAULT (0), darts TIMESTAMP DEFAULT (0), 
                basketball TIMESTAMP DEFAULT (0), football TIMESTAMP DEFAULT (0), 
                bowling TIMESTAMP DEFAULT (0), casino TIMESTAMP DEFAULT (0));
                ''')
        await self.__db_connection.execute('''-- Table: queries
                CREATE TABLE IF NOT EXISTS queries 
                (id INTEGER PRIMARY KEY, datetime TIMESTAMP NOT NULL, count INTEGER NOT NULL DEFAULT 0);
                ''')
        await self.__db_connection.execute('''-- Table: users
                CREATE TABLE IF NOT EXISTS users 
                (user_id INTEGER PRIMARY KEY UNIQUE NOT NULL, status INTEGER DEFAULT (0), username TEXT);
                ''')
        await self.__db_connection.commit()
