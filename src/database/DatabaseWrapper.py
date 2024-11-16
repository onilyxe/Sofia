import aiosqlite


class DatabaseWrapper:
    """ Обгортка для підключення до бази даних """

    def __init__(self, db_file: str):
        self.db_file = db_file
        self.__connection: aiosqlite.Connection | None = None

    async def connect(self):
        if self.__connection is None:
            self.__connection = await aiosqlite.connect(self.db_file)
        return self.__connection

    async def disconnect(self):
        if self.__connection:
            await self.__connection.close()
        self.__connection = None

    async def __aenter__(self):
        if not self.__connection:
            return await self.connect()
        return self.__connection

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()