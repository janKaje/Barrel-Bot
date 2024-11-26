import json
import math
import os
import random as rand
import re
import asyncio

import discord
from discord.ext import commands
from numpy.random import default_rng

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def setup(bot):
    await bot.add_cog(fun(bot))


with open(dir_path + "/data/customratings.json") as file:
    customratings = json.load(file)

with open(dir_path + "/data/randomnumberscores.json") as file:
    randomnumberscores = json.load(file)


class fun(commands.Cog, name="Fun"):
    """Random fun things"""

    def __init__(self, bot):
        self.bot = bot
        print(f"cog: {self.qualified_name} loaded")

    @commands.command()
    @commands.is_owner()
    async def savefundata(self, ctx: commands.Context):
        savealldata()
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def fetch_numberscores(self, ctx: commands.Context):
        await ctx.send(json.dumps(randomnumberscores))

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        await ctx.send(f'Pong! {round(self.bot.latency * 1000)}ms')

    @commands.command()
    async def introduce(self, ctx: commands.Context, *, arg):
        """Ask me to introduce myself!
        Example:
        `Hey BarrelBot, introduce yourself!`"""
        if re.match("yourself", arg) is not None:
            async with ctx.typing():
                await asyncio.sleep(1)
                await ctx.send("Hi! I'm BarrelBot. Nice to meet you!")
            async with ctx.typing():
                await asyncio.sleep(1.2)
                await ctx.send("I can do lots of things for you. If you want to see everything you can ask me, "
                               "type \"Hey BarrelBot, help\".")
            async with ctx.typing():
                await asyncio.sleep(1.8)
                await ctx.send("I'll understand you if you say hey, hi, or hello before my name! And feel free to use "
                               "capital letters or not. It doesn't really matter to me :slight_smile:")
            async with ctx.typing():
                await asyncio.sleep(2.1)
                await ctx.send("I'm here to help the <:barrel:1296987889942397001> cult in their spiritual journey "
                               "towards the Almighty <:barrel:1296987889942397001>, " + \
                               "so I try to help out around here where I can.")
            async with ctx.typing():
                await asyncio.sleep(1.7)
                await ctx.send("One cool thing I do is watch <#1297028406504067142> and keep track of everyone's "
                               "scores.")
            async with ctx.typing():
                await asyncio.sleep(1.2)
                await ctx.send("That's all for now! May the <:barrel:1296987889942397001> be with you :smile:")
            return
        else:
            await ctx.send(f"I don't know enough about {arg} to introduce him/her/them/it properly. You'll have to "
                           f"ask someone who knows more, sorry!")

    @commands.command()
    async def rate(self, ctx: commands.Context, *, item):
        """I'll rate whatever you tell me to.
        Example:
        `Hi BarrelBot, rate my neighbor's chicken pot pie`"""

        # if in custom ratings, send that
        if item.lower() in customratings.keys():
            await ctx.send(f"I'd give {item} a {customratings[item.lower()]}/10")
            return

        # if is a mention, return 10 with a :3 face
        if re.match(r"<@\d+>", item) is not None:
            await ctx.send(f"I'd give {item} a 10/10 :3")
            return

        # otherwise, seed the rng with the item string and get a random number from 0-10
        r = rand.getstate()
        rand.seed(item)
        rate_value = rand.randint(0, 10)
        rand.setstate(r)
        await ctx.send(f"I'd give {item} a {rate_value}/10")

    @commands.command()
    async def eightball(self, ctx: commands.Context):
        """Roll me and I'll decide your fate."""
        responses = ["It is certain.",
                     "It is decidedly so.",
                     "Without a doubt.",
                     "Yes - definitely.",
                     "You may rely on it.",
                     "As I see it, yes.",
                     "Most likely.",
                     "Outlook good.",
                     "Yes.",
                     "Signs point to yes.",
                     "Reply hazy, try again.",
                     "Ask again later.",
                     "Better not tell you now.",
                     "Cannot predict now.",
                     "Concentrate and ask again.",
                     "Don't count on it.",
                     "My reply is no.",
                     "My sources say no.",
                     "Outlook not so good.",
                     "Very doubtful."]
        await ctx.send(rand.choice(responses))

    @commands.command()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def random(self, ctx: commands.Context):
        """Gives a random number. Keeps track of high scores."""

        # fetch their random number
        value = getRandInt()

        # send fancy embed and update high scores
        embed = discord.Embed(color=discord.Color.brand_green(), )
        authorid = str(ctx.author.id)
        if authorid not in randomnumberscores.keys():
            # where it's the user's first random number
            randomnumberscores[authorid] = value
            embed.title = "Congrats!";
            embed.description = f"You got your first random number: {value}"
            if value > randomnumberscores["overall"][0]:
                # in the very slim chance it's also a new overall high score
                olduser = await self.bot.fetch_user(randomnumberscores["overall"][1])
                embed.add_field(name="You also beat the high score!",
                                value=f"Old high score: {olduser.display_name} got {randomnumberscores['overall'][0]}",
                                inline=False)
                randomnumberscores["overall"] = [value, ctx.author.id]
            else:
                embed.add_field(name='New high score:', value=str(value), inline=False)
        elif value > randomnumberscores[authorid]:
            # if you beat your personal high score
            if value > randomnumberscores["overall"][0]:
                # if you also beat the overall high score
                embed.title = "Congrats!";
                embed.description = "You beat the high score!"
                olduser = await self.bot.fetch_user(randomnumberscores["overall"][1])
                embed.add_field(name="Old high score:",
                                value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}", inline=False)
                embed.add_field(name='New high score:', value=f'{ctx.author.display_name} got {value}', inline=False)
                randomnumberscores["overall"] = [value, ctx.author.id]
            else:
                # otherwise
                embed.title = "Congrats!";
                embed.description = "You beat your personal best!"
                embed.add_field(name="Old high score:", value=str(randomnumberscores[authorid]), inline=False)
                embed.add_field(name='New high score:', value=str(value), inline=False)
            randomnumberscores[authorid] = value
        else:
            # default case, nothing is updated
            embed.title = "You did not beat the high score."
            embed.description = str(value)
            embed.color = discord.Color.darker_gray()
            olduser = await self.bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="Current high score:",
                            value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}", inline=False)
            embed.add_field(name="Current personal best:", value=str(randomnumberscores[authorid]), inline=False)

        # send the embed
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called whenever a message is sent that the bot can see."""
        # don't interact with bots
        if message.author.bot:
            return

        # auto react
        m = re.search(r"<:\w*barrel\w*:\d+>", message.content)
        if m is not None:
            try:
                await message.add_reaction(m.group(0))
            except:
                pass

    @commands.Cog.listener()
    async def on_disconnect(self, ):
        """Called when the bot disconnects."""
        savealldata()

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        """Called when the shard disconnects."""
        savealldata()


def save_to_json(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)


def getRandInt() -> int:
    """Gets a random number from an exponential distribution"""
    return math.ceil(default_rng().exponential(40))


def savealldata():
    """Saves data to file."""
    save_to_json(randomnumberscores, dir_path + "/data/randomnumberscores.json")
    print("random scores saved")
