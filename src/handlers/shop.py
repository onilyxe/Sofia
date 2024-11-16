from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, CallbackQuery
from aiogram.utils.formatting import Code, TextLink
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src import config
from src.handlers.commands import commands_router
from src.types import (ShopCallback, ShopEnum)
from src.utils import TextBuilder, reply_and_delete


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


@commands_router.callback_query(ShopCallback.filter((F.menu == ShopEnum.WHAT_IS_PRICE)))
async def shop_what_is_price(query: CallbackQuery):
    tb = TextBuilder()
    tb.add("Курс гривні до русофобії 1:10")
    tb.add("1 грн = 10 кг", new_line=True)
    tb.add("100 кг - 10 грн", new_line=True)
    tb.add("1000 кг - 100 грн", new_line=True)
    tb.add("Беремо потрібну кількість русофобії і ділимо на 10", new_line=True)
    tb.add("500 кг / 10 = 50 грн", new_line=True)

    kb = InlineKeyboardBuilder()
    back_button = InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_shop")
    kb.row(back_button)

    await query.message.edit_text(tb.render(), reply_markup=kb.as_markup())


@commands_router.callback_query(ShopCallback.filter((F.menu == ShopEnum.WHERE_MONEY_GO)))
async def shop_where_money_go(query: CallbackQuery):
    tb = TextBuilder()
    tb.add("Розробник бота зараз служить в артилерії. Їбашить кацапів щодня "
           "(Його канал: {channel})", channel=TextLink("5011", url="https://t.me/ua5011"))
    tb.add("Зібрані гроші підуть на поновлення екіпірування", new_line=True)

    kb = InlineKeyboardBuilder()
    back_button = InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_shop")
    kb.row(back_button)

    await query.message.edit_text(tb.render(), reply_markup=kb.as_markup(), disable_web_page_preview=True)


@commands_router.callback_query(F.data == "back_to_shop")
async def back_to_shop(query: CallbackQuery):
    kb = get_shop_keyboard()
    await query.message.edit_text("💳 Хочеш більше русофобії?\n"
                                  "Тут ти зможеш дізнатися як її купити", reply_markup=kb.as_markup())