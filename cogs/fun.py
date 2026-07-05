import copy
from io import BytesIO
import json
import math
import os
import random as rand
import re
import asyncio
import sys
from typing import Optional
from datetime import time, timezone as tz
from PIL import Image, ImageDraw

import discord
from discord import app_commands
from discord.ext import commands, tasks
from numpy.random import default_rng

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(dir_path, "base"))

from checks import Checks
from env import BBGLOBALS
from extra_exceptions import NotInBbChannelIntc
from guild_config import GUILD_CONFIG as GC
from misc import today_utc, obfuscate

MAX_BARRELDLE_GUESSES = 6

BARRELDLE_RESET = time(hour=0, tzinfo=tz.utc)


async def setup(bot):
    await bot.add_cog(Fun(bot))

async def temp_bot_send(ctx: commands.Context, content: str = None, embed: discord.Embed = None, file: discord.File = None):
    pass


with open(os.path.join(dir_path, "config", "customratings.json")) as file:
    customratings = json.load(file)

with open(os.path.join(dir_path, "data", "randomnumberscores.json")) as file:
    randomnumberscores = json.load(file)

with open(os.path.join(dir_path, "config", "introductions.json")) as file:
    introductions = json.load(file)

with open(os.path.join(dir_path, "config", "possible_barreldle_words.json")) as file:
    possible_barreldle_words = json.load(file)

with open(os.path.join(dir_path, "config", "allowed_barreldle_words.json")) as file:
    allowed_barreldle_words = json.load(file)



async def savealldata():
    """Saves data to file."""
    save_to_json(randomnumberscores, os.path.join(dir_path, "data", "randomnumberscores.json"))
    save_to_json(Fun.barreldle_scores, os.path.join(dir_path, "data", "barreldle_scores.json"))

    print("Fun scores saved")


class Fun(commands.Cog, name="Fun"):
    """Random Fun things"""
    
    with open(os.path.join(dir_path, "data", "barreldle_scores.json")) as file:
        barreldle_scores = json.load(file)
    for key in list(barreldle_scores.keys()):
        barreldle_scores[int(key)] = barreldle_scores[key]
        del barreldle_scores[key]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_send = temp_bot_send

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    @commands.command()
    @commands.is_owner()
    async def savefundata(self, ctx: commands.Context):
        await savealldata()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getfundata(self, ctx: commands.Context):
        await self.bot_send(ctx, json.dumps(randomnumberscores))

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        to_send = f'Pong! Latency: {round(self.bot.latency * 1000)}ms'
        isowner = await self.bot.is_owner(ctx.author)
        if isowner and os.environ["MACHINE"] == "homelaptop":
            to_send += "\nI'm running in development mode. How's the coding?"
        await self.bot_send(ctx, to_send)

    @commands.command()
    async def introduce(self, ctx: commands.Context, *, arg:str):
        """Ask me to introduce myself!
        Example:
        `Hey BarrelBot, introduce yourself!`"""
        if arg.lower().startswith("yourself"):
            if ctx.guild.id == BBGLOBALS.BARREL_CULT_GUILD_ID:
                messages = introductions['cult']
            else:
                messages = introductions['default']
            for type_sec, msg in messages:
                async with ctx.typing():
                    await asyncio.sleep(type_sec)
                    await self.bot_send(ctx, msg)
        else:
            await self.bot_send(ctx,
                                f"I don't know enough about {arg} to introduce him/her/them/it properly. You'll have "
                                f"to ask someone who knows more, sorry!")

    @commands.command()
    async def rate(self, ctx: commands.Context, *, item):
        """I'll rate whatever you tell me to.
        Example:
        `Hi BarrelBot, rate my neighbor's chicken pot pie`"""

        # if in custom ratings, send that
        if item.lower() in customratings.keys():
            await self.bot_send(ctx, f"I'd give {item} a {customratings[item.lower()]}/10")
            return

        # if is a mention, return 10 with a :3 face
        if re.match(r"<@\d+>", item) is not None:
            await self.bot_send(ctx, f"I'd give {item} a 10/10 :3")
            return

        # otherwise, seed the rng with the item string and get a random number from 0-10
        r = rand.getstate()
        rand.seed(item)
        rate_value = rand.randint(0, 10)
        rand.setstate(r)
        await self.bot_send(ctx, f"I'd give {item} a {rate_value}/10")

    @commands.command(aliases=["8ball"])
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
        await self.bot_send(ctx, rand.choice(responses))

    @commands.command()
    @Checks.in_bb_channel()
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def random(self, ctx: commands.Context):
        """Gives a random number. Keeps track of high scores."""

        # fetch their random number
        value = get_randint()

        # send fancy embed and update high scores
        embed = discord.Embed(color=discord.Color.brand_green(), )
        authorid = str(ctx.author.id)
        if authorid not in randomnumberscores.keys():
            # where it's the user's first random number
            randomnumberscores[authorid] = value
            embed.title = "Congrats!"
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
                embed.title = "Congrats!"
                embed.description = "You beat the high score!"
                olduser = await self.bot.fetch_user(randomnumberscores["overall"][1])
                embed.add_field(name="Old high score:",
                                value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}", inline=False)
                embed.add_field(name='New high score:', value=f'{ctx.author.display_name} got {value}', inline=False)
                randomnumberscores["overall"] = [value, ctx.author.id]
            else:
                # otherwise
                embed.title = "Congrats!"
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
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    async def cheese(self, ctx: commands.Context):
        await self.bot_send(ctx, "🧀")
    
    @app_commands.command(
        name=obfuscate(b'\x144J\x1c\x06\x0c\x03\x01P').decode(),
        description=obfuscate(b'30O\x1dH\x00\x08\x11QS?7\x08\x0b\x017\n=@\x11<2g\x01*M\x1fKs\t7:\x0b!\x10\x1fEW\x11\x0bhC\x1d]\x04\x1bQ!QU^%\x13@*xZW\n\xd3\xc5\xc9\xcb').decode()
    )
    @app_commands.guilds(1397052812269195395)
    async def _abyss_only(self, intc: discord.Interaction):
        msg = rand.choice([
            b'+8O\x1dH\x0e\x0f\x05WS4=\x11J\x06;\x00l\x13\x89\xca\xda\xce', 
            b"$>I\x1dH\x16\x11\x01QS,<\x00J\x0c1\x10sD\x16;e3V-\\\x12\x0f\x11\x1c*h\x1d!7\x15AW\x04\x08'Y\x10\x18P\x1aZ0B\x1dFnK\x0b", 
            b"/4]VFWG\x1dL\x06m'\x14U", 
            b'.qI\x11\x1b\nG\x1dL\x06c|J', 
            b'.vR\x1dH\x1b\x02\x01MS,r\x06\x0b\x14?\x042WY2+5\x1acM\x18\x0fP\x11e\xb8\xf1\xd5\xda', 
            b'\x97\xce\xb5\xf1\x98\xe6\xf6\xe8\xd3\xec\xc0\xd4\x86\xe5\xc5aZl', 
            b'$0JX!Y\x14\x01FS4=\x11J\x011\x0b:T\x11!}'
        ])
        imgpaths = os.path.join(dir_path, "assets", "abyss")
        imgpath = os.path.join(imgpaths, rand.choice(os.listdir(imgpaths)))
        file = discord.File(imgpath, filename="a.png")
        emb = discord.Embed(type="image")
        emb.set_image(url="attachment://a.png")
        await intc.response.send_message(obfuscate(msg).decode(), embed=emb, file=file)

    @app_commands.command()
    @Checks.in_bb_channel_intc()
    @app_commands.describe(guess="Your guess for the word of the day")
    async def barreldle(self, intc: discord.Interaction, guess: Optional[str] = None):
        """Wordle, but 90% of the time the word is "barrel". 
        This is a slash command, so can't be invoked with the usual command prefix."""
        word = get_barreldle_word()
        prev = Fun.barreldle_scores.get(intc.user.id, 
                    {"completed": False, "guesses": [], "shown_msg_id": None, "channel_id": intc.channel_id, "shown_msg_n": None})
        
        if prev["completed"] is True or guess is None:
            # display solution so far
            img = get_barreldle_img(prev["guesses"], True)

            image = discord.File(img, filename="barreldle.png")
            emb = discord.Embed(color=discord.Colour.dark_embed(), title=f"Barreldle for {today_utc()}")
            if prev["completed"] == True:
                emb.description = f"You solved today's barreldle in {len(prev['guesses'])} tries!"
            emb.set_image(url="attachment://barreldle.png")

            await intc.response.send_message(embed=emb, file=image, ephemeral=True)
            return

        # guess logic
        guess = guess.upper()
        if len(prev["guesses"]) >= MAX_BARRELDLE_GUESSES:
            await intc.response.send_message("You don't have any more guesses available. Try again tomorrow", ephemeral=True)
            return
        
        if len(guess) != 6:
            await intc.response.send_message("All guesses have to be 6 letters long.", ephemeral=True)
            return
        
        if guess not in allowed_barreldle_words:
            await intc.response.send_message("That word isn't in the word list.", ephemeral=True)
            return
        
        prev["guesses"].append(guess)
        if guess == word:
            prev["completed"] = True

        img = get_barreldle_img(prev["guesses"], True)

        Fun.barreldle_scores[intc.user.id] = prev

        image = discord.File(img, filename="barreldle.png")
        emb = discord.Embed(color=discord.Colour.dark_embed(), title=f"Barreldle for {today_utc()}")
        if prev["completed"] == True:
            emb.description = f"You solved today's barreldle in {len(prev['guesses'])} tries!"
        emb.set_image(url="attachment://barreldle.png")

        await intc.response.send_message(embed=emb, file=image, ephemeral=True)

    @commands.command()
    async def barreldle_word(self, ctx: commands.Context):
        await self.bot_send(ctx, get_barreldle_word())

    @barreldle.error
    async def on_barreldle_error(self, intc: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, NotInBbChannelIntc):
            bb_channels = [self.bot.get_channel(i) for i in GC.get_bb_channels(intc.guild)]
            return await intc.response.send_message(f"This command can only be done in {' or '.join([i.mention for i in bb_channels])}.", ephemeral=True)
        else:
            print(error.with_traceback(None))
            return await intc.response.send_message(f"An unknown error occurred:\n{type(error)}\n{error.with_traceback(None)}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called whenever a message is sent that the bot can see."""
        # don't interact with bots
        if message.author.bot:
            return
        
        # auto ken 🏳️‍⚧️ react
        if message.author.id == BBGLOBALS.KEN_USER_ID:
            try:
                await message.add_reaction("🏳️‍⚧️")
            except:
                pass

        # auto react
        m = re.search(r"<:\w*barrel\w*:\d+>", message.content)
        if m is not None:
            try:
                await message.add_reaction(m.group(0))
            except:
                pass

    async def cog_load(self):

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

        # start hourly loop
        self.hourlyloop.start()
        self.daily_barreldle_reset.start()
        self.intermittent_show_barreldles.start()

    @tasks.loop(hours=9)
    async def hourlyloop(self):
        await savealldata()

    @tasks.loop(time=BARRELDLE_RESET)
    async def daily_barreldle_reset(self):
        # collect and sort by channel
        all_channels = set(i["channel_id"] for i in Fun.barreldle_scores.values())

        for ch in all_channels:
            # gather images, send as embed
            as_list = [
                v | {"user_id":k} for k, v in Fun.barreldle_scores.items() if v["channel_id"] == ch
            ]

            channel = self.bot.get_channel(ch)

            # get image
            img = await self.get_barreldle_daily_img(as_list, channel, prev=True)

            # add image to embed
            image = discord.File(img, filename="barreldle.png")
            emb = discord.Embed(color=discord.Colour.dark_embed(), title=f"Barreldle for {today_utc()}")
            emb.set_image(url="attachment://barreldle.png")

            # sort, get members, individual scores
            as_list.sort(key=lambda x: len(x["guesses"]))
            members = [channel.guild.get_member(score["user_id"]) for score in as_list]

            ind_scores = list(set([len(score['guesses']) for score in as_list if score["completed"] == True]))
            ind_scores.sort()
            any_incomplete = any(score["completed"] == False for score in as_list)

            # add description with results
            emb.description = f"Here are yesterday's results:"
            for score in ind_scores:
                emb.description += f"\n{score}/{MAX_BARRELDLE_GUESSES}: " 
                for i in range(len(as_list)):
                    if len(as_list[i]["guesses"]) == score and as_list[i]["completed"] == True:
                        emb.description += members[i].mention + " "

            if any_incomplete:
                emb.description += f"\nX/{MAX_BARRELDLE_GUESSES}: "
                for i in range(len(as_list)):
                    if as_list[i]["completed"] == False:
                        emb.description += members[i].mention + " " 

            await self.bot_send(channel, embed=emb, file=image)

        Fun.barreldle_scores = dict()

    @tasks.loop(minutes=2)
    async def intermittent_show_barreldles(self):
        # every 10 minutes, show how barreldle is going
        for user_id, score in Fun.barreldle_scores.items():
            channel = self.bot.get_channel(score["channel_id"])
            member = channel.guild.get_member(user_id)
            if score["shown_msg_id"] is None:
                # send image
                as_list = [copy.copy(score) | {"user_id": user_id}]
                img = await self.get_barreldle_daily_img(as_list, channel)
                image = discord.File(img, filename="barreldle.png")
                emb = discord.Embed(color=discord.Colour.dark_embed(), title=f"{member.display_name} was playing Barreldle")
                emb.set_image(url="attachment://barreldle.png")
                msg = await channel.send(embed=emb, file=image)

                Fun.barreldle_scores[user_id]["shown_msg_id"] = msg.id
                Fun.barreldle_scores[user_id]["shown_msg_n"] = len(score["guesses"])

            
            elif score["shown_msg_n"] != len(score["guesses"]):
                # edit image
                message = await channel.fetch_message(score["shown_msg_id"])
                as_list = [copy.copy(score) | {"user_id": user_id}]
                img = await self.get_barreldle_daily_img(as_list, channel)
                image = discord.File(img, filename="barreldle.png")
                emb = discord.Embed(color=discord.Colour.dark_embed(), title=f"{member.display_name} was playing Barreldle")
                emb.set_image(url="attachment://barreldle.png")
                await message.edit(embed=emb, attachments=[image])

                Fun.barreldle_scores[user_id]["shown_msg_n"] = len(score["guesses"])

    @commands.command()
    @commands.is_owner()
    async def test_intermittent(self, ctx: commands.Context):
        await self.intermittent_show_barreldles()

    @commands.command()
    @commands.is_owner()
    async def test_daily(self, ctx: commands.Context):
        await self.daily_barreldle_reset()

    async def get_barreldle_daily_img(self, scores:list[dict], channel:discord.abc.GuildChannel, prev:bool=False) -> BytesIO:

        cols = min(4, len(scores))
        rows = math.ceil(len(scores)/4)

        # gather members
        members = [channel.guild.get_member(score["user_id"]) for score in scores]

        # remove possible errors
        for i in reversed(range(len(members))):
            if members[i] is None:
                members.pop(i)
                scores.pop(i)

        # collect avatar images
        avatar_images = [BytesIO() for _ in members]
        for i in range(len(members)):
            await members[i].avatar.save(avatar_images[i])
            avatar_images[i].seek(0)

        avatar_images = [Image.open(i) for i in avatar_images]

        # collect barreldle images
        ind_images = [get_barreldle_img(score["guesses"], False, True, prev) for score in scores]
        isize = ind_images[0].size
        asize = int(isize[0] * 0.6)
        sizediff = isize[0]-asize

        for i in range(len(avatar_images)):
            if avatar_images[i].mode != "RGB":
                avatar_images[i] = avatar_images[i].convert("RGB")
            avatar_images[i] = avatar_images[i].resize((asize, asize))

        # collect into single list
        guesses_scores = [len(score["guesses"]) for score in scores]
        as_one_list = list(zip(guesses_scores, avatar_images, ind_images))
        as_one_list.sort(key=lambda x: x[0])

        # create background image
        margin = 20
        padding = 20

        colsize = max(asize, isize[0]) + padding
        rowsize = asize + isize[1] + padding

        imgsize = (
            colsize * cols + margin*2,
            rowsize * rows + margin*2
        )

        black = (0,0,0)

        bgimg = Image.new(
            "RGB",
            imgsize,
            black
        )

        # paste avatars and barreldle images onto background
        for i in range(len(as_one_list)):
            _, av_img, bd_img = as_one_list[i]
            col = i % 4
            row = i // 4
            bgimg.paste(av_img, [margin + col*colsize + sizediff//2, margin + row*rowsize])
            bgimg.paste(bd_img, [margin + col*colsize, margin + row*rowsize + asize])

        image_stream = BytesIO()
        bgimg.save(image_stream, format="PNG")
        image_stream.seek(0)

        return image_stream


def save_to_json(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)


def get_randint() -> int:
    """Gets a random number from an exponential distribution"""
    return math.ceil(default_rng().exponential(40))


def get_barreldle_word(prev:bool=False) -> str:
    """Picks the random word for today's barreldle"""
    today = today_utc()
    r = rand.getstate()
    if prev:
        rand.seed(today.toordinal()-1)
    else:
        rand.seed(today.toordinal())
    if rand.random() < 0.90:
        ret = "BARREL"
    else:
        ret = rand.choice(possible_barreldle_words)
    rand.setstate(r)
    return ret

def get_barreldle_img(guesses:list[str], show_letters:bool, as_python:bool=False, prev:bool=False) -> BytesIO|Image.Image:
    """Generates the barreldle image"""
    soln = get_barreldle_word(prev)

    sqsize = 50
    borderwidth = 2
    padding = 3
    margin = 10
    font_size = 32

    squares = (6,MAX_BARRELDLE_GUESSES)

    black = (0,0,0)
    gray = (120,124,127)
    yellow = (200,182,83)
    green = (108,169,101)
    white = (255,255,255)

    imgsize = (
        sqsize*squares[0] + padding*(squares[0]-1) + margin*2,
        sqsize*squares[1] + padding*(squares[1]-1) + margin*2
    )

    if len(guesses) > squares[1]:
        raise ValueError("too many guesses")

    img = Image.new("RGB", imgsize, black)

    draw = ImageDraw.Draw(img)

    for y in range(squares[1]):
        offset_y = margin + sqsize*y + padding*y

        if y < len(guesses):
            word = guesses[y]

            soln_copy = copy.copy(soln)
            colors = [gray]*6

            # find green letters first
            for i, letter in enumerate(word):
                if soln_copy[i] == letter:
                    soln_copy = soln_copy[:i] + "_" + soln_copy[i+1:]
                    colors[i] = green

            # then find yellow letters
            for i, letter in enumerate(word):
                if letter in soln_copy and colors[i] == gray:
                    soln_copy = soln_copy.replace(letter, "_", 1)
                    colors[i] = yellow

        else:
            colors = [black]*6
        
        for x in range(squares[0]):
            offset_x = margin + sqsize*x + padding*x
            draw.rectangle(
                [offset_x, offset_y, offset_x+sqsize, offset_y+sqsize],
                fill=colors[x],
                outline=gray,
                width=borderwidth
            )
            if show_letters and y < len(guesses):
                draw.text(
                    [offset_x+sqsize//2, offset_y+sqsize//2],
                    word[x].upper(),
                    fill=white,
                    anchor="mm",
                    font_size=font_size
                )

    if as_python:
        return img

    image_stream = BytesIO()
    img.save(image_stream, format="PNG")
    image_stream.seek(0)

    if __name__ == "__main__":
        img.show()

    return image_stream

def main():
    for _ in range(100):
        print(rand.choice(possible_barreldle_words))

if __name__ == "__main__":
    main()
