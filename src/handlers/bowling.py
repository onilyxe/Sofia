import asyncio
import math
import time

from aiogram import types, F
from aiogram.exceptions import TelegramRetryAfter
from aiogram.filters import Command
from aiogram.utils.formatting import Text, Code, TextMention
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import Database
from src.filters import CooldownFilter, IsChat, IsCurrentUser, GamesFilter
from src.handlers.games import games_router
from src.types import Games, BetButtonType, BetCallback, BowlingCallback, BaseGameEnum
from src.utils import TextBuilder, get_bet_buttons
from src.utils.utils import process_regular_bet


@games_router.message(Command(Games.BOWLING), IsChat(), CooldownFilter(Games.BOWLING, True), GamesFilter())
async def bowling_command(message: types.Message, chat_user):
    tb, kb = TextBuilder(), InlineKeyboardBuilder()
    kb.row(*get_bet_buttons(message.from_user.id, Games.BOWLING), width=2)
    tb.add("🎳 {user}, зіграй у боулінг\nВибери ставку\n\n🏷️ У тебе: {balance} кг\n",
           user=TextMention(message.from_user.first_name, user=message.from_user),
           balance=Code(chat_user[3]))
    await message.answer(tb.render(), reply_markup=kb.as_markup())


@games_router.callback_query(BetCallback.filter((F.action == BetButtonType.BET) & (F.game == Games.BOWLING)),
                             IsCurrentUser(True))
async def bowling_callback_bet(callback: types.CallbackQuery, callback_data: BetCallback, chat_user):
    await process_regular_bet(callback, callback_data, chat_user, BowlingCallback, "🎳", 2)


@games_router.callback_query(BowlingCallback.filter(F.action == BaseGameEnum.PLAY), IsCurrentUser(True))
async def bowling_callback_bet_play(callback: types.CallbackQuery,
                                    callback_data: BowlingCallback, db: Database, chat_user):
    balance = chat_user[3]
    chat_id = callback.message.chat.id
    current_time = int(time.time())
    await callback.message.edit_text(Text("🎳 Ловимо рівновагу..").as_markdown())

    user = TextMention(callback.from_user.first_name, user=callback.from_user)
    bowling_value = (await callback.message.reply_dice(emoji='🎳')).dice.value

    tb = TextBuilder(user=user)

    if bowling_value == 6:
        bet_won = math.ceil(callback_data.bet * 1.5)
        new_balance = balance + bet_won
        tb.add("🏆 {user}, точне попадання!")
        tb.add("🎳 Ти виграв(ла): {bet_won} кг\n", True, bet_won=Code(bet_won))
        tb.add("🏷️ Тепер у тебе: {new_balance} кг", True, new_balance=Code(new_balance))
    else:
        new_balance = balance - callback_data.bet
        tb.add("😔 {user}, ти не влучив(ла).")
        tb.add("🎳 Втрата: {bet} кг\n", True, bet=Code(callback_data.bet))
        tb.add("🏷️ Тепер у тебе: {new_balance} кг", True, new_balance=Code(new_balance))
    await asyncio.sleep(4)
    try:
        await callback.bot.answer_callback_query(callback.id, "🎳 Шар кинуто")
        await callback.message.edit_text(tb.render())
    except TelegramRetryAfter as e:
        pass
    else:
        await db.cooldown.update_user_cooldown(chat_id, callback.from_user.id, Games.CASINO, current_time)
        await db.chat_user.update_user_russophobia(chat_id, callback.from_user.id, new_balance)


@games_router.callback_query(BowlingCallback.filter(F.action == BaseGameEnum.CANCEL), IsCurrentUser(True))
async def bowling_callback_bet_cancel(callback: types.CallbackQuery, callback_data: BowlingCallback):
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Скасовую гру..")
    await callback.message.edit_text(TextBuilder("ℹ️ Гру скасовано. Твої {bet} кг повернуто",
                                                 bet=callback_data.bet).render())
