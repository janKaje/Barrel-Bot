import os
import re
import datetime as dt
import pickle
from time import time
import io
from json import dumps

import discord
from discord.ext import commands, tasks
import matplotlib.pyplot as plt
import numpy as np

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Get is_in_dev_mode data to know whether it's in dev or on the server
# .env is loaded from barrelbot.py
IS_IN_DEV_MODE = os.environ["IS_IN_DEV_MODE"]

# Consts
BARREL_CULT_GUILD_ID = 1296983356541501440

## Debug
if IS_IN_DEV_MODE :
    BARREL_CULT_GUILD_ID = 733508144185081939
##

try:
    with open(dir_path + "/data/analytics.pkl", "rb") as file:
        analytics:dict = pickle.load(file)
except:
    analytics = {"prev_update": {}}


async def setup(bot):
    await bot.add_cog(Analytics(bot))


class Analytics(commands.Cog, name="Analytics"):

    """Keeps track of some cool things."""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_analytics(self, ctx: commands.Context, graphtype='normal', style='seaborn-v0_8'):

        """Shows an analytics graph.
        `graphtype` The type of graph to show.
        options: normal, adjusted
        default: normal
        `style` The style to use for displaying the graph.
        options: any found on https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
        default: seaborn-v0_8"""
        
        async with ctx.channel.typing():
            if graphtype == 'normal':
                data_stream = await self.get_analytics_stackplot(style)
            elif graphtype == 'adjusted':
                data_stream = await self.get_adj_stackplot(style)
            else:
                await self.bot_send(ctx, "I don't know that type. Try again or get more info with `bb help show_analytics`")
                return
        
        chart = discord.File(data_stream, filename="analytics_chart.png")
        emb = discord.Embed()
        emb.set_image(url="attachment://analytics_chart.png")

        await self.bot_send(ctx, embed=emb, file=chart)

    async def cog_load(self):
        global analytics
        await self.bot.wait_until_ready()
        self.barrelcultguild = await self.bot.fetch_guild(BARREL_CULT_GUILD_ID)
        self.memberinst = None
        async for member in self.barrelcultguild.fetch_members():
            if member.id == self.bot.user.id:
                self.memberinst = member
        timer = time()
        msgcount = 0
        channelcount = 0
        print(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t Starting analytics...")
        # go back through all messages not done
        if len(analytics.keys()) == 1:
            print(f"First time analytics!")
        for channel in self.bot.get_all_channels():

            #make sure is a valid channel for analytics
            if not self.is_analytics_channel(channel):
                continue

            channelcount += 1
            # if not previously loaded, set last load time to way long ago
            if channel.id not in analytics["prev_update"].keys():
                analytics["prev_update"][channel.id] = dt.datetime.fromtimestamp(1729295514) # earliest message

            thischmsgcount = 0
            # iterate through previous messages in channel
            async for message in channel.history(after=analytics["prev_update"][channel.id], limit=None):
                if message.author.bot:
                    continue
                msgcount += await self.parse_message(message)
                thischmsgcount += 1
                if thischmsgcount % 100 == 0:
                    print(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t {thischmsgcount} messages analyzed in {channel.name}")

        print(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t Analytics complete! Analyzed {msgcount} messages in {channelcount} channels. Time elapsed: {round(time()-timer, 5)} seconds")
        
        self.sixhourlyloop.start()

    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        if self.is_analytics_channel(message.channel):
            await self.parse_message(message)

    async def parse_message(self, message:discord.Message) -> int:
        global analytics

        authorid = message.author.id
        
        if authorid not in analytics.keys():
            analytics[authorid] = [[], {}] # timestamps, emojis + usages
        
        # add timestamp of message
        analytics[authorid][0].append(int(message.created_at.timestamp()))

        # go through emojis
        for emoji in message.guild.emojis:
            # find all emojis in message
            for match in re.finditer(f"<{('a' if emoji.animated else '')}:{emoji.name}:{emoji.id}>", message.content):
                # debug: make sure this regex works
                if match == None:
                    continue
                # add 1 to emoji count
                if emoji.id not in analytics[authorid][1].keys():
                    analytics[authorid][1][emoji.id] = 1
                else:
                    analytics[authorid][1][emoji.id] += 1

        # update data of when analytics was last done in each channel
        analytics["prev_update"][message.channel.id] = message.created_at
        return 1

    @commands.command()
    @commands.is_owner()
    async def saveanalyticsdata(self, ctx:commands.Context):
        save_to_pickle(analytics, dir_path+"/data/analytics.pkl")
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getanalyticsdata(self, ctx: commands.Context, key:str):
        if key == "prev_update":
            tosend = dict([[self.bot.get_channel(id).name, dtobj.isoformat(sep=' ', timespec='seconds')] for id, dtobj in analytics['prev_update'].items()])
            await self.bot_send(ctx, dumps(tosend, indent=1))
            return
        try:
            key = int(key)
            analytics[key]
        except:
            await self.bot_send(ctx, "Don't know that one...")
            return
        await self.bot_send(ctx, dumps(analytics[key]))

    @commands.command()
    @commands.is_owner()
    async def redo_analytics(self, ctx:commands.Context):
        return
        
        global analytics
        analytics = {"prev_update": {}}
        await self.bot.wait_until_ready()
        self.barrelcultguild = await self.bot.fetch_guild(BARREL_CULT_GUILD_ID)
        self.memberinst = None
        async for member in self.barrelcultguild.fetch_members():
            if member.id == self.bot.user.id:
                self.memberinst = member
        timer = time()
        msgcount = 0
        channelcount = 0
        print(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t Starting analytics...")
        # go back through all messages not done
        if len(analytics.keys()) == 1:
            print(f"First time analytics!")
        for channel in self.bot.get_all_channels():

            #make sure is a valid channel for analytics
            if not self.is_analytics_channel(channel):
                continue

            channelcount += 1
            analytics["prev_update"][channel.id] = dt.datetime.fromtimestamp(1729295514) # earliest message

            thischmsgcount = 0
            # iterate through previous messages in channel
            async for message in channel.history(after=analytics["prev_update"][channel.id], limit=None):
                if message.author.bot:
                    continue
                msgcount += await self.parse_message(message)
                thischmsgcount += 1
                if thischmsgcount % 100 == 0:
                    print(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t {thischmsgcount} messages analyzed in {channel.name}")

        print(f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t Analytics complete! Analyzed {msgcount} messages in {channelcount} channels. Time elapsed: {round(time()-timer, 5)} seconds")

    @tasks.loop(hours=6)
    async def sixhourlyloop(self):
        save_to_pickle(analytics, dir_path+"/data/analytics.pkl")
        print("analytics saved")

    async def get_analytics_stackplot(self, style:str) -> io.BytesIO:
        plt.style.use('default') # reset so things don't persist
        plt.style.use(style)

        xdata, ydata, authors = await self.get_graph_data()

        fig, ax = plt.subplots()

        ax.stackplot(xdata, ydata, labels=authors)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc="center left", bbox_to_anchor=(1, 0.5))
        ax.set_ylabel("Total number of messages sent")

        tickvals = np.linspace(xdata[0], xdata[-1], 4)
        ax.set_xticks(tickvals)
        ax.set_xticklabels([dt.date.fromtimestamp(ts).isoformat() for ts in tickvals])
        ax.set_xlim(xdata[0], xdata[-1])

        plt.title("Total Messages in the Server, by person")

        data_stream = io.BytesIO()
        fig.savefig(data_stream, format="png", bbox_inches = "tight")
        plt.close()
        data_stream.seek(0)
        return data_stream

    async def get_adj_stackplot(self, style:str) -> io.BytesIO:
        plt.style.use('default') # reset so things don't persist
        plt.style.use(style)

        xdata, ydata, authors = await self.get_graph_data()

        tydata = ydata.transpose()
        tydata2 = np.array([100*timeslot/sum(timeslot) for timeslot in tydata])
        ydata = tydata2.transpose()

        fig, ax = plt.subplots()

        ax.stackplot(xdata, ydata, labels=authors)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles[::-1], labels[::-1], loc="center left", bbox_to_anchor=(1, 0.5))
        ax.set_ylabel("Total number of messages sent")

        tickvals = np.linspace(xdata[0], xdata[-1], 4)
        ax.set_xticks(tickvals)
        ax.set_xticklabels([dt.date.fromtimestamp(ts).isoformat() for ts in tickvals])
        ax.set_xlim(xdata[0], xdata[-1])
        ax.set_ylim(0,100)

        plt.title("Percent of Messages in the Server, by person")

        data_stream = io.BytesIO()
        fig.savefig(data_stream, format="png", bbox_inches = "tight")
        plt.close()
        data_stream.seek(0)
        return data_stream

    async def get_graph_data(self):
        mintime = 1729295514 # a little before epoch time of first msg in barrel cult server
        nowtime = np.ceil(time()) # make sure to catch everything in analytics
        xdata = np.linspace(mintime, nowtime, 101)
        ydata = []
        authors = []

        for authorid in analytics.keys():
            if authorid == "prev_update":
                continue
            hist, _ = np.histogram(analytics[authorid][0], bins=100, range=(mintime, nowtime))
            ydata.append(np.cumsum(hist))
            try:
                author = await self.barrelcultguild.fetch_member(int(authorid))
                authors.append(author.display_name)
            except discord.NotFound:
                authors.append(f"User {authorid}")
        
        return xdata[1:], np.array(ydata), authors

    def is_analytics_channel(self, channel):
        return isinstance(channel, discord.TextChannel)\
            and channel.guild.id == BARREL_CULT_GUILD_ID\
            and channel.permissions_for(self.memberinst).read_message_history\
            and channel.id != 1297596333976453291\
            and channel.id != 1364450362421022750

def save_to_pickle(data, filename: str) -> None:
    """Saves specific dataset to file"""
    with open(filename, "wb") as file:
        pickle.dump(data, file)