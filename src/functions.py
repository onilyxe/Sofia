from aiogram import types, Bot

from src import Database, DatabaseWrapper, config


async def setup_database():
    async with DatabaseWrapper(config.DBFILE) as db_conn:
        db = Database(db_conn)
        await db.init_database()


# Функція під час старту
async def startup(bot: Bot):
    await setup_database()
    commands = [
        types.BotCommand(command="/killru", description="Спробувати підвищити свою русофобію"),
        types.BotCommand(command="/my", description="Моя русофобія"),
        types.BotCommand(command="/game", description="Знайди і вбий москаля"),
        types.BotCommand(command="/dice", description="Міні гра, кинь кістки"),
        types.BotCommand(command="/darts", description="Гра в дартс"),
        types.BotCommand(command="/basketball", description="Гра в баскетбол"),
        types.BotCommand(command="/football", description="Гра у футбол"),
        types.BotCommand(command="/bowling", description="Гра в боулінг"),
        types.BotCommand(command="/casino", description="Гра в казино"),
        types.BotCommand(command="/help", description="Допомога"),
        types.BotCommand(command="/settings", description="Тільки для адмінів чату"),
        types.BotCommand(command="/give", description="Поділиться русофобією"),
        types.BotCommand(command="/top10", description="Топ 10 гравців"),
        types.BotCommand(command="/top", description="Топ гравців"),
        types.BotCommand(command="/globaltop10", description="Топ 10 серед всіх гравців"),
        types.BotCommand(command="/globaltop", description="Топ всіх гравців"),
        types.BotCommand(command="/leave", description="Покинути гру"),
        types.BotCommand(command="/about", description="Про бота"),
        types.BotCommand(command="/ping", description="Статус бота"),
    ]

    await bot.set_my_commands(commands)
    if config.STATUS:
        try:
            await bot.send_message(config.CHANNEL, f"🚀 Бот запущений")
        except Exception as e:
            print(f"Старт error: {e}")


# Функція під час завершення
async def shutdown(bot: Bot):
    if config.STATUS:
        try:
            await bot.send_message(config.CHANNEL, f"⛔️ Бот зупинений")
        except Exception as e:
            print(f"Стоп error: {e}")
