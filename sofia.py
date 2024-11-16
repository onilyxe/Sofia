import asyncio

import aiogram
from aiogram import Bot, Dispatcher

from src.config import Config
from src.functions import startup, shutdown
from src.handlers import games_router, commands_router, admin_commands_router
from src.logger import init_logger
from src.middliwares import LoggingMiddleware, DatabaseMiddleware, RegisterChatMiddleware, RegisterUserMiddleware, \
    RateLimitMiddleware

# Імпортуємо конфігураційний файл
config = Config()

# Ініціалізація бота та диспетчера
bot = Bot(config.TOKEN, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2)
dp = Dispatcher()
dp.message.outer_middleware(DatabaseMiddleware())
dp.message.outer_middleware(LoggingMiddleware())
dp.message.outer_middleware(RegisterChatMiddleware())
dp.message.outer_middleware(RateLimitMiddleware(config.SPEED, config.MESSAGES, config.BAN))
dp.message.middleware(RegisterUserMiddleware())
dp.callback_query.outer_middleware(DatabaseMiddleware())
dp.callback_query.middleware(RegisterUserMiddleware())
dp.include_routers(commands_router, games_router, admin_commands_router)


async def main() -> None:
    if config.SKIPUPDATES:
        await bot.delete_webhook(drop_pending_updates=True)

    await startup(bot)  # Виклик функції при запуску
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown(bot)  # Виклик функції при завершенні


if __name__ == "__main__":
    init_logger()
    asyncio.run(main())