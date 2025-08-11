import json
import math
import os
import random as rand
import re
import asyncio
from copy import deepcopy
import sys
import time

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(dir_path, "base"))

from checks import checks
from extra_exceptions import *
from item import Item
from player import Player, research


async def setup(bot):
    await bot.add_cog(research(bot))


# Get is_in_dev_mode data to know whether it's in dev or on the server
# .env is loaded from barrelbot.py
IS_IN_DEV_MODE = os.environ["IS_IN_DEV_MODE"]
if isinstance(IS_IN_DEV_MODE, str):
    IS_IN_DEV_MODE = os.environ["IS_IN_DEV_MODE"].lower() == "true"

## Consts
DATA_CHANNEL_ID = 735631640939986964

BARREL_COIN = "<:barrelcoin:1364027068936884405>"
BARREL_EMOJI = "<:barrel:1296987889942397001>"
HOLY_BARREL_EMOJI = "<:holybarrel:1303080132642209826>"


## Debug
if IS_IN_DEV_MODE :
    DATA_CHANNEL_ID = 735631714558148701 # data-log

    # Same emoji because we only have one on the test server
    BARREL_COIN = "<:TESTbarrel:1303842935715921941>"
    BARREL_EMOJI = "<:TESTbarrel:1303842935715921941>"
    HOLY_BARREL_EMOJI = "<:TESTbarrel:1303842935715921941>"
##

class research(commands.Cog, name="Research"):
    """Research module"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    def cog_load(self):

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

        # start loop
        self.update_all_research_queues.start()

    @tasks.loop(minutes=10)
    async def update_all_research_queues(self):
        Player.update_all_research_queues()

    @commands.command()
    @commands.is_owner()
    async def forceendqueue(self, ctx:commands.Context, usr:discord.User=None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        player.force_end_queue()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getresearch(self, ctx:commands.Context, usr:discord.User=None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        await self.bot_send(ctx, str(player.get_research_data()))

    @commands.command()
    @commands.is_owner()
    async def startresearch(self, ctx:commands.Context, techid:str):
        player = Player(ctx.author)
        try:
            player.begin_research(techid)
            await self.bot_send(ctx, "Done!")
        except KeyError:
            await self.bot_send(ctx, "Not a valid techid")
        except ResearchQueueFull:
            await self.bot_send(ctx, "Research queue full")
        except MissingPrerequisites:
            await self.bot_send(ctx, "Missing prerequisites")
        except NotEnoughCoins:
            await self.bot_send(ctx, "Not enough coins")
        except Exception as e:
            await self.bot_send(ctx, str(e.with_traceback(None)))