from src.handlers.game import *
from src.handlers.dice import *
from src.handlers.darts import *
from src.handlers.casino import *
from src.handlers.bowling import *
from src.handlers.football import *
from src.handlers.basketball import *
from src.handlers.games import games_router
from src.handlers.commands import commands_router
from src.handlers.admin_commands import admin_commands_router

__all__ = ["games_router", "commands_router", "admin_commands_router"]
