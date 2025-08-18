import re

from discord.ext.commands import check, Context, UserConverter, MissingPermissions

from barrelbot import bb_channel_ids
from extra_exceptions import *
from player import Player
from env import BBGLOBALS

usrconv = UserConverter()


class Checks:

    @staticmethod
    def can_fish():
        async def predicate(ctx: Context):
            if not Player(ctx.author).has_in_inventory(1):
                raise NotAbleTo("You need to buy a fishing rod")
            return True

        return check(predicate)

    @staticmethod
    def can_rob():
        async def predicate(ctx: Context):
            if not Player(ctx.author).has_in_inventory(2):
                raise NotAbleTo("You need to buy a dagger to do crime")
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
            if ctx.channel.id not in bb_channel_ids:
                raise NotInBbChannel()
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
