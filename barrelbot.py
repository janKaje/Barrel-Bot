import math
import os
import re
import sys
import asyncio
import datetime as dt
from sqlite3 import OperationalError
from shutil import copyfile

from base import env
from base.emojis import EmojiDefs as ED
from base.messagetosend import UnsentMessage
from base.guild_config import GUILD_CONFIG as GC
from base.misc import is_command, time_str

import discord
from discord.ext import commands, tasks

dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(dir_path, "base"))
from extra_exceptions import NotAbleTo, PlayerNotFound, NotInBbChannel

env.BBGLOBALS.init_globals()

# Debug
if env.BBGLOBALS.IS_IN_DEV_MODE:
    print("New debugging session started in bot testing server")


# Initialize intents
Intents = discord.Intents.default()
Intents.messages = True
Intents.members = True
Intents.guild_messages = True
Intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=is_command, intents=Intents,
                   allowed_mentions=discord.AllowedMentions(everyone=False))
bot.remove_command('help')

# Create global variables
dir_path = os.path.dirname(os.path.abspath(__file__))
defaultctx = None
messagequeue = asyncio.Queue()


# get token
TOKEN = os.environ["TOKEN"]


# prep for save functions
async def save_everything():

    global defaultctx
    assert defaultctx is not None, "Default context hasn't been established yet"

    funcog = bot.get_cog("Fun")
    spamcog = bot.get_cog("Barrel Spam")
    analyticscog = bot.get_cog("Analytics")
    economycog = bot.get_cog("Economy")

    for command in economycog.get_commands():
        if command.name == "saveeconomydata":
            await command.__call__(defaultctx)
            break

    for command in funcog.get_commands():
        if command.name == "savefundata":
            await command.__call__(defaultctx)
            break

    for command in spamcog.get_commands():
        if command.name == "savespamdata":
            await command.__call__(defaultctx)
            break

    for command in analyticscog.get_commands():
        if command.name == "saveanalyticsdata":
            await command.__call__(defaultctx)
            break


async def load_cog(cogname, cogn2):
    try:
        await bot.load_extension(cogname)
    except Exception as e:
        print(f"was not able to load cog {cogname}:\n{e.with_traceback(None)}")
    try:
        cog = bot.get_cog(cogn2)
        cog.set_bot_send(bot_send)
    except Exception as e:
        print(f"Error in adding bot_send: {e.with_traceback(None)}")

# guild configuration
# always active: fun, utilities, economy
# cult specific: analytics, chat, spam, news
# toggleable: robbing, gambling
# configurable: bb channel
@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def view_server_config(ctx: commands.Context):
    """View current server settings"""

    gambling, robbing, channel_ids = GC.get_server_config(ctx.guild)

    emb = discord.Embed(color=discord.Colour.og_blurple(),
                        title=f"Settings for {ctx.guild.name}",
                        description=f"Gambling: {('enabled' if gambling else 'disabled')}\n" +\
                            f"Robbing: {('enabled' if robbing else 'disabled')}")
    
    emb.add_field(name="Channels with economy enabled", 
                  value='\n'.join([bot.get_channel(id).mention for id in channel_ids]),
                  inline = False)
    
    await bot_send(ctx, embed=emb)

@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def enable_gambling(ctx: commands.Context):
    """Enable gambling on this server"""
    if GC.is_gambling_enabled(ctx.guild):
        await bot_send(ctx, "Gambling is already enabled for this server.")
    else:
        GC.update_gambling(ctx.guild, True)
        await bot_send(ctx, f"Gambling is now enabled on {ctx.guild.name}")

@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def disable_gambling(ctx: commands.Context):
    """Disable gambling on this server"""
    if not GC.is_gambling_enabled(ctx.guild):
        await bot_send(ctx, "Gambling is already disabled for this server.")
    else:
        GC.update_gambling(ctx.guild, False)
        await bot_send(ctx, f"Gambling is now disabled on {ctx.guild.name}")
        
@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def enable_robbing(ctx: commands.Context):
    """Enable robbing on this server"""
    if GC.is_robbing_enabled(ctx.guild):
        await bot_send(ctx, "Robbing is already enabled for this server.")
    else:
        GC.update_robbing(ctx.guild, True)
        await bot_send(ctx, f"Robbing is now enabled on {ctx.guild.name}")

@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def disable_robbing(ctx: commands.Context):
    """Disable robbing on this server"""
    if not GC.is_robbing_enabled(ctx.guild):
        await bot_send(ctx, "Robbing is already disabled for this server.")
    else:
        GC.update_robbing(ctx.guild, False)
        await bot_send(ctx, f"Robbing is now disabled on {ctx.guild.name}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def add_channel(ctx: commands.Context):
    """Adds this channel to BarrelBot's list of channels that economy commands are enabled in."""
    if GC.is_bb_channel(ctx.channel):
        await bot_send(ctx, "Economy commands are already enabled in this channel")
    else:
        GC.add_bb_channel(ctx.channel)
        await bot_send(ctx, f"Economy commands are now enabled in {ctx.channel.name}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def remove_channel(ctx: commands.Context):
    """Removes this channel from BarrelBot's list of channels that economy commands are enabled in."""
    if not GC.is_bb_channel(ctx.channel):
        await bot_send(ctx, "Economy commands are already disabled in this channel")
    else:
        GC.remove_bb_channel(ctx.channel)
        await bot_send(ctx, f"Economy commands are now disabled in {ctx.channel.name}")

@bot.listen()
async def on_guild_join(guild:discord.Guild):

    # set up config
    GC.add_guild(guild)

    #send first message
    embed = discord.Embed(title='Hello!', 
        description=("I'm BarrelBot, your personal assistant in your spiritual"
                     f" journey towards oneness with the {ED.BARREL_EMOJI}. "
                     "Use `bb help` to see all of my commands, or ask me to "
                     "introduce myself with `Hey BarrelBot, introduce yourself`\n\n"
                     "If you're the admin, please set up a channel for economy"
                     " commands with `bb add_channel`. Also, take a look at "
                     "the help command to configure specific features."))
    
    for channel in guild.text_channels:
        try:
            await channel.send(embed=embed)
            break
        except:
            pass

@bot.listen()
async def on_guild_remove(guild:discord.Guild):

    # delete config
    GC.remove_guild(guild)

# Bot events

@bot.event
async def on_ready():
    """Called when the bot starts and is ready."""
    # Startup Logging
    print("")
    print("\033[37mUserName\033[1;34m :", bot.user.name)
    print("\033[37mUserID\033[1;34m :", bot.user.id)
    print("\033[37mVersion\033[1;34m  :", os.environ["VERSION"])
    print("\033[37mIS_IN_DEV_MODE\033[1;34m :", env.BBGLOBALS.IS_IN_DEV_MODE)
    print("\033[0;34m---\033[0m")
    print("\033[32m")
    # Load cogs
    await load_cog("cogs.utilities", "Utilities")
    await load_cog("cogs.barrelspam", "Barrel Spam")
    await load_cog("cogs.fun", "Fun")
    await load_cog("cogs.economy", "Economy")
    await load_cog("cogs.barrelnews", "Barrel News")
    await load_cog("cogs.research", "Research")
    if not env.BBGLOBALS.IS_IN_DEV_MODE:
        # compute-heavy cogs not needed during normal development
        await load_cog("cogs.chat", "Chatbot")
        await load_cog("cogs.analytics", "Analytics")
    print("\033[0m")

    await bot.change_presence(activity=discord.Game('My name is BarrelBot!'))

    sendnextmsg.start()
    backup_playerdata.start()

    global defaultctx
    defaultctx = await bot.get_context(
        await (await bot.fetch_channel(735631686313967646)).fetch_message(1315938006259073087))

    print(f"\033[32mLoaded and ready! Running on {os.environ['MACHINE']}\033[0m")
    print("")


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """Called when a command produces an error."""
    if isinstance(error, commands.CommandNotFound):
        return
    if ctx.command.name == "sell":
        if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument, commands.TooManyArguments)):
            if len(re.search(r"(?<=sell).*", ctx.message.content).group(0)) >= 0x71 or len(
                    ctx.message.attachments) != 0:
                return
    if isinstance(error, commands.MissingRequiredArgument):
        await bot_send(ctx, 'You\'re missing a required argument: ' + error.param.name + \
                       ' - Take a look at the command\'s help text with `bb help <command>`')
    elif isinstance(error, commands.TooManyArguments):
        await bot_send(ctx, 'You input too many arguments. '+ \
                       ' - Take a look at the command\'s help text with `bb help <command>`')
    elif isinstance(error, commands.NotOwner):
        await bot_send(ctx, 'You have to be the owner to excute this command.')
    elif isinstance(error, commands.MissingPermissions):
        await bot_send(ctx, "You don't have the right permissions to execute that command.")
    elif isinstance(error, commands.BotMissingPermissions):
        try:
            await ctx.send('The bot is missing the required permissions to invoke this command: ' + str(
                               error.missing_permissions))
        except commands.CommandInvokeError:
            await ctx.author.send(
                "An error occurred and I wasn't able to handle it normally. I can't send messages to the channel you "
                "entered that command in. Other permissions I'm missing are " + str(
                    error.missing_permissions))
    elif isinstance(error, commands.ExtensionError):
        await bot_send(ctx, f'The extension {str(error.name)} raised an exception.')
    elif isinstance(error, commands.CommandOnCooldown):
        await bot_send(ctx, f'That command is on cooldown. Try again in {time_str(math.ceil(error.retry_after))}.')
    elif isinstance(error, NotAbleTo):
        await bot_send(ctx, str(error))
    elif isinstance(error, commands.BadArgument):
        await bot_send(ctx, f"The command arguments need to be in a different format. "+\
            "Take a look at the command\'s help text with `bb help <command>`")
    elif isinstance(error, commands.CommandInvokeError):
        await bot_send(ctx, str(error))
    elif isinstance(error, PlayerNotFound):
        await bot_send(ctx, "Unknown user.")
    elif isinstance(error, NotInBbChannel):
        bb_channels = [bot.get_channel(i) for i in GC.get_bb_channels(ctx.guild)]
        msg = await ctx.send(
            f"This command can only be done in {' or '.join([i.mention for i in bb_channels])}.")
        await ctx.message.delete(delay=5)
        await msg.delete(delay=5)
    elif isinstance(error, commands.CheckFailure):
        pass
    elif isinstance(error, OperationalError):
        await bot_send(ctx, f"Well that REALLY isn't supposed to happen.\n<@474349369274007552>\n{error.with_traceback(None)}\n{sys.exc_info()}")
    else:
        await bot_send(ctx, f'An unknown error occurred:\n{type(error)}\n{error.with_traceback(None)}')


@bot.event
async def on_error(event, *args, **kwargs):
    if env.BBGLOBALS.IS_IN_DEV_MODE:
        tosend = bot.get_channel(733508144617226302) # bot testing general chat
    else:
        tosend = bot.get_user(474349369274007552) # jan Kaje's DMs
    if event == "on_ready":
        error_info = sys.exc_info()
        if isinstance(error_info[1], RuntimeError):
            return
    await tosend.send(f'There was an error on {event}:\n{args}\n{kwargs}\n'
                      f'Error message:\n{sys.exc_info()}')


# Bot commands

@bot.command()
@commands.is_owner()
async def olape(ctx: commands.Context):
    """Gently puts the bot to sleep, so he can rest and recover for the coming day."""
    await save_everything()
    await ctx.send("Goodnight! See you tomorrow :)")
    quit()


@bot.command()
@commands.is_owner()
async def saveeverything(ctx: commands.Context):
    await save_everything()
    await bot_send(ctx, "success")


@bot.command()
@commands.is_owner()
async def reloadcog(ctx: commands.Context, cogname: str, *, cogn2: str):
    try:
        await bot.unload_extension("cogs." + cogname)
        await load_cog(cogname, cogn2)
        await bot_send(ctx, f"Reloaded {cogname}")
    except Exception as e:
        print(f"was not able to reload cog {cogname}:\n{e.Player.get_json_data()(None)}")
        pass


@bot.command()
@commands.is_owner()
async def run_raw_code(ctx: commands.Context, *, code: str):
    if code == '':
        return
    try:
        exec(code)
    except Exception as e:
        await bot_send(ctx, f"Something went wrong:\n{e.with_traceback(None)}")

# Bot tasks

# Global safe-message send function
async def bot_send(ctx: commands.Context, content: str = None, embed: discord.Embed = None, file: discord.File = None):
    global messagequeue
    await messagequeue.put(UnsentMessage(ctx, content, embed, file))


@tasks.loop(seconds=0.25)
async def sendnextmsg():
    global messagequeue
    message: UnsentMessage = await messagequeue.get()
    try:
        await message.send()
    except Exception as e:
        print(e)
        await message.ctx.send(str(e))


@tasks.loop(time = dt.time(hour=0, tzinfo=dt.timezone.utc))
async def backup_playerdata():
    copyfile(os.path.join(dir_path, "data", "player_data.db"), 
             os.path.join(dir_path, "data", "player_data.db.bak"))


# Run the bot

def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
