import asyncio
import math
import random
import time

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.formatting import Text, Code, TextMention
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import Database
from src.filters import CooldownFilter, IsChat, IsCurrentUser
from src.functions import get_time_until_midnight
from src.types import Games, BetButtonType, BetCallback, DiceCallback, DiceParityEnum
from src.utils import TextBuilder

games_router = Router(name="Games router")


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


@games_router.message(Command(Games.DICE), IsChat(), CooldownFilter(Games.DICE, True))
async def dice_command(message: types.Message, db: Database, chat_user):
    tb, kb = TextBuilder(), InlineKeyboardBuilder()
    kb.row(*get_bet_buttons(message.from_user.id, Games.DICE), width=2)
    tb.add("🎲 {user}, зіграй у кості\nВибери ставку\n\n🏷️ У тебе: {balance} кг\n",
           user=TextMention(message.from_user.first_name, user=message.from_user),
           balance=Code(chat_user[3]))
    await message.answer(tb.render(), reply_markup=kb.as_markup())


@games_router.callback_query(BetCallback.filter((F.action == BetButtonType.BET) & (F.game == Games.DICE)),
                             IsCurrentUser(True))
async def dice_callback_bet(callback: types.CallbackQuery, callback_data: BetCallback, chat_user):
    balance = chat_user[3]
    bet = callback_data.bet
    potential_win = math.ceil(bet * 1.5)
    user = callback.from_user

    if balance < bet:
        await callback.bot.answer_callback_query(callback.id, "ℹ️ Недостатньо русофобії")
        return
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Ставка прийнята")

    tb, kb = TextBuilder(), InlineKeyboardBuilder()
    even = DiceCallback(user_id=user.id, bet=bet, parity=DiceParityEnum.EVEN)
    odd = DiceCallback(user_id=user.id, bet=bet, parity=DiceParityEnum.ODD)
    cancel = DiceCallback(user_id=user.id, bet=bet, parity=DiceParityEnum.CANCEL)

    kb.row(InlineKeyboardButton(text="➗ Парне", callback_data=even.pack()),
           InlineKeyboardButton(text="✖️ Непарне", callback_data=odd.pack()),
           InlineKeyboardButton(text="❌ Відміна", callback_data=cancel.pack()), width=2)

    tb.add("🎲 {user}, зроби свій вибір:\n", user=TextMention(user.first_name, user=user))
    tb.add("🏷️ Твоя ставка: {bet} кг", True, bet=Code(bet))
    tb.add("🏷💰 Можливий виграш: {potential_win} кг", True, potential_win=Code(potential_win))

    await callback.message.edit_text(text=tb.render(), reply_markup=kb.as_markup())


@games_router.callback_query(DiceCallback.filter(F.parity != DiceParityEnum.CANCEL), IsCurrentUser(True))
async def dice_callback_bet_play(callback: types.CallbackQuery, callback_data: DiceCallback, db: Database, chat_user):
    balance = chat_user[3]
    chat_id = callback.message.chat.id
    current_time = int(time.time())
    await db.cooldown.update_user_cooldown(chat_id, callback.from_user.id, Games.DICE, current_time)
    await callback.message.edit_text(Text("🎲 Кидаємо кубик..").as_markdown())

    user = TextMention(callback.from_user.first_name, user=callback.from_user)
    dice_value = (await callback.message.reply_dice()).dice.value
    parity = 0 if callback_data.parity == DiceParityEnum.EVEN else 1

    tb = TextBuilder(user=user, dice_value=Code(dice_value), parity='парне' if not dice_value % 2 else 'непарне')

    if dice_value % 2 == parity:
        bet_won = math.ceil(callback_data.bet * 1.5)
        new_balance = balance + bet_won
        await db.chat_user.update_user_russophobia(chat_id, callback.from_user.id, new_balance)
        tb.add("🏆 {user}, ти виграв(ла)! Випало {dice_value}, {parity}")
        tb.add("🎲 Твій виграш: {bet_won} кг\n", True, bet_won=Code(bet_won))
        tb.add("🏷️ Тепер у тебе: {new_balance} кг", True, new_balance=Code(new_balance))
    else:
        new_balance = balance - callback_data.bet
        await db.chat_user.update_user_russophobia(chat_id, callback.from_user.id, new_balance)
        tb.add("😔 {user}, ти програв(ла). Випало {dice_value}, {parity}")
        tb.add("🎲 Втрата: {bet} кг\n", True, bet=Code(callback_data.bet))
        tb.add("🏷️ Тепер у тебе: {new_balance} кг", True, new_balance=Code(new_balance))
    await asyncio.sleep(4)
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Гру завершено")
    await callback.message.edit_text(tb.render())


@games_router.callback_query(BetCallback.filter(F.action == BetButtonType.CANCEL), IsCurrentUser(True))
async def dice_callback_cancel(callback: types.CallbackQuery, callback_data: BetCallback):
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Скасовую гру..")
    await callback.message.edit_text("ℹ️ Гру скасовано")


@games_router.callback_query(DiceCallback.filter(F.parity == DiceParityEnum.CANCEL), IsCurrentUser(True))
async def dice_callback_bet_cancel(callback: types.CallbackQuery, callback_data: DiceCallback):
    await callback.bot.answer_callback_query(callback.id, "ℹ️ Скасовую гру..")
    await callback.message.edit_text(TextBuilder("ℹ️ Гру скасовано. Твої {bet} кг повернуто",
                                                 bet=callback_data.bet).render())
