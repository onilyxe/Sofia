import time

from aiogram import types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import Code, TextMention
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.database import Database
from src.filters import IsChat, IsCurrentUser, GiveFilter, CooldownFilter
from src.handlers.commands import commands_router
from src.types import (Actions, GiveCallback, GiveEnum)
from src.utils import TextBuilder, reply_and_delete


@commands_router.message(Command(Actions.GIVE), IsChat(), GiveFilter(), CooldownFilter(Actions.GIVE, True))
async def give(message: types.Message, command: CommandObject, db: Database, chat_user):
    args = command.args
    tb = TextBuilder()
    if (not message.reply_to_message
            or message.from_user.id == message.reply_to_message.from_user.id
            or message.reply_to_message.from_user.is_bot
            or not args or len(args := args.split()) != 1
    ):
        tb.add("ℹ️ Використовуй {cmd} у відповідь на повідомлення", cmd=Code(f"/give N"))
        await reply_and_delete(message, tb.render())
        return
    if not (value := args[0]).isdigit() or (value := int(value)) == 0:
        tb.add("🤨 Типу розумний, так? Введи плюсове і ціле число. Наприклад: {cmd} у відповідь на повідомлення",
               cmd=Code(f"/give N"))
        await reply_and_delete(message, tb.render())
        return

    giver_id = message.from_user.id
    receiver_user = message.reply_to_message.from_user
    receiver_id = receiver_user.id

    giver = chat_user
    receiver = await db.chat_user.get_chat_user(message.chat.id, receiver_id)

    if not giver or giver[3] < value:
        tb.add("ℹ️ У тебе {russophobia} кг. Цього недостатньо", russophobia=Code(giver[3] if giver else 0))
        await reply_and_delete(message, tb.render())
        return

    if not receiver:
        tb.add("ℹ️ Цей користувач не грає в русофобію")
        await reply_and_delete(message, tb.render())
        return

    kb = InlineKeyboardBuilder()
    yes = GiveCallback(user_id=giver_id, receiver_id=receiver_id, value=value,
                       receiver_balance=receiver[3], action=GiveEnum.YES)
    no = GiveCallback(user_id=giver_id, receiver_id=0, value=0, receiver_balance=0, action=GiveEnum.NO)
    kb.row(InlineKeyboardButton(text="✅ Так", callback_data=yes.pack()))
    kb.row(InlineKeyboardButton(text="❌ Ні", callback_data=no.pack()))

    tb.add("🔄 {giver} збирається передати {value} кг русофобії {receiver}. \n🏷️ В тебе: {current_value} кг",
           value=Code(value), giver=TextMention(message.from_user.first_name, user=message.from_user),
           receiver=TextMention(receiver_user.first_name, user=receiver_user), current_value=Code(giver[3]))

    await reply_and_delete(message, tb.render(), reply_markup=kb.as_markup())


@commands_router.callback_query(GiveCallback.filter((F.action == GiveEnum.YES)), IsCurrentUser(True),
                                CooldownFilter(Actions.GIVE, True))
async def give_yes(query: CallbackQuery, callback_data: GiveCallback, db: Database, chat_user):
    giver_id = callback_data.user_id
    receiver_id = callback_data.receiver_id
    value = callback_data.value
    receiver_balance = callback_data.receiver_balance
    new_balance = chat_user[3] - value

    current_time = int(time.time())

    receiver = await query.bot.get_chat_member(query.message.chat.id, receiver_id)
    tb = TextBuilder()
    tb.add("✅ {giver} передав {value} кг русофобії {receiver}.\n🏷️ Тепер в тебе: {new_value} кг",
           value=Code(value), new_value=Code(new_balance),
           giver=TextMention(query.from_user.first_name, user=query.from_user),
           receiver=TextMention(receiver.user.first_name, user=receiver.user))

    try:
        await query.bot.answer_callback_query(query.id, "ℹ️ Переказую кг..")
        await query.message.edit_text(tb.render())
    except TelegramBadRequest:
        pass
    else:
        await db.cooldown.update_user_cooldown(query.message.chat.id, giver_id, Actions.GIVE, current_time)
        await db.chat_user.update_user_russophobia(query.message.chat.id, receiver_id, receiver_balance + value)
        await db.chat_user.update_user_russophobia(query.message.chat.id, giver_id, new_balance)


@commands_router.callback_query(GiveCallback.filter((F.action == GiveEnum.NO)), IsCurrentUser(True), )
async def give_yes(query: CallbackQuery):
    await query.bot.answer_callback_query(query.id, "ℹ️ Скасовую..")
    await query.message.edit_text("🔄 Передача русофобії скасована")