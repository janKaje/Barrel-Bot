import json
import math
import os
import random as rand
import re
import asyncio
from copy import deepcopy

import discord
from discord.ext import commands, tasks
from numpy.random import default_rng

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Inventory item ids
# Fishing rod: 1
# Dagger: 2
# Shield: 3
# Barrel Crate: 4
# Golden Barrel Crate: 5
# ...
# Prizes and unique items: 20-99
# Fish: (second two numbers are stats: length and weight)
#   Squid: 100
#   Jellyfish: 200
#   Shrimp: 300
#   Lobster: 400
#   Crab: 500
#   Blowfish: 600
#   Yellow fish: 700
#   Blue fish: 800
#   Shark: 900
# Pets:
#   1000s?
# Tech:
#   100000s (find good storage method)


async def setup(bot):
    await bot.add_cog(fun(bot))


with open(dir_path + "/data/customratings.json") as file:
    customratings = json.load(file)

with open(dir_path + "/data/randomnumberscores.json") as file:
    randomnumberscores = json.load(file)

with open(dir_path + "/data/barrelcoins.json") as file:
    barrelcoins = json.load(file)
    
with open(dir_path + "/data/inventories.json") as file:
    inventories = json.load(file)


DATA_CHANNEL_ID = 735631640939986964

DATA_MSG_ID = 1310847777302908929
BARREL_COIN_DATA_MSG = 1363307787848912896
INVENTORY_MSG = 1363370297121705985

BARREL_COIN = "<:barrelcoin:1364027068936884405>"
BARREL_EMOJI = "<:barrel:1296987889942397001>"
HOLY_BARREL_EMOJI = "<:holybarrel:1303080132642209826>"

aliases = {
    1: ["1", "fishing rod", "🎣"],
    2: ["2", "dagger", "🗡️"],
    3: ["3", "shield", "🛡️"],
    4: ["4", "barrel", "barrel crate", BARREL_EMOJI],
    5: ["5", "golden barrel", "golden barrel crate", "holy barrel", HOLY_BARREL_EMOJI],
    100: ["squid", "🦑"],
    200: ["jellyfish", "🪼"],
    300: ["shrimp", "🦐"],
    400: ["lobster", "🦞"],
    500: ["crab", "🦀"],
    600: ["blowfish", "🐡"],
    700: ["yellow fish", "🐠"],
    800: ["blue fish", "🐟"],
    900: ["shark", "🦈"]
}

prices = {
    1: 100,
    2: 20,
    3: 20
}


class fun(commands.Cog, name="Fun"):
    """Random fun things"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def savefundata(self, ctx: commands.Context):
        await self.savealldata()
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def getfundata(self, ctx: commands.Context):
        await ctx.send(json.dumps(randomnumberscores))
        await ctx.send(json.dumps(barrelcoins))
        await ctx.send(json.dumps(inventories))

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Pong!"""
        to_send = f'Pong! {round(self.bot.latency * 1000)}ms'
        isowner = await self.bot.is_owner(ctx.author)
        if isowner and os.environ["MACHINE"] == "homelaptop":
            to_send += "\nI'm running in development mode. How's the coding?"
        await ctx.send(to_send)

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
                               "scores. I also keep track of who sends how many messages - you can see the results by asking me to show_analytics.")
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
        await ctx.send(embed=embed)

    @commands.command()
    async def cheese(self, ctx:commands.Context):
        await ctx.send("🧀")

    @commands.command()
    @commands.cooldown(1, 1800, commands.BucketType.user) # every 30 min
    async def work(self, ctx: commands.Context):
        f"""Every 30 minutes, you can work to earn {BARREL_COIN}."""
        workresult = rand.randint(0, 99)
        if workresult < 4:
            coinsadd = rand.randint(5,15)
            await self.give_coins(ctx.author.id, -coinsadd)
            await ctx.send(ctx.author.mention + ", you somehow managed to completely screw up everything at the barrel factory and had to pay " + \
                           str(coinsadd) + BARREL_COIN + " in damages.")
        elif workresult < 20:
            coinsadd = rand.randint(10,15)
            await self.give_coins(ctx.author.id, coinsadd)
            await ctx.send(ctx.author.mention + ", you worked hard, but things weren't in your favor today. You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        elif workresult < 65:
            coinsadd = rand.randint(25, 30)
            await self.give_coins(ctx.author.id, coinsadd)
            await ctx.send(ctx.author.mention + ", you had a really normal and boring day at the barrel factory. You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        elif workresult < 85:
            coinsadd = rand.randint(30, 40)
            await self.give_coins(ctx.author.id, coinsadd)
            await ctx.send(ctx.author.mention + ", you made a new friend at work today! You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        elif workresult < 98:
            coinsadd = rand.randint(40, 50)
            await self.give_coins(ctx.author.id, coinsadd)
            await ctx.send(ctx.author.mention + ", you had a tough day but you powered through it! You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        else:
            coinsadd = rand.randint(50, 75)
            await self.give_coins(ctx.author.id, coinsadd)
            await ctx.send(ctx.author.mention + ", you got a raise at work! You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
            
    @commands.command()
    async def shop(self, ctx: commands.Context, *, item:str=None):
        """See what's for sale. Use `bb shop <item>` to see the details of a particular item."""
        embed = discord.Embed(color=discord.Color.gold())
        if item is None:
            embed.title = "Welcome to the BarrelBot Shop!"
            embed.description = "Type `bb shop <item>` to see more about an item, or `bb buy <item>` to buy it"
            embed.add_field(name="🎣 - Fishing Rod", value="100"+BARREL_COIN)
        elif item.lower() == "fishing rod":
            embed.title = "🎣 - Fishing Rod"
            embed.description = "Cost: 100" + BARREL_COIN + "\nAllows you to use the command `fish`. Collect fish to keep as trophies or sell for more " + BARREL_COIN
            embed.set_footer(text="Type `bb buy fishing rod` to buy this item")
        else:
            embed.title = "Item not found."
            embed.description = ""
        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx:commands.Context, *, item:str):
        """Buy an item from the shop."""
        if item.lower() == "fishing rod":
            if await self.get_coins(ctx.author.id) < 100:
                await ctx.send("You don't have enough " + BARREL_COIN + " to buy this item!")
                return
            await self.give_coins(ctx.author.id, -100)
            await self.add_to_inventory(ctx.author.id, 1)
            await ctx.send("You bought a 🎣! If you didn't have one before, now you can do `bb fish`. You now have " + str(inventories[str(ctx.author.id)].count(1)) + " of this item.")            
        else:
            await ctx.send("Item not found.")

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user) # every 5 min
    async def fish(self, ctx:commands.Context):
        """Cast out your fishing line and see what you get! You can fish once every 5 minutes."""
        if not await self.can_fish(ctx.author.id):
            await ctx.send("You need to buy a fishing rod first!")
            return
        outstr, fishid = fish_()
        if fishid != 0:
            await self.add_to_inventory(ctx.author.id, fishid)
        await ctx.send(outstr)
        
    @commands.command()
    async def inventory(self, ctx:commands.Context, pageno=1):
        """Displays your personal inventory."""
        try:
            pageno = int(pageno)
        except:
            await ctx.send("Page number must be an integer.")
            return
        if str(ctx.author.id) not in inventories.keys():
            invdisplay = []
        else:
            invdisplay = deepcopy(inventories[str(ctx.author.id)])
            invdisplay.sort()
        invitems_ = list(set(invdisplay))
        invitems_.sort()
        invitems = invitems_[(pageno-1)*25:pageno*25]
        nopages = 1 + len(invitems_)//25
        embed = discord.Embed(color=discord.Color.light_gray())
        embed.title = ctx.author.display_name + "'s Inventory"
        embed.description = "Total items: " + str(len(invdisplay))
        for item in invitems:
            embed.add_field(name=get_item_str(item), value = str("" if invdisplay.count(item)==1 else "Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages} - type `bb inventory <page>` to see a different page")
        await ctx.send(embed=embed)

    @commands.command()
    async def balance(self, ctx:commands.Context):
        f"""Displays how many {BARREL_COIN} you have."""
        nocoins = await self.get_coins(ctx.author.id)
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = ctx.author.display_name + "'s " + BARREL_COIN + " balance"
        embed.description = str(nocoins) + BARREL_COIN
        await ctx.send(embed=embed)

    @commands.command()
    async def sellall(self, ctx:commands.Context):
        """Sells all of your fish."""
        authorid = str(ctx.author.id)
        if authorid not in inventories.keys() or len(inventories[authorid]) == 0:
            await ctx.send("Your inventory is empty! You need to get fish before selling them.")
            return
        inventory = inventories[authorid]
        fishinv = []
        for item in inventory:
            if len(str(item)) == 3:
                fishinv.append(item)
        if len(fishinv) == 0:
            await ctx.send("You don't have any fish to sell.")
            return
        nosold = 0
        saleprice = 0
        for fish in fishinv:
            nosold += 1
            saleprice += get_fish_value(fish)
            await self.remove_from_inventory(authorid, fish)
        await self.give_coins(authorid, saleprice)
        await ctx.send(f"You sold {nosold} fish for a total of {saleprice}{BARREL_COIN}")

    @commands.command()
    async def openall(self, ctx:commands.Context):
        """Opens all of your crates."""
        authorid = str(ctx.author.id)
        if authorid not in inventories.keys() or len(inventories[authorid]) == 0:
            await ctx.send("Your inventory is empty! You need to get crates before opening them.")
            return
        inventory = inventories[authorid]
        crateinv = []
        for item in inventory:
            if item in [4, 5]:
                crateinv.append(item)
        if len(crateinv) == 0:
            await ctx.send("You don't have any crates to open.")
            return
        nosold = 0
        saleprice = 0
        for crate in crateinv:
            nosold += 1
            saleprice += get_crate_value(crate)
            await self.remove_from_inventory(authorid, crate)
        await self.give_coins(authorid, saleprice)
        await ctx.send(f"You opened {nosold} crates and got a total of {saleprice}{BARREL_COIN}!")

    @commands.command(pass_context=True)
    async def gift(self, ctx:commands.Context, nocoins:str, *, user:discord.User):
        """Allows you to give someone else some coins. Example: `bb gift 50 @jan Kaje`"""
        nocoins = int(nocoins)
        if user.bot:
            await ctx.send("You can't give bots money.")
            return
        await self.give_coins(ctx.author.id, -nocoins)
        await self.give_coins(user.id, nocoins)
        await ctx.send(f"You've given {user.display_name} {nocoins}{BARREL_COIN}")

    @commands.command()
    async def baltop(self, ctx:commands.Context):
        """Shows the 10 people with the most money, as well as your own ranking."""
        balances = list(barrelcoins.items())
        balances.sort(key=lambda i: i[1], reverse=True)
        users = [i[0] for i in balances]
        bals = [i[1] for i in balances]
        ranking = users.index(str(ctx.author.id))
        embed = discord.Embed(color=discord.Color.gold(), title="Top 10 moneys")
        valstr = ""
        for i in range(min(10, len(users))):
            valstr += str(i+1) + ") "
            valstr += self.bot.get_user(int(users[i])).global_name
            valstr += " - " + str(bals[i]) + BARREL_COIN + "\n"
        embed.description = valstr
        if ranking >= 10:
            embed.add_field(name="Your ranking:", value=str(ranking+1) + "/" + str(len(users)))
        await ctx.send(embed=embed)
        

    # @commands.command()
    # async def sell(self, ctx:commands.Context, *, item=None):
    #     """Lets you sell items in your inventory. You can sell one at a time with item names, or multiple at a time with item ids."""
    #     if item is None:
    #         await ctx.send("Specify an item to sell. You can select by emoji, name, or id.")
    #         return
    #     authorid = str(ctx.author.id)
    #     if authorid not in inventories.keys() or len(inventories[authorid]) == 0:
    #         await ctx.send("Your inventory is empty! You need to get items before selling them.")
    #         return
    #     item_match = re.match(r"(\d+|[^\d]+)", item)
    #     itemname = item_match.group(0).strip().lower()
    #     for i in aliases.keys():
    #         if itemname in aliases[i]:
    #             if await self.has_in_inventory(authorid, i):
    #                 await self.remove_from_inventory(authorid, i)
    #                 await self.give_coins(int(math.floor(prices[i]*0.75)))
    #                 await ctx.send("Sold 1 " + get_item_str(i) + " for " + str(int(math.floor(prices[i]*0.75))) + BARREL_COIN)
    #             else:
    #                 await ctx.send("You don't have that item.")
    #             return

    @commands.command()
    @commands.is_owner()
    async def forcegivemoney(self, ctx:commands.Context, userid, nocoins):
        """Gives the specified user id a certain number of coins"""
        await self.give_coins(userid, int(nocoins))
        await ctx.send("Done. They now have " + str(await self.get_coins(userid)) + BARREL_COIN)

    @commands.command()
    @commands.is_owner()
    async def clearbalance(self, ctx:commands.Context, userid):
        """Clears the user's balance."""
        await self.give_coins(userid, -1*(await self.get_coins(userid)))
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def forcegiveitem(self, ctx:commands.Context, userid, itemid):
        """Gives the specified user id an item"""
        await self.add_to_inventory(userid, int(itemid))
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def forcetakeitem(self, ctx:commands.Context, userid, itemid):
        """Takes the specified item from the user"""
        done = await self.remove_from_inventory(userid, int(itemid))
        if done:
            await ctx.send("Done!")
        else:
            await ctx.send("Item not in their inventory.")

    @commands.command()
    @commands.is_owner()
    async def peekinv(self, ctx:commands.Context, userid, pageno=1):
        """Spies on the user's inventory."""
        try:
            pageno = int(pageno)
        except:
            await ctx.send("Page number must be an integer.")
            return
        if str(userid) not in inventories.keys():
            invdisplay = []
        else:
            invdisplay = deepcopy(inventories[str(userid)])
            invdisplay.sort()
        invitems_ = list(set(invdisplay))
        invitems_.sort()
        invitems = invitems_[(pageno-1)*25:pageno*25]
        nopages = 1 + len(invitems_)//25
        embed = discord.Embed(color=discord.Color.light_gray())
        embed.title = (await self.bot.fetch_user(int(userid))).global_name + "'s Inventory"
        embed.description = "Total items: " + str(len(invdisplay))
        for item in invitems:
            embed.add_field(name=get_item_str(item), value = str("" if invdisplay.count(item)==1 else "Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def clearinv(self, ctx:commands.Context, userid):
        """Clears the specified user's inventory."""
        global inventories
        inventories[str(userid)] = []
        await ctx.send("Done!")

        

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

    async def cog_load(self):
        
        # load for data saving
        await self.saveprep()

        # print loaded
        print(f"cog: {self.qualified_name} loaded")
        
        # start hourly loop
        self.hourlyloop.start()

    async def saveprep(self):
        
        # load for data saving
        self.datachannel = await self.bot.fetch_channel(DATA_CHANNEL_ID)
        self.datamsg = await self.datachannel.fetch_message(DATA_MSG_ID)
        self.coinmsg = await self.datachannel.fetch_message(BARREL_COIN_DATA_MSG)
        self.invmsg = await self.datachannel.fetch_message(INVENTORY_MSG)

    async def savealldata(self):
        """Saves data to file."""
        save_to_json(randomnumberscores, dir_path + "/data/randomnumberscores.json")
        save_to_json(barrelcoins, dir_path + "/data/barrelcoins.json")
        save_to_json(inventories, dir_path + "/data/inventories.json")

        await self.datamsg.edit(content=json.dumps(randomnumberscores))
        await asyncio.sleep(1)
        await self.coinmsg.edit(content=json.dumps(barrelcoins))
        await asyncio.sleep(1)
        await self.invmsg.edit(content=json.dumps(inventories))

        print("fun scores saved")

    @tasks.loop(hours=1)
    async def hourlyloop(self):
        await self.savealldata()

    async def give_coins(self, userid:int, nocoins:int):
        global barrelcoins
        userid = str(userid)
        if userid in barrelcoins.keys():
            barrelcoins[userid] += nocoins
        else:
            barrelcoins[userid] = nocoins
        barrelcoins[userid] = max(barrelcoins[userid], 0) # no negatives
        return
    
    async def get_coins(self, userid:int) -> int:
        userid = str(userid)
        if userid in barrelcoins.keys():
            return barrelcoins[userid]
        return 0
    
    async def add_to_inventory(self, userid:int, itemid:int):
        userid = str(userid)
        global inventories
        if userid in inventories.keys():
            inventories[userid].append(itemid)
        else:
            inventories[userid] = [itemid]
        return
    
    async def remove_from_inventory(self, userid:int, itemid:int) -> bool:
        """Returns false if not in inventory."""
        userid = str(userid)
        global inventories
        if userid in inventories.keys():
            if itemid in inventories[userid]:
                inventories[userid].remove(itemid)
                return True
            return False
        return False
    
    async def can_fish(self, userid:int) -> bool:
        userid = str(userid)
        if userid in inventories.keys():
            if 1 in inventories[userid]:
                return True
            return False
        return False
    
    async def has_in_inventory(self, userid:int|str, itemid:int) -> bool:
        userid = str(userid)
        if userid in inventories.keys():
            if itemid in inventories[userid]:
                return True
            return False
        return False

        
def get_item_str(itemid:int):
    if itemid < 100:
        match itemid:
            case 1:
                return "🎣 - Fishing Rod"
            case 2: 
                return "🗡️ - Dagger"
            case 3: 
                return "🛡️ - Shield"
            case 4:
                return BARREL_EMOJI + " - Barrel Crate"
            case 5:
                return HOLY_BARREL_EMOJI + " - Golden Barrel Crate"
            case _:
                return "Item not found."
    if itemid < 1000:
        fishid = int(str(itemid)[0])
        length = int(str(itemid)[1])
        weight = int(str(itemid)[2])
        match fishid:
            case 1: 
                outstr = "🦑 - Squid"
            case 2:
                outstr = "🪼 - Jellyfish"
            case 3:
                outstr = "🦐 - Shrimp"
            case 4:
                outstr = "🦞 - Lobster"
            case 5:
                outstr = "🦀 - Crab"
            case 6: 
                outstr = "🐡 - Blowfish"
            case 7:
                outstr = "🐠 - Yellow Fish"
            case 8:
                outstr = "🐟 - Blue Fish"
            case 9:
                outstr = "🦈 - Shark"
            case _:
                return "Item not found."
        outstr += f" - {(length+1)*5} cm, {(weight+1)*0.5} kg"
        return outstr
    return "Item not found."
        
def fish_() -> tuple[str, int]:
    luck = rand.randint(0, 999)
    if luck == 0:
        outstr = "You caught some trash. This made you so upset that you threw it back into the ocean while screaming intensely. Now everyone around you is looking at you funny, and you're worried you'll get kicked off the pier."
        return outstr, 0
    if luck < 10:
        outstr = "You caught some really disgusting trash. You pinch your nose as you bring it to the trash can, wondering how it got into the ocean."
        return outstr, 0
    if luck < 50:
        outstr = "You caught some trash. Frustrated, you put it in the growing heap of garbage next to you, since you're too lazy to bring it to the garbage can."
        return outstr, 0
    if luck < 200:
        outstr = "You caught some trash. Better luck next time..."
        return outstr, 0
    if luck < 500:
        subluck = luck - 199
        length = int(round(subluck/30*rand.random()))
        weight = int(round(subluck/30*rand.random()))
        outstr = f"You caught a 🐟! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("8" + str(length) + str(weight))
    if luck < 700:
        subluck = luck - 499
        length = int(round(subluck/20*rand.random()))
        weight = int(round(subluck/20*rand.random()))
        outstr = f"You caught a 🐠! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("7" + str(length) + str(weight))
    if luck < 800:
        subluck = luck - 699
        length = int(round(subluck/10*rand.random()))
        weight = int(round(subluck/10*rand.random()))
        outstr = f"You caught a 🦐! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("3" + str(length) + str(weight))
    if luck < 850:
        subluck = luck - 799
        length = int(round(subluck/5*rand.random()))
        weight = int(round(subluck/5*rand.random()))
        outstr = f"You caught a 🦞! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("4" + str(length) + str(weight))
    if luck < 900:
        subluck = luck - 849
        length = int(round(subluck/5*rand.random()))
        weight = int(round(subluck/5*rand.random()))
        outstr = f"You caught a 🦀! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("5" + str(length) + str(weight))
    if luck < 940:
        subluck = luck - 899
        length = int(round(subluck/4*rand.random()))
        weight = int(round(subluck/4*rand.random()))
        outstr = f"You caught a 🪼! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("2" + str(length) + str(weight))
    if luck < 960:
        subluck = luck - 939
        length = int(round(subluck/2*rand.random()))
        weight = int(round(subluck/2*rand.random()))
        outstr = f"You caught a 🐡! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("6" + str(length) + str(weight))
    if luck < 980:
        subluck = luck - 959
        length = int(round(subluck/2*rand.random()))
        weight = int(round(subluck/2*rand.random()))
        outstr = f"You caught a 🦑! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("1" + str(length) + str(weight))
    if luck < 990:
        subluck = luck - 979
        length = int(round(subluck*rand.random()))
        weight = int(round(subluck*rand.random()))
        outstr = f"You caught a 🦈! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("9" + str(length) + str(weight))
    if luck < 999:
        outstr = "You caught a " + BARREL_EMOJI + "! Open it to see what's inside!"
        return outstr, 4
    else:
        outstr = "Wow! You caught a " + HOLY_BARREL_EMOJI + "! Open it to see what's inside!"
        return outstr, 5

def get_fish_value(fishid:int) -> int:
    type = int(str(fishid)[0])
    length = int(str(fishid)[1])
    weight = int(str(fishid)[2])
    match type:
        case 1: # squid
            multiplier = 5
        case 2: # jellyfish
            multiplier = 0.5
        case 3: # shrimp
            multiplier = 1.5
        case 4: # lobster
            multiplier = 2
        case 5: # crab
            multiplier = 2.5
        case 6: # blowfish
            multiplier = 4
        case 7: # yellow fish
            multiplier = 1
        case 8: # blue fish
            multiplier = 1
        case 9: # shark
            multiplier = 8
        case _: # ???
            multiplier = 1
    return int(multiplier * (math.exp(length/4) + 2*weight))

def get_crate_value(crateid:int) -> int:
    if crateid == 4:
        return rand.randint(200, 400)
    if crateid == 5:
        return rand.randint(600, 1000)

def save_to_json(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)


def getRandInt() -> int:
    """Gets a random number from an exponential distribution"""
    return math.ceil(default_rng().exponential(40))
