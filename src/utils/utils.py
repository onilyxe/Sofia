import asyncio
from datetime import datetime, timedelta
from math import ceil
from typing import Type

from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, User, InputFile
from aiogram.utils.formatting import TextMention, Code, Text
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config import config
from src.types import Games, BetButtonType, BetCallback, BaseGameEnum
from src.utils import TextBuilder


def get_bet_buttons(user_id: int, game: Games) -> list[InlineKeyboardButton]:
    BET_BUTTONS = [InlineKeyboardButton(
        text=str(bet),
        callback_data=BetCallback(user_id=user_id, bet=bet, action=BetButtonType.BET, game=game).pack()
    ) for bet in [1, 5, 10, 20, 30, 40, 50, 100]]
    BET_BUTTONS.append(
        InlineKeyboardButton(text="❌ Злитися", callback_data=BetCallback(user_id=user_id, bet=0,
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
        await callback.bot.answer_callback_query(callback.id, "Пішов нахуй бомжара. Зароби спочатку русофобію")
        return False
    await callback.bot.answer_callback_query(callback.id, "Ну і хуйня")
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
    else:
        potential_win = Code(0)
    user = callback.from_user

    if not await is_can_play(balance, bet, callback):
        return

    tb, kb = TextBuilder(), InlineKeyboardBuilder()
    play = callback_type(user_id=user.id, bet=bet, action=BaseGameEnum.PLAY)
    cancel = callback_type(user_id=user.id, bet=bet, action=BaseGameEnum.CANCEL)

    kb.row(InlineKeyboardButton(text="▶️ Полетіли", callback_data=play.pack()),
           InlineKeyboardButton(text="❌ Злитися", callback_data=cancel.pack()), width=1)

    tb.add("{emoji} {user}, готовий(а) курва?\n", emoji=emoji, user=TextMention(user.first_name, user=user))
    tb.add("🏷️ Шо ти поставив: {bet} кг", True, bet=Code(bet))
    tb.add("💰 Шо можеш виграти: {potential_win} кг", True, potential_win=potential_win)

    await callback.message.edit_text(text=tb.render(), reply_markup=kb.as_markup())


async def reply_and_delete(message: types.Message, text: str | TextBuilder, reply_markup=None) -> None:
    if isinstance(text, TextBuilder):
        text = text.render()
    reply = await message.reply(text, reply_markup=reply_markup)
    await asyncio.sleep(config.DELETE)
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=reply.message_id)
    except TelegramBadRequest:
        pass


async def reply_voice_and_delete(message: types.Message, voice: InputFile) -> None:
    reply = await message.reply_voice(voice=voice)
    await asyncio.sleep(config.DELETE)
    try:
        await message.bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await message.bot.delete_message(chat_id=message.chat.id, message_id=reply.message_id)
    except TelegramBadRequest:
        pass


def get_mentioned_user(message: types.Message) -> types.User | None:
    if message.reply_to_message and not is_service_message(message.reply_to_message):
        return message.reply_to_message.from_user

    for entity in message.entities:
        if entity.type == "text_mention":
            return entity.user

    return None


def is_service_message(message: types.Message) -> bool:
    return any([message.new_chat_members, message.left_chat_member, message.new_chat_title, message.new_chat_photo,
                message.delete_chat_photo, message.group_chat_created, message.supergroup_chat_created,
                message.forum_topic_created, message.forum_topic_reopened, message.forum_topic_closed,
                message.forum_topic_edited, message.general_forum_topic_hidden, message.general_forum_topic_unhidden,
                message.giveaway_created, message.giveaway, message.giveaway_completed, message.video_chat_started,
                message.video_chat_scheduled, message.video_chat_ended])


def format_uptime(uptime):
    days, remainder = divmod(uptime.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        return f"{int(days)} д. {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


async def generate_top(message: types.Message, results: list[tuple[int, int]], title: str, is_global: bool) -> None:
    tb = TextBuilder()
    if not results:
        await reply_and_delete(message, tb.add('Ніхто не грав. Нахуй я взагалі писав цього йобаного бота бляха').render())
    else:
        async def get_username(user_id):
            try:
                user_info = await message.bot.get_chat(user_id) if is_global \
                    else await message.bot.get_chat_member(message.chat.id, user_id)
                if not is_global:
                    user_info = user_info.user
                else:
                    user_info = User(is_bot=False, **user_info.model_dump())
                if user_info.username:
                    return TextMention(user_info.first_name, user=user_info)
                else:
                    return user_info.first_name
            except TelegramBadRequest:
                return None

        tasks = [get_username(user_id) for user_id, _ in results]
        user_names = await asyncio.gather(*tasks)

        total_kg = sum([value for _, value in results])

        
        tb.add(f'{title}:\n🎱 Усього: {total_kg} кг\n')
        count = 0
        for user_name, (_, rusophobia) in zip(user_names, results):
            if user_name:
                count += 1
                d = {f"count_{count}": count, f"user_name_{count}": user_name, f"rusophobia_{count}": Text(rusophobia)}
                tb.add('{count_%(count)s}. {user_name_%(count)s}: {rusophobia_%(count)s} кг' % {"count": count}, True,
                       **d)

        await reply_and_delete(message, tb.render())

