from math import ceil
from typing import Type
from datetime import datetime, timedelta

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.formatting import TextMention, Code
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.types import Games, BetButtonType, BetCallback, BaseGameEnum
from src.utils import TextBuilder


def get_bet_buttons(user_id: int, game: Games) -> list[InlineKeyboardButton]:
    BET_BUTTONS = [InlineKeyboardButton(
        text=str(bet),
        callback_data=BetCallback(user_id=user_id, bet=bet, action=BetButtonType.BET, game=game).pack()
    ) for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
    BET_BUTTONS.append(
        InlineKeyboardButton(text="❌ Вийти", callback_data=BetCallback(user_id=user_id, bet=0,
                                                                       action=BetButtonType.CANCEL, game=game).pack()
                             )
    )
    return BET_BUTTONS


# Отримання часу, який залишився до наступного дня
def get_time_until_midnight(timestamp: int) -> str:
    dt = datetime.fromtimestamp(timestamp)
    midnight = datetime(dt.year, dt.month, dt.day) + timedelta(days=1)
    remaining_time = midnight - dt
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    remaining_time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    return remaining_time_str


async def is_can_play(balance: int, bet: int, callback: types.CallbackQuery) -> bool:
    if balance < bet:
        await callback.bot.answer_callback_query(callback.id, "ℹ️ Недостатньо русофобії")
        return False
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Ставка прийнята")
    return True


async def process_regular_bet(
        callback: types.CallbackQuery, callback_data: BetCallback, chat_user,
        callback_type: Type[CallbackData], emoji: str, wins_multiplies: int | float | list[int]
) -> None:
    balance = chat_user[3]
    bet = callback_data.bet
    if isinstance(wins_multiplies, int | float):
        potential_win = Code(ceil(bet * wins_multiplies))
    elif isinstance(wins_multiplies, list):
        potential_win = Code(ceil(bet * wins_multiplies[0])) + " або " + Code(ceil(bet * wins_multiplies[1]))
    user = callback.from_user

    if not await is_can_play(balance, bet, callback):
        return

    tb, kb = TextBuilder(), InlineKeyboardBuilder()
    play = callback_type(user_id=user.id, bet=bet, action=BaseGameEnum.PLAY)
    cancel = callback_type(user_id=user.id, bet=bet, action=BaseGameEnum.CANCEL)

    kb.row(InlineKeyboardButton(text="▶️ Грати", callback_data=play.pack()),
           InlineKeyboardButton(text="❌ Відміна", callback_data=cancel.pack()), width=1)

    tb.add("{emoji} {user}, готовий(а)?\n", emoji=emoji, user=TextMention(user.first_name, user=user))
    tb.add("🏷️ Твоя ставка: {bet} кг", True, bet=Code(bet))
    tb.add("💰 Можливий виграш: {potential_win} кг", True, potential_win=potential_win)

    await callback.message.edit_text(text=tb.render(), reply_markup=kb.as_markup())
