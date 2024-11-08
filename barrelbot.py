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
    if re.match("bb ", message.content) is not None:
        return "bb "
    m = re.match("(hey |hello |hi )?barrel ?bot[,!.]? +", message.content, flags=re.I)
    if m == None:
        return "Barrelbot, "
    return m.group(0)

# Initialize
Intents = discord.Intents.default()
Intents.messages = True
Intents.members = True
Intents.guild_messages = True
Intents.message_content = True

bot = commands.Bot(command_prefix=isCommand, intents=Intents)
dir_path = os.path.dirname(os.path.abspath(__file__))

with open("token.txt") as file:
    TOKEN = file.read()

with open("channels.json") as file:
    channel_data = json.load(file)

with open("barrelemojis.json") as file:
    barrel_emojis = json.load(file)

with open("barrelspamdata.json") as file:
    barrelspamdata = json.load(file)

with open("barrelspamteamdata.json") as file:
    barrelspamteamdata = json.load(file)

with open("customratings.json") as file:
    customratings = json.load(file)

with open("randomnumberscores.json") as file:
    randomnumberscores = json.load(file)

timer = time.time()

# Math functions

def FirstPrimeFactor(n:int) -> int:
    if n & 1 == 0:
        return 2
    d= 3
    while d * d <= n:
        if n % d == 0:
            return d
        d= d + 2
    return n

def isPrime(number:int) -> bool:
    if number <= 2:
        return False
    return FirstPrimeFactor(number) == number

def isPerfectSquare(x:int) -> bool:
    s = int(math.sqrt(x))
    return s*s == x 

def isFibonacci(n:int) -> bool:
    # n is Fibonacci if one of 5*n*n + 4 or 5*n*n - 4 or both
    # is a perfect square
    if n <= 2:
        return False
    return isPerfectSquare(5*n*n + 4) or isPerfectSquare(5*n*n - 4)

def isMersenne(n:int) -> bool:
    if not isPrime(n):
        return False
    return all([b == '1' for b in bin(n)[2:]])

def getPrimeScore(n:int) -> int:
    return math.ceil(n/3)

def getFibScore(n:int) -> int:
    return math.ceil(n/2)

def getMersenneScore(n:int) -> int:
    return math.ceil(n/1.5)

def getRandInt() -> int:
    return math.ceil(default_rng().exponential(40))


# Command helper functions

def checkValidBarrelSpam(msg:discord.Message):
    m = re.match("(\d+) ?(<[^>]+>)", msg.content)
    if m == None:
        return False, 0
    if m.group(2) not in barrel_emojis:
        return False, 0
    return True, int(m.group(1))

async def prettyify_dict(data:dict) -> str:
    asArray = []
    for i,j in data.items():
        try:
            usr = await bot.fetch_user(i)
            asArray.append(f"{usr.display_name} has a score of {j}")
        except:
            usr = await bot.fetch_user(j[1])
            asArray.append(f"The overall score is {j[0]}, held by {usr.display_name}")
    return "\n".join(asArray)

def save_to_json(data, filename:str) -> None:
    with open(filename, "w") as file:
        json.dump(data, file)


# Bot events

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('My name is barrelbot!'))

@bot.event
async def on_message(message:discord.Message):
    # don't interact with bots
    if message.author.bot:
        return
    
    # barrel spam score logging
    if message.channel.id == channel_data["barrelcult_barrelspam"]:
        isspam, spamint = checkValidBarrelSpam(message)
        if isspam:
            authorid = str(message.author.id)
            if authorid not in barrelspamdata.keys():
                barrelspamdata[authorid] = 0
            isfib = isFibonacci(spamint)
            ispr = isPrime(spamint)
            if isfib:
                barrelspamdata[authorid] += getFibScore(spamint)
            if isMersenne(spamint):
                barrelspamdata[authorid] += getMersenneScore(spamint)
            elif ispr:
                barrelspamdata[authorid] += getPrimeScore(spamint)
            if (not isfib) and (not ispr):
                barrelspamdata[authorid] += 1
            
        else:
            pass # add what to do at end of run later

    # auto react
    m = re.search("<:barrel:1296987889942397001>", message.content)
    if m is not None:
        await message.add_reaction("<:barrel:1296987889942397001>")

    # process commands
    await bot.process_commands(message)

    global timer
    if time.time() - timer > 43200:
        save_to_json(randomnumberscores, "randomnumberscores.json")
        save_to_json(barrelspamdata, "barrelspamdata.json")
        save_to_json(barrelspamteamdata, "barrelspamteamdata.json")
        timer = time.time()

@bot.event
async def on_command_error(ctx, error):
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
    save_to_json(randomnumberscores, "randomnumberscores.json")
    save_to_json(barrelspamdata, "barrelspamdata.json")
    save_to_json(barrelspamteamdata, "barrelspamteamdata.json")

@bot.event
async def on_shard_disconnect(shard_id):
    save_to_json(randomnumberscores, "randomnumberscores.json")
    save_to_json(barrelspamdata, "barrelspamdata.json")
    save_to_json(barrelspamteamdata, "barrelspamteamdata.json")

# Bot commands

@bot.command()
async def ping(ctx):
    """Pong!"""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.command()
@commands.is_owner()
async def fetch(ctx, *, arg):
    """Fetch things"""
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


@bot.command()
@commands.is_owner()
async def save_data(ctx):
    """Manually save all data to file."""
    save_to_json(randomnumberscores, "randomnumberscores.json")
    save_to_json(barrelspamdata, "barrelspamdata.json")
    save_to_json(barrelspamteamdata, "barrelspamteamdata.json")
    await ctx.send("Done.")

@bot.command()
async def introduce(ctx, *, arg):
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
            await ctx.send("I'm starting to learn how <#1297028406504067142> works, and soon I'll be able to help everyone spam well!")
        async with ctx.typing():
            time.sleep(1.2)
            await ctx.send("That's all for now! May the <:barrel:1296987889942397001> be with you :smile:")
        return
    else:
        await ctx.send(f"I don't know enough about {arg} to introduce him/her/them/it properly. You'll have to ask someone who knows more, sorry!")

@bot.command()
async def rate(ctx, *, item):
    """I'll rate whatever you tell me to."""
    if item.lower() in customratings.keys():
        await ctx.send(f"I'd give {item} a {customratings[item.lower()]}/10")
        return
    if re.match("<@\d+>", item) is not None:
        await ctx.send(f"I'd give {item} a 10/10 :3")
        return
    r = rand.getstate()
    rand.seed(item)
    rate_value = rand.randint(0, 10)
    rand.setstate(r)
    await ctx.send(f"I'd give {item} a {rate_value}/10")

@bot.command()
async def github(ctx):
    """Provides a link to my github page."""
    await ctx.send("https://github.com/janKaje/Barrel-Bot")

@bot.command()
async def eightball(ctx):
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

@bot.command(aliases=["rand, r"])
@commands.cooldown(1,3, commands.BucketType.user)
async def random(ctx):
    """Gives a random number. Keeps track of high scores"""
    value = getRandInt()
    embed = discord.Embed(color=discord.Color.brand_green(), )
    authorid = str(ctx.author.id)
    if authorid not in randomnumberscores.keys():
        randomnumberscores[authorid] = value
        embed.title = "Congrats!"; embed.description= f"You got your first random number: {value}"
        if value > randomnumberscores["overall"][0]:
            olduser = await bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="You also beat the high score!", value=f"Old high score: {olduser.display_name} got {randomnumberscores['overall'][0]}")
            randomnumberscores["overall"] = [value, ctx.author.id]
        else:
            embed.add_field(name='New high score:', value=str(value))
    elif value > randomnumberscores[authorid]:
        if value > randomnumberscores["overall"][0]:
            embed.title = "Congrats!"; embed.description = "You beat the high score!"
            olduser = await bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="Old high score:", value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}")
            embed.add_field(name='New high score:', value=f'{ctx.author.display_name} got {value}')
            randomnumberscores["overall"] = [value, ctx.author.id]
        else:
            embed.title = "Congrats!"; embed.description= "You beat your personal best!"
            embed.add_field(name="Old high score:", value=str(randomnumberscores[authorid]))
            embed.add_field(name='New high score:', value=str(value))
        randomnumberscores[authorid] = value
    else:
        embed.title="You did not beat the high score."
        embed.description = str(value)
        embed.color=discord.Color.darker_gray()
        olduser = await bot.fetch_user(randomnumberscores["overall"][1])
        embed.add_field(name="Current high score:", value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}")
        embed.add_field(name="Current personal best:", value=str(randomnumberscores[authorid]))
    embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def omoli(ctx):
    """Kills the bot. You must be the bot owner to activate this command."""
    save_to_json(randomnumberscores, "randomnumberscores.json")
    save_to_json(barrelspamdata, "barrelspamdata.json")
    save_to_json(barrelspamteamdata, "barrelspamteamdata.json")
    await ctx.send("Ok bye bye")
    quit()

bot.run(TOKEN)