import random

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.enums import ChatType, ParseMode
from aiogram.utils.formatting import Text, Code, TextMention

from src.database import Database
from src.filters import CooldownFilter
from src.functions import get_time_until_midnight
from src.types import Games
from src.utils import TextBuilder

from src import config

games_router = Router(name="Games router")


@games_router.message(Command(Games.KILLRU), CooldownFilter(Games.KILLRU),
                      F.chat.type.in_([ChatType.SUPERGROUP, ChatType.GROUP]))
async def killru_command(message: types.Message, db: Database, chat_user):
    russophobia = 0
    while russophobia == 0:
        russophobia = round(random.uniform(-5, 25))

    new_russophobia = chat_user[3] + russophobia
    current_time = message.date.timestamp()

    await db.cooldown.update_user_cooldown(message.chat.id, message.from_user.id, Games.KILLRU, current_time)
    await db.chat_user.update_user_russophobia(message.chat.id, message.from_user.id, new_russophobia)

    tb = TextBuilder(
        user=message.from_user.mention_markdown(), russophobia=Code(abs(russophobia)),
        ttp=Code(get_time_until_midnight(current_time)),
        new_russophobia=Code(new_russophobia)
    )
    if russophobia > 0:
        tb.add("📈 {user}, твоя русофобія збільшилась на {russophobia} кг")
    else:
        tb.add("📉 {user}, твоя русофобія зменшилась на {russophobia} кг")
    tb.add("\n🏷️ Тепер в тебе: {new_russophobia} кг\n⏱ Продовжуй грати через {ttp}")

    await message.answer(tb.render(ParseMode.MARKDOWN_V2))


@games_router.message(Command(Games.KILLRU), ~CooldownFilter(Games.KILLRU),
                      F.chat.type.in_([ChatType.SUPERGROUP, ChatType.GROUP]))
async def killru_cooldown_command(message: types.Message):
    time = get_time_until_midnight(message.date.timestamp())
    text = Text("ℹ️ Ти можеш грати тільки один раз на день.\nСпробуй через ", Code(time))
    await message.answer(text.as_markdown())
