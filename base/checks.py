import re

from discord.ext.commands import check, Context, UserConverter, MissingPermissions

from extra_exceptions import *
from player import Player
from env import BBGLOBALS

usrconv = UserConverter()


class Checks:

    @staticmethod
    def can_fish():
        async def predicate(ctx: Context):
            if not Player(ctx.author).has_in_inventory(1):
                raise NotAbleTo("You need to buy a fishing rod.")
            return True

        return check(predicate)

    @staticmethod
    def can_rob():
        async def predicate(ctx: Context):
            if not BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["robbing"]:
                raise NotAbleTo("Robbing is not enabled on this server.")
            if not Player(ctx.author).has_in_inventory(2):
                raise NotAbleTo("You need to buy a dagger to do crime.")
            return True

        return check(predicate)

    @staticmethod
    def has_valid_user(regex):
        async def predicate(ctx: Context):
            try:
                await usrconv.convert(ctx, re.search(regex, ctx.message.content).group(0))
            except:
                raise PlayerNotFound("Unknown user")
            return True

        return check(predicate)

    @staticmethod
    def can_collect_rent():
        async def predicate(ctx: Context):
            if not Player(ctx.author).has_in_inventory(6):
                raise NotAbleTo("You need to buy a house to collect rent")
            return True

        return check(predicate)

    @staticmethod
    def in_bb_channel():
        async def predicate(ctx: Context):
            if ctx.channel.id not in BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["channel_ids"]:
                raise NotInBbChannel("This command can't be used here")
            return True
        return check(predicate)

    @staticmethod
    def is_bb_dev():
        async def predicate(ctx: Context):
            for role in ctx.author.roles:
                if role.id == BBGLOBALS.BB_DEV_ROLE_ID:
                    return True
            raise MissingPermissions("You need to be a dev to use this command")
        return check(predicate)

    @staticmethod
    def is_barrel_cult():
        async def predicate(ctx: Context):
            return ctx.guild.id == BBGLOBALS.BARREL_CULT_GUILD_ID
        return check(predicate)
    
    @staticmethod
    def can_gamble():
        async def predicate(ctx: Context):
            if not BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["gambling"]:
                raise NotAbleTo("Gambling is not enabled on this server.")
            return True

        return check(predicate)