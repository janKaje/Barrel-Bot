import json
import math
import os
import random as rand
import re
import asyncio
import sys
import time
from pickle import dumps as dpx
from PIL import Image, ImageDraw
from io import BytesIO

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(dir_path, "base"))

import env
from emojis import EmojiDefs as ED
from checks import Checks
from extra_exceptions import *
from item import Item
from player import Player
from barrelbot import is_command, time_str

env.BBGLOBALS.init_globals()
ED.init_emojis()

async def setup(bot):
    await bot.add_cog(Economy(bot))


with open(dir_path + "/data/trades.json") as file:
    trades = json.load(file)

slots = {
    "7️⃣": [1000, 4000, 20000],  # list is rewards for 3 in a row of low, med, high stakes
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

horse_races = {} # this can be semi-persistent horse racing thing

cooldwn = commands.CooldownMapping.from_cooldown(3.0, 86400.0, commands.BucketType.member)


async def temp_bot_send(ctx: commands.Context, content: str = None, embed: discord.Embed = None, file: discord.File = None):
    pass


class Economy(commands.Cog, name="Economy"):
    """Economy module"""

    # INITIALIZATION

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot_send = temp_bot_send

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    async def cog_load(self):

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

        # start tasks
        self.hourlyloop.start()
        self.clear_inactive_horseraces.start()

    # COMMANDS

    @commands.command(help=f"""Every 30 minutes, you can work to earn 
                      {ED.BARREL_COIN}.""")
    @Checks.in_bb_channel()
    @commands.cooldown(1, 1800, commands.BucketType.member)  # every 30 min
    async def work(self, ctx: commands.Context):
        player = Player(ctx.author)
        workresult = rand.randint(0, 99)
        if workresult < 2:
            coinsadd = -min(rand.randint(5, 15), player.get_whole_balance())
            msg = ctx.author.mention + ", you somehow managed to completely " + \
            "screw up everything at the barrel factory and had to pay " + \
            str(coinsadd) + ED.BARREL_COIN + " in damages."
        elif workresult < 20:
            coinsadd = rand.randint(10, 15)
            msg = ctx.author.mention + ", you worked hard, but things weren't " + \
            "in your favor today. You earned " + str(coinsadd) + ED.BARREL_COIN + "."
        elif workresult < 65:
            coinsadd = rand.randint(25, 30)
            msg = ctx.author.mention + ", you had a really normal and boring " + \
            "day at the barrel factory. You earned " +str(coinsadd) + ED.BARREL_COIN + "."
        elif workresult < 85:
            coinsadd = rand.randint(30, 40)
            msg = ctx.author.mention + ", you made a new friend at work today!" + \
            " You earned " + str(coinsadd) + ED.BARREL_COIN + "."
        elif workresult < 98:
            coinsadd = rand.randint(40, 50)
            msg = ctx.author.mention + ", you had a tough day but you powered " + \
            "through it! You earned " + str(coinsadd) + ED.BARREL_COIN + "."
        else:
            coinsadd = rand.randint(50, 75)
            msg = ctx.author.mention + ", you got a raise at work! You earned " + \
            str(coinsadd) + ED.BARREL_COIN + "."
        player.give_coins(coinsadd)
        await self.bot_send(ctx, msg)

    @commands.command()
    @Checks.in_bb_channel()
    async def shop(self, ctx: commands.Context, *, item: str = None):
        """See what's for sale. Use `bb shop <item>` to see the details of a particular item."""
        player = Player(ctx.author)
        embed = discord.Embed(color=discord.Color.gold())
        if item is None:
            embed.title = "Welcome to the BarrelBot Shop!"
            embed.description = "Type `bb shop <item>` to see more about an item, or `bb buy <item>` to buy it"
            for i in Item._shop_prices.keys():
                saleitem = Item(i)
                embed.add_field(name=saleitem.propername, value=f"{player.get_shop_price(saleitem)}{ED.BARREL_COIN}")
        else:
            try:
                item: Item = Item.get_from_string(item)
                embed.title = item.propername
                embed.description = (f"Cost: {player.get_shop_price(item)}{ED.BARREL_COIN}\n"
                                     f"{item.get_shop_description()}")
                embed.set_footer(text=f'Type "bb buy {item.easyalias}" to buy this item')
            except ItemNotFound:
                await self.bot_send(ctx, "Item not found.")
                return
            except Exception as e:
                print(e.with_traceback(None))
                await self.bot_send(ctx, "check logs")
                return
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @Checks.in_bb_channel()
    async def buy(self, ctx: commands.Context, *, item: str):
        """Buy an item from the shop."""
        try:
            item: Item = Item.get_from_string(item)
        except ItemNotFound:
            await self.bot_send(ctx, "Item not found.")
            return
        player = Player(ctx.author)
        try:
            player.give_coins(-player.get_shop_price(item))
            player.add_to_inventory(item)
            await self.bot_send(ctx, item.get_shop_message() + " You now have `" + str(
                player.amount_in_inventory(item)) + "` of this item.")
            if item.id == 6:
                player.reset_lcr()
                player.increment_nhouses()
        except NotEnoughCoins:
            await self.bot_send(ctx, f"You don't have enough {ED.BARREL_COIN}")
        return

    @commands.command()
    @Checks.in_bb_channel()
    @Checks.can_fish()
    @commands.cooldown(1, 600, commands.BucketType.member)  # every 10 min
    async def fish(self, ctx: commands.Context):
        """Cast out your fishing line and see what you get! You can fish once every 10 minutes."""
        player = Player(ctx.author)
        norods = player.amount_in_inventory(1)
        nocasts = min(norods, 3)
        for _ in range(nocasts):
            outstr, fishid = fish_()
            if fishid != 0:
                player.add_to_inventory(fishid)
            await self.bot_send(ctx, outstr)

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx: commands.Context, pageno=1):
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
        invitems = invitems_[(pageno - 1) * 25:pageno * 25]
        nopages = 1 + (len(invitems_) - 1) // 25
        embed = discord.Embed(color=discord.Color.light_gray())
        embed.title = ctx.author.display_name + "'s Inventory"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value="#" + str(i + 1 + (pageno - 1) * 25) + str(
                "" if invdisplay.count(item) == 1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages} - type `bb inventory <page>` to see a different page")
        await self.bot_send(ctx, embed=embed)

    @commands.command(aliases=["bal"])
    async def balance(self, ctx: commands.Context):
        f"""Displays how many {ED.BARREL_COIN} you have."""
        player = Player(ctx.author)
        nocoins = player.get_whole_balance()
        inbank = player.get_bank_balance()
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = ctx.author.display_name + "'s " + ED.BARREL_COIN + " balance"
        embed.description = str(nocoins) + ED.BARREL_COIN
        if inbank != 0:
            embed.description += f"\n\n{nocoins - inbank}{ED.BARREL_COIN} in wallet, {inbank}{ED.BARREL_COIN} in bank"
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @Checks.in_bb_channel()
    async def sellall(self, ctx: commands.Context):
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
        await self.bot_send(ctx, f"You sold {nosold} fish for a total of {saleprice}{ED.BARREL_COIN}")

    @commands.command()
    async def openall(self, ctx: commands.Context):
        """Opens all of your crates."""
        player = Player(ctx.author)
        inventory = player.get_inventory()
        if len(inventory) == 0:
            await self.bot_send(ctx, "Your inventory is empty! You need to get crates before opening them.")
            return
        crateinv = []
        for item in inventory:
            if item.id in [4, 5]:
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
        await self.bot_send(ctx, f"You opened {nosold} crates and got a total of {saleprice}{ED.BARREL_COIN}!")

    @commands.command(pass_context=True)
    async def gift(self, ctx: commands.Context, nocoins, *, user: discord.Member):
        """Allows you to give someone else some coins. Example: `bb gift 50 @jan Kaje`"""
        nocoins = abs(int(nocoins))
        if user.bot:
            await self.bot_send(ctx, "You can't give bots money.")
            return
        giver = Player(ctx.author)
        receiver = Player(user)
        try:
            giver.give_coins(-nocoins)
        except NotEnoughCoins:
            await self.bot_send(ctx, "You don't have enough " + ED.BARREL_COIN)
            return
        receiver.give_coins(nocoins)
        await self.bot_send(ctx, f"You've given {user.display_name} {nocoins}{ED.BARREL_COIN}")

    @commands.command()
    async def baltop(self, ctx: commands.Context):
        """Shows the 10 people with the most money, as well as your own ranking. Improved version."""
        # Gather all player balances
        balances = [[p, i["bal"], i["bank"]] for p, i in Player._playerdata.items()]
        # Sort by total balance (wallet + bank)
        balances.sort(key=lambda i: i[1] + i[2], reverse=True)
        balances = [i for i in balances if i[0].startswith(str(ctx.guild.id))]
        users = [re.search(r"(\d+)$", i[0]).group(1) for i in balances]
        bals = [i[1] + i[2] for i in balances]
        inbank = [i[2] for i in balances]
        try:
            ranking = users.index(str(ctx.author.id))
        except ValueError:
            ranking = None
        embed = discord.Embed(color=discord.Color.gold(), title="Top 10 Richest Players")
        valstr = ""
        for i in range(min(10, len(users))):
            user_obj = self.bot.get_user(int(users[i]))
            username = user_obj.display_name if user_obj else f"User {users[i]}"
            valstr += f"{i + 1}) {username} - {bals[i]}{ED.BARREL_COIN}"
            if inbank[i] != 0:
                valstr += f" - {inbank[i]} in bank"
            valstr += "\n"
        embed.description = valstr
        if ranking is not None and ranking >= 10:
            user_obj = self.bot.get_user(int(users[ranking]))
            username = user_obj.display_name if user_obj else f"User {users[ranking]}"
            embed.add_field(name="Your ranking:",
                            value=f"{ranking + 1}/{len(users)}: {username} - {bals[ranking]}{ED.BARREL_COIN}")

        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @Checks.in_bb_channel()
    async def display(self, ctx: commands.Context, item: str = "recent"):
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
    @Checks.in_bb_channel()
    async def takefromdisplay(self, ctx: commands.Context, item="recent"):
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

    @commands.command(aliases=["dc"])
    async def displaycase(self, ctx: commands.Context, pageno=1):
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
        invitems = invitems_[(pageno - 1) * 25:pageno * 25]
        nopages = 1 + (len(invitems_) - 1) // 25
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = ctx.author.display_name + "'s Display Case"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value="#" + str(i + 1 + (pageno - 1) * 25) + str(
                "" if invdisplay.count(item) == 1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages} - type `bb displaycase <page>` to see a different page")
        await self.bot_send(ctx, embed=embed)

    @commands.command(pass_context=True)
    async def trade(self, ctx: commands.Context, keyword: str = None, item1: discord.Member | str = None,
                    item2: str = None, *, recipient: discord.Member = None):
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

                if isinstance(item1, discord.Member) or item1 is None or item2 is None:
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
                    await self.offer_trade(ctx.author, recipient, item1, item2)
                    offerer = Player(ctx.author)
                    receiver = Player(recipient)
                    await self.bot_send(ctx,
                                        f"You offered to give {recipient.display_name} "
                                        f"{'1 ' + str(offerer.get_item_from_invno(int(item1))) if isinstance(item1, str) else str(item1) + ED.BARREL_COIN}"
                                        f"in exchange for "
                                        f"{'1 ' + str(receiver.get_item_from_invno(int(item2))) if isinstance(item2, str) else str(item2) + ED.BARREL_COIN}")
                except Exception as e:
                    await self.bot_send(ctx, str(e))
                    return

            case "accept":
                if not isinstance(item1, discord.Member):
                    await self.bot_send(ctx, "Invalid offering user syntax.")
                    return
                try:
                    offered, received, frombanko, frombankr = await self.accept_trade(item1.id, ctx.author.id)
                    msg = f"Offer complete! You received {get_obj_str(offered)} " + \
                          f"and {item1.display_name} received {get_obj_str(received)}."
                    if frombanko != 0:
                        msg += f" {item1.display_name} withdrew {frombanko}{ED.BARREL_COIN} in the process."
                    if frombankr != 0:
                        msg += f" You withdrew {frombankr}{ED.BARREL_COIN} in the process."
                    await self.bot_send(ctx, msg)
                except Exception as e:
                    await self.bot_send(ctx, str(e))
                    return

            case "view":

                incoming, outgoing = await get_trades(Player(ctx.author))
                embed = discord.Embed(color=discord.Color.light_gray(), title=f"Outstanding trade offers",
                                      description="")

                incoming_str = ""
                for trade in incoming:
                    offerer = self.bot.get_user(int(re.search(r"(\d+)$", trade[0]).group(1)))
                    incoming_str += (f"From: {offerer.display_name}\n\tOffering: {get_obj_str(trade[2])}\n\t"
                                     f"Wants in return: {get_obj_str(trade[3])}\n")
                embed.add_field(name="__Incoming__", value=incoming_str)

                outgoing_str = ""
                for trade in outgoing:
                    recipient = self.bot.get_user(int(re.search(r"(\d+)$", trade[1]).group(1)))
                    outgoing_str += (f"To: {recipient.display_name}\n\tOffering: {get_obj_str(trade[2])}\n\t"
                                     f"In return for: {get_obj_str(trade[3])}\n")
                embed.add_field(name="__Outgoing__", value=outgoing_str)

                await self.bot_send(ctx, embed=embed)

            case "remove":
                if not isinstance(item1, discord.Member):
                    await self.bot_send(ctx, "Invalid user syntax.")
                    return
                if not isinstance(item2, str):
                    await self.bot_send(ctx, "Invalid incoming/outgoing syntax.")
                if item2.lower() == "incoming":
                    try:
                        await remove_trade(Player(item1), Player(ctx.author))
                    except Exception as e:
                        await self.bot_send(ctx, e)
                        return
                elif item2.lower() == "outgoing":
                    try:
                        await remove_trade(Player(ctx.author), Player(item1))
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
    @Checks.in_bb_channel()
    async def sell(self, ctx: commands.Context, itemno: int, quantity: int = 1):
        """Lets you sell items in your inventory. Items bought from the shop sell for up to 75% of the original
        price. Input the slot in your inventory that the item is in, and optionally a quantity (default 1)"""
        itemno = abs(int(itemno))
        quantity = abs(int(quantity))
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
        moneyreceived = quantity * resaleprice
        for i in range(quantity):
            player.remove_from_inventory(item)
        player.give_coins(moneyreceived)
        await self.bot_send(ctx, f"You successfully sold {quantity} {item} for {moneyreceived}{ED.BARREL_COIN}.")

    @commands.command()
    @Checks.in_bb_channel()
    async def appraise(self, ctx: commands.Context, itemno: int = None):
        """Check how much your items will sell for before selling them."""
        player = Player(ctx.author)
        if itemno is None:
            if len(player.get_inventory()) == 0:
                await self.bot_send(ctx, "No items in your inventory.")
                return
            resaleprice = 0
            for item in player.get_inventory():
                resaleprice += item.get_sale_price()
            await self.bot_send(ctx, f"The items in your inventory would sell for {resaleprice}{ED.BARREL_COIN}")
            return
        itemno = abs(int(itemno))
        item = player.get_item_from_invno(itemno)
        resaleprice = item.get_sale_price()
        if resaleprice is None:
            await self.bot_send(ctx, "No way to sell this item.")
            return
        await self.bot_send(ctx, f"Your {item} would sell for {resaleprice}{ED.BARREL_COIN}")

    @commands.command()
    async def deposit(self, ctx: commands.Context, nocoins: int = 0):
        """Allows you to deposit coins in the bank. By default, deposits your entire balance into the bank.
        Coins in the bank will no longer count towards your balance, but can be retrieved at any time.
        The bank is significantly more safe against robbery, although not completely."""
        player = Player(ctx.author)
        nocoins = abs(nocoins)  # no negatives
        if nocoins == 0:
            bal = player.get_balance()
            player.deposit(bal)
            await self.bot_send(ctx, f"You deposited your entire balance - {bal}{ED.BARREL_COIN} - into the bank.")
        else:
            try:
                player.deposit(nocoins)
                await self.bot_send(ctx, f"You deposited {nocoins}{ED.BARREL_COIN} into the bank.")
            except NotEnoughCoins:
                await self.bot_send(ctx, f"You don't have that many coins.")

    @commands.command()
    async def withdraw(self, ctx: commands.Context, nocoins: int = 0):
        """Allows you to withdraw coins from the bank. By default, withdraws your entire balance."""
        player = Player(ctx.author)
        nocoins = abs(nocoins)  # no negatives
        if nocoins == 0:
            bal = player.get_bank_balance()
            player.withdraw(bal)
            await self.bot_send(ctx, f"You withdrew your entire balance - {bal}{ED.BARREL_COIN} - from the bank.")
        else:
            try:
                player.withdraw(nocoins)
                await self.bot_send(ctx, f"You withdrew {nocoins}{ED.BARREL_COIN} from the bank.")
            except NotEnoughCoins:
                await self.bot_send(ctx, f"You don't have that many coins.")

    @commands.command()
    @Checks.in_bb_channel()
    async def bank(self, ctx: commands.Context):
        """Allows you to see your current bank account balance."""
        player = Player(ctx.author)
        bal = player.get_bank_balance()
        embed = discord.Embed(color=discord.Color.dark_red(),
                              title=f"{ctx.author.display_name}'s Bank Account",
                              description=f"{bal}{ED.BARREL_COIN}")
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    @Checks.in_bb_channel()
    @Checks.can_gamble()
    @commands.cooldown(20, 86400, commands.BucketType.member)
    async def slots(self, ctx: commands.Context, *, stakes="low"):
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
            await self.bot_send(ctx,
                                f"You don't have enough coins to play {stakesmsg}-stakes slots! "
                                f"You need {slotprices[stakes]}")
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
            await msg.edit(
                content=f"Rolling a game of {stakesmsg}-stakes slots...\n\t{outcome}\nBetter luck next time!")
        else:
            await msg.edit(
                content=f"Rolling a game of {stakesmsg}-stakes slots...\n\t{outcome}\n"
                        f"You won {winnings}{ED.BARREL_COIN}!")
            player.give_coins(ctx.author.id, winnings)
        return

    @commands.command()
    @Checks.in_bb_channel()
    @Checks.can_gamble()
    @commands.cooldown(20, 86400, commands.BucketType.member)
    async def roulette(self, ctx: commands.Context, bet, *, bet_type: str):
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
            m = re.split(r"\s", bet_type)
            for i in m:
                if i != "":
                    try:
                        if i not in ["00"] + [str(i) for i in range(37)]:
                            await self.bot_send(ctx, "Invalid bet type.")
                            return
                        bet_vals.append(i)
                    except:
                        await self.bot_send(ctx, "Invalid bet type.")
                        return
            if len(bet_vals) == 0 or len(bet_vals) > 6:
                await self.bot_send(ctx, "Invalid bet type.")
                return
            bettype = len(bet_vals) + 6
            if bettype == 7:
                bettype += 6

        result, payout = roulette_(bet, bettype, bet_vals)

        player.give_coins(payout)

        if payout < 0:
            await self.bot_send(ctx,
                                f"The winning number is {result}. You lost {-payout}{ED.BARREL_COIN}. "
                                f"Better luck next time!")
        else:
            await self.bot_send(ctx, f"The winning number is {result}. You won {payout}{ED.BARREL_COIN}!")

    @commands.command(pass_context=True)
    @Checks.in_bb_channel()
    @Checks.can_rob()
    @Checks.has_valid_user(r"(?<=rob ).*")
    @commands.cooldown(1, 3600, commands.BucketType.member)  # every hr
    # add something to keep repeated robbings in check - maybe decreased luck if you do the same person twice in a row? 
    # maybe occasional jail time where you can't do any commands?
    async def rob(self, ctx: commands.Context, *, victim: discord.Member):
        """Attempts to rob the victim. You must have a dagger to rob people, and if they have a shield, your chances
        of success drop drastically."""
        perpetrator = Player(ctx.author)
        victim_player = Player(victim)
        opponent_has_shield = victim_player.has_in_inventory(3)
        luck_threshold = 90 if opponent_has_shield else 30
        luck = rand.randint(0, 99)
        richfactor = 1 + victim_player.get_balance() * 0.001
        if luck < 2:
            perpetrator.remove_from_inventory(2)
            await self.bot_send(ctx,
                                "While attempting to rob them, you tripped, fell, and broke your dagger. Serves you "
                                "right...")
            return
        if luck == 99 and opponent_has_shield:
            victim_player.remove_from_inventory(3)
            coinsmoved = min(victim_player.get_balance(), int(richfactor * rand.randint(30, 60)))
            victim_player.give_coins(-coinsmoved)
            perpetrator.give_coins(coinsmoved)
            await self.bot_send(ctx,
                                f"In trying to defend themselves, your victim's shield broke! You successfully stole "
                                f"{coinsmoved} from {victim.mention}!")
            return
        if luck >= luck_threshold:
            coinsmoved = min(victim_player.get_balance(), int(richfactor * rand.randint(30, 60)))
            victim_player.give_coins(-coinsmoved)
            perpetrator.give_coins(coinsmoved)
            success_msg = rand.choice([
                f"You broke into {victim.mention}'s house in the middle of the night and stole their jewelry.",
                f"You mugged {victim.mention} on the side of the road as they were going to " + rand.choice([
                    "their grandma's funeral.", "the grocery store.", "their son's piano recital.", "work.",
                    "their cousin's house.",
                    "a concert.", "eat lunch with their partner.", "the movie theater.",
                    "visit their partner at work and bring them cookies.",
                    "the barrel factory."
                ]),
                f"You broke {victim.mention}'s car window while they were shopping and took everything you could find.",
                f"You seduced {victim.mention} and made away with their wallet in the middle of the night.",
                f"You sent {victim.mention} a phishing email and somehow they fell for it.",
                f"You convinced {victim.mention} to invest in your pump and dump crypto scheme.",
                f"You resold {ED.BARREL_EMOJI} merch to {victim.mention} for an exorbitantly high price.",
                f"You flirted with {victim.mention} "
                f"long enough to distract them while your partner cleaned out their safe."
            ])
            await self.bot_send(ctx,
                                success_msg + f" You successfully stole {coinsmoved}{ED.BARREL_COIN} from "
                                              f"{victim.display_name}!")
            return
        coinsmoved = min(perpetrator.get_whole_balance(),
                         int(round((1 + perpetrator.get_balance() * 0.0005) * rand.randint(5, 10))))
        perpetrator.take_coins(coinsmoved, True)
        fail_msg = rand.choice([
            f"You tried to mug {victim.mention} with your dagger, but they pulled a gun on you. Are those even legal "
            f"here?",
            f"You got trapped inside {victim.mention}'s house after breaking in, and the police caught you.",
            f"You successfully robbed {victim.mention}, but while making a getaway, you slipped on a banana peel and "
            f"everything fell out of your pockets.",
            f"Right after robbing {victim.mention}, they robbed you right back.",
            f"You lied on your tax forms about your criminal activities, and the IRS found you out.",
            f"You stole {victim.mention}'s wallet, but it only had expired coupons and a drawing of a cat.",
            f"You tried to scam {victim.mention} online, but they reverse-hacked you and now own your crypto wallet.",
            f"You stole a priceless artifact from {victim.mention}, but then dropped it into a sewer drain while "
            f"taking a selfie.",
            f"You tried to mug {victim.mention}, but instead they gave you life advice over a cup of tea. Now you're "
            f"pursuing your passion and becoming a masseuse/masseur.",
            f"You followed {victim.mention} home to rob them, but got lost and ended up at your ex's house. Awkward."
        ])
        await self.bot_send(ctx, fail_msg + f" You lost {coinsmoved}{ED.BARREL_COIN}!")

    @commands.command()
    @Checks.in_bb_channel()
    @Checks.can_rob()
    @commands.cooldown(1, 21600, commands.BucketType.member)  # every 6 hr
    async def bankrob(self, ctx: commands.Context):
        """Attempts to rob the bank. The chance of succeeding is very low (~1%), but with more daggers your luck
        increases to just low (at most ~5%). Amount gained upon successful robbery: 20-40% of the bank's holdings,
        distributed equally amongst all bank accounts. Cooldown is six hours."""
        player = Player(ctx.author)
        success_luck = rand.random() * 100
        no_daggers = player.amount_in_inventory(2)
        chances = 5 * (1 - math.exp(-no_daggers / 5))
        if chances > success_luck:
            # successfully rob bank
            percent_robbed = 0.2 + 0.2 * rand.random()
            robbings = sum(Player.reduce_bank_holdings_by_percent(percent_robbed))
            player.give_coins(robbings)
            await self.bot_send(ctx,
                                f"You successfully robbed the bank! You made away with {robbings}{ED.BARREL_COIN}!")
        else:
            # failure
            coinsmoved = min(player.get_whole_balance(),
                             int(round((1 + player.get_whole_balance() * 0.0005) * rand.randint(10, 20))))
            player.take_coins(coinsmoved, True)
            await self.bot_send(ctx, f"You failed! You lost {coinsmoved}{ED.BARREL_COIN} in the attempt.")

    @commands.command()
    @Checks.in_bb_channel()
    @Checks.can_collect_rent()
    @commands.cooldown(1, 10, commands.BucketType.member)
    async def collectrent(self, ctx: commands.Context):
        """Collects rent for your houses. Rent is 500 coins per house per day."""
        player = Player(ctx.author)
        if player.amount_in_inventory(6) < 1:
            await self.bot_send(ctx, f"You don't have any property to collect rent on.")
            return
        nocoins, tpassed = player.collect_rent()
        if nocoins == 0:
            await self.bot_send(ctx, f"You don't have any rent to collect yet.")
        else:
            await self.bot_send(ctx,
                                f"You collected {time_str(int(tpassed.total_seconds()))} of rent from your "
                                f"{player.amount_in_inventory(6)} houses. You gained {nocoins}{ED.BARREL_COIN}")
            
    @commands.command()
    @Checks.in_bb_channel()
    @Checks.can_gamble()
    @commands.cooldown(1, 20, commands.BucketType.member)
    async def horserace(self, ctx: commands.Context):
        """Bet on a horse race!"""
        # ok what this is gonna do
        # pick 6-12 emojis to do a race
        # ask if they want to bet for first or to place, and how much to bet
        # calculate earnings based on luck + some random noise
        # make up random speed for each and influence throughout with random noise
        # display the horse race by stringing a series of images into a GIF
        # give out earnings

        # pick horses
        no_horses = min(rand.randint(6, 12), len(ED.ALL_EMOJIS))
        emojis_copy = ED.ALL_EMOJIS.copy()
        horses = []
        for _ in range(no_horses):
            horse = rand.choice(emojis_copy)
            horses.append(horse)
            emojis_copy.remove(horse)
        
        context_key = f"{ctx.author.id}_{ctx.channel.id}"
        
        global horse_races

        if context_key in horse_races.keys():
            await self.bot_send(ctx, "You already have an ongoing horse race!")
            return
        
        embed = discord.Embed(color=discord.Colour.og_blurple(), title="Here are your contestants!")
        embed.description = ''.join(horses)
        # embed.add_field(name='What kind of bet will you make?', 
        #                 value='Option 1: "straight" - your pick wins first place.\n' \
        #                 'Option 2: "place" - your pick wins either second or first place.\n' \
        #                 'Option 3: "show" - your pick is in the top three.')
        # embed.footer='Please respond with one of the three options.'
        embed.set_footer(text='Please reply with the contestant you\'d like to bet on.')

        await self.bot_send(ctx, embed=embed)
        
        horse_races[context_key] = {
            "prev_interaction_timestamp": time.time(),
            "horses": horses,
            "horse": None,
            "type": None,
            "amount": None,
            "strikes": 0
        }

    @commands.command()
    async def total(self, ctx: commands.Context):
        """Shows the total amount of coins in circulation."""
        players = Player.get_all_players()
        total = 0

        for player in players:
            total += player.get_whole_balance()

        await self.bot_send(ctx, f"There are currently {total}{ED.BARREL_COIN} in circulation.")

    @commands.command()
    @Checks.in_bb_channel()
    @commands.cooldown(1, 600, commands.BucketType.member)  # every 10 minutes
    async def fetchmeabeer(self, ctx: commands.Context):

        beerFetchMessages = {

            # success
            0: "Fine, here you go: 🍺",
            1: "Hmm, alright fine: 🍺",
            2: "... 🍺",
            3: "ugh, 🍺",
            4: "kk, 🍺",
            5: "can you ask more nicely next time? 🍺",

            # fail
            6: "Oh no! I accidentally dropped it on the way! Im so sorry.",
            7: "Nuh uh buddy, not today.",
            8: "I was thirsty and I drank it all, whoopsies.",
            9: "Oh no! I lost it! The falcon caught it midway and then there was this car and other.. things.. "
               "happened!",
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
    async def peekdc(self, ctx: commands.Context, user: discord.Member, pageno: int = 1):
        """Take a look at the user's displaycase."""
        invdisplay = Player(user).get_display()
        invitems_ = list(set(invdisplay))
        invitems_.sort(key=lambda i: i.id)
        invitems = invitems_[(pageno - 1) * 25:pageno * 25]
        nopages = 1 + len(invitems_) // 25
        embed = discord.Embed(color=discord.Color.gold())
        embed.title = user.display_name + "'s Display Case"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value="#" + str(i + 1 + (pageno - 1) * 25) + str(
                "" if invdisplay.count(item) == 1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages}")
        await self.bot_send(ctx, embed=embed)

    @commands.command()
    async def getcooldowns(self, ctx: commands.Context):
        """See your cooldowns so you don't have to take a guess anymore !"""
        # getting the cooldowns
        workcd = int(round(self.work.get_cooldown_retry_after(ctx)))  # possible breaking point
        fishcd = int(round(self.fish.get_cooldown_retry_after(ctx)))
        robcd = int(round(self.rob.get_cooldown_retry_after(ctx)))
        bankrobcd = int(round(self.bankrob.get_cooldown_retry_after(ctx)))

        listcd = {"work": workcd, "fish": fishcd, "rob": robcd, "bankrob": bankrobcd}

        # constructor
        embed = discord.Embed(color=discord.Color.blue(), title="Your cooldowns")
        embed_str = ""

        i = 1
        for elt in listcd.keys():
            embed_str += str(i) + ") "
            i += 1
            embed_str += elt + " - "
            if listcd[elt] == 0.0:  # not on cooldown !
                embed_str += "Not on cooldown ! " + ED.HOLY_BARREL_EMOJI + "\n"
            else:
                embed_str += time_str(listcd[elt]) + " :x:\n"
        embed.description = embed_str
        await self.bot_send(ctx, embed=embed)

    # ADMIN COMMANDS

    @commands.command()
    @commands.is_owner()
    async def saveeconomydata(self, ctx: commands.Context):
        await savealldata()
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def forcesaveplayerdata(self, ctx: commands.Context):
        with open("tempsave.pkl", "wb") as file:
            file.write(dpx(Player._playerdata))
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def run_raw_code_economy(self, ctx: commands.Context, *, code: str):
        if code == '':
            return
        try:
            exec(code)
        except Exception as e:
            await self.bot_send(ctx, f"Something went wrong:\n{e.with_traceback(None)}")

    @commands.command()
    @commands.is_owner()
    async def geteconomydata(self, ctx: commands.Context):
        outstr = json.dumps(Player.get_json_data())
        lenstr = len(outstr)
        nostrs = lenstr // 2000 + 1
        for i in range(nostrs):
            await self.bot_send(ctx, outstr[i * 2000:(i + 1) * 2000])
        return

    @commands.command()
    @commands.is_owner()
    async def kill_user(self, ctx: commands.Context, user: int|discord.Member):
        """Kills a user and removes all their data. Only for admins."""
        if user.bot:
            await self.bot_send(ctx, "You can't remove a bot's data.")
            return
        if isinstance(user, int):
            try:
                Player.remove_player_data(str(user))
                await self.bot_send(ctx, f"Data for User {user} removed.")
            except PlayerNotFound:
                await self.bot_send(ctx, f"User {user} not found.")
            return
        player = Player(user)
        player.remove_all_data()
        await self.bot_send(ctx, f"Removed all data for {user.display_name}.")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def forcegivemoney(self, ctx: commands.Context, user: discord.Member, nocoins: int):
        """Gives the specified user item_id a certain number of coins"""
        player = Player(user)
        player.give_coins(nocoins)
        await self.bot_send(ctx, "Done. They now have " + str(player.get_whole_balance()) + ED.BARREL_COIN)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def forcetakemoney(self, ctx: commands.Context, user: discord.Member, nocoins: int):
        """Takes a certain number of coins from the specified user"""
        player = Player(user)
        player.take_coins(nocoins, True)
        await self.bot_send(ctx, "Done. They now have " + str(player.get_whole_balance()) + ED.BARREL_COIN)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def clearbalance(self, ctx: commands.Context, user: discord.Member):
        """Clears the user's balance."""
        player = Player(user)
        player.give_coins(-1 * player.get_balance())
        await self.bot_send(ctx, "Done!")

    @commands.command(pass_context=True)
    async def forcegiveitem(self, ctx: commands.Context, user: discord.Member, itemid: int):
        """Gives the specified user item_id an item"""

        if (not env.BBGLOBALS.IS_IN_DEV_MODE) or (await ctx.bot.is_owner(ctx.author)):
            await self.bot_send(ctx, "You cannot use this command.")
            return

        player = Player(user)
        player.add_to_inventory(itemid)
        await self.bot_send(ctx, "Done!")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def forcetakeitem(self, ctx: commands.Context, user: discord.Member, itemid: int):
        """Takes the specified item from the user"""
        player = Player(user)
        try:
            player.remove_from_inventory(itemid)
            await self.bot_send(ctx, "Done!")
        except NotInInventory:
            await self.bot_send(ctx, "Item not in their inventory.")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def clearinv(self, ctx: commands.Context, user: discord.Member):
        """Clears the specified user's inventory."""
        player = Player(user)
        player.clear_inventory()
        await self.bot_send(ctx, "Done!")

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def test_horserace(self, ctx: commands.Context, no_horses: int = None):
        if no_horses is None:
            no_horses = rand.randint(6, 12)
        emojis_copy = ED.ALL_EMOJIS.copy()
        horses = []
        for _ in range(no_horses):
            horse = rand.choice(emojis_copy)
            horses.append(horse)
            emojis_copy.remove(horse)

        winners, image_stream = await self.simulate_horserace(horses)

        image = discord.File(image_stream, filename="horse_race.gif")
        emb = discord.Embed(color=discord.Colour.og_blurple())
        emb.set_image(url="attachment://horse_race.gif")

        await self.bot_send(ctx, embed=emb, file=image)
        await self.bot_send(ctx, f"{winners}")
        
    @commands.command()
    @commands.is_owner()
    async def refresh_playerdata(self, ctx: commands.Context):
        for m in ctx.guild.members:
            if not m.bot:
                Player(m)
                print(m.display_name)
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def get_all_trade_data(self, ctx: commands.Context):
        await self.bot_send(ctx, json.dumps(trades))

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def peekinv(self, ctx: commands.Context, user: discord.Member, pageno: int = 1):
        """Spies on the user's inventory."""
        invdisplay = Player(user).get_inventory()
        invitems_ = list(set(invdisplay))
        invitems_.sort(key=lambda i: i.id)
        invitems = invitems_[(pageno - 1) * 25:pageno * 25]
        nopages = 1 + len(invitems_) // 25
        embed = discord.Embed(color=discord.Color.light_gray())
        embed.title = user.display_name + "'s Inventory"
        embed.description = "Total items: " + str(len(invdisplay))
        for i, item in enumerate(invitems):
            embed.add_field(name=str(item), value="#" + str(i + 1 + (pageno - 1) * 25) + str(
                "" if invdisplay.count(item) == 1 else " - Count: " + str(invdisplay.count(item))))
        if nopages > 1:
            embed.set_footer(text=f"Page {pageno}/{nopages}")
        await self.bot_send(ctx, embed=embed)

    # ROUTINES

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # as of right now, only for horse races
        # eliminate other possibilities
        if message.author.bot:
            return
        if message.content.startswith(is_command(self.bot, message)): # command
            return
        context_key = f"{message.author.id}_{message.channel.id}"
        global horse_races
        if context_key not in horse_races.keys():
            return
        
        
        current_race = horse_races[context_key]
        if current_race["horse"] is None:
            # needs to be contestant
            msg = message.content.strip()
            if msg not in current_race['horses']:
                await self.invalid_hr_msg(context_key, "Not a valid horse to choose from. Try again", message.channel)
            else:
                horse_races[context_key]["strikes"] = 0
                horse_races[context_key]["prev_interaction_timestamp"] = time.time()
                horse_races[context_key]["horse"] = current_race['horses'].index(msg)
                await self.bot_send(message.channel, f'Your horse has been chosen. Please choose your bet type.\n' \
                                    '  Option 1: "straight" - your pick wins first place.\n' \
                                    '  Option 2: "place" - your pick wins either second or first place.\n' \
                                    '  Option 3: "show" - your pick is in the top three.')
            return

        elif current_race["type"] is None:
            # this message must be the type of bet
            msg = message.content.strip().lower()

            if msg not in ['straight', 'place', 'show']:
                # invalid input
                await self.invalid_hr_msg(context_key, 
                    'Not a valid bet type! Please reply with either "straight", "place", or "show".', message.channel)
            else:
                horse_races[context_key]["strikes"] = 0
                horse_races[context_key]["prev_interaction_timestamp"] = time.time()
                horse_races[context_key]["type"] = msg
                await self.bot_send(message.channel, f"Finally, choose the amount you would like to bet.")
            return
        
        elif current_race['amount'] is None:
            # this message must be the bet amount
            msg = message.content.strip()
            # convert to integer
            try:
                amt = int(msg)
            except TypeError:
                await self.invalid_hr_msg(context_key, 
                    "Could not convert your response to an integer. Try again.", message.channel)
                return
            
            if amt <= 0:
                await self.invalid_hr_msg(context_key, 
                    "Nice try. Positive numbers only.", message.channel)
                return

            player = Player(message.author)
            bal = player.get_whole_balance()
            if amt > bal:
                await self.invalid_hr_msg(context_key, 
                    "You don't have that much to bet. Try again.", message.channel)
                return

            horse_races[context_key]["strikes"] = 0
            horse_races[context_key]["prev_interaction_timestamp"] = time.time()
            horse_races[context_key]["amount"] = amt

            await self.bot_send(message.channel, "Thank you for your business! Here's your horse race.")
            
            winners, image_stream = await self.simulate_horserace(horse_races[context_key]['horses'])

            image = discord.File(image_stream, filename="horse_race.gif")
            emb = discord.Embed(color=discord.Colour.og_blurple())
            emb.set_image(url="attachment://horse_race.gif")

            await self.bot_send(message.channel, embed=emb, file=image)

            # calculate winnings (if any)
            winnings = 0
            n_horses = len(current_race['horses'])

            if current_race['type'] == 'straight' and winners[0] == current_race['horse']:
                winnings = round((n_horses-1)*current_race['amount']*rand.gauss(1, 0.2))

            elif current_race['type'] == 'place' and current_race['horse'] in winners[:2]:
                winnings = round((n_horses/2-1)*current_race['amount']*rand.gauss(1, 0.2))

            elif current_race['type'] == 'show' and current_race['horse'] in winners:
                winnings = round((n_horses/3-1)*current_race['amount']*rand.gauss(1, 0.2))

            await asyncio.sleep(5) # wait for the race to play

            if winnings > 0:
                player.give_coins(winnings)
                await self.bot_send(message.channel, f"Congrats! You won {winnings}{ED.BARREL_COIN}!")
            else:
                player.take_coins(current_race['amount'], include_bank=True)
                await self.bot_send(message.channel, "Better luck next time!")

            del horse_races[context_key]

    @tasks.loop(hours=6)
    async def hourlyloop(self):
        await savealldata()

    @tasks.loop(minutes=5)
    async def clear_inactive_horseraces(self):
        global horse_races
        now = time.time()
        hr_copy = horse_races.copy()
        for k, v in hr_copy.items():
            if now - v['prev_interaction_timestamp'] > 300: # 5 minutes since interact
                ch_id = int(re.match(r"\d+_(\d+)", k).group(1))
                channel = await self.bot.fetch_channel(ch_id)
                await self.bot_send(channel, "It's been more than 5 minutes since you interacted with this horse race," \
                "so I'll cancel it.")
                del horse_races[k]

    # METHODS        

    async def simulate_horserace(self, horses) -> tuple[list[int], BytesIO]:
        # this is just going to be simulation, no money stuff

        # collect emojis and files
        emoji_ids = [re.match(r"<a?:.*:(\d+)>", i).group(1) for i in horses]
        emojis = [self.bot.get_emoji(int(i)) for i in emoji_ids]
        emojis_raw = [await e.read() for e in emojis]

        # get horses ready
        n_horses = len(horses)
        accel_stats = [max(rand.gauss(5, 1), 0.1) for _ in range(n_horses)]
        drag_stats = [max(rand.gauss(0.1, 0.02), 0.001) for _ in range(n_horses)]
        positions = [[0] for _ in range(n_horses)]
        velocities = [[0] for _ in range(n_horses)]

        # do simulation
        maxiter = 1000
        count = 0
        order = []

        while min([positions[i][-1] for i in range(n_horses)]) < 100 and count < maxiter:
            count += 1
            for i in range(n_horses):
                try:
                    velocities[i].append(velocities[i][-1] + accel_stats[i]/max(2, velocities[i][-1]) - drag_stats[i] * max(0, velocities[i][-1])**2)
                    if positions[i][-1] >= 100:
                        velocities[i][-1] = 0
                        if i not in order:
                            order.append(i)
                except:
                    print(velocities[i][-1], accel_stats[i], drag_stats[i])
                    raise
                positions[i].append(positions[i][-1] + velocities[i][-1])

        # draw image
        # open emojis and resize
        horses = [Image.open(BytesIO(e)).resize((32, 32)) for e in emojis_raw]

        # paint the background
        bgrimgsize = (
            1024,
            16+32*n_horses
        )
        bgrimg = Image.new("RGBA", bgrimgsize, (30,33,36,255))

        finishline_xlevel = 900+32+8 # 900 px away from starting point

        draw = ImageDraw.Draw(bgrimg)

        y_ = 8+32
        for _ in range(n_horses-1):
            draw.line([(0, y_), (finishline_xlevel, y_)], fill=(200, 200, 200, 255), width=1)
            y_ += 32

        draw.line([(finishline_xlevel, 0), (finishline_xlevel, 1024)], fill=(200, 200, 200, 255), width=5)

        # outline
        draw.line([(0, 0), (bgrimgsize[0], 0)], fill=(255, 255, 255, 255), width=1)
        draw.line([(bgrimgsize[0], 0), (bgrimgsize[0], bgrimgsize[1])], fill=(255, 255, 255, 255), width=3)
        draw.line([(bgrimgsize[0], bgrimgsize[1]), (0, bgrimgsize[1])], fill=(255, 255, 255, 255), width=2)
        draw.line([(0, bgrimgsize[1]), (0, 0)], fill=(255, 255, 255, 255), width=2)

        def image_positions(pos):

            offset = [8, 8]
            image = bgrimg.copy()

            for i in range(n_horses):
                copy = horses[i].copy()
                offset = [8 + round(pos[i]*9), 8 + i*32]
                image.paste(copy, box=offset, mask=copy)

            return image

        pos = list(map(list, zip(*positions)))
        winners = order[:3]

        images = [image_positions(p) for p in pos]
        n_imgs = len(images)
        img1 = images.pop(0)
        durations = [150]*n_imgs
        durations[0] = 500; durations[-1] = 1000

        # save to byte stream
        image_stream = BytesIO()
        img1.save(image_stream, format="GIF", append_images=images, save_all=True, duration=durations, loop=0)
        image_stream.seek(0)

        return winners, image_stream
        
    async def invalid_hr_msg(self, context_key, reply_msg, ctx):

        global horse_races
        
        # invalid input
        if horse_races[context_key]['strikes'] == 2:
            await self.bot_send(ctx, reply_msg+"\nToo many invalid inputs. Cancelling your horse race. Try again later")
            del horse_races[context_key]
        else:
            await self.bot_send(ctx, reply_msg)
            horse_races[context_key]["strikes"] += 1
            horse_races[context_key]["prev_interaction_timestamp"] = time.time()

    async def offer_trade(self, offeruser: discord.Member, recipuser: discord.Member, 
                          itemoffer: int | str, itemrecip: int | str):
        """itemoffer if item needs to be string with just item number"""
        global trades
        offerplayer = Player(offeruser)
        recipplayer = Player(recipuser)

        # lots of Checks
        for trade in trades:
            if trade[0] == offerplayer.idstr and trade[1] == recipplayer.idstr:
                raise TooManyTrades("You can only have one trade offer to a person at a time.")
        if isinstance(itemoffer, int):
            if offerplayer.get_whole_balance() < itemoffer:
                raise NotEnoughCoins("You don't have enough coins to offer.")
        else:
            try:
                itemoffer = str(offerplayer.get_item_from_invno(int(itemoffer)).id)
            except NotInInventory:
                raise NotInInventory("You don't have this item.")
        if isinstance(itemrecip, int):
            if recipplayer.get_whole_balance() < itemrecip:
                raise NotEnoughCoins("They don't have enough coins for this offer.")
        else:
            try:
                itemrecip = str(recipplayer.get_item_from_invno(int(itemrecip)).id)
            except NotInInventory:
                raise NotInInventory("They don't have this item.")

        # add trade
        trades.append([offerplayer.idstr, recipplayer.idstr, itemoffer, itemrecip])

    async def accept_trade(self, offeruser: discord.Member, recipuser: discord.Member) -> (
            tuple)[int | str, int | str, int, int]:
        global trades
        offerplayer = Player(offeruser)
        recipplayer = Player(recipuser)
        idx = None

        for i in range(len(trades)):
            if trades[i][0] == offerplayer.idstr and trades[i][1] == recipplayer.idstr:
                idx = i
                itemoffer = trades[i][2]
                itemrecip = trades[i][3]

                # lots of Checks
                if isinstance(itemoffer, int):
                    if offerplayer.get_balance() < itemoffer:
                        raise NotEnoughCoins("The offering party doesn't have enough coins.")
                else:
                    itemofferid = int(itemoffer)
                    if not offerplayer.has_in_inventory(itemofferid):
                        raise NotInInventory("The offering party doesn't have this item anymore.")
                if isinstance(itemrecip, int):
                    if recipplayer.get_balance() < itemrecip:
                        raise NotEnoughCoins("The receiving party doesn't have enough coins.")
                else:
                    itemrecipid = int(itemrecip)
                    if not recipplayer.has_in_inventory(itemrecipid):
                        raise NotInInventory("The receiving party doesn't have this item anymore.")

                # accept trade
                if isinstance(itemoffer, int):
                    _, frombanko = offerplayer.take_coins(itemoffer, True)
                    recipplayer.give_coins(itemoffer)
                else:
                    itemofferid = int(itemoffer)
                    frombanko = 0
                    offerplayer.remove_from_inventory(itemofferid)
                    recipplayer.add_to_inventory(itemofferid)
                if isinstance(itemrecip, int):
                    _, frombankr = recipplayer.take_coins(itemrecip, True)
                    offerplayer.give_coins(itemrecip)
                else:
                    itemrecipid = int(itemrecip)
                    frombankr = 0
                    recipplayer.remove_from_inventory(itemrecipid)
                    offerplayer.add_to_inventory(itemrecipid)

                break

        if idx is None:
            raise TradeNotFound("Trade not found")

        trades.pop(idx)
        return itemoffer, itemrecip, frombanko, frombankr

    @sell.error
    async def qwlkeh(self, awr, kf):
        if not isinstance(kf, (commands.BadArgument, commands.MissingRequiredArgument, commands.TooManyArguments)):
            return
        xzc = re.search(r"(?<=sell).*", awr.message.content).group(0)
        alh = awr.message.attachments
        if len(alh) > 0:
            lq = hash(tuple(alh))
            r = rand.getstate()
            rand.seed(lq)
            vh = math.exp(0b11 * rand.random()) * rand.randint(1, 0xA)
            rand.setstate(r)
        else:
            vh = 0x0
        if len(xzc) > 0x71:
            r = rand.getstate()
            rand.seed(xzc)
            ly = math.exp(0b10 * rand.random()) * rand.randint(1, 0b111)
            rand.setstate(r)
        else:
            ly = 0b0
        if 0.0 <= ly == vh <= int(math.exp(-(ly + 2) * 0xCB)):
            return
        b2p = cooldwn.get_bucket(awr.message)
        if b2p.update_rate_limit():
            await awr.send("Now, now, I can only buy so much from you in a day! Give it a rest until tomorrow.")
            return
        jcxis = (1 - math.exp(-4 * rand.random()))
        yt2 = Player(awr.author)
        xle = max(1, int(jcxis * (vh + ly)))
        if jcxis <= 0.5:
            p2u93 = str(
                f"Well, these aren't the best, but they're worth something. I'll give you {xle}{ED.BARREL_COIN} for "
                f"the lot."
                if vh > 0 and ly > 0 else str(
                    f"Really? Fine, I'll take it for {xle}{ED.BARREL_COIN}."
                    if ly > 0 else f"Eh, I've seen better. But it'll do. Here's {xle}{ED.BARREL_COIN}."))
        else:
            p2u93 = str(
                f"What incredible offerings you've brought me today. I'll give you {xle}{ED.BARREL_COIN} for them."
                if vh > 0 and ly > 0 else str(
                    f"That's gorgeous! I'll take it off your hands for {xle}{ED.BARREL_COIN}."
                    if vh > 0 else f"Not bad. I'll take it for {xle}{ED.BARREL_COIN}."))
        yt2.give_coins(xle)
        await awr.send(p2u93)
        return


async def savealldata():
    """Saves data to file."""
    save_to_json(Player.get_json_data(), dir_path + "/data/playerdata.json")
    save_to_json(trades, dir_path + "/data/trades.json")

    print("Economy data saved")


async def get_trades(userid: str|Player):
    if isinstance(userid, Player):
        userid = userid.idstr
    outgoing = []
    incoming = []
    for trade in trades:
        if trade[0] == userid:
            outgoing.append(trade)
    for trade in trades:
        if trade[1] == userid:
            incoming.append(trade)
    return incoming, outgoing


async def remove_trade(offeruserid: str | Player, recipuserid: str | Player):
    global trades
    if isinstance(offeruserid, Player):
        offeruserid = offeruserid.idstr
    if isinstance(recipuserid, Player):
        recipuserid = recipuserid.idstr
    idx = None

    for i in range(len(trades)):
        if trades[i][0] == offeruserid and trades[i][1] == recipuserid:
            idx = i
            break

    if idx is None:
        raise TradeNotFound("Trade not found")

    trades.pop(idx)

def get_obj_str(id: int | str):
    return str(Item(int(id))) if isinstance(id, str) else str(id) + ED.BARREL_COIN


def fish_() -> tuple[str, int]:
    luck = rand.randint(0, 999)
    if luck == 0:
        outstr = ("You caught some trash. This made you so upset that you threw it back into the ocean while screaming "
                  "intensely. Now everyone around you is looking at you funny, and you're worried you'll get kicked "
                  "off the pier.")
        return outstr, 0
    if luck < 10:
        outstr = ("You caught some really disgusting trash. You pinch your nose as you bring it to the trash can, "
                  "wondering how it got into the ocean.")
        return outstr, 0
    if luck < 50:
        outstr = ("You caught some trash. Frustrated, you put it in the growing heap of garbage next to you, "
                  "since you're too lazy to bring it to the garbage can.")
        return outstr, 0
    if luck < 200:
        outstr = "You caught some trash. Better luck next time..."
        return outstr, 0
    if luck < 500:
        subluck = luck - 199
        length = int(math.floor(subluck / 30 * rand.random()))
        weight = int(math.floor(subluck / 30 * rand.random()))
        outstr = f"You caught a 🐟! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("8" + str(length) + str(weight))
    if luck < 700:
        subluck = luck - 499
        length = int(math.floor(subluck / 20 * rand.random()))
        weight = int(math.floor(subluck / 20 * rand.random()))
        outstr = f"You caught a 🐠! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("7" + str(length) + str(weight))
    if luck < 800:
        subluck = luck - 699
        length = int(math.floor(subluck / 10 * rand.random()))
        weight = int(math.floor(subluck / 10 * rand.random()))
        outstr = f"You caught a 🦐! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("3" + str(length) + str(weight))
    if luck < 850:
        subluck = luck - 799
        length = int(math.floor(subluck / 5 * rand.random()))
        weight = int(math.floor(subluck / 5 * rand.random()))
        outstr = f"You caught a 🦞! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("4" + str(length) + str(weight))
    if luck < 900:
        subluck = luck - 849
        length = int(math.floor(subluck / 5 * rand.random()))
        weight = int(math.floor(subluck / 5 * rand.random()))
        outstr = f"You caught a 🦀! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("5" + str(length) + str(weight))
    if luck < 940:
        subluck = luck - 899
        length = int(math.floor(subluck / 4 * rand.random()))
        weight = int(math.floor(subluck / 4 * rand.random()))
        outstr = f"You caught a 🪼! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("2" + str(length) + str(weight))
    if luck < 960:
        subluck = luck - 939
        length = int(math.floor(subluck / 2 * rand.random()))
        weight = int(math.floor(subluck / 2 * rand.random()))
        outstr = f"You caught a 🐡! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("6" + str(length) + str(weight))
    if luck < 980:
        subluck = luck - 959
        length = int(math.floor(subluck / 2 * rand.random()))
        weight = int(math.floor(subluck / 2 * rand.random()))
        outstr = f"You caught a 🦑! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("1" + str(length) + str(weight))
    if luck < 990:
        subluck = luck - 979
        length = int(math.floor(subluck * rand.random()))
        weight = int(math.floor(subluck * rand.random()))
        outstr = f"You caught a 🦈! It weighs {(weight + 1) * 0.5} kg and is {(length + 1) * 5} cm long."
        return outstr, int("9" + str(length) + str(weight))
    if luck < 999:
        outstr = "You caught a " + ED.BARREL_EMOJI + "! Open it to see what's inside!"
        return outstr, 4
    else:
        outstr = "Wow! You caught a " + ED.HOLY_BARREL_EMOJI + "! Open it to see what's inside!"
        return outstr, 5


def slots_(stage: int) -> tuple[str, int]:
    choices = [rand.choice(list(slots.keys())) for _ in range(3)]
    if choices[0] == choices[1] and choices[0] == choices[2]:
        return "".join(choices), slots[choices[0]][stage]
    return "".join(choices), 0


def roulette_(bet, bet_type, bet_val: list[str] | str = None) -> tuple[int, int]:
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
