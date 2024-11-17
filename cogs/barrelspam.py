import json
import math
import os
import re
import time

import discord
from discord.ext import commands

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
next_barrelspam = None
timer = time.time()


async def setup(bot):
    await bot.add_cog(barrelspam(bot))


# Define constants
SPAM_THRESHOLD = 10

DECIMALROLEID = 1303766261574008943
BINARYROLEID = 1303766864391831644

BARRELCULTSPAMCHANNELID = 1297028406504067142

# Test IDs for the bot testing server
TESTROLEID = 735637859872276501
TESTCHANNELID = 733508209288937544

# Open data files
with open(dir_path + "/data/barrelspamdata.json") as file:
    barrelspamdata = json.load(file)

with open(dir_path + "/data/barrelspamteamdata.json") as file:
    barrelspamteamdata = json.load(file)

with open(dir_path + "/data/barrelspamtempdata.json") as file:
    barrelspamtempdata = json.load(file)


class barrelspam(commands.Cog, name="Barrel Spam"):
    """Functionality for barrel spam game"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        print(f"cog: {self.qualified_name} loaded")

    @commands.command()
    async def join(self, ctx: commands.Context, *, teamname):
        """Join a team to spam some barrels! You can join Team Decimal or Team Binary.
        Example:
        `Hey BarrelBot, join Team Decimal`"""
        # if they ask to join team decimal
        if re.match("(team )?decimal", teamname, flags=re.I):
            # iterate through roles to clean up
            for role in ctx.author.roles:
                if role.id == DECIMALROLEID:
                    await ctx.send("You're already in Team Decimal!")
                    return
                if role.id == BINARYROLEID:
                    # if they're in team binary, remove them from the team
                    await ctx.author.remove_roles(ctx.guild.get_role(BINARYROLEID))
            # finally, add role and confirm
            await ctx.author.add_roles(ctx.guild.get_role(DECIMALROLEID))
            await ctx.send("Added to Team Decimal!")

        # if they ask to join team binary
        elif re.match("(team )?binary", teamname, flags=re.I):
            # iterate through roles to clean up
            for role in ctx.author.roles:
                if role.id == BINARYROLEID:
                    await ctx.send("You're already in Team Binary!")
                    return
                if role.id == DECIMALROLEID:
                    # if they're in team decimal, remove them from the team
                    await ctx.author.remove_roles(ctx.guild.get_role(DECIMALROLEID))
            # finally, add role and confirm
            await ctx.author.add_roles(ctx.guild.get_role(BINARYROLEID))
            await ctx.send("Added to Team Binary!")
        else:
            # invalid entry
            await ctx.send(
                "Didn't quite get that. You can ask to join Team Decimal or Team Binary with \"barrelbot, join team "
                "decimal\" or \"barrelbot, join team binary\"")

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        """Shows the team scores and individual leaderboard of barrel spam scores."""
        # start embed
        embed = discord.Embed(color=discord.Color.dark_blue(), title="Barrel Spam Leaderboard", description="")
        embed.add_field(name="Team Scores",
                        value=f"**Decimal: {barrelspamteamdata['decimal']}**\n**Binary: {barrelspamteamdata['binary']}**",
                        inline=False)

        # collect and sort all scores
        ind_data_as_array = [[i, j] for i, j in barrelspamdata.items()]
        ind_data_as_array.sort(key=lambda x: x[1], reverse=True)
        valstr = ""
        for i, _list in enumerate(ind_data_as_array):
            valstr += "**" + str(i + 1) + ") "
            member = ctx.guild.get_member(int(_list[0]))
            valstr += member.display_name + "**"
            team = self.get_user_team(_list[0], ctx.guild)
            if team == "decimal":
                valstr += " *(Decimal Enthusiast)*"
            elif team == "binary":
                valstr += " *(Binary Enjoyer)*"
            valstr += ": **" + str(_list[1]) + "**\n"
        embed.add_field(name="Individual Scores", value=valstr, inline=False)

        # send
        await ctx.send(embed=embed)

    @commands.command()
    async def rank(self, ctx: commands.Context):
        """Shows your individual barrel spam score and rank."""
        # start embed
        embed = discord.Embed(color=discord.Color.dark_blue(), title="Barrel Spam Rank", description="")
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

        # get scores and sort
        ind_data_as_array = [[i, j] for i, j in barrelspamdata.items()]
        ind_data_as_array.sort(key=lambda x: x[1], reverse=True)
        for i, _list in enumerate(ind_data_as_array):
            if _list[0] == str(ctx.author.id):
                embed.add_field(name=f"Rank: {i + 1} out of {len(ind_data_as_array)}", value=f"**Score: {_list[1]}**")
                break

        # send
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def savespamdata(self, ctx: commands.Context):
        savealldata()
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def fetch_spamdata(self, ctx: commands.Context):
        await ctx.send(json.dumps(barrelspamdata))
        await ctx.send(json.dumps(barrelspamteamdata))
        await ctx.send(json.dumps(barrelspamtempdata))
        await ctx.send(next_barrelspam)

    async def cog_load(self):
        """Called when the bot starts and is ready."""

        # first get channel
        global next_barrelspam
        spamchannel = self.bot.get_channel(BARRELCULTSPAMCHANNELID)

        # get last message and if spam
        async for past_spam in spamchannel.history(limit=1):
            check, last_spamint = self.checkValidBarrelSpam(past_spam, ignore_number=True)
            break

        if check == False:
            # if the previous message isn't spam, the numbers reset to 0
            next_barrelspam = 0
        else:
            # iterate through message history, increasing next spam number until the previous 0 is found
            next_barrelspam = 0
            async for past_spam in spamchannel.history(limit=last_spamint + 20):
                check2, past_spamint = self.checkValidBarrelSpam(past_spam, ignore_number=True)
                next_barrelspam += 1
                if check2 and past_spamint == 0:
                    break

        # if the current number is wrong, next spam number resets to 0
        if last_spamint != next_barrelspam - 1:
            await spamchannel.send(
                f"I took a nap and when I came back, the spam number was off! You guys were supposed to be at {next_barrelspam - 1}... " + \
                "Guess you get to restart at 0!")
            next_barrelspam = 0

        # print next spam number
        print(f"Next spam number: {next_barrelspam}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called whenever a message is sent that the bot can see."""
        # don't interact with bots
        if message.author.bot:
            return

        # barrel spam score logging
        if message.channel.id == BARRELCULTSPAMCHANNELID or message.channel.id == TESTCHANNELID:
            team = self.get_user_team(str(message.author.id), message.guild)
            if team == "not in team":
                responsemsg = await message.channel.send(
                    f"{message.author.mention}, you must join a team before spamming!")
                await message.delete(delay=5)
                await responsemsg.delete(delay=5)
                return
            isspam, spamint = self.checkValidBarrelSpam(message)
            if isspam:
                await self.continueSequence(message, spamint)
            elif next_barrelspam is None:
                await self.endShortRunSequence(message)
            elif next_barrelspam > SPAM_THRESHOLD:
                await self.endLongRunSequence(message)
            else:
                await self.endShortRunSequence(message)

        # save 
        global timer
        if time.time() - timer > 43200:
            savealldata()
            timer = time.time()

    @commands.Cog.listener()
    async def on_message_edit(self, msgbefore: discord.Message, msgafter: discord.Message):
        """Called when a message is edited."""
        if msgbefore.channel.id == BARRELCULTSPAMCHANNELID or msgbefore.channel.id == TESTCHANNELID:
            if next_barrelspam > SPAM_THRESHOLD:
                await self.endLongRunSequence(msgbefore)
            else:
                await self.endShortRunSequence(msgbefore)

    def checkValidBarrelSpam(self, msg: discord.Message, ignore_number: bool = False):
        """Checks if the given message is a valid spam message. By default, it takes into account the expected next spam number.
        However, if ignore_number is set to True, it only checks if the format is valid and returns the decimal interpretation
        of the spam number."""
        m = re.match("(\d+) ?(<:\w*barrel\w*:\d+>)", msg.content, flags=re.I)
        if m == None:
            return False, 0
        global next_barrelspam
        if ignore_number:
            return True, int(m.group(1))
        if (int(m.group(1)) == next_barrelspam) or (next_barrelspam == None):
            return True, int(m.group(1))
        try:
            if int(m.group(1), base=2) == next_barrelspam:
                return True, int(m.group(1), base=2)
        except:
            pass
        return False, int(m.group(1))

    def get_user_team(self, userid: str, guild: discord.Guild) -> str:
        """Gets the team that the user is on. Requires the user id in string format and the guild they're in."""
        member = guild.get_member(int(userid))
        for role in member.roles:
            if role.id == DECIMALROLEID:
                return "decimal"
            if role.id == BINARYROLEID:
                return "binary"
            if role.id == TESTROLEID:
                return "decimal"
        return "not in team"

    async def continueSequence(self, message: discord.Message, spamint: int) -> None:
        """To be called when the spam sequence continues. Requires the spam message and the spam number."""
        # update next spam
        global next_barrelspam
        global barrelspamdata
        global barrelspamtempdata
        global barrelspamteamdata
        if next_barrelspam == None:
            next_barrelspam = spamint
        next_barrelspam += 1

        # add user to data if not in
        authorid = str(message.author.id)
        if authorid not in barrelspamdata.keys():
            barrelspamdata[authorid] = 0
        if authorid not in barrelspamteamdata.keys():
            barrelspamtempdata[authorid] = 0

        # increase score
        score = 0
        if isPrime(spamint):
            if isMersenne(spamint):
                score += getMersenneScore(spamint)
            else:
                score += getPrimeScore(spamint)
        if isFibonacci(spamint):
            score += getFibScore(spamint)
        if isBinPali(spamint):
            score += getPaliScore(spamint)
        if isDecPali(spamint):
            score += getPaliScore(spamint)
        if score == 0:
            score += 1

        barrelspamdata[authorid] += score
        barrelspamtempdata[authorid] += score

        # to add in future: react to spam msg with emojis that indicate score or special numbers

    async def endLongRunSequence(self, message: discord.Message) -> None:
        """To be called when a long run is complete."""
        # update next spam
        global next_barrelspam
        global barrelspamdata
        global barrelspamtempdata
        global barrelspamteamdata
        finalint = max(0, next_barrelspam - 1)
        next_barrelspam = 0
        penalty = math.floor(finalint / 4)

        # Send end run msg
        init_msg = await message.channel.send(f"Run over! Fetching data...")

        async with message.channel.typing():

            # get team scores, mvp data
            thisrunteamdata = {"decimal": 0, "binary": 0}
            mvp = [0, 0]
            for usrid in barrelspamtempdata.keys():
                team = self.get_user_team(usrid, message.guild)
                if team != "not in team":
                    score = barrelspamtempdata[usrid]
                    thisrunteamdata[team] += score
                    if score > mvp[1]:
                        mvp = [usrid, score]
                else:
                    pass  # womp womp

            # check winning team, add score
            if thisrunteamdata["decimal"] > thisrunteamdata["binary"]:
                winningteam = "decimal"
                barrelspamteamdata["decimal"] += thisrunteamdata["decimal"]
            elif thisrunteamdata["decimal"] < thisrunteamdata["binary"]:
                winningteam = "binary"
                barrelspamteamdata["binary"] += thisrunteamdata["binary"]
            else:
                winningteam = "tie"
                barrelspamteamdata["decimal"] += math.ceil(thisrunteamdata["decimal"] / 2)
                barrelspamteamdata["binary"] += math.ceil(thisrunteamdata["binary"] / 2)

            # compile message
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.description = f"Final number reached: {finalint} | {bin(finalint)[2:]}"
            embed.set_footer(text="Remember to start at 0!")

            # winning team stuff
            if winningteam == "decimal":
                embed.title = "Run over, Team Decimal won!"
                embed.add_field(name="Points won for Team Decimal:", value=str(thisrunteamdata["decimal"]),
                                inline=False)
            elif winningteam == "binary":
                embed.title = "Run over, Team Binary won!"
                embed.add_field(name="Points won for Team Binary:", value=str(thisrunteamdata["binary"]), inline=False)
            else:
                embed.title = "Run over, and ended in a tie!"
                embed.add_field(name="Since it was a tie, both teams earn points:", \
                                value=f"Decimal: {math.ceil(thisrunteamdata['decimal'] / 2)}\nBinary: {math.ceil(thisrunteamdata['binary'] / 2)}",
                                inline=False)

            # inflict penalty
            penaltyteam = self.get_user_team(str(message.author.id), message.guild)
            barrelspamteamdata[penaltyteam] -= penalty
            embed.add_field(
                name=f"{message.author.display_name} ended the run, and got Team {penaltyteam.capitalize()} a penalty of {penalty} points <:barrelsadge:1298695216185872500>",
                value="", inline=False)

            # mvp and team standings
            mvpmember = message.guild.get_member(int(mvp[0]))
            embed.add_field(name="MVP of this run goes to:",
                            value=f"{mvpmember.display_name}, with a total of {mvp[1]} this run", inline=False)
            embed.add_field(name="Current team standings:",
                            value=f"Decimal: {barrelspamteamdata['decimal']}\nBinary: {barrelspamteamdata['binary']}",
                            inline=False)

            # send message
            await message.channel.send(embed=embed)

        await init_msg.delete()

        # reset run scores
        barrelspamtempdata = {}

    async def endShortRunSequence(self, message: discord.Message) -> None:
        """To be called when a short run is complete."""
        # update next spam
        global next_barrelspam
        global barrelspamdata
        global barrelspamtempdata
        global barrelspamteamdata
        if next_barrelspam == None:
            finalint = 0
        else:
            finalint = max(0, next_barrelspam - 1)
        next_barrelspam = 0

        # reset run scores
        for authorid in barrelspamtempdata.keys():
            barrelspamdata[authorid] -= barrelspamtempdata[authorid]
        barrelspamtempdata = {}

        # send quick message
        msg = await message.channel.send(
            f"Whoops!\nSince this run only got to {finalint}, scores aren't counted. Runs must be {SPAM_THRESHOLD} or higher to count. Start again below! You've got this!")
        await msg.delete(delay=5)

    @commands.Cog.listener()
    async def on_disconnect(self):
        """Called when the bot disconnects."""
        savealldata()

    @commands.Cog.listener()
    async def on_shard_disconnect(self, shard_id):
        """Called when the shard disconnects."""
        savealldata()


# MATH FUNCTIONS
def FirstPrimeFactor(n: int) -> int:
    """Returns the first prime factor of n"""
    if n & 1 == 0:
        return 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return d
        d = d + 2
    return n


def isPrime(number: int) -> bool:
    """Checks if the number is prime"""
    if number <= 2:
        return False
    return FirstPrimeFactor(number) == number


def isPerfectSquare(x: int) -> bool:
    """Checks if the number is a perfect square"""
    s = int(math.sqrt(x))
    return s * s == x


def isFibonacci(n: int) -> bool:
    """Checks if the number is part of the Fibonacci sequence"""
    # n is Fibonacci if one of 5*n*n + 4 or 5*n*n - 4 or both
    # is a perfect square
    if n <= 2:
        return False
    return isPerfectSquare(5 * n * n + 4) or isPerfectSquare(5 * n * n - 4)


def isMersenne(n: int) -> bool:
    """Checks if the number is a Mersenne prime"""
    if not isPrime(n):
        return False
    return all([b == '1' for b in bin(n)[2:]])


def isPalindrome(inputstr: str) -> bool:
    """Checks if the string is a palindrome"""
    if len(inputstr) <= 1:
        return False
    return inputstr == inputstr[::-1]


def isBinPali(inputint: int) -> bool:
    """Checks if the number is a palindrome in binary"""
    return isPalindrome(bin(inputint)[2:])


def isDecPali(inputint: int) -> bool:
    """Checks if the number is a palindrome in decimal"""
    return isPalindrome(str(inputint))


def getPrimeScore(n: int) -> int:
    """Gets score of a prime number"""
    return math.ceil(n / 3)


def getFibScore(n: int) -> int:
    """Gets score of a fibonacci number"""
    return math.ceil(n / 2)


def getMersenneScore(n: int) -> int:
    """Gets score of a mersenne prime number"""
    return math.ceil(n / 1.5)


def getPaliScore(n: int) -> int:
    """Gets score of a palindrome number"""
    return math.ceil(n / 2)


def save_to_json(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)


def savealldata():
    save_to_json(barrelspamdata, dir_path + "/data/barrelspamdata.json")
    save_to_json(barrelspamteamdata, dir_path + "/data/barrelspamteamdata.json")
    save_to_json(barrelspamtempdata, dir_path + "/data/barrelspamtempdata.json")
