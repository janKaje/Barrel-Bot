import math
import os
import re
import sys
import asyncio
from base import env
import discord
from discord.ext import commands, tasks
from base.messagetosend import UnsentMessage

dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(dir_path, "base"))
from extra_exceptions import NotAbleTo, PlayerNotFound, NotInBbChannel

env.BBGLOBALS.init_globals()

# Debug
if env.BBGLOBALS.IS_IN_DEV_MODE:
    print("New debugging session started in bot testing server")


# Command prefix function
def is_command(_: commands.Bot, message: discord.Message) -> str:
    # Allow to match with "bb " or "bb, "
    if env.BBGLOBALS.IS_IN_DEV_MODE:
        # !bb as dev-mode command
        _m = re.match("!?bb,? ", message.content)
        if _m is not None:
            return _m.group(0)
    else:
        _m = re.match("bb,? ", message.content)
        if _m is not None:
            return _m.group(0)

    # Allow to match with direct address
    m = re.match("(hey |hello |hi )?barrel ?bot[,!.]? +", message.content, flags=re.I)
    if m is not None:
        return m.group(0)

    # Allow to match with mention
    m_ = re.match("<@733514909823926293>[,!.]? +", message.content)
    if m_ is not None:
        return m_.group(0)

    # Default
    return "BarrelBot, "


# Initialize intents
Intents = discord.Intents.default()
Intents.messages = True
Intents.members = True
Intents.guild_messages = True
Intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=is_command, intents=Intents)
bot.remove_command('help')

# Create global variables
dir_path = os.path.dirname(os.path.abspath(__file__))
defaultctx = None
messagequeue = asyncio.Queue()


# get token
TOKEN = os.environ["TOKEN"]


# prep for save functions
async def save_everything():

    env.BBGLOBALS.save_guild_config()

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

    gambling = env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["gambling"]
    robbing = env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["robbing"]
    channel_ids = env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["channel_ids"]

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
    if env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["gambling"] is True:
        await bot_send(ctx, "Gambling is already enabled for this server.")
    else:
        env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["gambling"] = True
        await bot_send(ctx, f"Gambling is now enabled on {ctx.guild.name}")

@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def disable_gambling(ctx: commands.Context):
    """Disable gambling on this server"""
    if env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["gambling"] is False:
        await bot_send(ctx, "Gambling is already disabled for this server.")
    else:
        env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["gambling"] = False
        await bot_send(ctx, f"Gambling is now disabled on {ctx.guild.name}")
        
@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def enable_robbing(ctx: commands.Context):
    """Enable robbing on this server"""
    if env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["robbing"] is True:
        await bot_send(ctx, "Robbing is already enabled for this server.")
    else:
        env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["robbing"] = True
        await bot_send(ctx, f"Robbing is now enabled on {ctx.guild.name}")

@bot.command()
@commands.has_guild_permissions(manage_guild=True)
async def disable_robbing(ctx: commands.Context):
    """Disable robbing on this server"""
    if env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["robbing"] is False:
        await bot_send(ctx, "Robbing is already disabled for this server.")
    else:
        env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["robbing"] = False
        await bot_send(ctx, f"Robbing is now disabled on {ctx.guild.name}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def add_channel(ctx: commands.Context):
    """Adds this channel to BarrelBot's list of channels that economy commands are enabled in."""
    if ctx.channel.id in env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["channel_ids"]:
        await bot_send(ctx, "Economy commands are already enabled in this channel")
    else:
        env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["channel_ids"].append(ctx.channel.id)
        await bot_send(ctx, f"Economy commands are now enabled in {ctx.channel.name}")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def remove_channel(ctx: commands.Context):
    """Removes this channel from BarrelBot's list of channels that economy commands are enabled in."""
    if ctx.channel.id not in env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["channel_ids"]:
        await bot_send(ctx, "Economy commands are already disabled in this channel")
    else:
        env.BBGLOBALS.GUILD_CONFIG[str(ctx.guild.id)]["channel_ids"].remove(ctx.channel.id)
        await bot_send(ctx, f"Economy commands are now disabled in {ctx.channel.name}")

# helper function
def time_str(time):
    """Takes a float of seconds and turns it into appropriate hours, minutes, and seconds."""
    st = ""

    if time // 86400 > 1:
        st += str(time // 86400) + ' days'
    elif time // 86400 > 0:
        st += str(time // 86400) + ' day'

    if time % 86400 // 3600 > 0:
        if time // 86400 > 0:
            st += ', ' + str(time % 86400 // 3600) + ' hour'
        else:
            st += str(time // 3600) + ' hour'
        if time % 86400 // 3600 > 1 or time // 86400 > 0:
            st += "s"

    if time % 3600 // 60 > 0 or time % 86400 // 3600 > 0:
        if time % 86400 // 3600 > 0:
            st += ', ' + str(time % 3600 // 60) + ' minute'
        else:
            st += str(time // 60) + ' minute'
        if time % 3600 // 60 > 1 or time // 3600 > 0:
            st += "s"

    if time % 60 > 0 or time % 3600 // 60 > 0:
        if time % 3600 // 60 > 0 or time // 3600 > 0:
            st += ', ' + str(time % 60) + ' second'
        else:
            st += str(time % 60) + ' second'
        if time % 60 > 1 or time % 60 == 0:
            st += "s"

    return st


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
    await load_cog("cogs.chat", "Chatbot")
    # await load_cog("cogs.analytics", "Analytics")
    # await load_cog("cogs.research", "Research")
    print("\033[0m")

    await bot.change_presence(activity=discord.Game('My name is BarrelBot!'))

    sendnextmsg.start()
    save_guild_config.start()

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
        await bot_send(ctx, 'You\'re missing a required argument: ' + str(error.param))
    elif isinstance(error, commands.TooManyArguments):
        await bot_send(ctx, 'You input too many arguments.')
    elif isinstance(error, commands.NotOwner):
        await bot_send(ctx, 'You have to be the owner to excute this command.')
    elif isinstance(error, commands.MissingPermissions):
        await bot_send(ctx, "You don't have the right permissions to execute that command.")
    elif isinstance(error, commands.BotMissingPermissions):
        try:
            await bot_send(ctx,
                           'The bot is missing the required permissions to invoke this command: ' + str(
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
        await bot_send(ctx, str(error))
    elif isinstance(error, commands.CommandInvokeError):
        await bot_send(ctx, str(error))
    elif isinstance(error, PlayerNotFound):
        await bot_send(ctx, "Unknown user.")
    elif isinstance(error, NotInBbChannel):
        bb_channels = []
        for i in env.BBGLOBALS.BB_CHANNEL_IDS:
            ch = bot.get_channel(i)
            if ch is not None and ch.guild.id == ctx.guild.id:
                bb_channels.append(ch)
        msg = await ctx.send(
            f"This command can only be done in {' or '.join([i.mention for i in bb_channels])}.")
        await ctx.message.delete(delay=5)
        await msg.delete(delay=5)
    else:
        await bot_send(ctx, f'An unknown error occurred:\n{type(error)}\n{error.with_traceback(None)}')


@bot.event
async def on_error(event, *args, **kwargs):
    if env.BBGLOBALS.IS_IN_DEV_MODE:
        tosend = bot.get_channel(733508144617226302) # bot testing general chat
    else:
        tosend = bot.get_user(474349369274007552) # jan Kaje's DMs
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

@tasks.loop(hours=24)
async def save_guild_config():
    env.BBGLOBALS.save_guild_config()


# Run the bot

def main():
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
