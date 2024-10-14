import random

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.formatting import Code, TextMention

from src.database import Database
from src.filters import CooldownFilter, IsChat, IsCurrentUser
from src.types import Games, BetButtonType, BetCallback
from src.utils import TextBuilder, get_time_until_midnight

games_router = Router(name="Games router")


@games_router.message(Command(Games.KILLRU), IsChat(), CooldownFilter(Games.KILLRU, True))
async def killru_command(message: types.Message, db: Database, chat_user):
    russophobia = 0
    while russophobia == 0:
        russophobia = round(random.uniform(-5, 25))

    new_russophobia = chat_user[3] + russophobia
    current_time = message.date.timestamp()

    await db.cooldown.update_user_cooldown(message.chat.id, message.from_user.id, Games.KILLRU, current_time)
    await db.chat_user.update_user_russophobia(message.chat.id, message.from_user.id, new_russophobia)

    tb = TextBuilder(
        user=TextMention(message.from_user.first_name, user=message.from_user),
        ttp=Code(get_time_until_midnight(current_time)),
        new_russophobia=Code(new_russophobia),
        russophobia=Code(abs(russophobia))
    )
    if russophobia > 0:
        tb.add("📈 {user}, твоя русофобія збільшилась на {russophobia} кг")
    else:
        tb.add("📉 {user}, твоя русофобія зменшилась на {russophobia} кг")
    tb.add("🏷️ Тепер в тебе: {new_russophobia} кг\n⏱ Продовжуй грати через {ttp}", True)

    await message.answer(tb.render())


@games_router.callback_query(BetCallback.filter(F.action == BetButtonType.CANCEL), IsCurrentUser(True))
async def bet_callback_cancel(callback: types.CallbackQuery, callback_data: BetCallback):
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Скасовую гру..")
    await callback.message.edit_text(TextBuilder("ℹ️ Гру скасовано. Твої {bet} кг повернуто",
                                                 bet=callback_data.bet).render())
