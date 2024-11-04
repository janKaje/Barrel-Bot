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
    asArray = [[await bot.fetch_user(i),j] for i,j in data.items()]
    asListStrs = [f"{l[0].display_name} has a score of {l[1]}" for l in asArray]
    return "\n".join(asListStrs)

def save_to_json(data, filename:str) -> None:
    with open(filename, "w") as file:
        json.dump(data, file)


# Bot functions

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('My name is barrelbot!'))

@bot.command()
async def ping(ctx):
    """Pong!"""
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.event
async def on_message(message:discord.Message):
    if message.author.bot:
        return
    if message.channel.id == channel_data["barrelcult_barrelspam"]:
        isspam, spamint = checkValidBarrelSpam(message)
        if isspam:
            if message.author.id not in barrelspamdata.keys():
                barrelspamdata[message.author.id] = 0
            isfib = isFibonacci(spamint)
            ispr = isPrime(spamint)
            if isfib:
                barrelspamdata[message.author.id] += getFibScore(spamint)
            if isMersenne(spamint):
                barrelspamdata[message.author.id] += getMersenneScore(spamint)
            elif ispr:
                barrelspamdata[message.author.id] += getPrimeScore(spamint)
            if (not isfib) and (not ispr):
                barrelspamdata[message.author.id] += 1
            
        else:
            pass # add what to do at end of run later
    
    await bot.process_commands(message)

@bot.command()
async def get_spam_scores(ctx):
    """Fetch barrel spam scores"""
    outstr = await prettyify_dict(barrelspamdata)
    if outstr == "":
        await ctx.send("No data to send!")
        return
    await ctx.send(outstr)

@bot.command()
async def save_spam_scores(ctx):
    """Manually save barrel spam scores to file."""
    save_to_json(barrelspamdata, "barrelspamdata.json")
    await ctx.send("Done.")

@bot.command()
async def rate(ctx, *, item):
    """I'll rate whatever you tell me to."""
    if item in customratings.keys():
        await ctx.send(f"I'd give {item} a {customratings[item]}/10")
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
    if ctx.author.id not in randomnumberscores.keys():
        randomnumberscores[ctx.author.id] = value
        embed.title = "Congrats!"; embed.description= f"You got your first random number: {value}"
        if value > randomnumberscores["overall"][0]:
            olduser = await bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="You also beat the high score!", value=f"Old high score: {olduser.display_name} got {randomnumberscores['overall'][0]}")
            randomnumberscores["overall"] = [value, ctx.author.id]
        else:
            embed.add_field(name='New high score:', value=str(value))
    elif value > randomnumberscores[ctx.author.id]:
        if value > randomnumberscores["overall"][0]:
            embed.title = "Congrats!"; embed.description = "You beat the high score!"
            olduser = await bot.fetch_user(randomnumberscores["overall"][1])
            embed.add_field(name="Old high score:", value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}")
            embed.add_field(name='New high score:', value=f'{ctx.author.display_name} got {value}')
            randomnumberscores["overall"] = [value, ctx.author.id]
        else:
            embed.title = "Congrats!"; embed.description= "You beat your personal best!"
            embed.add_field(name="Old high score:", value=str(randomnumberscores[ctx.author.id]))
            embed.add_field(name='New high score:', value=str(value))
        randomnumberscores[ctx.author.id] = value
    else:
        embed.title="You did not beat the high score."
        embed.description = str(value)
        embed.color=discord.Color.darker_gray()
        olduser = await bot.fetch_user(randomnumberscores["overall"][1])
        embed.add_field(name="Current high score:", value=f"{olduser.display_name} got {randomnumberscores['overall'][0]}")
        embed.add_field(name="Current personal best:", value=str(randomnumberscores[ctx.author.id]))
    await ctx.send(embed=embed)

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

@bot.command()
@commands.is_owner()
async def omoli(ctx):
    """Kills the bot. You must be the bot owner to activate this command."""
    await ctx.send("Ok bye bye")
    quit()

@bot.command()
@commands.is_owner()
async def randomscores(ctx):
    await ctx.send(str(randomnumberscores))

bot.run(TOKEN)