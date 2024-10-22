from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class Games(StrEnum):
    KILLRU = "killru"
    GAME = "game"
    DICE = "dice"
    DARTS = "darts"
    BOWLING = "bowling"
    BASKETBALL = "basketball"
    FOOTBALL = "football"
    CASINO = "casino"


class BaseGameEnum(StrEnum):
    PLAY = "play"
    CANCEL = "cancel"


class BetButtonType(StrEnum):
    BET = "bet"
    CANCEL = "cancel"


class DiceParityEnum(StrEnum):
    EVEN = "even"
    ODD = "odd"
    CANCEL = "cancel"


class GameCellEnum(StrEnum):
    CELL = "cell"
    CANCEL = "cancel"


class BetCallback(CallbackData, prefix="bet"):
    user_id: int
    bet: int
    action: BetButtonType
    game: Games


class GameCallback(CallbackData, prefix="game"):
    user_id: int
    bet: int
    cell: GameCellEnum


class DiceCallback(CallbackData, prefix="dice"):
    user_id: int
    bet: int
    parity: DiceParityEnum


class DartsCallback(CallbackData, prefix="darts"):
    user_id: int
    bet: int
    action: BaseGameEnum


class BowlingCallback(CallbackData, prefix="bowling"):
    user_id: int
    bet: int
    action: BaseGameEnum


class BasketballCallback(CallbackData, prefix="basketball"):
    user_id: int
    bet: int
    action: BaseGameEnum


class FootballCallback(CallbackData, prefix="football"):
    user_id: int
    bet: int
    action: BaseGameEnum


class CasinoCallback(CallbackData, prefix="casino"):
    user_id: int
    bet: int
    action: BaseGameEnum


class LeaveCallback(CallbackData, prefix="leave"):
    user_id: int
    confirm: bool
