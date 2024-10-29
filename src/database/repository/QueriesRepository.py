from datetime import datetime
from sqlite3 import Row, Cursor

from aiosqlite import Connection


class QueriesRepository:
    def __init__(self, connection: Connection):
        self.connection = connection

    async def add_query(self, time: datetime, count: int = 1) -> Row | None:
        data: Row = await self.connection.execute_insert("INSERT INTO queries (datetime, count) VALUES (?, ?)",
                                                         (time, count))
        await self.connection.commit()
        return data

    async def get_query(self, time: datetime) -> list | None:
        data: Cursor = await self.connection.execute("SELECT id, count FROM queries "
                                                     "WHERE datetime >= ? AND datetime < ? "
                                                     "ORDER BY datetime DESC LIMIT 1",
                                                     [time.replace(hour=0, minute=0, second=0, microsecond=0),
                                                      time.replace(hour=23, minute=59, second=59, microsecond=999999)])

        return await data.fetchone()

    async def add_count_by_id(self, row_id: int) -> None:
        await self.connection.execute("UPDATE queries SET count = count + 1 WHERE id = ?", (row_id,))
        await self.connection.commit()
