import asyncio

import aiogram
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatType
from aiogram.filters import Command

from src import CooldownFilter
from src.config import Config
from src.database import Database
from src.logger import init_logger
from src.middliwares import LoggingMiddleware, DatabaseMiddleware, RegisterChatMiddleware, RegisterUserMiddleware
from src.types import Games
from src.handlers import games_router, commands_router

# Імпортуємо конфігураційний файл
config = Config()

# Ініціалізація бота та диспетчера
bot = Bot(config.TOKEN, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2)
dp = Dispatcher()
dp.message.outer_middleware(DatabaseMiddleware())
dp.callback_query.outer_middleware(DatabaseMiddleware())
dp.message.outer_middleware(LoggingMiddleware())
dp.message.outer_middleware(RegisterChatMiddleware())
dp.message.middleware(RegisterUserMiddleware())
dp.include_routers(commands_router, games_router)


async def main() -> None:
    if config.SKIPUPDATES:
        await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    init_logger()
    asyncio.run(main())
