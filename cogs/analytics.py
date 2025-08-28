import os
import sys
import re
import datetime as dt
import pickle
from time import time
import io
from json import dumps
import itertools

import discord
from discord.ext import commands, tasks
import matplotlib.pyplot as plt
import matplotlib.colorizer as clrs
import numpy as np

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(dir_path, "base"))

import env

try:
    with open(dir_path + "/data/analytics.pkl", "rb") as file:
        analytics: dict = pickle.load(file)
except:
    analytics = {"prev_update": {}}

DEFAULT_STACKPLOT_STYLE = 'seaborn-v0_8'
DEFAULT_BARCHART_STYLE = 'seaborn-v0_8-dark'
DEFAULT_BARCHART_COLOR = '#329F55'
DEFAULT_HEATMAP_STYLE = 'seaborn-v0_8-dark'
DEFAULT_HEATMAP_COLORMAP = 'YlGn'

async def setup(bot):
    await bot.add_cog(Analytics(bot))


class Analytics(commands.Cog, name="Analytics"):
    """Keeps track of some cool things."""

    def __init__(self, bot: commands.Bot):
        self.memberinst = None
        self.barrelcultguild = None
        self.bot = bot
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    @commands.command(help=f"""Shows an analytics graph.
        `graphtype` The type of graph to show.
        options: normal, adjusted
        default: normal
        `style` The style to use for displaying the graph.
        options: any found on https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
        default: {DEFAULT_STACKPLOT_STYLE}""")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_analytics(self, ctx: commands.Context, graphtype='normal', style=DEFAULT_STACKPLOT_STYLE):

        async with ctx.channel.typing():
            if graphtype == 'normal':
                data_stream = await self.get_analytics_stackplot(style)
            elif graphtype == 'adjusted':
                data_stream = await self.get_adj_stackplot(style)
            else:
                await self.bot_send(ctx,
                                    "I don't know that type. Try again or get more info with `bb help show_analytics`")
                return

        chart = discord.File(data_stream, filename="analytics_chart.png")
        emb = discord.Embed()
        emb.set_image(url="attachment://analytics_chart.png")

        await self.bot_send(ctx, embed=emb, file=chart)

    @commands.command(help=f"""Shows which emojis you've used, and how many times each was used.
        `style` The style to use for displaying the graph.
        options: any found on https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
        default: {DEFAULT_BARCHART_STYLE}
        `color` The color to fill the bars with.
        options: any found on https://matplotlib.org/stable/users/explain/colors/colors.html#colors-def
        default: {DEFAULT_BARCHART_COLOR}""")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_my_emoji_usages(self, ctx:commands.Context, style=DEFAULT_BARCHART_STYLE, color:str=DEFAULT_BARCHART_COLOR):

        async with ctx.channel.typing():
            try:
                data_stream = await self.get_emoji_barchart(member=ctx.author, style=style, color=color)
            except ValueError as e:
                await self.bot_send(ctx, f"Something happened that shouldn't have:\n{e}")
                return
            except discord.NotFound as e:
                await self.bot_send(ctx, f"Something happened that REALLY shouldn't have:\n{e}")
                return
            
        chart = discord.File(data_stream, filename="emoji_barchart.png")
        emb = discord.Embed()
        emb.set_image(url="attachment://emoji_barchart.png")

        await self.bot_send(ctx, embed=emb, file=chart)

    @commands.command(help=f"""Shows who has used the given emoji, and how many times each person used it.
        `emoji` The emoji to see usages for.
        `style` The style to use for displaying the graph.
        options: any found on https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
        default: {DEFAULT_BARCHART_STYLE}
        `color` The color to fill the bars with.
        options: any found on https://matplotlib.org/stable/users/explain/colors/colors.html#colors-def
        default: {DEFAULT_BARCHART_COLOR}""")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_this_emojis_usages(self, ctx:commands.Context, emoji:discord.Emoji, style:str=DEFAULT_BARCHART_STYLE, color:str=DEFAULT_BARCHART_COLOR):

        async with ctx.channel.typing():
            try:
                data_stream = await self.get_emoji_barchart(emoji=emoji, style=style, color=color)
            except ValueError as e:
                await self.bot_send(ctx, f"Something happened that shouldn't have:\n{e}")
                return
            except discord.NotFound as e:
                await self.bot_send(ctx, f"Something happened that REALLY shouldn't have:\n{e}")
                return
            
        chart = discord.File(data_stream, filename="emoji_barchart.png")
        emb = discord.Embed()
        emb.set_image(url="attachment://emoji_barchart.png")

        await self.bot_send(ctx, embed=emb, file=chart)

    @commands.command(help=f"""Shows all emoji usage data.
        `style` The style to use for displaying the graph.
        options: any found on https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
        default: {DEFAULT_HEATMAP_STYLE}
        `cmap` The color map to use for the graph.
        options: any found on https://matplotlib.org/stable/gallery/color/colormap_reference.html
        default: {DEFAULT_HEATMAP_COLORMAP}""")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def show_emoji_usages(self, ctx:commands.Context, style:str=DEFAULT_HEATMAP_STYLE, cmap:str=DEFAULT_HEATMAP_COLORMAP):

        async with ctx.channel.typing():
            try:
                data_stream = await self.get_emoji_heatmap(style=style, cmap=cmap)
            except ValueError as e:
                if env.BBGLOBALS.IS_IN_DEV_MODE:
                    await self.bot_send(ctx, f"Something happened that shouldn't have:\n{e.with_traceback(None)}")
                    print(e.with_traceback(None))
                    return
                else:
                    await self.bot_send(ctx, f"Something happened that shouldn't have:\n{e}")
                    return
            except discord.NotFound as e:
                await self.bot_send(ctx, f"Something happened that REALLY shouldn't have:\n{e}")
                return
            
        chart = discord.File(data_stream, filename="emoji_heatmap.png")
        emb = discord.Embed()
        emb.set_image(url="attachment://emoji_heatmap.png")

        await self.bot_send(ctx, embed=emb, file=chart)

    async def cog_load(self):
        global analytics
        await self.bot.wait_until_ready()
        self.barrelcultguild = await self.bot.fetch_guild(env.BBGLOBALS.BARREL_CULT_GUILD_ID)
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

            # make sure is a valid channel for analytics
            if not self.is_analytics_channel(channel):
                continue

            channelcount += 1
            # if not previously loaded, set last load time to way long ago
            if channel.id not in analytics["prev_update"].keys():
                analytics["prev_update"][channel.id] = dt.datetime.fromtimestamp(1729295514)  # earliest message

            thischmsgcount = 0
            # iterate through previous messages in channel
            async for message in channel.history(after=analytics["prev_update"][channel.id], limit=None):
                if message.author.bot:
                    continue
                msgcount += await self.parse_message(message)
                thischmsgcount += 1
                if thischmsgcount % 100 == 0:
                    print(
                        f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t {thischmsgcount} messages "
                        f"analyzed in {channel.name}")

        print(
            f"{dt.datetime.now().isoformat(sep=' ', timespec='seconds')} INFO\t Analytics complete! Analyzed "
            f"{msgcount} messages in {channelcount} channels. Time elapsed: {round(time() - timer, 5)} seconds")

        self.sixhourlyloop.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if self.is_analytics_channel(message.channel) and not message.author.bot:
            await self.parse_message(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        channel = await self.bot.fetch_channel(payload.channel_id)
        user = await channel.guild.fetch_member(payload.user_id)
        emoji = payload.emoji
        if self.is_analytics_channel(channel) and not user.bot and emoji.is_custom_emoji():
            if user.id not in analytics.keys():
                return
            if emoji.id not in analytics[user.id][1].keys():
                analytics[user.id][1][emoji.id] = 1
            else:
                analytics[user.id][1][emoji.id] += 1

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        channel = await self.bot.fetch_channel(payload.channel_id)
        user = await channel.guild.fetch_member(payload.user_id)
        emoji = payload.emoji
        if self.is_analytics_channel(channel) and not user.bot and emoji.is_custom_emoji():
            if user.id not in analytics.keys():
                return
            if emoji.id not in analytics[user.id][1].keys():
                pass
            else:
                analytics[user.id][1][emoji.id] -= 1

    @staticmethod
    async def parse_message(message: discord.Message) -> int:
        global analytics

        authorid = message.author.id

        if authorid not in analytics.keys():
            analytics[authorid] = [[], {}]  # timestamps, emojis + usages

        # add timestamp of message
        analytics[authorid][0].append(int(message.created_at.timestamp()))

        # go through emojis
        for emoji in message.guild.emojis:
            # find all emojis in message
            for match in re.finditer(f"<{('a' if emoji.animated else '')}:{emoji.name}:{emoji.id}>", message.content):
                # debug: make sure this regex works
                if match is None:
                    continue
                # add 1 to emoji count
                if emoji.id not in analytics[authorid][1].keys():
                    analytics[authorid][1][emoji.id] = 1
                else:
                    analytics[authorid][1][emoji.id] += 1

        # go through reactions
        for reaction in message.reactions:
            if isinstance(reaction.emoji, discord.Emoji):
                async for reactor in reaction.users():
                    if reactor.bot:
                        continue
                    if reactor.id not in analytics.keys():
                        analytics[reactor.id] = [[], {}]
                    if reaction.emoji.id not in analytics[reactor.id][1].keys():
                        analytics[reactor.id][1][reaction.emoji.id] = 1
                    else:
                        analytics[reactor.id][1][reaction.emoji.id] += 1

        # update data of when analytics was last done in each channel
        analytics["prev_update"][message.channel.id] = message.created_at
        return 1

    @commands.command()
    @commands.is_owner()
    async def saveanalyticsdata(self, ctx: commands.Context):
        save_to_pickle(analytics, dir_path + "/data/analytics.pkl")
        await self.bot_send(ctx, "Done!")

    @commands.command()
    @commands.is_owner()
    async def getanalyticsdata(self, ctx: commands.Context, key: str):
        if key == "prev_update":
            tosend = dict(
                [[self.bot.get_channel(ch_id).name, dtobj.isoformat(sep=' ', timespec='seconds')] for ch_id, dtobj in
                 analytics['prev_update'].items()])
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
    async def delete_analytics_data(self, ctx: commands.Context):

        global analytics
        analytics = {"prev_update": {}}
        save_to_pickle(analytics, dir_path + "/data/analytics.pkl")

        await self.bot_send(ctx, "Analytics deleted. Restart the bot to redo all analytics")

    @tasks.loop(hours=6)
    async def sixhourlyloop(self):
        save_to_pickle(analytics, dir_path + "/data/analytics.pkl")
        print("analytics saved")

    async def get_analytics_stackplot(self, style: str) -> io.BytesIO:
        plt.style.use('default')  # reset so things don't persist
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
        fig.savefig(data_stream, format="png", bbox_inches="tight")
        plt.close()
        data_stream.seek(0)
        return data_stream

    async def get_adj_stackplot(self, style: str) -> io.BytesIO:
        plt.style.use('default')  # reset so things don't persist
        plt.style.use(style)

        xdata, ydata, authors = await self.get_graph_data()

        tydata = ydata.transpose()
        tydata2 = np.array([100 * timeslot / sum(timeslot) for timeslot in tydata])
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
        ax.set_ylim(0, 100)

        plt.title("Percent of Messages in the Server, by person")

        data_stream = io.BytesIO()
        fig.savefig(data_stream, format="png", bbox_inches="tight")
        plt.close()
        data_stream.seek(0)
        return data_stream
    
    async def get_emoji_barchart(self, *, member:discord.Member=None, emoji:discord.Emoji=None, style:str=DEFAULT_BARCHART_STYLE, color:str=DEFAULT_BARCHART_COLOR) -> io.BytesIO:
        plt.style.use('default')  # reset so things don't persist
        plt.style.use(style)

        fig, ax = plt.subplots()

        if member is None:
            emojidat = await self.get_emoji_usages(emoji=emoji)
            ax.set_title(f"Emoji usage statistics for :{emoji.name}:")
        elif emoji is None:
            emojidat = await self.get_emoji_usages(member=member)
            ax.set_title(f"Emoji usage statistics for {member.display_name}")
        else:
            raise ValueError("Only one of member or emoji can be specified for get_emoji_barchart")

        p = ax.bar(emojidat.keys(), emojidat.values(), color=color)
        ax.bar_label(p, padding=3)
        ax.set_ylabel("Times used in server")
        ax.set_ylim(0, max(emojidat.values())*1.1)
        ax.set_xticks(range(len(emojidat.keys())), labels=emojidat.keys(),
                      rotation=45, ha="right", rotation_mode="anchor")
        fig.set_size_inches(1.25 + 0.35*len(emojidat), 3 + 0.1*len(emojidat))

        data_stream = io.BytesIO()
        fig.savefig(data_stream, format="png", bbox_inches="tight")
        plt.close()
        data_stream.seek(0)
        return data_stream
    
    async def get_emoji_heatmap(self, style:str=DEFAULT_HEATMAP_STYLE, cmap:str=DEFAULT_HEATMAP_COLORMAP) -> io.BytesIO:
        plt.style.use('default')  # reset so things don't persist
        plt.style.use(style)

        emojidat = await self.get_emoji_usages()
        usernames = list(emojidat.keys())
        emojis = list(set(itertools.chain(*[emojidat[key].keys() for key in emojidat.keys()])))

        usages = np.zeros((len(usernames), len(emojis)))
        for i, usern in enumerate(usernames):
            for j, emoji in enumerate(emojis):
                if emoji in emojidat[usern].keys():
                    usages[i,j] = emojidat[usern][emoji]

        maxusages = np.max(usages)
        norm = "symlog"
        aspect = 0.9

        fig, ax = plt.subplots()
        im = ax.imshow(usages, cmap=cmap, norm=norm, aspect=aspect, extent=(-0.5, len(emojis)/aspect-0.5, len(usernames)-0.5, -0.5))

        # Show all ticks and label them with the respective list entries
        ax.set_xticks(np.arange(len(emojis))/aspect, labels=emojis,
                    rotation=45, ha="right", rotation_mode="anchor")
        ax.set_yticks(range(len(usernames)), labels=usernames)

        # Loop over data dimensions and create text annotations.
        for i in range(len(emojis)):
            for j in range(len(usernames)):
                try:
                    rgba = clrs.Colorizer(cmap=cmap, norm=norm).to_rgba([usages[j, i], maxusages, 0])
                    r, g, b, a = rgba[0]
                    brightness = a*np.sqrt(0.299*r**2 + 0.587*g**2 + 0.114*b**2)
                    useblack = brightness > 0.5
                    text = ax.text(i/aspect+0.075, j+0.05, int(usages[j, i]),
                                ha="center", va="center", color=str("k" if useblack else "w"), fontsize=7)
                except Exception as e:
                    if env.BBGLOBALS.IS_IN_DEV_MODE:
                        print(i, j)
                        print(e.with_traceback(None))
                    raise e

        ax.set_title("Emoji usages")
        ax.spines[:].set_visible(False)

        ax.set_xticks(np.arange(len(emojis)+1)/aspect-.5, minor=True)
        ax.set_yticks(np.arange(len(usernames)+1)-.5, minor=True)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)
        fig.set_size_inches(1 + 0.3*len(emojis), 1 + 0.3*len(usernames))

        data_stream = io.BytesIO()
        fig.savefig(data_stream, format="png", bbox_inches="tight")
        plt.close()
        data_stream.seek(0)
        return data_stream

    async def get_graph_data(self):
        mintime = 1729295514  # a little before epoch time of first msg in barrel cult server
        nowtime = np.ceil(time())  # make sure to catch everything in analytics
        xdata = np.linspace(mintime, nowtime, 101)
        ydata = []
        authors = []

        for authorid in analytics.keys():
            if authorid == "prev_update":
                continue
            try:
                author = await self.barrelcultguild.fetch_member(int(authorid))
                authors.append(author.display_name)
            except discord.NotFound:
                continue
            hist, _ = np.histogram(analytics[authorid][0], bins=100, range=(mintime, nowtime))
            ydata.append(np.cumsum(hist))

        return xdata[1:], np.array(ydata), authors
    
    async def get_emoji_usages(self, *, member:discord.Member=None, emoji:discord.Emoji=None) -> dict:
        """Get data for emoji usages. If member is specified, gets their personal emoji usage data.
        If emoji is specified, gets server data for that emoji. If neither are specified, gets all emoji usage
        data."""

        if member is None and emoji is None:
            # All usage data
            # Data structure: {
            #   authorname: {
            #       emojiid: timesused
            #   }
            # }
            dat = {}
            emojis = {}
            for memberid in analytics.keys():
                if memberid == "prev_update":
                    continue
                try:
                    member = await self.barrelcultguild.fetch_member(int(memberid))
                except discord.NotFound:
                    continue
                if member.bot:
                    continue
                dat[member.display_name] = {}
                for emojiid, timesused in analytics[memberid][1].items():
                    if emojiid in emojis.keys():
                        dat[member.display_name][emojis[emojiid]] = timesused
                        continue
                    try:
                        emoji = await self.barrelcultguild.fetch_emoji(emojiid)
                    except discord.NotFound:
                        continue
                    dat[member.display_name][emoji.name] = timesused
                    emojis[emojiid] = emoji.name
                if len(dat[member.display_name].keys()) == 0:
                    dat.pop(member.display_name)
            if len(dat.keys()) == 0:
                raise ValueError("Wow, there is... zero emoji data. Maybe you need to redo analytics?")
            return dat
        
        elif emoji is None:
            # Member usage data
            # Data structure: {
            #   emoji: timesused
            # }
            _ = await self.barrelcultguild.fetch_member(int(member.id))
            dat = {}
            if member.id not in analytics.keys():
                raise ValueError("You don't have any emoji data - maybe start using them!")
            for key, val in analytics[member.id][1].items():
                try:
                    emoji = await self.barrelcultguild.fetch_emoji(key)
                except discord.NotFound:
                    continue
                dat[emoji.name] = val
            return dat
        
        elif member is None:
            # Emoji usage data
            # Data structure: {
            #   authorname: timesused
            # }
            dat = {}
            for memberid in analytics.keys():
                if memberid == "prev_update":
                    continue
                try:
                    member = await self.barrelcultguild.fetch_member(int(memberid))
                except discord.NotFound:
                    continue
                if emoji.id in analytics[memberid][1].keys():
                    dat[member.display_name] = analytics[memberid][1][emoji.id]
            if len(dat.keys()) == 0:
                raise ValueError("Wow, there is... zero data on this emoji. Literally nobody has used it yet")
            return dat
        
        else:
            raise ValueError("Either member or emoji must be specified for get_emoji_usages")


    def is_analytics_channel(self, channel):
        return isinstance(channel, discord.TextChannel) \
            and channel.guild.id == env.BBGLOBALS.BARREL_CULT_GUILD_ID \
            and channel.permissions_for(self.memberinst).read_message_history \
            and channel.id not in env.BBGLOBALS.BB_CHANNEL_IDS


def save_to_pickle(data, filename: str) -> None:
    """Saves specific dataset to file"""
    if env.BBGLOBALS.IS_IN_DEV_MODE:
        print("dev mode - analytics NOT saved")
        return
    with open(filename, "wb") as file:
        pickle.dump(data, file)
