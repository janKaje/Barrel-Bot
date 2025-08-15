import os
import sys

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(dir_path, "base"))

from extra_exceptions import *
from player import Player, research


async def setup(bot):
    await bot.add_cog(Research(bot))


class Research(commands.Cog, name="Research"):
    """Research module"""

    def __init__(self, bot: commands.Bot):
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
    async def forceendqueue(self, ctx: commands.Context, usr: discord.User = None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        player.force_end_queue()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getresearch(self, ctx: commands.Context, usr: discord.User = None):
        if usr is None:
            player = Player(ctx.author)
        else:
            player = Player(usr)
        await self.bot_send(ctx, str(player.get_research_data()))

    @commands.command()
    @commands.is_owner()
    async def startresearch(self, ctx: commands.Context, techid: str):
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
