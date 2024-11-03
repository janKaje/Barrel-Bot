import discord
from discord.ext import commands, tasks
import os
import time
import math
from datetime import datetime as dt
import json
import re

# Initialize
Intents = discord.Intents.default()
Intents.messages = True
Intents.members = True
Intents.guild_messages = True
Intents.message_content = True

bot = commands.Bot(command_prefix="barrelbot, ", intents=Intents)
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
    await ctx.send(f'Pong! {round(bot.latency * 1000)}ms')

@bot.event
async def on_message(message:discord.Message):
    if message.author.bot:
        return
    if message.channel.id == channel_data["barrelcult_barrelspam"] or message.channel.id == channel_data["testingchannel"]:
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
    outstr = await prettyify_dict(barrelspamdata)
    if outstr == "":
        await ctx.send("No data to send!")
        return
    await ctx.send(outstr)

@bot.command()
async def save_spam_scores(ctx):
    save_to_json(barrelspamdata, "barrelspamdata.json")
    await ctx.send("Done.")

bot.run(TOKEN)