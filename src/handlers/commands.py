from datetime import datetime, timedelta

import psutil
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import Text, Code, TextMention, TextLink
from aiogram.utils.formatting import Italic as It
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import config
from src.database import Database
from src.filters import IsChat, IsCurrentUser, IsChatAdmin, GiveFilter
from src.types import LeaveCallback, SettingsCallback, SettingsEnum, ShopCallback, ShopEnum, HelpCallback, Games
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


def get_settings_keyboard(minigames_enabled: bool, give_enabled: bool) -> InlineKeyboardBuilder:
    kb = InlineKeyboardBuilder()
    minigames_btn = SettingsCallback(setting=SettingsEnum.MINIGAMES)
    give_btn = SettingsCallback(setting=SettingsEnum.GIVE)

    kb.row(InlineKeyboardButton(text=f"Міні-ігри: {'✅' if minigames_enabled else '❌'}",
                                callback_data=minigames_btn.pack()),
           InlineKeyboardButton(text=f"Передача кг: {'✅' if give_enabled else '❌'}",
                                callback_data=give_btn.pack()))

    return kb


@commands_router.message(Command("settings"), IsChat(), IsChatAdmin())
async def settings(message: types.Message, db: Database):
    chat = await db.chat.get_chat(message.chat.id)
    minigames_enabled = bool(chat[1])
    give_enabled = bool(chat[2])

    kb = get_settings_keyboard(minigames_enabled, give_enabled)

    await message.reply("🔧 Налаштування чату", reply_markup=kb.as_markup())


@commands_router.callback_query(SettingsCallback.filter(), IsChatAdmin())
async def settings_callback(query: CallbackQuery, callback_data: SettingsCallback, db: Database):
    chat = await db.chat.get_chat(query.message.chat.id)
    minigames_enabled = bool(chat[1])
    give_enabled = bool(chat[2])

    if callback_data.setting == SettingsEnum.MINIGAMES:
        minigames_enabled = not minigames_enabled
    elif callback_data.setting == SettingsEnum.GIVE:
        give_enabled = not give_enabled

    await db.chat.set_chat_setting(query.message.chat.id, minigames_enabled, give_enabled)
    kb = get_settings_keyboard(minigames_enabled, give_enabled)

    try:
        await query.message.edit_reply_markup(reply_markup=kb.as_markup())
    except TelegramBadRequest:
        pass
    await query.bot.answer_callback_query(query.id, "🔧 Налаштування змінено")


def get_shop_keyboard():
    kb = InlineKeyboardBuilder()
    how_to_buy_btn = ShopCallback(menu=ShopEnum.HOW_TO_BUY)
    what_is_price_btn = ShopCallback(menu=ShopEnum.WHAT_IS_PRICE)
    where_money_go_btn = ShopCallback(menu=ShopEnum.WHERE_MONEY_GO)

    kb.row(InlineKeyboardButton(text="❔ Як купити кг?", callback_data=how_to_buy_btn.pack()))
    kb.row(InlineKeyboardButton(text="💲 Яка ціна?", callback_data=what_is_price_btn.pack()))
    kb.row(InlineKeyboardButton(text="🛸 Куди підуть гроші?", callback_data=where_money_go_btn.pack()))

    return kb


@commands_router.message(Command("shop"))
async def shop(message: types.Message):
    kb = get_shop_keyboard()

    await reply_and_delete(message, "💳 Хочеш більше русофобії?\n"
                                    "Тут ти зможеш дізнатися як її купити",
                           reply_markup=kb.as_markup())


@commands_router.callback_query(ShopCallback.filter((F.menu == ShopEnum.HOW_TO_BUY)))
async def shop_how_to_buy(query: CallbackQuery):
    is_private = query.message.chat.type == "private"
    tb = TextBuilder()
    tb.add("Посилання на банку: {bank}", bank=TextLink("send.monobank.ua", url=config.DONATE))
    tb.add("Робите донат на потрібну вам суму, і відправляєте скріншот оплати в @OnilyxeBot", new_line=True)
    tb.add("Головна умова, вказати ID чату де ви хочете поповнення балансу. "
           "Якщо ти не знаєш що це таке, то просто напиши цю команду у потрібному чаті"
           if is_private else
           "ID цього чату: {chat_id}", new_line=True, chat_id=Code(query.message.chat.id))
    tb.add("Після чекай поки адміни оброблять твій запит", new_line=True)

    kb = InlineKeyboardBuilder()
    back_button = InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_shop")
    kb.row(back_button)

    await query.message.edit_text(tb.render(), reply_markup=kb.as_markup())


@commands_router.callback_query(F.data == "back_to_shop")
async def back_to_shop(query: CallbackQuery):
    kb = get_shop_keyboard()
    await query.message.edit_text("💳 Хочеш більше русофобії?\n"
                                  "Тут ти зможеш дізнатися як її купити", reply_markup=kb.as_markup())


def get_help_keyboard():
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="Основна гра - /killru", callback_data=HelpCallback(game=Games.KILLRU).pack()),
           width=1)

    buttons = [
        InlineKeyboardButton(text="🎲", callback_data=HelpCallback(game=Games.DICE).pack()),
        InlineKeyboardButton(text="🎯", callback_data=HelpCallback(game=Games.DARTS).pack()),
        InlineKeyboardButton(text="🎳", callback_data=HelpCallback(game=Games.BOWLING).pack()),
        InlineKeyboardButton(text="🏀", callback_data=HelpCallback(game=Games.BASKETBALL).pack()),
        InlineKeyboardButton(text="⚽", callback_data=HelpCallback(game=Games.FOOTBALL).pack()),
        InlineKeyboardButton(text="🎰", callback_data=HelpCallback(game=Games.CASINO).pack())
    ]

    kb.row(*buttons, width=4)
    return kb


@commands_router.message(Command("help"))
async def help_command(message: types.Message):
    kb = get_help_keyboard()
    await reply_and_delete(message, text="⚙️ Тут ти зможеш дізнатися\nпро мене все", reply_markup=kb.as_markup())


@commands_router.callback_query(F.data == "back_to_help")
async def back_to_help(query: CallbackQuery):
    kb = get_help_keyboard()
    await query.message.edit_text("⚙️ Тут ти зможеш дізнатися\nпро мене все", reply_markup=kb.as_markup())


@commands_router.callback_query(HelpCallback.filter())
async def callback_help(query: CallbackQuery, callback_data: HelpCallback):
    game_emojis = {
        "killru":
            f"Гра в русофобію"
            "\nУ гру можна зіграти кожен день один раз, виконавши /killru"
            "\nПри цьому кількість русофобії випадковим чином збільшиться(до +25) або зменшиться(до -5)"
            "\nРейтин можна подивитися виконавши /top. Є маленький варіант /top10, і глобальний топ, показує топ серед усіх учасників /globaltop10 і маленький варіант /globaltop10 "
            "\nВиконавши /my можна дізнатися свою кількість русофобії"
            "\nПередати свою русофобію іншому користувачу, можна відповівши йому командою /give, вказавши кількість русофобії"
            "\nІнформацію про бота можна подивитися, виконавши /about"
            "\nСлужбова інформація: /ping"
            "\nВаріанти міні-ігор можна переглянути за командою /help, вибравши знизу емодзі, що вказує на гру"
            "\nЗа командою /settings можна вимкнути в чаті міні-ігри та передачу русофобії. Налаштування доступні тільки адмінам чату"
            "\nВийти з гри (прогрес видаляється): /leave"
            "\n\n\nЯкщо мені видати права адміна (видалення повідомлень), то я через годину буду видаляти повідомлення від мене і які мене викликали. Залишаючи тільки про зміни в русофобії"
            "\n\n\nKillru. Смерть всьому російському. 🫡",

        "game":
            f"🧌 Знайди і вбий москаля. Суть гри вгадати де знаходиться москаль на сітці 3х3"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /game",

        "dice":
            f"🎲 Гра у кості. Суть гри вгадати яке випаде число, парне чи непарне"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 15. Буде 65"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /dice",

        "darts":
            f"🎯 Гра в дартс. Суть гри потрапити в центр"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 2. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /darts",

        "basketball":
            f"🏀 Гра в баскетбол. Суть гри потрапити в кошик м'ячем"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 15. Буде 65"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /basketball",

        "football":
            f"⚽️ Гра у футбол. Суть гри потрапити м'ячем у ворота"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 1.5. Було 50 кг. При виграші зі ставкою 10, отримуєш 15. Буде 65"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /football",

        "bowling":
            f"🎳 Гра в боулінг. Суть гри вибити страйк"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 2. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /bowling",

        "casino":
            f"🎰 Гра в казино. Суть гри вибити джекпот"
            "\n⏱️ Можна зіграти раз на 2 години"
            "\n🔀 Приз: ставка множиться на 2. Було 50 кг. При виграші зі ставкою 10, отримуєш 20. Буде 70. Якщо вибити джекпот (777), то ставка множиться на 10"
            "\n💰 Ставки: 1, 5, 10, 20, 30, 40, 50, 100"
            "\n🚀 Команда гри: /casino",
    }
    tb = TextBuilder()
    tb.add(game_emojis[callback_data.game])
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_help"))
    await query.message.edit_text(tb.render(), reply_markup=kb.as_markup())
