import random

from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import Text, Code, TextMention, TextLink
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import Database
from src.filters import IsChat, IsCurrentUser
from src.types import LeaveCallback
from src.utils import TextBuilder

from src import config

commands_router = Router(name="Base commands router")


@commands_router.message(CommandStart())
async def start(message: types.Message):
    await message.reply(Text("🫡 Привіт. Я бот для гри в русофобію. Додавай мене в чат і розважайся. Щоб дізнатися як "
                             "мною користуватися, вивчай /help").as_markdown())


@commands_router.message(Command("about"))
async def about(message: types.Message):
    tb = TextBuilder(
        version=Code(config.VERSION),
        news_channel=TextLink("News Channel", url="t.me/SofiaBotRol"),
        source=TextLink("Source", url="https://github.com/onilyxe/Sofia"),
        onilyxe=TextLink("onilyxe", url="https://t.me/onilyxe"),
        den=TextLink("den", url="https://t.me/itsokt0cry")
    )
    tb.add("📡 Sofia {version}\n", True)
    tb.add("{news_channel}", True)
    tb.add("{source}\n", True)
    tb.add("Made {onilyxe}. Idea {den}", True)
    await message.reply(tb.render())


@commands_router.message(Command("my"), IsChat())
async def my_command(message: types.Message, chat_user):
    russophobia = chat_user[3]
    tb = TextBuilder(user=TextMention(
        message.from_user.username or message.from_user.first_name, user=message.from_user
    ))
    if russophobia:
        tb.add("😡 {user}, твоя русофобія: {russophobia} кг", russophobia=Code(russophobia))
    else:
        tb.add("😠 {user}, у тебе немає русофобії, губися")
    await message.reply(tb.render())


@commands_router.message(Command("leave"), IsChat())
async def leave(message: types.Message, chat_user: list):
    user = message.from_user
    russophobia = chat_user[3]
    tb, kb = TextBuilder(user=TextMention(user.first_name, user=user)), InlineKeyboardBuilder()

    if russophobia:
        tb.add("😡 {user}, ти впевнений, що хочеш проїхати свою русофобію? Твої дані зі всіх чатів буде видалено з "
               "бази даних. Цю дію не можна буде скасувати")
    else:
        tb.add("😯 {user}, у тебе і так немає русофобії, губися")

    kb.add(
        InlineKeyboardButton(
            text="✅ Так", callback_data=LeaveCallback(user_id=message.from_user.id, confirm=True).pack()
        ),
        InlineKeyboardButton(
            text="❌ Ні", callback_data=LeaveCallback(user_id=message.from_user.id, confirm=False).pack()
        )
    )

    await message.answer(
        text=tb.render(),
        reply_markup=(kb.as_markup() if russophobia else None)
    )


@commands_router.callback_query(LeaveCallback.filter(), IsCurrentUser(True))
async def leave_callback(query: CallbackQuery, callback_data: LeaveCallback, db: Database):
    if callback_data.confirm:
        await db.user.remove_user(query.from_user.id)
        await query.bot.answer_callback_query(query.id, "👹 Ох братику, даремно ти це зробив...")
        await query.bot.edit_message_text(
            f"🤬 {query.from_user.mention_markdown()}, ти покинув гру, і тебе було видалено з бази даних",
            chat_id=query.message.chat.id,
            message_id=query.message.message_id
        )
    else:
        await query.bot.answer_callback_query(query.id, "ℹ️ Cкасовуємо..")
        await query.bot.edit_message_text(
            f"🫡 {query.from_user.mention_markdown()} красунчик, ти залишився у грі",
            chat_id=query.message.chat.id,
            message_id=query.message.message_id
        )
