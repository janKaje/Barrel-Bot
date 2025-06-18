import json
import math
import os
import random as rand
import re
import asyncio
from copy import deepcopy
import sys
from pickle import dumps as dpx

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(dir_path, "base"))

from checks import checks
from extra_exceptions import *
from item import Item
from player import Player
from barrelbot import time_str

async def setup(bot):
    await bot.add_cog(economy(bot))

    
with open(dir_path + "/data/trades.json") as file:
    trades = json.load(file)


DATA_CHANNEL_ID = 735631640939986964

PLAYER_DATA_MSG = 1363307787848912896

BARREL_COIN = "<:barrelcoin:1364027068936884405>"
BARREL_EMOJI = "<:barrel:1296987889942397001>"
HOLY_BARREL_EMOJI = "<:holybarrel:1303080132642209826>"

slots = {
    "7️⃣": [1000, 4000, 20000], #list is rewards for 3 in a row of low, med, high stakes
    "🍒": [500, 3000, 10000],
    "🍌": [300, 2000, 6000],
    "🍍": [400, 3000, 9000],
    "🥝": [300, 2000, 6000],
    "🍓": [300, 2000, 6000],
    "🔔": [1500, 5000, 30000],
    "🍫": [500, 2000, 9000],
    "🃏": [2000, 10000, 40000]
}

slotprices = [10, 50, 200]

rouletteslots = {'00': 'green', '0': 'green', '1': 'red', '2': 'black',
        '3': 'red', '4': 'black', '5': 'red', '6': 'black', '7': 'red',
        '8': 'black', '9': 'red', '10': 'black', '11': 'red',
        '12': 'black', '13': 'red', '14': 'black', '15': 'red',
        '16': 'black', '17': 'red', '18': 'black', '19': 'red',
        '20': 'black', '21': 'red', '22': 'black', '23': 'red',
        '24': 'black', '25': 'red', '26': 'black', '27': 'red',
        '28': 'black', '29': 'red', '30': 'black', '31': 'red',
        '32': 'black', '33': 'red', '34': 'black', '35': 'red',
        '36': 'black'}

cooldwn = commands.CooldownMapping.from_cooldown(3.0, 86400.0, commands.BucketType.user)

class economy(commands.Cog, name="Economy"):
    """Economy module"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    @commands.command()
    @commands.is_owner()
    async def saveeconomydata(self, ctx: commands.Context):
        await self.savealldata()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def geteconomydata(self, ctx: commands.Context):
        await self.bot_send(ctx, json.dumps(Player._playerdata, indent=2))
        await self.bot_send(ctx, json.dumps(trades))

    @commands.command()
    @checks.in_bb_channel()
    @commands.cooldown(1, 1800, commands.BucketType.user) # every 30 min
    async def work(self, ctx: commands.Context):
        f"""Every 30 minutes, you can work to earn {BARREL_COIN}."""
        player = Player(ctx.author)
        workresult = rand.randint(0, 99)
        if workresult < 2:
            coinsadd = rand.randint(5,15)
            try:
                player.give_coins(-coinsadd)
            except NotEnoughCoins:
                player.give_coins(-1*player.get_balance())
            await self.bot_send(ctx, ctx.author.mention + ", you somehow managed to completely screw up everything at the barrel factory and had to pay " + \
                           str(coinsadd) + BARREL_COIN + " in damages.")
        elif workresult < 20:
            coinsadd = rand.randint(10,15)
            player.give_coins(coinsadd)
            await self.bot_send(ctx, ctx.author.mention + ", you worked hard, but things weren't in your favor today. You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        elif workresult < 65:
            coinsadd = rand.randint(25, 30)
            player.give_coins(coinsadd)
            await self.bot_send(ctx, ctx.author.mention + ", you had a really normal and boring day at the barrel factory. You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        elif workresult < 85:
            coinsadd = rand.randint(30, 40)
            player.give_coins(coinsadd)
            await self.bot_send(ctx, ctx.author.mention + ", you made a new friend at work today! You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        elif workresult < 98:
            coinsadd = rand.randint(40, 50)
            player.give_coins(coinsadd)
            await self.bot_send(ctx, ctx.author.mention + ", you had a tough day but you powered through it! You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
        else:
            coinsadd = rand.randint(50, 75)
            player.give_coins(coinsadd)
            await self.bot_send(ctx, ctx.author.mention + ", you got a raise at work! You earned " + \
                           str(coinsadd) + BARREL_COIN + ".")
            
    @commands.command()
    @checks.in_bb_channel()
    async def shop(self, ctx: commands.Context, *, item:str=None):
        """See what's for sale. Use `bb shop <item>` to see the details of a particular item."""
        player = Player(ctx.author)
        embed = discord.Embed(color=discord.Color.gold())
        if item is None:
            embed.title = "Welcome to the BarrelBot Shop!"
            embed.description = "Type `bb shop <item>` to see more about an item, or `bb buy <item>` to buy it"
            for i in Item._shop_prices.keys():
                saleitem = Item(i)
                embed.add_field(name=saleitem.propername, value=f"{player.get_shop_price(saleitem)}{BARREL_COIN}")
        else:
            try:
                item:Item = Item.get_from_string(item)
                embed.title = item.propername
                embed.description = f"Cost: {player.get_shop_price(item)}{BARREL_COIN}\n{item.get_shop_description()}"
                embed.set_footer(text = f'Type "bb buy {item.easyalias}" to buy this item')
            except ItemNotFound:
                await self.bot_send(ctx, "Item not found.")
                return
            except Exception as e:
                print(e.with_traceback(None))
                await self.bot_send(ctx, "check logs")
                return
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @checks.in_bb_channel()
    async def buy(self, ctx:commands.Context, *, item:str):
        """Buy an item from the shop."""
        try:
            item:Item = Item.get_from_string(item)
        except ItemNotFound:
            await self.bot_send(ctx, "Item not found.")
            return
        player = Player(ctx.author)
        try:
            player.give_coins(-player.get_shop_price(item))
            player.add_to_inventory(item)
            await self.bot_send(ctx, item.get_shop_message() + " You now have `" + str(player.amount_in_inventory(item)) + "` of this item.")
            if item.id == 6:
                player.reset_lcr()
        except NotEnoughCoins:
            await self.bot_send(ctx, f"You don't have enough {BARREL_COIN}")
        return

    @commands.command()
    @checks.in_bb_channel()
    @checks.can_fish()
    @commands.cooldown(1, 600, commands.BucketType.user) # every 10 min
    async def fish(self, ctx:commands.Context):
        """Cast out your fishing line and see what you get! You can fish once every 5 minutes."""
        player = Player(ctx.author)
        norods = player.amount_in_inventory(1)
        nocasts = min(norods, 3)
        for _ in range(nocasts):
            outstr, fishid = fish_()
            if fishid != 0:
                player.add_to_inventory(fishid)
            await self.bot_send(ctx, outstr)
        
    @commands.command(aliases=["inv"])
    async def inventory(self, ctx:commands.Context, pageno=1):
        """Displays your personal inventory."""
        try:
            pageno = int(pageno)
        except:
            await self.bot_send(ctx, "Page number must be an integer.")
            return
        player = Player(ctx.author)
        invdisplay = player.get_inventory()
        invitems_ = list(set(invdisplay))
        invitems_.sort(key=lambda i: i.id)
        invitems = invitems_[(pageno-1)*25:pageno*25]
        nopages = 1 + (len(invitems_)-1)//25
        embed = discord.Embed(color=discord.Color.light_gray())
        embed.title = ctx.author.display_name + "'s Inventory"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value = "#" + str(i+1+(pageno-1)*25) + str("" if invdisplay.count(item)==1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages} - type `bb inventory <page>` to see a different page")
        await self.bot_send(ctx, embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx:commands.Context):
        f"""Displays how many {BARREL_COIN} you have."""
        player = Player(ctx.author)
        nocoins = player.get_whole_balance()
        inbank = player.get_bank_balance()
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = ctx.author.display_name + "'s " + BARREL_COIN + " balance"
        embed.description = str(nocoins) + BARREL_COIN
        if inbank != 0:
            embed.description += f"\n\n{nocoins-inbank}{BARREL_COIN} in wallet, {inbank}{BARREL_COIN} in bank"
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @checks.in_bb_channel()
    async def sellall(self, ctx:commands.Context):
        """Sells all of your fish."""
        player = Player(ctx.author)
        inventory = player.get_inventory()
        if len(inventory) == 0:
            await self.bot_send(ctx, "Your inventory is empty! You need to get fish before selling them.")
            return
        fishinv = []
        for item in inventory:
            if item.basetype == "fish":
                fishinv.append(item)
        if len(fishinv) == 0:
            await self.bot_send(ctx, "You don't have any fish to sell.")
            return
        nosold = 0
        saleprice = 0
        for fish in fishinv:
            nosold += 1
            saleprice += fish.get_sale_price()
            player.remove_from_inventory(fish)
        player.give_coins(saleprice)
        await self.bot_send(ctx, f"You sold {nosold} fish for a total of {saleprice}{BARREL_COIN}")

    @commands.command()
    async def openall(self, ctx:commands.Context):
        """Opens all of your crates."""
        player = Player(ctx.author)
        inventory = player.get_inventory()
        if len(inventory) == 0:
            await self.bot_send(ctx, "Your inventory is empty! You need to get crates before opening them.")
            return
        crateinv = []
        for item in inventory:
            if item.id in [4,5]:
                crateinv.append(item)
        if len(crateinv) == 0:
            await self.bot_send(ctx, "You don't have any crates to open.")
            return
        nosold = 0
        saleprice = 0
        for crate in crateinv:
            nosold += 1
            saleprice += crate.get_sale_price()
            player.remove_from_inventory(crate)
        player.give_coins(saleprice)
        await self.bot_send(ctx, f"You opened {nosold} crates and got a total of {saleprice}{BARREL_COIN}!")

    @commands.command(pass_context=True)
    async def gift(self, ctx:commands.Context, nocoins, *, user:discord.User):
        """Allows you to give someone else some coins. Example: `bb gift 50 @jan Kaje`"""
        nocoins = abs(int(nocoins))
        if user.bot:
            await self.bot_send(ctx, "You can't give bots money.")
            return
        giver = Player(ctx.author); receiver = Player(user)
        try:
            giver.give_coins(-nocoins)
        except NotEnoughCoins:
            await self.bot_send(ctx, "You don't have enough " + BARREL_COIN)
            return
        receiver.give_coins(nocoins)
        await self.bot_send(ctx, f"You've given {user.display_name} {nocoins}{BARREL_COIN}")

    @commands.command()
    async def baltop(self, ctx:commands.Context):
        """Shows the 10 people with the most money, as well as your own ranking."""
        balances = [[p, i["bal"], i["bank"]] for p, i in Player._playerdata.items()]
        balances.sort(key=lambda i: i[1]+i[2], reverse=True)
        users = [i[0] for i in balances]
        bals = [i[1] + i[2] for i in balances]
        inbank = [i[2] for i in balances]
        ranking = users.index(str(ctx.author.id))
        embed = discord.Embed(color=discord.Color.gold(), title="Top 10 moneys")
        valstr = ""
        for i in range(min(10, len(users))):
            valstr += str(i+1) + ") "
            valstr += (await self.bot.fetch_user(int(users[i]))).display_name
            valstr += " - " + str(bals[i]) + BARREL_COIN # + "\n"
            if inbank[i] != 0:
                valstr += f" - {inbank[i]} in bank"
            valstr += "\n"
        embed.description = valstr
        if ranking >= 10:
            embed.add_field(name="Your ranking:", value=str(ranking+1) + "/" + str(len(users)))
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @checks.in_bb_channel()
    async def display(self, ctx:commands.Context, item:str="recent"):
        """Moves an item to the display case. By default, moves your most recent acquisition to display. 
        You can specify a different item by its numerical place in your inventory (not zero-indexed)."""
        player = Player(ctx.author)
        if len(player.get_inventory()) == 0:
            await self.bot_send(ctx, "Your inventory is empty! You need to get items before putting them on display.")
            return
        if item.lower() == "recent":
            itemtomove = player.recent_in_inventory()
            player.move_to_display(itemtomove)
            await self.bot_send(ctx, f"Moved 1 {itemtomove.propername} to your display case.")
            return
        try:
            itemno = abs(int(item))
        except:
            await self.bot_send(ctx, "Invalid item number.")
            return
        try:
            itemtomove = player.get_item_from_invno(itemno)
            player.move_to_display(itemtomove)
            await self.bot_send(ctx, f"Moved 1 {itemtomove.propername} to your display case.")
        except Exception as e:
            await self.bot_send(ctx, "You don't have this item.")
            raise e

    @commands.command()
    @checks.in_bb_channel()
    async def takefromdisplay(self, ctx:commands.Context, item="recent"):
        """Moves an item from the display case to your inventory. By default, moves your most recent addition. 
        You can specify a different item by its numerical place in your display case (not zero-indexed)."""
        player = Player(ctx.author)
        if len(player.get_display()) == 0:
            await self.bot_send(ctx, "Your display case is empty!")
            return
        if item.lower() == "recent":
            itemtomove = player.recent_in_display()
            player.move_from_display(itemtomove)
            await self.bot_send(ctx, f"Moved 1 {itemtomove.propername} to your inventory.")
            return
        try:
            itemno = abs(int(item))
        except:
            await self.bot_send(ctx, "Invalid item number.")
            return
        try:
            itemtomove = player.get_item_from_dcno(itemno)
            player.move_from_display(itemtomove)
            await self.bot_send(ctx, f"Moved 1 {itemtomove.propername} to your inventory.")
        except:
            await self.bot_send(ctx, "You don't have this item.")

    @commands.command()
    async def displaycase(self, ctx:commands.Context, pageno=1):
        """Shows off your display case."""
        try:
            pageno = int(pageno)
        except:
            await self.bot_send(ctx, "Page number must be an integer.")
            return
        player = Player(ctx.author)
        invdisplay = player.get_display()
        invitems_ = list(set(invdisplay))
        invitems_.sort(key=lambda i: i.id)
        invitems = invitems_[(pageno-1)*25:pageno*25]
        nopages = 1 + (len(invitems_)-1)//25
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = ctx.author.display_name + "'s Display Case"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value = "#" + str(i+1+(pageno-1)*25) + str("" if invdisplay.count(item)==1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages} - type `bb displaycase <page>` to see a different page")
        await self.bot_send(ctx, embed=embed)

    @commands.command(pass_context=True)
    async def trade(self, ctx:commands.Context, keyword:str=None, item1:discord.User|str=None, item2:str=None, *, recipient:discord.User=None):
        """Allows you to trade with other players.
        
        `bb trade offer <offering> <requesting> <recipient>`
        -- offers <recipient> to trade <offering> for <requesting>
        `bb trade accept <recipient>`
        -- accepts <recipient>'s trade offer
        `bb trade view`
        -- shows your current trade offers, both outgoing and incoming
        `bb trade remove <recipient/offerer> <incoming/outgoing>`
        -- removes the given trade

        `<offering>` and `<requesting>` can be either money or an item. 
        -- For money, input an integer. 
        -- For an item, use the format "item<no>" with <no> being the number of the item as it appears in your or their inventory.

        `<recipient/offerer>` should be the user whose trade with you you want to remove, and `<incoming/outgoing>` should be either "incoming" or "outgoing" depending on which trade you want to remove. """

        match keyword:
            case "offer":

                if isinstance(item1, discord.User) or item1 is None or item2 is None:
                    await self.bot_send(ctx, "Invalid item offering syntax.")
                    return

                m1 = re.fullmatch(r"item(\d+)", item1)
                if m1 is None and not item1.isdecimal():
                    await self.bot_send(ctx, "Invalid item offering syntax.")
                    return
                if item1.isdecimal():
                    item1 = abs(int(item1))
                else:
                    item1 = m1.group(1)

                m2 = re.fullmatch(r"item(\d+)", item2)
                if m2 is None and not item2.isdecimal():
                    await self.bot_send(ctx, "Invalid item offering syntax.")
                    return
                if item2.isdecimal():
                    item2 = abs(int(item2))
                else:
                    item2 = m2.group(1)

                if recipient is None:
                    await self.bot_send(ctx, "Invalid receiving user syntax.")
                    return
                
                try:
                    await self.offer_trade(ctx.author.id, recipient.id, item1, item2)
                    offerer = Player(ctx.author); receiver = Player(recipient)
                    await self.bot_send(ctx, f"You offered to give {recipient.display_name} {'1 ' + str(offerer.get_item_from_invno(int(item1))) if isinstance(item1, str) else str(item1) + BARREL_COIN} " + \
                                   f"in exchange for {'1 ' + str(receiver.get_item_from_invno(int(item2))) if isinstance(item2, str) else str(item2) + BARREL_COIN}")
                except Exception as e:
                    await self.bot_send(ctx, str(e))
                    return
                
            case "accept":
                if not isinstance(item1, discord.User):
                    await self.bot_send(ctx, "Invalid offering user syntax.")
                    return
                try:
                    offered, received, frombanko, frombankr = await self.accept_trade(item1.id, ctx.author.id)
                    msg = f"Offer complete! You received {get_obj_str(offered)} "+\
                          f"and {item1.display_name} received {get_obj_str(received)}."
                    if frombanko != 0:
                        msg += f" {item1.display_name} withdrew {frombanko}{BARREL_COIN} in the process."
                    if frombankr != 0:
                        msg += f" You withdrew {frombankr}{BARREL_COIN} in the process."
                    await self.bot_send(ctx, msg)
                except Exception as e:
                    await self.bot_send(ctx, str(e))
                    return

            case "view":

                incoming, outgoing = await self.get_trades(ctx.author.id)
                embed = discord.Embed(color=discord.Color.light_gray(), title=f"Outstanding trade offers", description="")

                incoming_str = ""
                for trade in incoming:
                    offerer = self.bot.get_user(int(trade[0]))
                    incoming_str += f"From: {offerer.display_name}\n\tOffering: {get_obj_str(trade[2])}\n\tWants in return: {get_obj_str(trade[3])}\n"
                embed.add_field(name="__Incoming__", value=incoming_str)

                outgoing_str = ""
                for trade in outgoing:
                    recipient = self.bot.get_user(int(trade[1]))
                    outgoing_str += f"To: {recipient.display_name}\n\tOffering: {get_obj_str(trade[2])}\n\tIn return for: {get_obj_str(trade[3])}\n"
                embed.add_field(name="__Outgoing__", value=outgoing_str) 

                await self.bot_send(ctx, embed=embed)

            case "remove":
                if not isinstance(item1, discord.User):
                    await self.bot_send(ctx, "Invalid user syntax.")
                    return
                if not isinstance(item2, str):
                    await self.bot_send(ctx, "Invalid incoming/outgoing syntax.")
                if item2.lower() == "incoming":
                    try:
                        await self.remove_trade(item1.id, ctx.author.id)
                    except Exception as e:
                        await self.bot_send(ctx, e)
                        return
                elif item2.lower() == "outgoing":
                    try:
                        await self.remove_trade(ctx.author.id, item1.id)
                    except Exception as e:
                        await self.bot_send(ctx, e)
                        return
                else:
                    await self.bot_send(ctx, "You must specify incoming or outgoing.")
                    return
                await self.bot_send(ctx, f"Removed your trade with {item1.display_name}")


            case None:
                await self.bot_send(ctx, "Please input a keyword: offer, accept, view, or remove.")
                return

    @commands.command()
    @checks.in_bb_channel()
    async def sell(self, ctx:commands.Context, itemno:int, quantity:int=1):
        """Lets you sell items in your inventory. Items bought from the shop sell for up to 75% of the original price. Input the slot in your inventory that the item is in, and optionally a quantity (default 1)"""
        itemno = abs(int(itemno)); quantity = abs(int(quantity))
        player = Player(ctx.author)
        item = player.get_item_from_invno(itemno)
        qheld = player.amount_in_inventory(item)
        resaleprice = item.get_sale_price()
        if resaleprice is None:
            await self.bot_send(ctx, "No way to sell this item.")
            return
        if quantity > qheld:
            await self.bot_send(ctx, "You don't have that many of that item.")
            return
        moneyreceived = quantity*resaleprice
        for i in range(quantity):
            player.remove_from_inventory(item)
        player.give_coins(moneyreceived)
        await self.bot_send(ctx, f"You successfully sold {quantity} {item} for {moneyreceived}{BARREL_COIN}.")

    @commands.command()
    @checks.in_bb_channel()
    async def appraise(self, ctx:commands.Context, itemno:int):
        """Check how much your items will sell for before selling them."""
        itemno = abs(int(itemno))
        player = Player(ctx.author)
        item = player.get_item_from_invno(itemno)
        resaleprice = item.get_sale_price()
        if resaleprice is None:
            await self.bot_send(ctx, "No way to sell this item.")
            return
        await self.bot_send(ctx, f"Your {item} would sell for {resaleprice}{BARREL_COIN}")

    @commands.command()
    async def deposit(self, ctx:commands.Context, nocoins:int=0):
        """Allows you to deposit coins in the bank. By default, deposits your entire balance into the bank.
        Coins in the bank will no longer count towards your balance, but can be retrieved at any time.
        The bank is significantly more safe against robbery, although not completely."""
        player = Player(ctx.author)
        nocoins = abs(nocoins) # no negatives
        if nocoins == 0:
            bal = player.get_balance()
            player.deposit(bal)
            await self.bot_send(ctx, f"You deposited your entire balance - {bal}{BARREL_COIN} - into the bank.")
        else:
            try:
                player.deposit(nocoins)
                await self.bot_send(ctx, f"You deposited {nocoins}{BARREL_COIN} into the bank.")
            except NotEnoughCoins:
                await self.bot_send(ctx, f"You don't have that many coins.")

    @commands.command()
    async def withdraw(self, ctx:commands.Context, nocoins:int=0):
        """Allows you to withdraw coins from the bank. By default, withdraws your entire balance."""
        player = Player(ctx.author)
        nocoins = abs(nocoins) # no negatives
        if nocoins == 0:
            bal = player.get_bank_balance()
            player.withdraw(bal)
            await self.bot_send(ctx, f"You withdrew your entire balance - {bal}{BARREL_COIN} - from the bank.")
        else:
            try:
                player.withdraw(nocoins)
                await self.bot_send(ctx, f"You withdrew {nocoins}{BARREL_COIN} from the bank.")
            except NotEnoughCoins:
                await self.bot_send(ctx, f"You don't have that many coins.")

    @commands.command()
    @checks.in_bb_channel()
    async def bank(self, ctx:commands.Context):
        """Allows you to see your current bank account balance."""
        player = Player(ctx.author)
        bal = player.get_bank_balance()
        embed = discord.Embed(color=discord.Color.dark_red(),
                              title=f"{ctx.author.display_name}'s Bank Account",
                              description=f"{bal}{BARREL_COIN}") 
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @checks.in_bb_channel()
    @commands.cooldown(20, 86400, commands.BucketType.user)
    async def slots(self, ctx:commands.Context, *, stakes="low"):
        """Lets you play slots.
        You can specify either low, medium, or high stakes (default is low.)
        Low stakes slots costs 10, medium stakes costs 50, and high stakes costs 200"""
        player = Player(ctx.author)
        if stakes.lower() in ["1", "low", "lo", "low stakes"]:
            stakes = 0
            stakesmsg = "low"
        elif stakes.lower() in ["2", "medium", "med", "medium stakes"]:
            stakes = 1
            stakesmsg = "medium"
        elif stakes.lower() in ["3", "high", "hi", "high stakes"]:
            stakes = 2
            stakesmsg = "high"
        else:
            await self.bot_send(ctx, "Invalid stakes.")
            return
        try:
            player.give_coins(-slotprices[stakes])
        except NotEnoughCoins:
            await self.bot_send(ctx, f"You don't have enough coins to play {stakesmsg}-stakes slots! You need {slotprices[stakes]}")
            return
        msg = await ctx.send(f"Rolling a game of {stakesmsg}-stakes slots...\n\t🔹🔹🔹")
        outcome, winnings = slots_(stakes)
        async with ctx.typing():
            await asyncio.sleep(2)
            await msg.edit(content=f"Rolling a game of {stakesmsg}-stakes slots...\n\t{outcome[0]}🔹🔹")
            await asyncio.sleep(2)
            await msg.edit(content=f"Rolling a game of {stakesmsg}-stakes slots...\n\t{outcome[0]}{outcome[1]}🔹")
            await asyncio.sleep(2)
        if winnings == 0:
            await msg.edit(content=f"Rolling a game of {stakesmsg}-stakes slots...\n\t{outcome}\nBetter luck next time!")
        else:
            await msg.edit(content=f"Rolling a game of {stakesmsg}-stakes slots...\n\t{outcome}\nYou won {winnings}{BARREL_COIN}!")
            player.give_coins(ctx.author.id, winnings)
        return

    @commands.command()
    @checks.in_bb_channel()
    @commands.cooldown(20, 86400, commands.BucketType.user)
    async def roulette(self, ctx:commands.Context, bet, *, bet_type:str):
        """Lets you play American-style roulette. Bet an amount of money and choose what you want to bet on.
        Options for bet_type:
        * even/odd/red/black
        * first/second/third twelve
        * first/second eighteen
        * 1-2-3-0-00
        * list of one to six specific numbers (00, 0, 1-36)"""
        try:
            bet = abs(int(bet))
        except:
            await self.bot_send(ctx, "Invalid bet amount.")
            return
        player = Player(ctx.author)
        if bet > player.get_balance():
            await self.bot_send(ctx, "You don't have enough money.")
            return 
        
        # parse bet_type
        special_types = {
            "first twelve": 3,
            "second twelve": 4,
            "third twelve": 5,
            "first eighteen": 6,
            "second eighteen": 7,
            "1-2-3-0-00": 12
        }
        
        bet_vals = []

        if bet_type.lower() in special_types.keys():
            bettype = special_types[bet_type.lower()]
        elif bet_type.lower() in ["even", "odd", "red", "black"]:
            bettype = bet_type.lower()
        else:
            m = re.split("\s", bet_type)
            for i in m:
                if i != "":
                    try:
                        if not i in ["00"] + [str(i) for i in range(37)]:
                            await self.bot_send(ctx, "Invalid bet type.")
                            return
                        bet_vals.append(i)
                    except:
                        await self.bot_send(ctx, "Invalid bet type.")
                        return
            if len(bet_vals) == 0 or len(bet_vals) > 6:
                await self.bot_send(ctx, "Invalid bet type.")
                return
            bettype = len(bet_vals)+6
            if bettype == 7:
                bettype += 6
        
        result, payout = roulette_(bet, bettype, bet_vals)

        player.give_coins(payout)
        
        if payout < 0:
            await self.bot_send(ctx, f"The winning number is {result}. You lost {-payout}{BARREL_COIN}. Better luck next time!")
        else:
            await self.bot_send(ctx, f"The winning number is {result}. You won {payout}{BARREL_COIN}!")

    @commands.command(pass_context=True)
    @checks.in_bb_channel()
    @checks.can_rob()
    @checks.has_valid_user(r"(?<=rob ).*")
    @commands.cooldown(1, 3600, commands.BucketType.user) # every 60 min
    async def rob(self, ctx:commands.Context, *, victim:discord.User):
        """Attempts to rob the victim. You must have a dagger to rob people, and if they have a shield, your chances of success drop drastically."""
        perpetrator = Player(ctx.author); victim_player = Player(victim)
        opponent_has_shield = victim_player.has_in_inventory(3)
        luck_threshold = 80 if opponent_has_shield else 20
        luck = rand.randint(0, 99)
        richfactor = 1 + victim_player.get_balance()*0.001
        if luck < 2:
            perpetrator.remove_from_inventory(2)
            await self.bot_send(ctx, "While attempting to rob them, you tripped, fell, and broke your dagger. Serves you right...")
            return
        if luck > 97 and opponent_has_shield:
            victim_player.remove_from_inventory(3)
            coinsmoved = min(victim_player.get_balance(), int(richfactor*rand.randint(30, 60)))
            victim_player.give_coins(-coinsmoved)
            perpetrator.give_coins(coinsmoved)
            await self.bot_send(ctx, f"In trying to defend themselves, your victim's shield broke! You successfully stole {coinsmoved} from {victim.display_name}!")
            return
        if luck >= luck_threshold:
            coinsmoved = min(victim_player.get_balance(), int(richfactor*rand.randint(30, 60)))
            victim_player.give_coins(-coinsmoved)
            perpetrator.give_coins(coinsmoved)
            success_msg = rand.choice([
                f"You broke into {victim.display_name}'s house in the middle of the night and stole their jewelry.",
                f"You mugged {victim.display_name} on the side of the road as they were going to " + rand.choice([
                    "their grandma's funeral.", "the grocery store.", "their son's piano recital.", "work.", "their cousin's house.",
                    "a concert.", "eat lunch with their partner.", "the movie theater.", "visit their partner at work and bring them cookies.",
                    "the barrel factory."
                ]),
                f"You broke {victim.display_name}'s car window while they were shopping and took everything you could find.",
                f"You seduced {victim.display_name} and made away with their wallet in the middle of the night.",
                f"You sent {victim.display_name} a phishing email and somehow they fell for it.",
                f"You convinced {victim.display_name} to invest in your pump and dump crypto scheme.",
                f"You resold {BARREL_EMOJI} merch to {victim.display_name} for an exorbitantly high price.",
                f"You flirted with {victim.display_name} long enough to distract them while your partner cleaned out their safe."
            ])
            await self.bot_send(ctx, success_msg + f" You successfully stole {coinsmoved}{BARREL_COIN} from {victim.display_name}!")
            return
        coinsmoved = min(perpetrator.get_whole_balance(), rand.randint(5, 10))
        perpetrator.take_coins(coinsmoved, True)
        fail_msg = rand.choice([
            f"You tried to mug {victim.display_name} with your dagger, but they pulled a gun on you. Are those even legal here?",
            f"You got trapped inside {victim.display_name}'s house after breaking in, and the police caught you.",
            f"You successfully robbed {victim.display_name}, but while making a getaway, you slipped on a banana peel and everything fell out of your pockets.",
            f"Right after robbing {victim.display_name}, they robbed you right back.",
            f"You lied on your tax forms about your criminal activities, and the IRS found you out.",
            f"You stole {victim.display_name}'s wallet, but it only had expired coupons and a drawing of a cat.",
            f"You tried to scam {victim.display_name} online, but they reverse-hacked you and now own your crypto wallet.",
            f"You stole a priceless artifact from {victim.display_name}, but then dropped it into a sewer drain while taking a selfie.",
            f"You tried to mug {victim.display_name}, but instead they gave you life advice over a cup of tea. Now you're pursuing your passion and becoming a masseuse/masseur.",
            f"You followed {victim.display_name} home to rob them, but got lost and ended up at your ex's house. Awkward."
        ])
        await self.bot_send(ctx, fail_msg + f" You lost {coinsmoved}{BARREL_COIN}!")

    @commands.command()
    @checks.in_bb_channel()
    @checks.can_rob()
    @commands.cooldown(1, 21600, commands.BucketType.user) # every 6 hr
    async def bankrob(self, ctx:commands.Context):
        """Attempts to rob the bank. The chance of succeeding is very low (~1%), but with more daggers your luck increases to just low (at most ~5%).
        Amount gained upon successful robbery: 20-50% of the bank's holdings, distributed equally amongst all bank accounts.
        Cooldown is six hours."""
        player = Player(ctx.author)
        success_luck = rand.random()*100
        no_daggers = player.amount_in_inventory(2)
        chances = 5*(1-math.exp(-no_daggers/5))
        if chances > success_luck:
            # successfully rob bank
            percent_robbed = 0.2 + 0.3*rand.random()
            robbings = sum(Player.reduce_bank_holdings_by_percent(percent_robbed))
            player.give_coins(robbings)
            await self.bot_send(ctx, f"You successfully robbed the bank! You made away with {robbings}{BARREL_COIN}!")
        else:
            # failure
            coinsmoved = min(player.get_whole_balance(), rand.randint(10, 20))
            player.take_coins(coinsmoved, True)
            await self.bot_send(ctx, f"You failed! You lost {coinsmoved}{BARREL_COIN} in the attempt.")

    @commands.command()
    @checks.in_bb_channel()
    @checks.can_collect_rent()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def collectrent(self, ctx:commands.Context):
        """Collects rent for your houses. Rent is 500 coins per house per day."""
        player = Player(ctx.author)
        if player.amount_in_inventory(6) < 1:
            await self.bot_send(ctx, f"You don't have any property to collect rent on.")
            return
        nocoins, tpassed = player.collect_rent()
        if nocoins == 0:
            await self.bot_send(ctx, f"You don't have any rent to collect yet.")
        else:
            await self.bot_send(ctx, f"You collected {time_str(int(tpassed.total_seconds()))} of rent from your {player.amount_in_inventory(6)} houses. You gained {nocoins}{BARREL_COIN}")
        
    @commands.command(pass_context=True)
    @commands.is_owner()
    async def forcegivemoney(self, ctx:commands.Context, user:discord.User, nocoins:int):
        """Gives the specified user id a certain number of coins"""
        player = Player(user)
        player.give_coins(nocoins)
        await self.bot_send(ctx, "Done. They now have " + str(player.get_balance()) + BARREL_COIN)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def clearbalance(self, ctx:commands.Context, user:discord.User):
        """Clears the user's balance."""
        player = Player(user)
        player.give_coins(-1*player.get_balance())
        await self.bot_send(ctx, "Done!")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def forcegiveitem(self, ctx:commands.Context, user:discord.User, itemid:int):
        """Gives the specified user id an item"""
        player = Player(user)
        player.add_to_inventory(itemid)
        await self.bot_send(ctx, "Done!")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def forcetakeitem(self, ctx:commands.Context, user:discord.User, itemid:int):
        """Takes the specified item from the user"""
        player = Player(user)
        try:
            player.remove_from_inventory(itemid)
            await self.bot_send(ctx, "Done!")
        except NotInInventory:
            await self.bot_send(ctx, "Item not in their inventory.")

    @commands.command()
    async def total(self, ctx:commands.Context):
        """Shows the total amount of coins in circulation."""
        players = Player.get_all_players()
        total = 0
        
        for player in players:
            total += player.get_whole_balance()

        await self.bot_send(ctx, f"There are currently {total}{BARREL_COIN} in circulation.")

    @commands.command()
    @checks.in_bb_channel()
    @commands.cooldown(1, 600, commands.BucketType.user) # every 10 minutes
    async def fetchmeabeer(self, ctx:commands.Context):

        beerFetchMessages = {

            #success
            0: "Fine, here you go: 🍺",
            1: "Hmm, alright fine: 🍺",
            2: "... 🍺",
            3: "ugh, 🍺",
            4: "kk, 🍺",
            5: "can you ask more nicely next time? 🍺",

            #fail
            6: "Oh no! I accidentally dropped it on the way! Im so sorry.",
            7: "Nuh uh buddy, not today.",
            8: "I was thirsty and I drank it all, whoopsies.",
            9: "Oh no! I lost it! The falcon caught it midway and then there was this car and other.. things.. happened!",
            10: "I was bribed to not bring you the beer, sorry dude...",
        }

        player = Player(ctx.author)
        success = rand.randint(0, 1)

        if success == 1:
            msgID = rand.randint(0, 5)
            player.add_to_inventory(7)
        else:
            msgID = rand.randint(6, 10)
        
        await self.bot_send(ctx, beerFetchMessages[msgID])



    @commands.command(pass_context=True)
    @commands.is_owner()
    async def peekinv(self, ctx:commands.Context, user:discord.User, pageno:int=1):
        """Spies on the user's inventory."""
        invdisplay = Player(user).get_inventory()
        invitems_ = list(set(invdisplay))
        invitems_.sort(key=lambda i: i.id)
        invitems = invitems_[(pageno-1)*25:pageno*25]
        nopages = 1 + len(invitems_)//25
        embed = discord.Embed(color=discord.Color.light_gray())
        embed.title = user.display_name + "'s Inventory"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value = "#" + str(i+1+(pageno-1)*25) + str("" if invdisplay.count(item)==1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages}")
        await self.bot_send(ctx, embed=embed)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def clearinv(self, ctx:commands.Context, user:discord.User):
        """Clears the specified user's inventory."""
        player = Player(user)
        player.clear_inventory()
        await self.bot_send(ctx, "Done!")


    async def cog_load(self):

        # print loaded
        print(f"cog: {self.qualified_name} loaded")
        
        # start hourly loop
        self.hourlyloop.start()

    async def savealldata(self):
        """Saves data to file."""
        save_to_json(Player.get_json_data(), dir_path + "/data/playerdata.json")
        save_to_json(trades, dir_path + "/data/trades.json")

        print("economy data saved")

    @tasks.loop(hours=6)
    async def hourlyloop(self):
        await self.savealldata()
    
    async def offer_trade(self, offeruserid:int|str, recipuserid:int|str, itemoffer:int|str, itemrecip:int|str) -> bool:
        """itemoffer if item needs to be string with just item number"""
        global trades
        offeruserid = str(offeruserid)
        recipuserid = str(recipuserid)
        offeruser = Player((await self.bot.fetch_user(int(offeruserid))))
        recipuser = Player((await self.bot.fetch_user(int(recipuserid))))

        # lots of checks
        for trade in trades:
            if trade[0] == offeruserid and trade[1] == recipuserid:
                raise TooManyTrades("You can only have one trade offer to a person at a time.")
        if isinstance(itemoffer, int):
            if offeruser.get_whole_balance() < itemoffer:
                raise NotEnoughCoins("You don't have enough coins to offer.")
        else:
            try:
                itemoffer = str(offeruser.get_item_from_invno(int(itemoffer)).id)
            except NotInInventory:
                raise NotInInventory("You don't have this item.")
        if isinstance(itemrecip, int):
            if recipuser.get_whole_balance() < itemrecip:
                raise NotEnoughCoins("They don't have enough coins for this offer.")
        else:
            try:
                itemrecip = str(recipuser.get_item_from_invno(int(itemrecip)).id)
            except NotInInventory:
                raise NotInInventory("They don't have this item.")
            
        # add trade
        trades.append([offeruserid, recipuserid, itemoffer, itemrecip])

    async def accept_trade(self, offeruserid:int|str, recipuserid:int|str) -> tuple[int|str, int|str, int, int]:
        global trades
        offeruserid = str(offeruserid)
        recipuserid = str(recipuserid)
        offeruser = Player((await self.bot.fetch_user(int(offeruserid))))
        recipuser = Player((await self.bot.fetch_user(int(recipuserid))))
        idx = None
        
        for i in range(len(trades)):
            if trades[i][0] == offeruserid and trades[i][1] == recipuserid:
                idx = i
                itemoffer = trades[i][2]; itemrecip = trades[i][3]

                # lots of checks
                if isinstance(itemoffer, int):
                    if offeruser.get_balance() < itemoffer:
                        raise NotEnoughCoins("The offering party doesn't have enough coins.")
                else:
                    itemofferid = int(itemoffer)
                    if not offeruser.has_in_inventory(itemofferid):
                        raise NotInInventory("The offering party doesn't have this item anymore.")
                if isinstance(itemrecip, int):
                    if recipuser.get_balance() < itemrecip:
                        raise NotEnoughCoins("The receiving party doesn't have enough coins.")
                else:
                    itemrecipid = int(itemrecip)
                    if not recipuser.has_in_inventory(itemrecipid):
                        raise NotInInventory("The receiving party doesn't have this item anymore.")
                    
                # accept trade
                if isinstance(itemoffer, int):
                    _, frombanko = offeruser.take_coins(itemoffer, True)
                    recipuser.give_coins(itemoffer)
                else:
                    itemofferid = int(itemoffer)
                    frombanko = 0
                    offeruser.remove_from_inventory(itemofferid)
                    recipuser.add_to_inventory(itemofferid)
                if isinstance(itemrecip, int):
                    _, frombankr = recipuser.take_coins(itemrecip, True)
                    offeruser.give_coins(itemrecip)
                else:
                    itemrecipid = int(itemrecip)
                    frombankr = 0
                    recipuser.remove_from_inventory(itemrecipid)
                    offeruser.add_to_inventory(itemrecipid)
                
                break
        
        if idx is None:
            raise TradeNotFound("Trade not found")
        
        trades.pop(idx)
        return itemoffer, itemrecip, frombanko, frombankr

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

    @sell.error
    async def qwlkeh(self, awr, kf):
        if not isinstance(kf, (commands.BadArgument, commands.MissingRequiredArgument, commands.TooManyArguments)):
            return
        xzc = re.search(r"(?<=sell).*", awr.message.content).group(0); alh = awr.message.attachments
        if len(alh) > 0:
            lq = hash(tuple(alh)); r = rand.getstate(); rand.seed(lq); vh = math.exp(0b11*rand.random())*rand.randint(1, 0xA); rand.setstate(r)
        else:
            vh = 0x0
        if len(xzc) > 0x71:
            r = rand.getstate(); rand.seed(xzc); ly = math.exp(0b10*rand.random())*rand.randint(1, 0b111); rand.setstate(r)
        else:
            ly = 0b0
        if ly >= 0.0 and vh <= int(math.exp(-(ly+2)*0xCB)) and ly == vh:
            return
        b2p = cooldwn.get_bucket(awr.message)
        if b2p.update_rate_limit():
            await awr.send("Now, now, I can only buy so much from you in a day! Give it a rest until tomorrow.")
            return
        jcxis = (1-math.exp(-4*rand.random())); yt2 = Player(awr.author); xle = max(1, int(jcxis*(vh+ly)))
        if jcxis <= 0.5:
            p2u93 = str(f"Well, these aren't the best, but they're worth something. I'll give you {xle}{BARREL_COIN} for the lot." if vh > 0 and ly > 0 else str(f"Really? Fine, I'll take it for {xle}{BARREL_COIN}." if ly > 0 else f"Eh, I've seen better. But it'll do. Here's {xle}{BARREL_COIN}."))
        else:
            p2u93 = str(f"What incredible offerings you've brought me today. I'll give you {xle}{BARREL_COIN} for them." if vh > 0 and ly > 0 else str(f"That's gorgeous! I'll take it off your hands for {xle}{BARREL_COIN}." if vh > 0 else f"Not bad. I'll take it for {xle}{BARREL_COIN}."))
        yt2.give_coins(xle)
        await awr.send(p2u93)    
        return     


def get_obj_str(id:int|str):
    return str(Item(int(id))) if isinstance(id, str) else str(id) + BARREL_COIN
        
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
        length = int(math.floor(subluck/30*rand.random()))
        weight = int(math.floor(subluck/30*rand.random()))
        outstr = f"You caught a 🐟! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("8" + str(length) + str(weight))
    if luck < 700:
        subluck = luck - 499
        length = int(math.floor(subluck/20*rand.random()))
        weight = int(math.floor(subluck/20*rand.random()))
        outstr = f"You caught a 🐠! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("7" + str(length) + str(weight))
    if luck < 800:
        subluck = luck - 699
        length = int(math.floor(subluck/10*rand.random()))
        weight = int(math.floor(subluck/10*rand.random()))
        outstr = f"You caught a 🦐! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("3" + str(length) + str(weight))
    if luck < 850:
        subluck = luck - 799
        length = int(math.floor(subluck/5*rand.random()))
        weight = int(math.floor(subluck/5*rand.random()))
        outstr = f"You caught a 🦞! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("4" + str(length) + str(weight))
    if luck < 900:
        subluck = luck - 849
        length = int(math.floor(subluck/5*rand.random()))
        weight = int(math.floor(subluck/5*rand.random()))
        outstr = f"You caught a 🦀! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("5" + str(length) + str(weight))
    if luck < 940:
        subluck = luck - 899
        length = int(math.floor(subluck/4*rand.random()))
        weight = int(math.floor(subluck/4*rand.random()))
        outstr = f"You caught a 🪼! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("2" + str(length) + str(weight))
    if luck < 960:
        subluck = luck - 939
        length = int(math.floor(subluck/2*rand.random()))
        weight = int(math.floor(subluck/2*rand.random()))
        outstr = f"You caught a 🐡! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("6" + str(length) + str(weight))
    if luck < 980:
        subluck = luck - 959
        length = int(math.floor(subluck/2*rand.random()))
        weight = int(math.floor(subluck/2*rand.random()))
        outstr = f"You caught a 🦑! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("1" + str(length) + str(weight))
    if luck < 990:
        subluck = luck - 979
        length = int(math.floor(subluck*rand.random()))
        weight = int(math.floor(subluck*rand.random()))
        outstr = f"You caught a 🦈! It weighs {(weight+1)*0.5} kg and is {(length+1)*5} cm long."
        return outstr, int("9" + str(length) + str(weight))
    if luck < 999:
        outstr = "You caught a " + BARREL_EMOJI + "! Open it to see what's inside!"
        return outstr, 4
    else:
        outstr = "Wow! You caught a " + HOLY_BARREL_EMOJI + "! Open it to see what's inside!"
        return outstr, 5

    
def slots_(stage:int) -> int:
    choices = [rand.choice(list(slots.keys())) for _ in range(3)]
    if choices[0] == choices[1] and choices[0] == choices[2]:
        return "".join(choices), slots[choices[0]][stage]
    return "".join(choices), 0

def roulette_(bet, bet_type, bet_val:list[str]=[]) -> tuple[int, int]:
    result = rand.choice(list(rouletteslots.keys()))
    payout = -bet

    # Adjust player balance for even/odd bets.
    if bet_type == "even":  # Even
        if (int(result) % 2 == 0) and (int(result) != 0):
            payout += 2 * bet
    if bet_type == "odd":  # Odd
        if int(result) % 2 == 1:
            payout += 2 * bet
    # Adjust player balance for red/black bets.
    if bet_type == "red":  # Red
        if rouletteslots[result] == 'red':
            payout += 2 * bet
    if bet_type == "black":  # Black
        if rouletteslots[result] == 'black':
            payout += 2 * bet
    # Adjust player balance for the set of twelves.k
    if bet_type == 3:  # First Twelve
        if (int(result) >= 1) and (int(result) <= 12):
            payout += 3 * bet
    if bet_type == 4:  # Second Twelve
        if (int(result) >= 13) and (int(result) <= 24):
            payout += 3 * bet
    if bet_type == 5:  # Third Twelve
        if (int(result) >= 25) and (int(result) <= 36):
            payout += 3 * bet
    # Adjust the player balance for the first and second set of eighteen.
    if bet_type == 6:  # First Eighteen
        if (int(result) >= 1) and (int(result) <= 18):
            payout += 2 * bet
    if bet_type == 7:  # Second Eighteen
        if (int(result) >= 19) and (int(result) <= 36):
            payout += 2 * bet
    # Adjust for betting multiple numbers at the same time.
    if bet_type == 8:  # Combination of two numbers
        if result in bet_val:
            payout += 18 * bet
    if bet_type == 9:  # Combination of three numbers
        if result in bet_val:
            payout += 12 * bet
    if bet_type == 10:  # Combination of four numbers
        if result in bet_val:
            payout += 9 * bet
    if bet_type == 11:  # Combination of six numbers
        if result in bet_val:
            payout += 6 * bet
    if bet_type == 12:  # Combination of 00-0-1-2-3
        if result in bet_val:
            payout += 7 * bet
    # Adjust player balance if bet a single number.
    if bet_type == 13:
        if result == bet_val:
            payout += 36 * bet

    return result, payout




def save_to_json(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "w") as file:
        json.dump(data, file)


def main():
    
    pass

if __name__ == "__main__":
    main()