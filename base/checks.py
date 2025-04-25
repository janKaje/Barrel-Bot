import re

import discord
from discord.ext.commands import check, Context, UserConverter

from base.extra_exceptions import *
from player import Player

usrconv = UserConverter()

class checks:

    def can_fish():
        async def predicate(ctx:Context):
            if not Player(ctx.author).has_in_inventory(1):
                raise NotAbleToFish
            return True
        return check(predicate)
    
    def can_rob():
        async def predicate(ctx:Context):
            if not Player(ctx.author).has_in_inventory(2):
                raise NotAbleToRob("You need to buy a dagger to rob people")
            try:
                await usrconv.convert(ctx, re.search(r"(?<=rob ).*", ctx.message.content).group(0))
            except:
                raise NotAbleToRob("Unknown user to rob")
            return True
        return check(predicate)
    