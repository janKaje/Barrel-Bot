from discord.ext.commands import CheckFailure

class NotAbleTo(CheckFailure):
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
