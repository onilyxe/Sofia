from aiogram import types
from aiogram.filters import Command

from src.database import Database
from src.handlers.commands import commands_router
from src.utils import generate_top


@commands_router.message(Command("globaltop"))
async def global_top(message: types.Message, db: Database):
    results = await db.chat_user.get_global_top()
    title = "🏆 Глобальний топ русофобії"
    await generate_top(message, results, title, True)


@commands_router.message(Command("globaltop10"))
async def global_top10(message: types.Message, db: Database):
    results = await db.chat_user.get_global_top(10)
    title = "🏆 Глобальний топ 10 русофобії"
    await generate_top(message, results, title, True)


@commands_router.message(Command("top"))
async def top(message: types.Message, db: Database):
    results = await db.chat_user.get_chat_top(message.chat.id)
    title = "🏆 Топ русофобії чату"
    await generate_top(message, results, title, False)


@commands_router.message(Command("top10"))
async def top10(message: types.Message, db: Database):
    results = await db.chat_user.get_chat_top(message.chat.id, 10)
    title = "🏆 Топ 10 русофобії чату"
    await generate_top(message, results, title, False)