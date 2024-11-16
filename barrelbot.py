import discord
from discord.ext import commands, tasks
import os
import time
import math
from datetime import datetime as dt
import json
import re
import random as rand
from numpy.random import default_rng


# Command prefix function
def isCommand(bot:commands.Bot, message:discord.Message) -> bool:

    # Allow to match with "bb " or "bb, "
    _m = re.match("bb,? ", message.content)
    if _m is not None:
        return _m.group(0)
    
    # Allow to match with direct address
    m = re.match("(hey |hello |hi )?barrel ?bot[,!.]? +", message.content, flags=re.I)
    if m is not None:
        return m.group(0)
    
    # Allow to match with mention
    m_ = re.match("<@733514909823926293>[,!.]? +", message.content)
    if m_ is not None:
        return m.group(0)
    
    # Default
    return "BarrelBot, "

# Initialize intents
Intents = discord.Intents.default()
Intents.messages = True
Intents.members = True
Intents.guild_messages = True
Intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=isCommand, intents=Intents)

# Create global variables
dir_path = os.path.dirname(os.path.abspath(__file__))
timer = time.time()
next_barrelspam = None
spam_threshold = 10

# Define constants
DECIMALROLEID = 1303766261574008943
BINARYROLEID = 1303766864391831644

BARRELCULTSPAMCHANNELID = 1297028406504067142

# Test IDs for the bot testing server
TESTROLEID = 735637859872276501
TESTCHANNELID = 733508209288937544

# Open saved data
with open("token.txt") as file:
    TOKEN = file.read()

with open("barrelspamdata.json") as file:
    barrelspamdata = json.load(file)

with open("barrelspamteamdata.json") as file:
    barrelspamteamdata = json.load(file)

with open("barrelspamtempdata.json") as file:
    barrelspamtempdata = json.load(file)

with open("customratings.json") as file:
    customratings = json.load(file)

with open("randomnumberscores.json") as file:
    randomnumberscores = json.load(file)

# Math functions

def FirstPrimeFactor(n:int) -> int:
    """Returns the first prime factor of n"""
    if n & 1 == 0:
        return 2
    d= 3
    while d * d <= n:
        if n % d == 0:
            return d
        d= d + 2
    return n

def isPrime(number:int) -> bool:
    """Checks if the number is prime"""
    if number <= 2:
        return False
    return FirstPrimeFactor(number) == number

def isPerfectSquare(x:int) -> bool:
    """Checks if the number is a perfect square"""
    s = int(math.sqrt(x))
    return s*s == x 

def isFibonacci(n:int) -> bool:
    """Checks if the number is part of the Fibonacci sequence"""
    # n is Fibonacci if one of 5*n*n + 4 or 5*n*n - 4 or both
    # is a perfect square
    if n <= 2:
        return False
    return isPerfectSquare(5*n*n + 4) or isPerfectSquare(5*n*n - 4)

def isMersenne(n:int) -> bool:
    """Checks if the number is a Mersenne prime"""
    if not isPrime(n):
        return False
    return all([b == '1' for b in bin(n)[2:]])

def isPalindrome(inputstr:str) -> bool:
    """Checks if the string is a palindrome"""
    if len(inputstr) <= 1:
        return False
    return inputstr == inputstr[::-1]

def isBinPali(inputint:int) -> bool:
    """Checks if the number is a palindrome in binary"""
    return isPalindrome(bin(inputint)[2:])

def isDecPali(inputint:int) -> bool:
    """Checks if the number is a palindrome in decimal"""
    return isPalindrome(str(inputint))

def getPrimeScore(n:int) -> int:
    """Gets score of a prime number"""
    return math.ceil(n/3)

def getFibScore(n:int) -> int:
    """Gets score of a fibonacci number"""
    return math.ceil(n/2)

def getMersenneScore(n:int) -> int:
    """Gets score of a mersenne prime number"""
    return math.ceil(n/1.5)

def getPaliScore(n:int) -> int:
    """Gets score of a palindrome number"""
    return math.ceil(n/2)

def getRandInt() -> int:
    """Gets a random number from an exponential distribution"""
    return math.ceil(default_rng().exponential(40))


# Command helper functions

def checkValidBarrelSpam(msg:discord.Message, ignore_number:bool=False):
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
        if (int(m.group(1), base=2) == next_barrelspam):
            return True, int(m.group(1), base=2)
    except:
        pass
    return False, int(m.group(1))

def savealldata():
    """Saves data to file."""
    save_to_json(randomnumberscores, "randomnumberscores.json")
    save_to_json(barrelspamdata, "barrelspamdata.json")
    save_to_json(barrelspamteamdata, "barrelspamteamdata.json")
    save_to_json(barrelspamtempdata, "barrelspamtempdata.json")

async def prettyify_dict(data:dict) -> str:
    """Turns score dictionary to a more readable string"""
    asArray = []
    for i,j in data.items():
        try:
            # most likely, the keys are user ids.
            usr = await bot.fetch_user(i)
            asArray.append(f"{usr.display_name} has a score of {j}")
        except:
            # however, in one case the data is the overall high score.
            usr = await bot.fetch_user(j[1])
            asArray.append(f"The overall score is {j[0]}, held by {usr.display_name}")
    # turn the array into a single string
    return "\n".join(asArray)

def save_to_json(data, filename:str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)

def get_user_team(userid:str, guild:discord.Guild) -> str:
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

async def continueSequence(message:discord.Message, spamint:int) -> None:
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
    
async def endLongRunSequence(message:discord.Message) -> None:
    """To be called when a long run is complete."""
    # update next spam
    global next_barrelspam
    global barrelspamdata
    global barrelspamtempdata
    global barrelspamteamdata
    finalint = max(0, next_barrelspam-1)
    next_barrelspam = 0
    penalty = math.floor(finalint/4)

    # Send end run msg
    init_msg = await message.channel.send(f"Run over! Fetching data...")

    async with message.channel.typing():

        # get team scores, mvp data
        thisrunteamdata = {"decimal": 0, "binary": 0}
        mvp = [0,0]
        for usrid in barrelspamtempdata.keys():
            team = get_user_team(usrid, message.guild)
            if team != "not in team":
                score = barrelspamtempdata[usrid]
                thisrunteamdata[team] += score
                if score > mvp[1]:
                    mvp = [usrid, score]
            else:
                pass # womp womp

        # check winning team, add score
        if thisrunteamdata["decimal"] > thisrunteamdata["binary"]:
            winningteam = "decimal"
            barrelspamteamdata["decimal"] += thisrunteamdata["decimal"]
        elif thisrunteamdata["decimal"] < thisrunteamdata["binary"]:
            winningteam = "binary"
            barrelspamteamdata["binary"] += thisrunteamdata["binary"]
        else:
            winningteam = "tie"
            barrelspamteamdata["decimal"] += math.ceil(thisrunteamdata["decimal"]/2)
            barrelspamteamdata["binary"] += math.ceil(thisrunteamdata["binary"]/2)

        # compile message
        embed = discord.Embed(color=discord.Color.brand_red())
        embed.description = f"Final number reached: {finalint} | {bin(finalint)[2:]}"
        embed.set_footer(text="Remember to start at 0!")

        # winning team stuff
        if winningteam == "decimal":
            embed.title = "Run over, Team Decimal won!"
            embed.add_field(name="Points won for Team Decimal:", value=str(thisrunteamdata["decimal"]), inline=False)
        elif winningteam == "binary":
            embed.title = "Run over, Team Binary won!"
            embed.add_field(name="Points won for Team Binary:", value=str(thisrunteamdata["binary"]), inline=False)
        else:
            embed.title = "Run over, and ended in a tie!"
            embed.add_field(name="Since it was a tie, both teams earn points:",\
                            value=f"Decimal: {math.ceil(thisrunteamdata['decimal']/2)}\nBinary: {math.ceil(thisrunteamdata['binary']/2)}", inline=False)

        # inflict penalty
        penaltyteam = get_user_team(str(message.author.id), message.guild)
        barrelspamteamdata[penaltyteam] -= penalty
        embed.add_field(name=f"{message.author.display_name} ended the run, and got Team {penaltyteam.capitalize()} a penalty of {penalty} points <:barrelsadge:1298695216185872500>", value="", inline=False)

        # mvp and team standings
        mvpmember = message.guild.get_member(int(mvp[0]))
        embed.add_field(name="MVP of this run goes to:", value=f"{mvpmember.display_name}, with a total of {mvp[1]} this run", inline=False)
        embed.add_field(name="Current team standings:", value=f"Decimal: {barrelspamteamdata['decimal']}\nBinary: {barrelspamteamdata['binary']}", inline=False)

        # send message
        await message.channel.send(embed=embed)
    
    await init_msg.delete()

    # reset run scores
    barrelspamtempdata = {}

async def endShortRunSequence(message:discord.Message) -> None:
    """To be called when a short run is complete."""
    # update next spam
    global next_barrelspam
    global barrelspamdata
    global barrelspamtempdata
    global barrelspamteamdata
    if next_barrelspam == None:
        finalint = 0
    else:
        finalint = max(0, next_barrelspam-1)
    next_barrelspam = 0

    # reset run scores
    for authorid in barrelspamtempdata.keys():
        barrelspamdata[authorid] -= barrelspamtempdata[authorid]
    barrelspamtempdata = {}

    # send quick message
    msg = await message.channel.send(f"Whoops!\nSince this run only got to {finalint}, scores aren't counted. Runs must be {spam_threshold} or higher to count. Start again below! You've got this!")
    await msg.delete(delay=5)


# Bot events

@bot.event
async def on_ready():
    """Called when the bot starts and is ready."""
    await bot.change_presence(activity=discord.Game('My name is barrelbot!'))

    # update barrel spam
    # first get channel
    global next_barrelspam
    spamchannel = bot.get_channel(BARRELCULTSPAMCHANNELID)

    # get last message and if spam
    last_spam = await spamchannel.fetch_message(spamchannel.last_message_id)
    check, last_spamint = checkValidBarrelSpam(last_spam, ignore_number=True)

    if check == False:
        # if the previous message isn't spam, the numbers reset to 0
        next_barrelspam = 0
    else:
        # iterate through message history, increasing next spam number until the previous 0 is found
        next_barrelspam = 0
        async for past_spam in spamchannel.history(limit=last_spamint+20):
            check2, past_spamint = checkValidBarrelSpam(past_spam, ignore_number=True)
            next_barrelspam += 1
            if check2 and past_spamint == 0:
                break

    # if the current number is wrong, next spam number resets to 0
    checkagain, _ = checkValidBarrelSpam(last_spam)
    if checkagain == False:
        spamchannel.send(f"I took a nap and when I came back, the spam number was off! You guys were supposed to be at {next_barrelspam-1}... "+\
                         "Guess you get to restart at 0!")
        next_barrelspam = 0

    # print next spam number
    print(f"Next spam number: {next_barrelspam}")

@bot.event
async def on_message(message:discord.Message):
    """Called whenever a message is sent that the bot can see."""
    # don't interact with bots
    if message.author.bot:
        return
    
    # barrel spam score logging
    if message.channel.id == BARRELCULTSPAMCHANNELID or message.channel.id == TESTCHANNELID:
        team = get_user_team(str(message.author.id), message.guild)
        if team == "not in team":
            responsemsg = await message.channel.send(f"{message.author.mention}, you must join a team before spamming!")
            await message.delete(delay=5)
            await responsemsg.delete(delay=5)
            return
        isspam, spamint = checkValidBarrelSpam(message)
        if isspam:
            await continueSequence(message, spamint)
        elif next_barrelspam == None:
            await endShortRunSequence(message)
        elif next_barrelspam > spam_threshold:
            await endLongRunSequence(message)
        else:
            await endShortRunSequence(message)
        
    # auto react
    m = re.search("<:\w*barrel\w*:\d+>", message.content)
    if m is not None:
        try:
            await message.add_reaction(m.group(0))
        except:
            pass

    # process commands
    await bot.process_commands(message)

    # save 
    global timer
    if time.time() - timer > 43200:
        savealldata()
        timer = time.time()

@bot.event
async def on_message_edit(msgbefore:discord.Message, msgafter:discord.Message):
    """Called when a message is edited."""
    if msgbefore.channel.id == BARRELCULTSPAMCHANNELID or msgbefore.channel.id == TESTCHANNELID:
        if next_barrelspam > spam_threshold:
            await endLongRunSequence(msgbefore)
        else:
            await endShortRunSequence(msgbefore)

@bot.event
async def on_command_error(ctx:commands.Context, error):
    """Called when a command produces an error."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('You\'re missing a required argument: '+str(error.param))
    elif isinstance(error, commands.TooManyArguments):
        await ctx.send('You input too many arguments.')
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.NotOwner):
        await ctx.send('You have to be the owner to excute this command.')
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the right permissions to execute that command.")
    elif isinstance(error, commands.BotMissingPermissions):
        try:
            await ctx.send('The bot is missing the required permissions to invoke this command: '+str(error.missing_perms))
        except commands.CommandInvokeError:
            await ctx.author.send("An error occurred and I wasn't able to handle it normally. I can't send messages to the channel you entered that command in. Other permissions I'm missing are "+str(error.missing_perms))
    elif isinstance(error, commands.ExtensionError):
        await ctx.send(f'The extension {str(error.name)} raised an exception.')
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'That command is on cooldown. Try again in {math.ceil(error.retry_after)} second(s).')
    else:
        await ctx.send(f'An unknown error occurred:\n{error}')

@bot.event
async def on_disconnect():
    """Called when the bot disconnects."""
    savealldata()

@bot.event
async def on_shard_disconnect(shard_id):
    """Called when the shard disconnects."""
    savealldata()

# Bot commands

@bot.command()
async def ping(ctx:commands.Context):
    """Pong!"""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command()
async def join(ctx:commands.Context, *, teamname):
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
        await ctx.send("Didn't quite get that. You can ask to join Team Decimal or Team Binary with \"barrelbot, join team decimal\" or \"barrelbot, join team binary\"")

@bot.command()
@commands.is_owner()
async def fetch(ctx:commands.Context, *, arg):
    """Fetch things
    Things you can fetch:
    barrel spam scores
    random number scores
    raw barrel spam scores
    raw random number scores
    all data"""
    if re.match("barrel spam scores", arg) is not None:
        async with ctx.typing():
            outstr = await prettyify_dict(barrelspamdata)
        if outstr == "":
            await ctx.send("No data to send!")
            return
        await ctx.send(outstr)
    elif re.match("random number scores", arg) is not None:
        async with ctx.typing():
            outstr = await prettyify_dict(randomnumberscores)
        if outstr == "":
            await ctx.send("No data to send!")
            return
        await ctx.send(outstr)
    elif re.match("raw barrel spam scores", arg) is not None:
        await ctx.send(json.dumps(barrelspamdata))
    elif re.match("raw random number scores", arg) is not None:
        await ctx.send(json.dumps(randomnumberscores))
    elif re.match("all data", arg) is not None:
        await ctx.send(f"next barrel spam: {next_barrelspam}\nbarrel spam temp data: {json.dumps(barrelspamtempdata)}\n"+\
                       f"barrel spam data: {json.dumps(barrelspamdata)}\n ")


@bot.command()
@commands.is_owner()
async def save_data(ctx:commands.Context):
    """Manually save all data to file."""
    savealldata()
    await ctx.send("Done.")

@bot.command()
async def introduce(ctx:commands.Context, *, arg):
    """Ask me to introduce myself!
    Example:
    `Hey BarrelBot, introduce yourself!`"""
    if re.match("yourself", arg) is not None:
        async with ctx.typing():
            time.sleep(1)
            await ctx.send("Hi! I'm BarrelBot. Nice to meet you!")
        async with ctx.typing():
            time.sleep(1.2)
            await ctx.send("I can do lots of things for you. If you want to see everything you can ask me, type \"Hey BarrelBot, help\".")
        async with ctx.typing():
            time.sleep(1.8)
            await ctx.send("I'll understand you if you say hey, hi, or hello before my name! And feel free to use capital letters or not. It doesn't really matter to me :slight_smile:")
        async with ctx.typing():
            time.sleep(2.1)
            await ctx.send("I'm here to help the <:barrel:1296987889942397001> cult in their spiritual journey towards the Almighty <:barrel:1296987889942397001>, "+\
                           "so I try to help out around here where I can.")
        async with ctx.typing():
            time.sleep(1.7)
            await ctx.send("One cool thing I do is watch <#1297028406504067142> and keep track of everyone's scores.")
        async with ctx.typing():
            time.sleep(1.2)
            await ctx.send("That's all for now! May the <:barrel:1296987889942397001> be with you :smile:")
        return
    else:
        await ctx.send(f"I don't know enough about {arg} to introduce him/her/them/it properly. You'll have to ask someone who knows more, sorry!")

@bot.command()
async def rate(ctx:commands.Context, *, item):
    """I'll rate whatever you tell me to.
    Example:
    `Hi BarrelBot, rate my neighbor's chicken pot pie`"""

    # if in custom ratings, send that
    if item.lower() in customratings.keys():
        await ctx.send(f"I'd give {item} a {customratings[item.lower()]}/10")
        return
    
    # if is a mention, return 10 with a :3 face
    if re.match("<@\d+>", item) is not None:
        await ctx.send(f"I'd give {item} a 10/10 :3")
        return
    
    # otherwise, seed the rng with the item string and get a random number from 0-10
    r = rand.getstate()
    rand.seed(item)
    rate_value = rand.randint(0, 10)
    rand.setstate(r)
    await ctx.send(f"I'd give {item} a {rate_value}/10")

@bot.command()
async def github(ctx:commands.Context):
    """Provides a link to my github page."""
    await ctx.send("https://github.com/janKaje/Barrel-Bot")

@bot.command()
async def eightball(ctx:commands.Context):
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

@bot.command()
@commands.cooldown(1,3, commands.BucketType.user)
async def random(ctx:commands.Context):
    """Gives a random number. Keeps track of high scores."""

    # fetch their random number
    value = getRandInt()

    # send fancy embed and update high scores
    embed = discord.Embed(color=discord.Color.brand_green(), )
    authorid = str(ctx.author.id)
    if authorid not in randomnumberscores.keys():
        # where it's the user's first random number
        randomnumberscores[authorid] = value
        embed.title = "Congrats!"; embed.description= f"You got your first random number: {value}"
        if value > randomnumberscores["overall"][0]:
            # in the very slim chance it's also a new overall high score
            olduser = await bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="You also beat the high score!", value=f"Old high score: {olduser.display_name} got {randomnumberscores['overall'][0]}", inline=False)
            randomnumberscores["overall"] = [value, ctx.author.id]
        else:
            embed.add_field(name='New high score:', value=str(value), inline=False)
    elif value > randomnumberscores[authorid]:
        # if you beat your personal high score
        if value > randomnumberscores["overall"][0]:
            # if you also beat the overall high score
            embed.title = "Congrats!"; embed.description = "You beat the high score!"
            olduser = await bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="Old high score:", value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}", inline=False)
            embed.add_field(name='New high score:', value=f'{ctx.author.display_name} got {value}', inline=False)
            randomnumberscores["overall"] = [value, ctx.author.id]
        else:
            # otherwise
            embed.title = "Congrats!"; embed.description= "You beat your personal best!"
            embed.add_field(name="Old high score:", value=str(randomnumberscores[authorid]), inline=False)
            embed.add_field(name='New high score:', value=str(value), inline=False)
        randomnumberscores[authorid] = value
    else:
        # default case, nothing is updated
        embed.title="You did not beat the high score."
        embed.description = str(value)
        embed.color=discord.Color.darker_gray()
        olduser = await bot.fetch_user(randomnumberscores["overall"][1])
        embed.add_field(name="Current high score:", value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}", inline=False)
        embed.add_field(name="Current personal best:", value=str(randomnumberscores[authorid]), inline=False)

    # send the embed
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def olape(ctx:commands.Context):
    """Gently puts the bot to sleep, so he can rest and recover for the coming day."""
    savealldata()
    await ctx.send("Goodnight! See you tomorrow :)")
    quit()

@bot.command()
async def leaderboard(ctx:commands.Context):
    """Shows the team scores and individual leaderboard of barrel spam scores."""
    # start embed
    embed = discord.Embed(color=discord.Color.dark_blue(), title="Barrel Spam Leaderboard", description="")
    embed.add_field(name="Team Scores", value=f"**Decimal: {barrelspamteamdata['decimal']}**\n**Binary: {barrelspamteamdata['binary']}**", inline=False)
    
    # collect and sort all scores
    ind_data_as_array = [[i,j] for i,j in barrelspamdata.items()]
    ind_data_as_array.sort(key=lambda x: x[1], reverse=True)
    valstr = ""
    for i, _list in enumerate(ind_data_as_array):
        valstr += "**"+str(i+1)+") "
        member = ctx.guild.get_member(int(_list[0]))
        valstr += member.display_name + "**"
        team = get_user_team(_list[0], ctx.guild)
        if team == "decimal":
            valstr += " *(Decimal Enthusiast)*"
        elif team == "binary":
            valstr += " *(Binary Enjoyer)*"
        valstr += ": **"+str(_list[1])+"**\n"
    embed.add_field(name="Individual Scores", value=valstr, inline=False)

    # send
    await ctx.send(embed=embed)    

@bot.command()
async def rank(ctx:commands.Context):
    """Shows your individual barrel spam score and rank."""
    # start embed
    embed = discord.Embed(color=discord.Color.dark_blue(), title="Barrel Spam Rank", description="")
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)

    # get scores and sort
    ind_data_as_array = [[i,j] for i,j in barrelspamdata.items()]
    ind_data_as_array.sort(key=lambda x: x[1], reverse=True)
    for i, _list in enumerate(ind_data_as_array):
        if _list[0] == str(ctx.author.id):
            embed.add_field(name=f"Rank: {i+1} out of {len(ind_data_as_array)}", value=f"**Score: {_list[1]}**")
            break
    
    # send
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)