import json
import math
import os
import random as rand
import re
import asyncio
from copy import deepcopy

import discord
from discord.ext import commands, tasks

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
#   10000s?
# Tech:
#   10000s (find good storage method)


async def setup(bot):
    await bot.add_cog(economy(bot))


with open(dir_path + "/data/barrelcoins.json") as file:
    barrelcoins = json.load(file)
    
with open(dir_path + "/data/inventories.json") as file:
    inventories = json.load(file)
    
with open(dir_path + "/data/displaycase.json") as file:
    displaycases = json.load(file)
    
with open(dir_path + "/data/trades.json") as file:
    trades = json.load(file)


DATA_CHANNEL_ID = 735631640939986964

BARREL_COIN_DATA_MSG = 1363307787848912896
INVENTORY_MSG = 1363370297121705985
DISPLAYCASE_MSG = 1364315745563054143

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

class NotAbleToFish(commands.CheckFailure):
    pass

class NotEnoughCoins(Exception):
    pass

class TooManyTrades(Exception):
    pass

class NotInInventory(Exception):
    pass

class NotInDisplayCase(Exception):
    pass

class TradeNotFound(Exception):
    pass

# def can_fish() -> bool:
#     # no clue if this is going to work.... but we'll try

#     @commands.cooldown(1, 300, commands.BucketType.user)
#     async def predicate(ctx:commands.Context):
#         userid = str(ctx.author.id)
#         if userid in inventories.keys():
#             if 1 not in inventories[userid]:
#                 raise NotAbleToFish("You need to buy a fishing rod first!")
#         else:
#             raise NotAbleToFish("You need to buy a fishing rod first!")
        
#         return True
            
#     return commands.check(predicate)

class economy(commands.Cog, name="Economy"):
    """Economy module"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def saveeconomydata(self, ctx: commands.Context):
        await self.savealldata()
        await ctx.send("Done!")

    @commands.command()
    @commands.is_owner()
    async def geteconomydata(self, ctx: commands.Context):
        await ctx.send(json.dumps(barrelcoins))
        await ctx.send(json.dumps(inventories))
        await ctx.send(json.dumps(displaycases))
        await ctx.send(json.dumps(trades))

    @commands.command()
    @commands.cooldown(1, 1800, commands.BucketType.user) # every 30 min
    async def work(self, ctx: commands.Context):
        f"""Every 30 minutes, you can work to earn {BARREL_COIN}."""
        workresult = rand.randint(0, 99)
        if workresult < 3:
            coinsadd = rand.randint(5,15)
            try:
                await self.give_coins(ctx.author.id, -coinsadd)
            except NotEnoughCoins:
                await self.give_coins(ctx.author.id, -1*(await self.get_coins(ctx.author.id)))
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
            embed.add_field(name="🎣 - Fishing Rod", value=str(prices[1])+BARREL_COIN)
            embed.add_field(name="🗡️ - Dagger", value=str(prices[2])+BARREL_COIN)
        elif item.lower() in aliases[1]:
            embed.title = "🎣 - Fishing Rod"
            embed.description = "Cost: " + str(prices[1]) + BARREL_COIN + "\nAllows you to use the command `fish`. Collect fish to keep as trophies or sell for more " + BARREL_COIN
            embed.set_footer(text="Type `bb buy fishing rod` to buy this item")
        # elif item.lower() in aliases[2]:
        #     embed.title = "🗡️ - Dagger"
        #     embed.description = "Cost: " + str(prices[2]) + BARREL_COIN + "\nAllows you to try to rob other people."
        #     embed.set_footer(text="Type `bb buy fishing rod` to buy this item")
        # elif item.lower() in aliases[3]:
        #     embed.title = "🛡️ - Shield"
        #     embed.description = "Cost: " + str(prices[3]) + BARREL_COIN + "\nDoes a good job of blocking you from getting robbed."
        #     embed.set_footer(text="Type `bb buy fishing rod` to buy this item")
        else:
            embed.title = "Item not found."
            embed.description = ""
        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx:commands.Context, *, item:str):
        """Buy an item from the shop."""
        if item.lower() == "fishing rod":
            try:
                await self.give_coins(ctx.author.id, -100)
            except NotEnoughCoins:
                await ctx.send(f"You don't have enough {BARREL_COIN}!")
                return
            await self.add_to_inventory(ctx.author.id, 1)
            await ctx.send("You bought a 🎣! If you didn't have one before, now you can do `bb fish`. You now have " + str(inventories[str(ctx.author.id)].count(1)) + " of this item.")            
        else:
            await ctx.send("Item not found.")

    @commands.command()
    @commands.cooldown(1, 600, commands.BucketType.user) # every 10 min
    async def fish(self, ctx:commands.Context):
        """Cast out your fishing line and see what you get! You can fish once every 5 minutes."""
        if not await self.has_in_inventory(ctx.author.id, 1):
            await ctx.send("You need to buy a fishing rod first!")
            return
        norods = await self.amount_in_inventory(ctx.author.id, 1)
        nocasts = min(norods, 3)
        for _ in range(nocasts):
            outstr, fishid = fish_()
            if fishid != 0:
                await self.add_to_inventory(ctx.author.id, fishid)
            await ctx.send(outstr)
        
    @commands.command(aliases=["inv"])
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
        for i, item in enumerate(invitems):
            embed.add_field(name=get_item_str(item), value = "#" + str(i+1+(pageno-1)*25) + str("" if invdisplay.count(item)==1 else " - Count: " + str(invdisplay.count(item))))
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
    async def gift(self, ctx:commands.Context, nocoins, *, user:discord.User):
        """Allows you to give someone else some coins. Example: `bb gift 50 @jan Kaje`"""
        nocoins = abs(int(nocoins))
        if user.bot:
            await ctx.send("You can't give bots money.")
            return
        try:
            await self.give_coins(ctx.author.id, -nocoins)
        except NotEnoughCoins:
            await ctx.send("You don't have enough " + BARREL_COIN)
            return
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

    @commands.command()
    async def display(self, ctx:commands.Context, item="recent"):
        """Moves an item to the display case. By default, moves your most recent acquisition to display. 
        You can specify a different item by its numerical place in your inventory (not zero-indexed)."""
        authorid = str(ctx.author.id)
        if authorid not in inventories.keys() or len(inventories[authorid]) == 0:
            await ctx.send("Your inventory is empty! You need to get items before putting them on display.")
            return
        if item.lower() == "recent":
            itemtomove = inventories[authorid][-1]
            await self.move_to_display(authorid, itemtomove)
            await ctx.send(f"Moved 1 {get_item_str(itemtomove)} to your display case.")
            return
        try:
            itemno = abs(int(item))
        except:
            await ctx.send("Invalid item number.")
            return
        try:
            itemid = await self.get_id_from_inventory_number(authorid, itemno)
            await self.move_to_display(authorid, itemid)
            await ctx.send(f"Moved 1 {get_item_str(itemid)} to your display case.")
        except:
            await ctx.send("You don't have this item.")

    @commands.command()
    async def takefromdisplay(self, ctx:commands.Context, item="recent"):
        """Moves an item from the display case to your inventory. By default, moves your most recent addition. 
        You can specify a different item by its numerical place in your display case (not zero-indexed)."""
        authorid = str(ctx.author.id)
        if authorid not in displaycases.keys() or len(displaycases[authorid]) == 0:
            await ctx.send("Your display case is empty!")
            return
        if item.lower() == "recent":
            itemtomove = displaycases[authorid][-1]
            await self.move_from_display(authorid, itemtomove)
            await ctx.send(f"Moved 1 {get_item_str(itemtomove)} to your inventory.")
            return
        try:
            itemno = abs(int(item))-1
        except:
            await ctx.send("Invalid item number.")
            return
        invitems = list(set(displaycases[authorid]))
        invitems.sort()
        
        try:
            itemid = invitems[itemno]
            await self.move_from_display(authorid, itemid)
            await ctx.send(f"Moved 1 {get_item_str(itemid)} to your inventory.")
        except:
            await ctx.send("You don't have this item.")

    @commands.command()
    async def displaycase(self, ctx:commands.Context, pageno=1):
        """Shows off your display case."""
        try:
            pageno = int(pageno)
        except:
            await ctx.send("Page number must be an integer.")
            return
        if str(ctx.author.id) not in displaycases.keys():
            invdisplay = []
        else:
            invdisplay = deepcopy(displaycases[str(ctx.author.id)])
            invdisplay.sort()
        invitems_ = list(set(invdisplay))
        invitems_.sort()
        invitems = invitems_[(pageno-1)*25:pageno*25]
        nopages = 1 + len(invitems_)//25
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = ctx.author.display_name + "'s Display Case"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=get_item_str(item), value = "#" + str(i+1+(pageno-1)*25) + str("" if invdisplay.count(item)==1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages} - type `bb displaycase <page>` to see a different page")
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def trade(self, ctx:commands.Context, keyword:str=None, item1:discord.User|str=None, item2:str=None, *, recipient:discord.User=None):
        """Allows you to trade with other players.
        `bb trade offer <offering> <requesting> <recipient>` - offers <recipient> to trade <offering> for <requesting>
        `bb trade accept <recipient>` - accepts <recipient>'s trade offer
        `bb trade view` - shows your current trade offers, both outgoing and incoming
        `bb trade remove <recipient/offerer> <incoming/outgoing>` - removes the given trade.
        `<offering>` and `<requesting>` can be either money or an item. For money, input an integer. 
        For an item, use the format "item<no>" with <no> being the number of the item as it appears in your or their inventory (not zero-indexed.)
        `<recipient/offerer>` should be the user whose trade with you you want to remove, and `<incoming/outgoing>` should be either "incoming" or "outgoing" depending on which trade you want to remove. """

        match keyword:
            case "offer":

                if isinstance(item1, discord.User) or item1 is None or item2 is None:
                    await ctx.send("Invalid item offering syntax.")
                    return

                m1 = re.fullmatch(r"item(\d+)", item1)
                if m1 is None and not item1.isdecimal():
                    await ctx.send("Invalid item offering syntax.")
                    return
                if item1.isdecimal():
                    item1 = abs(int(item1))
                else:
                    item1 = m1.group(1)

                m2 = re.fullmatch(r"item(\d+)", item2)
                if m2 is None and not item2.isdecimal():
                    await ctx.send("Invalid item offering syntax.")
                    return
                if item2.isdecimal():
                    item2 = abs(int(item2))
                else:
                    item2 = m2.group(1)

                if recipient is None:
                    await ctx.send("Invalid receiving user syntax.")
                    return
                
                try:
                    await self.offer_trade(ctx.author.id, recipient.id, item1, item2)
                    await ctx.send(f"You offered to give {recipient.display_name} {'1 ' + get_item_str(await self.get_id_from_inventory_number(ctx.author.id, int(item1))) if isinstance(item1, str) else str(item1) + BARREL_COIN} " + \
                                   f"in exchange for {'1 ' + get_item_str(await self.get_id_from_inventory_number(recipient.id, int(item2))) if isinstance(item2, str) else str(item2) + BARREL_COIN}")
                except Exception as e:
                    await ctx.send(e)
                    return
                
            case "accept":
                if not isinstance(item1, discord.User):
                    await ctx.send("Invalid offering user syntax.")
                    return
                try:
                    offered, received = await self.accept_trade(item1.id, ctx.author.id)
                    await ctx.send(f"Offer complete! You received {get_obj_str(offered)} and {item1.display_name} received {get_obj_str(received)}")
                except Exception as e:
                    await ctx.send(e)
                    return

            case "view":

                incoming, outgoing = await self.get_trades(ctx.author.id)
                embed = discord.Embed(color=discord.Color.light_gray(), title=f"Outstanding trade offers", description="")

                incoming_str = ""
                for trade in incoming:
                    offerer = self.bot.get_user(int(trade[0]))
                    incoming_str += f"From: {offerer.display_name} \t Offering: {get_obj_str(trade[2])} \t Wants in return: {get_obj_str(trade[3])}\n"
                embed.add_field(name="__Incoming__", value=incoming_str)

                outgoing_str = ""
                for trade in outgoing:
                    recipient = self.bot.get_user(int(trade[1]))
                    outgoing_str += f"To: {recipient.display_name} \t Offering: {get_obj_str(trade[2])} \t In return for: {get_obj_str(trade[3])}"
                embed.add_field(name="__Outgoing__", value=outgoing_str) 

                await ctx.send(embed=embed)

            case "remove":
                if not isinstance(item1, discord.User):
                    await ctx.send("Invalid user syntax.")
                    return
                if item2.lower() == "incoming":
                    try:
                        await self.remove_trade(item1.id, ctx.author.id)
                    except Exception as e:
                        await ctx.send(e)
                        return
                elif item2.lower() == "outgoing":
                    try:
                        await self.remove_trade(ctx.author.id, item1.id)
                    except Exception as e:
                        await ctx.send(e)
                        return
                else:
                    await ctx.send("You must specify incoming or outgoing.")
                    return
                await ctx.send(f"Removed your trade with {item1.display_name}")


            case None:
                await ctx.send("Please input a keyword: offer, accept, view, or remove.")
                return

    @commands.command()
    async def sell(self, ctx:commands.Context, itemno:int, quantity:int=1):
        """Lets you sell items in your inventory. Items bought from the shop sell for up to 75% of the original price. Input the slot in your inventory that the item is in, and optionally a quantity (default 1)"""
        itemno = abs(int(itemno)); quantity = abs(int(quantity))
        itemid, qheld = await self.get_id_from_inventory_number(ctx.author.id, itemno, True)
        if itemid < 100:
            try:
                resaleprice = int(math.floor(prices[itemid]*0.75))
            except KeyError:
                await ctx.send("No known price for this item.")
                return
        elif itemid < 1000:
            resaleprice = get_fish_value(itemid)
        else:
            await ctx.send("No known price for this item.")
            return
        if quantity > qheld:
            await ctx.send("You don't have that many of that item.")
            return
        moneyreceived = quantity*resaleprice
        for i in range(quantity):
            await self.remove_from_inventory(ctx.author.id, itemid)
        await self.give_coins(ctx.author.id, moneyreceived)
        await ctx.send(f"You successfully sold {quantity} {get_item_str(itemid)} for {moneyreceived}{BARREL_COIN}.")
        

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
        self.coinmsg = await self.datachannel.fetch_message(BARREL_COIN_DATA_MSG)
        self.invmsg = await self.datachannel.fetch_message(INVENTORY_MSG)
        self.displaymsg = await self.datachannel.fetch_message(DISPLAYCASE_MSG)

    async def savealldata(self):
        """Saves data to file."""
        save_to_json(barrelcoins, dir_path + "/data/barrelcoins.json")
        save_to_json(inventories, dir_path + "/data/inventories.json")
        save_to_json(displaycases, dir_path + "/data/displaycase.json")
        save_to_json(trades, dir_path + "/data/trades.json")

        await self.coinmsg.edit(content=json.dumps(barrelcoins))
        await asyncio.sleep(1)
        await self.invmsg.edit(content=json.dumps(inventories))
        await asyncio.sleep(1)
        await self.displaymsg.edit(content=json.dumps(displaycases))

        print("economy data saved")

    @tasks.loop(hours=1)
    async def hourlyloop(self):
        await self.savealldata()

    async def give_coins(self, userid:int, nocoins:int):
        global barrelcoins
        userid = str(userid)
        if userid in barrelcoins.keys():
            if nocoins + barrelcoins[userid] < 0:
                raise NotEnoughCoins("Not enough coins to remove.")
            barrelcoins[userid] += nocoins
        else:
            if nocoins < 0:
                raise NotEnoughCoins("Not enough coins to remove.")
            barrelcoins[userid] = nocoins
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
    
    async def remove_from_inventory(self, userid:int, itemid:int):
        userid = str(userid)
        global inventories
        if userid in inventories.keys():
            if itemid in inventories[userid]:
                inventories[userid].remove(itemid)
                return
        raise NotInInventory("Not in inventory")
    
    async def has_in_inventory(self, userid:int|str, itemid:int) -> bool:
        userid = str(userid)
        if userid in inventories.keys():
            if itemid in inventories[userid]:
                return True
        return False
    
    async def amount_in_inventory(self, userid:int|str, itemid:int) -> int:
        userid = str(userid)
        if not await self.has_in_inventory(userid, itemid):
            return 0
        return inventories[userid].count(itemid)
    
    async def move_to_display(self, userid:int|str, itemid:int):
        userid = str(userid)
        await self.remove_from_inventory(userid, itemid)
        if userid in displaycases.keys():
            displaycases[userid].append(itemid)
        else:
            displaycases[userid] = [itemid]
    
    async def move_from_display(self, userid:int|str, itemid:int) -> bool:
        userid = str(userid)
        if userid in displaycases.keys():
            if itemid in displaycases[userid]:
                displaycases[userid].remove(itemid)
                await self.add_to_inventory(userid, itemid)
                return
        raise NotInDisplayCase("Not in display case")
    
    async def get_id_from_inventory_number(self, userid:int|str, itemno:int, include_quantity:bool=False) -> int|tuple[int, int]:
        """Not zero indexed."""
        userid = str(userid)
        if userid not in inventories.keys():
            raise NotInInventory("Not in inventory")
        invitems = list(set(inventories[userid]))
        invitems.sort()
        try:
            itemid = invitems[itemno-1]
        except IndexError:
            raise NotInInventory("Not in inventory")
        if include_quantity == True:
            return itemid, inventories[userid].count(itemid)
        return itemid
    
    async def offer_trade(self, offeruserid:int|str, recipuserid:int|str, itemoffer:int|str, itemrecip:int|str) -> bool:
        """itemoffer if item needs to be string with just item number"""
        global trades
        offeruserid = str(offeruserid)
        recipuserid = str(recipuserid)

        # lots of checks
        for trade in trades:
            if trade[0] == offeruserid and trade[1] == recipuserid:
                raise TooManyTrades("You can only have one trade offer to a person at a time.")
        if isinstance(itemoffer, int):
            if await self.get_coins(offeruserid) < itemoffer:
                raise NotEnoughCoins("You don't have enough coins to offer.")
        else:
            try:
                itemoffer = str(await self.get_id_from_inventory_number(offeruserid, int(itemoffer)))
            except NotInInventory:
                raise NotInInventory("You don't have this item.")
        if isinstance(itemrecip, int):
            if await self.get_coins(recipuserid) < itemrecip:
                raise NotEnoughCoins("They don't have enough coins for this offer.")
        else:
            try:
                itemrecip = str(await self.get_id_from_inventory_number(recipuserid, int(itemrecip)))
            except NotInInventory:
                raise NotInInventory("They don't have this item.")
            
        # add trade
        trades.append([offeruserid, recipuserid, itemoffer, itemrecip])

    async def accept_trade(self, offeruserid:int|str, recipuserid:int|str) -> tuple[int|str, int|str]:
        global trades
        offeruserid = str(offeruserid)
        recipuserid = str(recipuserid)
        idx = None
        
        for i in range(len(trades)):
            if trades[i][0] == offeruserid and trades[i][1] == recipuserid:
                idx = i
                itemoffer = trades[i][2]; itemrecip = trades[i][3]

                # lots of checks
                if isinstance(itemoffer, int):
                    if await self.get_coins(offeruserid) < itemoffer:
                        raise NotEnoughCoins("The offering party doesn't have enough coins.")
                else:
                    itemofferid = int(itemoffer)
                    if not await self.has_in_inventory(offeruserid, itemofferid):
                        raise NotInInventory("The offering party doesn't have this item anymore.")
                if isinstance(itemrecip, int):
                    if await self.get_coins(recipuserid) < itemrecip:
                        raise NotEnoughCoins("The receiving party doesn't have enough coins.")
                else:
                    itemrecipid = int(itemrecip)
                    if not await self.has_in_inventory(recipuserid, itemrecipid):
                        raise NotInInventory("The receiving party doesn't have this item anymore.")
                    
                # accept trade
                if isinstance(itemoffer, int):
                    await self.give_coins(offeruserid, -itemoffer)
                    await self.give_coins(recipuserid, itemoffer)
                else:
                    itemofferid = int(itemoffer)
                    await self.remove_from_inventory(offeruserid, itemofferid)
                    await self.add_to_inventory(recipuserid, itemofferid)
                if isinstance(itemrecip, int):
                    await self.give_coins(recipuserid, -itemrecip)
                    await self.give_coins(offeruserid, itemrecip)
                else:
                    itemrecipid = int(itemrecip)
                    await self.remove_from_inventory(recipuserid, itemrecipid)
                    await self.add_to_inventory(offeruserid, itemrecipid)
                
                break
        
        if idx is None:
            raise TradeNotFound("Trade not found")
        
        trades.pop(idx)
        return itemoffer, itemrecip

    async def get_trades(self, userid:int|str):
        userid = str(userid)
        outgoing = []; incoming = []
        for trade in trades:
            if trade[0] == userid:
                outgoing.append(trade)
        for trade in trades:
            if trade[1] == userid:
                incoming.append(trade)
        return incoming, outgoing
    
    async def remove_trade(self, offeruserid:int|str, recipuserid:int|str):
        global trades
        offeruserid = str(offeruserid)
        recipuserid = str(recipuserid)
        idx = None
        
        for i in range(len(trades)):
            if trades[i][0] == offeruserid and trades[i][1] == recipuserid:
                idx = i
                break
        
        if idx is None:
            raise TradeNotFound("Trade not found")
        
        trades.pop(idx)


def get_obj_str(id:int|str):
    if isinstance(id, int):
        return str(id) + BARREL_COIN
    return get_item_str(int(id))
        
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