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
        types.BotCommand(command="/killru", description="підвищити свою русофобію"),
        types.BotCommand(command="/my", description="моя русофобія"),
        types.BotCommand(command="/game", description="вбий москаля"),
        types.BotCommand(command="/dice", description="кинь кістки"),
        types.BotCommand(command="/darts", description="дартс"),
        types.BotCommand(command="/basketball", description="баскетбол"),
        types.BotCommand(command="/football", description="футбол"),
        types.BotCommand(command="/bowling", description="боулінг"),
        types.BotCommand(command="/casino", description="казино"),
        types.BotCommand(command="/help", description="довідка"),
        types.BotCommand(command="/give", description="передати русофобію"),
        types.BotCommand(command="/top10", description="топ 10"),
        types.BotCommand(command="/top", description="топ"),
        types.BotCommand(command="/globaltop10", description="глобальний топ 10"),
        types.BotCommand(command="/globaltop", description="глобальний топ"),
        types.BotCommand(command="/leave", description="покинути гру"),
        types.BotCommand(command="/about", description="про бота"),
        types.BotCommand(command="/ping", description="статус бота"),
    ]

    await bot.set_my_commands(commands)
    if config.STATUS:
        print("Бот запущений")
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
