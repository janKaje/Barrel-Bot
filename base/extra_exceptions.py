from discord.ext.commands import CheckFailure
from discord.app_commands.errors import AppCommandError


class NotAbleTo(CheckFailure):
    pass


class NotInBbChannel(CheckFailure):
    pass


class NotInBbChannelIntc(AppCommandError):
    pass


class NotEnoughCoins(Exception):
    pass


class TooManyTrades(Exception):
    pass


class NotInInventory(Exception):
    pass


class NotInDisplayCase(Exception):
    pass


class TradeNotFound(Exception):
    pass


class ItemNotFound(Exception):
    pass


class PlayerNotFound(CheckFailure):
    pass


class ResearchQueueFull(Exception):
    pass


class MissingPrerequisites(Exception):
    pass
