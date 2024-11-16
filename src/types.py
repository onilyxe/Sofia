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


class Actions(StrEnum):
    GIVE = "give"


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


class SettingsEnum(StrEnum):
    MINIGAMES = "minigames"
    GIVE = "give"


class ShopEnum(StrEnum):
    HOW_TO_BUY = "how_to_buy"
    WHAT_IS_PRICE = "what_is_price"
    WHERE_MONEY_GO = "where_money_go"


class GiveEnum(StrEnum):
    YES = "yes"
    NO = "no"


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


class SettingsCallback(CallbackData, prefix="settings"):
    setting: SettingsEnum


class ShopCallback(CallbackData, prefix="shop"):
    menu: ShopEnum


class HelpCallback(CallbackData, prefix="help"):
    game: Games


class GiveCallback(CallbackData, prefix="give"):
    user_id: int
    receiver_id: int
    value: int
    receiver_balance: int
    action: GiveEnum
