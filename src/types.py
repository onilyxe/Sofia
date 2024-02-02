from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class Games(StrEnum):
    KILLRU = "killru"
    GAME = "game"
    DICE = "dice"


class BetButtonType(StrEnum):
    BET = "BET"
    CANCEL = "CANCEL"


class DiceParityEnum(StrEnum):
    EVEN = "EVEN"
    ODD = "ODD"
    CANCEL = "CANCEL"


class LeaveCallback(CallbackData, prefix="leave"):
    user_id: int
    confirm: bool


class BetCallback(CallbackData, prefix="bet"):
    user_id: int
    bet: int
    action: BetButtonType
    game: Games


class DiceCallback(CallbackData, prefix="dice"):
    user_id: int
    bet: int
    parity: DiceParityEnum
