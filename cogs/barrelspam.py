import json
import math
import os
import re
import sys
from datetime import datetime as dt

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
next_barrelspam = None
sys.path.append(os.path.join(dir_path, "base"))

import env


async def setup(bot):
    await bot.add_cog(BarrelSpam(bot))


env.BBGLOBALS.init_globals()  # needs to be initialized again at the cog level

# Consts
SPAM_THRESHOLD = 10

DECIMALROLEID = 1303766261574008943
BINARYROLEID = 1303766864391831644

BARRELCULTSPAMCHANNELID = 1297028406504067142

LORD_ROLE_ID = 1313332375849009193

IND_DATA_MSG_ID = 1310847757921157150
TEAM_DATA_MSG_ID = 1310847752871350313
TEMP_DATA_MSG_ID = 1310847765517172776

DATA_CHANNEL_ID = 735631640939986964

# Debug
if env.BBGLOBALS.IS_IN_DEV_MODE:
    # same role item_id (& channel ID) everywhere because I can't be bothered to create new ones in the test server
    # (I don't have the perms anyways)
    DECIMALROLEID = 735637859872276501
    BINARYROLEID = 735637859872276501

    BARRELCULTSPAMCHANNELID = 733508209288937544

    LORD_ROLE_ID = 735637859872276501

    IND_DATA_MSG_ID = 735637859872276501
    TEAM_DATA_MSG_ID = 735637859872276501
    TEMP_DATA_MSG_ID = 735637859872276501

    DATA_CHANNEL_ID = 733508209288937544
##

# Open data files
with open(dir_path + "/data/barrelspamdata.json") as file:
    barrelspamdata = json.load(file)

with open(dir_path + "/data/barrelspamteamdata.json") as file:
    barrelspamteamdata = json.load(file)

try:
    with open(dir_path + "/data/barrelspamtempdata.json") as file:
        barrelspamtempdata = json.load(file)
except FileNotFoundError:
    barrelspamtempdata = {}


def check_valid_barrel_spam(msg: discord.Message, ignore_number: bool = False):
    """Checks if the given message is a valid spam message. By default, it takes into account the expected next
    spam number. However, if ignore_number is set to True, it only Checks if the format is valid and returns the
    decimal interpretation of the spam number."""

    m = re.match(r"(\d+) ?(<a?:\w*barrel\w*:\d+>)", msg.content, flags=re.I)
    if m is None:
        return False, 0
    global next_barrelspam
    if ignore_number:
        return True, int(m.group(1))
    if (int(m.group(1)) == next_barrelspam) or (next_barrelspam is None):
        return True, int(m.group(1))
    try:
        if int(m.group(1), base=2) == next_barrelspam:
            return True, int(m.group(1), base=2)
    except:
        pass
    return False, int(m.group(1))


def get_user_team(userid: str, guild: discord.Guild) -> str:
    """Gets the team that the user is on. Requires the user item_id in string format and the guild they're in."""
    member = guild.get_member(int(userid))
    for role in member.roles:
        if role.id == DECIMALROLEID:
            return "decimal"
        if role.id == BINARYROLEID:
            return "binary"
    return "not in team"


async def end_long_run_sequence(message: discord.Message) -> None:
    """To be called when a long run is complete."""
    # update next spam
    global next_barrelspam
    global barrelspamdata
    global barrelspamtempdata
    global barrelspamteamdata
    finalint = max(0, next_barrelspam - 1)
    next_barrelspam = 0
    penalty = math.floor(finalint / 5)

    # Send end run msg
    init_msg = await message.channel.send(f"Run over! Fetching data...")

    async with message.channel.typing():

        # get team scores, mvp data
        thisrunteamdata = {"decimal": 0, "binary": 0}
        mvp = [0, 0]
        for usrid in barrelspamtempdata.keys():
            team = get_user_team(usrid, message.guild)
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
            barrelspamteamdata["binary"] += math.ceil(thisrunteamdata["binary"] / 2)

        elif thisrunteamdata["decimal"] < thisrunteamdata["binary"]:
            winningteam = "binary"
            barrelspamteamdata["binary"] += thisrunteamdata["binary"]
            barrelspamteamdata["decimal"] += math.ceil(thisrunteamdata["decimal"] / 2)

        else:
            winningteam = "tie"
            barrelspamteamdata["decimal"] += math.ceil(thisrunteamdata["decimal"] * 0.75)
            barrelspamteamdata["binary"] += math.ceil(thisrunteamdata["binary"] * 0.75)

        # compile message
        embed = discord.Embed(color=discord.Color.brand_red())
        embed.description = f"Final number reached: {finalint} | {bin(finalint)[2:]}"
        embed.set_footer(text="Remember to start at 0!")

        # winning team stuff
        if winningteam == "decimal":
            embed.title = "Run over - Team Decimal won!"
            embed.add_field(name="__Points Won__",
                            value=f"Decimal: {math.ceil(thisrunteamdata['decimal'])}\n"
                                  f"Binary: {math.ceil(thisrunteamdata['binary'] * 0.5)}",
                            inline=False)
        elif winningteam == "binary":
            embed.title = "Run over - Team Binary won!"
            embed.add_field(name="__Points Won__",
                            value=f"Decimal: {math.ceil(thisrunteamdata['decimal'] * 0.5)}\n"
                                  f"Binary: {math.ceil(thisrunteamdata['binary'])}",
                            inline=False)
        else:
            embed.title = "Run over - and ended in a tie!"
            embed.add_field(name="__Points Won__",
                            value=f"Decimal: {math.ceil(thisrunteamdata['decimal'] * 0.75)}\n"
                                  f"Binary: {math.ceil(thisrunteamdata['binary'] * 0.75)}",
                            inline=False)

        # inflict penalty
        penaltyteam = get_user_team(str(message.author.id), message.guild)
        barrelspamteamdata[penaltyteam] -= penalty
        embed.add_field(
            name=f"{message.author.display_name} ended the run, and got Team {penaltyteam.capitalize()} a penalty "
                 f"of {penalty} points <:barrelsadge:1298695216185872500>",
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


async def end_short_run_sequence(message: discord.Message) -> None:
    """To be called when a short run is complete."""
    # update next spam
    global next_barrelspam
    global barrelspamdata
    global barrelspamtempdata
    global barrelspamteamdata
    if next_barrelspam is None:
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
        f"Whoops!\nSince this run only got to {finalint}, scores aren't counted. Runs must be {SPAM_THRESHOLD} "
        f"or higher to count. Start again below! You've got this!")
    await msg.delete(delay=5)


async def savealldata():
    save_to_json(barrelspamdata, dir_path + "/data/barrelspamdata.json")
    save_to_json(barrelspamteamdata, dir_path + "/data/barrelspamteamdata.json")

    print("spam data saved")


class BarrelSpam(commands.Cog, name="Barrel Spam"):
    """Functionality for barrel spam game"""

    def __init__(self, bot: commands.Bot):
        self.lord_role = None
        self.cult_guild = None
        self.bot = bot
        self.emoji_reactions = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟"
        }
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

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
                    await self.bot_send(ctx, "You're already in Team Decimal!")
                    return
                if role.id == BINARYROLEID:
                    # if they're in team binary, remove them from the team
                    await ctx.author.remove_roles(ctx.guild.get_role(BINARYROLEID))
            # finally, add role and confirm
            await ctx.author.add_roles(ctx.guild.get_role(DECIMALROLEID))
            await self.bot_send(ctx, "Added to Team Decimal!")

        # if they ask to join team binary
        elif re.match("(team )?binary", teamname, flags=re.I):
            # iterate through roles to clean up
            for role in ctx.author.roles:
                if role.id == BINARYROLEID:
                    await self.bot_send(ctx, "You're already in Team Binary!")
                    return
                if role.id == DECIMALROLEID:
                    # if they're in team decimal, remove them from the team
                    await ctx.author.remove_roles(ctx.guild.get_role(DECIMALROLEID))
            # finally, add role and confirm
            await ctx.author.add_roles(ctx.guild.get_role(BINARYROLEID))
            await self.bot_send(ctx, "Added to Team Binary!")
        else:
            # invalid entry
            await self.bot_send(ctx,
                                "Didn't quite get that. You can ask to join Team Decimal or Team Binary with "
                                "\"barrelbot, join team decimal\" or \"barrelbot, join team binary\"")

    @commands.command()
    async def leaderboard(self, ctx: commands.Context):
        """Shows the team scores and individual leaderboard of barrel spam scores."""

        # start embed
        embed = discord.Embed(color=discord.Color.dark_blue(), title="Barrel Spam Leaderboard", description="")
        embed.add_field(name="Team Scores",
                        value=f"**Decimal: {barrelspamteamdata['decimal']}**\n**Binary: "
                              f"{barrelspamteamdata['binary']}**",
                        inline=False)

        # collect and sort all scores
        ind_data_as_array = [[i, j] for i, j in barrelspamdata.items()]
        ind_data_as_array.sort(key=lambda x: x[1], reverse=True)
        valstr = ""
        for i, _list in enumerate(ind_data_as_array):
            valstr += "**" + str(i + 1) + ") "
            member = ctx.guild.get_member(int(_list[0]))
            valstr += member.display_name + "**"
            team = get_user_team(_list[0], ctx.guild)
            if team == "decimal":
                valstr += " *(Decimal Enthusiast)*"
            elif team == "binary":
                valstr += " *(Binary Enjoyer)*"
            valstr += ": **" + str(_list[1]) + "**\n"
        embed.add_field(name="Individual Scores", value=valstr, inline=False)

        # send
        await self.bot_send(ctx, embed=embed)

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
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @commands.is_owner()
    async def savespamdata(self, ctx: commands.Context):
        await savealldata()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getspamdata(self, ctx: commands.Context):
        await self.bot_send(ctx, json.dumps(barrelspamdata))
        await self.bot_send(ctx, json.dumps(barrelspamteamdata))
        await self.bot_send(ctx, json.dumps(barrelspamtempdata))
        await self.bot_send(ctx, next_barrelspam)

    @commands.command()
    @commands.is_owner()
    async def lordify(self, ctx: commands.Context):
        await self.update_whos_lord()
        await self.bot_send(ctx,
                            f"Complete. Now {self.lord_role.members[0].display_name} is Lord of <#1297028406504067142>")

    async def cog_load(self):
        """Called when the bot starts and is ready."""

        # first get channel
        global next_barrelspam
        spamchannel = self.bot.get_channel(BARRELCULTSPAMCHANNELID)

        last_spamint = 0
        check = False

        # get last message and if spam
        async for past_spam in spamchannel.history(limit=1):
            check, last_spamint = check_valid_barrel_spam(past_spam, ignore_number=True)
            break

        if check is False:
            # if the previous message isn't spam, the numbers reset to 0
            next_barrelspam = 0
        else:
            # iterate through message history, increasing next spam number until the previous 0 is found
            next_barrelspam = 0
            async for past_spam in spamchannel.history(limit=last_spamint + 20):
                check2, past_spamint = check_valid_barrel_spam(past_spam, ignore_number=True)
                next_barrelspam += 1
                if check2 and past_spamint == 0:
                    break

        # if the current number is wrong, next spam number resets to 0
        if last_spamint != next_barrelspam - 1:  # only works if previous number was printed in decimal

            # this mess makes sure that it's actually wrong and not just in binary
            try:
                if int(str(last_spamint), base=2) == next_barrelspam - 1:
                    is_wrong = False
                else:
                    is_wrong = True
            except ValueError:
                is_wrong = True

            if is_wrong and env.BBGLOBALS.IS_IN_DEV_MODE == False:
                print(f"Spam number off: should be {next_barrelspam}, was {last_spamint}")
                await spamchannel.send(
                    f"I took a nap and when I came back, the spam number was off! You guys were supposed to be at "
                    f"{next_barrelspam - 1}... Guess you get to restart at 0!")
                next_barrelspam = 0

        # print next spam number
        print(f"Next spam number: {next_barrelspam}")

        self.cult_guild = (await self.bot.fetch_channel(BARRELCULTSPAMCHANNELID)).guild
        self.lord_role = self.cult_guild.get_role(LORD_ROLE_ID)

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

        # start hourly loop
        self.hourlyloop.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called whenever a message is sent that the bot can see."""
        # don't interact with bots
        if message.author.bot:
            return

        global next_barrelspam

        # barrel spam score logging
        if message.channel.id == BARRELCULTSPAMCHANNELID:  # or message.channel.item_id == TESTCHANNELID:
            team = get_user_team(str(message.author.id), message.guild)
            if team == "not in team":
                responsemsg = await message.channel.send(
                    f"{message.author.mention}, you must join a team before spamming! Go to <#1297596333976453291> "
                    f"and type `bb help join`")
                await message.delete(delay=10)
                await responsemsg.delete(delay=10)
                return
            isspam, spamint = check_valid_barrel_spam(message)
            if isspam:
                await self.continue_sequence(message, spamint)
            elif next_barrelspam is None:
                await end_short_run_sequence(message)
            elif next_barrelspam > SPAM_THRESHOLD:
                await end_long_run_sequence(message)
            else:
                await end_short_run_sequence(message)

        # debug
        # if message.channel.item_id == 733508144617226302:
        #     print(message.content)
        #     print(self.check_valid_barrel_spam(message, ignore_number=True))

    @commands.Cog.listener()
    async def on_message_edit(self, msgbefore: discord.Message, _: discord.Message):
        """Called when a message is edited."""
        if msgbefore.channel.id == BARRELCULTSPAMCHANNELID:  # or msgbefore.channel.item_id == TESTCHANNELID:
            if next_barrelspam > SPAM_THRESHOLD:
                await end_long_run_sequence(msgbefore)
            else:
                await end_short_run_sequence(msgbefore)

    async def continue_sequence(self, message: discord.Message, spamint: int) -> None:
        """To be called when the spam sequence continues. Requires the spam message and the spam number."""
        # update next spam
        global next_barrelspam
        global barrelspamdata
        global barrelspamtempdata
        global barrelspamteamdata
        if next_barrelspam is None:
            next_barrelspam = spamint
        next_barrelspam += 1

        # add user to data if not in
        authorid = str(message.author.id)
        if authorid not in barrelspamdata.keys():
            barrelspamdata[authorid] = 0
        if authorid not in barrelspamtempdata.keys():
            barrelspamtempdata[authorid] = 0

        # increase score
        score = 0
        reactions = []
        if is_prime(spamint):
            if is_mersenne(spamint):
                score += get_mersenne_score(spamint)
                reactions.append("🇲")
            else:
                score += get_prime_score(spamint)
                reactions.append("🇵")
        if is_fibonacci(spamint):
            score += get_fib_score(spamint)
            reactions.append("🇫")
        if is_binary_palindrome(spamint):
            score += get_pali_score(spamint)
            reactions.append("✨")
        if is_decimal_palindrome(spamint):
            score += get_pali_score(spamint)
            reactions.append("<:holybarrel:1303080132642209826>")
        if is_power_of_two(spamint):
            score += get_power_two_score(spamint)
            reactions.append("↗️")
        if is_perfect_square(spamint):
            score += get_perfect_square_score(spamint)
            reactions.append("⏹️")
        if is_thue_morse(spamint):
            score += get_thue_morse_score(spamint)
            reactions.append("🇹")
        if score == 0:
            score += 1

        barrelspamdata[authorid] += score
        barrelspamtempdata[authorid] += score

        scorereactions = [self.emoji_reactions[min(score, 10)]]

        if score > 10:
            scorereactions.append("➕")

        reactions = scorereactions + reactions

        for reaction in reactions:
            try:
                await message.add_reaction(reaction)
            except:
                pass

        # to add in future: react to spam msg with emojis that indicate score or special numbers

    async def update_whos_lord(self):
        """Just updates who the barrel spam lord is"""

        # get spam data and sort
        ind_data_as_array = [[i, j] for i, j in barrelspamdata.items()]
        ind_data_as_array.sort(key=lambda x: x[1], reverse=True)
        next_lord = self.cult_guild.get_member(int(ind_data_as_array[0][0]))

        if next_lord is None:
            print("No lord found, skipping lord update")
            return

        # remove the lord role from everyone but the next lord (if applicable)
        lords = self.lord_role.members
        for member in lords:
            if member.id != next_lord.id:
                await member.remove_roles(self.lord_role)

        # add it to the next lord (if applicable)
        if self.lord_role not in next_lord.roles:
            await next_lord.add_roles(self.lord_role)

            print(f"{next_lord.display_name} is now lord of barrel spam")  # only prints on switch bc why not

    @tasks.loop(hours=7)
    async def hourlyloop(self):
        """Runs every hour - mostly to save data and update lord role"""
        await savealldata()
        await self.update_whos_lord()
        print(f"{dt.now().isoformat(sep=' ', timespec='seconds')} INFO\t Hourly loop finished!")


# MATH FUNCTIONS
def first_prime_factor(n: int) -> int:
    """Returns the first prime factor of n"""
    if n & 1 == 0:
        return 2
    d = 3
    while d * d <= n:
        if n % d == 0:
            return d
        d = d + 2
    return n


def is_prime(number: int) -> bool:
    """Checks if the number is prime"""
    if number <= 2:
        return False
    return first_prime_factor(number) == number


def is_perfect_square(x: int) -> bool:
    """Checks if the number is a perfect square"""
    if x <= 2:
        return False
    s = int(math.sqrt(x))
    return s * s == x


def is_fibonacci(n: int) -> bool:
    """Checks if the number is part of the Fibonacci sequence"""
    # n is Fibonacci if one of 5*n*n + 4 or 5*n*n - 4 or both
    # is a perfect square
    if n <= 2:
        return False
    return is_perfect_square(5 * n * n + 4) or is_perfect_square(5 * n * n - 4)


def is_mersenne(n: int) -> bool:
    """Checks if the number is a Mersenne prime"""
    if not is_prime(n):
        return False
    return all([b == '1' for b in bin(n)[2:]])


def is_palindrome(inputstr: str) -> bool:
    """Checks if the string is a palindrome"""
    if len(inputstr) <= 1:
        return False
    return inputstr == inputstr[::-1]


def is_binary_palindrome(inputint: int) -> bool:
    """Checks if the number is a palindrome in binary"""
    binstr = format(inputint, "b")
    padding = 8 - (len(binstr) % 8)
    binstr = "0" * padding + binstr
    return is_palindrome(binstr)


def is_decimal_palindrome(inputint: int) -> bool:
    """Checks if the number is a palindrome in decimal"""
    return is_palindrome(str(inputint))


def is_power_of_two(inputint: int) -> bool:
    """Checks if the number is a power of 2"""
    if inputint <= 1:
        return False
    return (inputint & (inputint - 1)) == 0


def generate_sequence(seq_length: int):
    """Thue–Morse sequence."""
    value = 1
    for n in range(seq_length):
        # Note: assumes that (-1).bit_length() gives 1
        x = (n ^ (n - 1)).bit_length() + 1
        if x & 1 == 0:
            # Bit index is even, so toggle value
            value = 1 - value
        yield str(value)


def get_thuemorse(n: int) -> int:
    asstr = "".join(generate_sequence(n))
    return int(asstr, base=2)


def is_thue_morse(n: int) -> bool:
    if n <= 1:
        return False
    lenseq = len(format(n, "b")) + 1
    if n == 0:
        lenseq = 1
    thue_morse_at_len = get_thuemorse(lenseq)
    return thue_morse_at_len == n


def get_prime_score(n: int) -> int:
    """Gets score of a prime number"""
    return math.ceil(n / 4)


def get_fib_score(n: int) -> int:
    """Gets score of a fibonacci number"""
    return math.ceil(n / 2)


def get_mersenne_score(n: int) -> int:
    """Gets score of a mersenne prime number"""
    return math.ceil(n / 1.5)


def get_pali_score(n: int) -> int:
    """Gets score of a palindrome number"""
    return math.ceil(n / 2)


def get_power_two_score(n: int) -> int:
    """Gets score of a power of 2"""
    return math.ceil(n / 2)


def get_perfect_square_score(n: int) -> int:
    """Gets score of a perfect square"""
    return math.ceil(n / 2)


def get_thue_morse_score(n: int) -> int:
    return math.ceil(n / 1.5)


def save_to_json(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)
