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
from src.handlers import games_router

# Імпортуємо конфігураційний файл
config = Config()

# Ініціалізація бота та диспетчера
bot = Bot(config.TOKEN, parse_mode=aiogram.enums.ParseMode.MARKDOWN_V2)
dp = Dispatcher()
dp.message.outer_middleware(DatabaseMiddleware())
dp.message.outer_middleware(LoggingMiddleware())
dp.message.outer_middleware(RegisterChatMiddleware())
dp.message.middleware(RegisterUserMiddleware())
dp.include_router(games_router)


@dp.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}), Command("mention"))
async def echo(message: aiogram.types.Message, bot: Bot, db: Database):
    if message.text == "ping":
        await message.answer(f'[you](tg://user?id={message.from_user.id})\n', disable_notification=True)


async def main() -> None:
    if config.SKIPUPDATES:
        await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    init_logger()
    asyncio.run(main())
