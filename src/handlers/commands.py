from datetime import datetime, timedelta

import psutil
from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import Text, Code, TextMention, TextLink
from aiogram.utils.formatting import Italic as It
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import config
from src.database import Database
from src.filters import IsChat, IsCurrentUser
from src.types import LeaveCallback
from src.utils import TextBuilder, reply_and_delete, format_uptime, generate_top

commands_router = Router(name="Base commands router")
bot_start_time = datetime.now()


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


@commands_router.message(Command("ping"))
async def ping(message: types.Message, db: Database):
    start_time = datetime.now()
    await message.bot.get_me()
    ping_time = (datetime.now() - start_time).total_seconds() * 1000
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    now = datetime.now()
    uptime = now - bot_start_time
    formatted_uptime = format_uptime(uptime)
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_today - timedelta(days=now.weekday())

    today_record = await db.query.get_query(start_time)
    today_queries = today_record[1] if today_record else 0

    period_start = start_of_today if now.weekday() == 0 else start_of_week
    week_queries = await db.query.get_count_from_date(period_start)

    all_time_queries = await db.query.get_total_count()

    tb = TextBuilder()
    (tb.add("📡 Ping: {ping_time} ms\n", ping_time=Code(f"{ping_time:.2f}"))
     .add("🔥 CPU: {cpu_usage}%", True, cpu_usage=Code(cpu_usage))
     .add("💾 RAM: {ram_usage}%", True, ram_usage=Code(ram_usage))
     .add("⏱️ Uptime: {formatted_uptime}\n", True, formatted_uptime=Code(formatted_uptime))
     .add("📊 Кількість запитів:", True)
     .add("{today}: {today_queries}", True, today=It("За сьогодні"), today_queries=Code(today_queries))
     .add("{week}: {week_queries}", True, week=It("За тиждень"), week_queries=Code(week_queries))
     .add("{all_time}: {all_time_queries}", True, all_time=It("За весь час"), all_time_queries=Code(all_time_queries))
     )

    await reply_and_delete(message, tb.render())


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
