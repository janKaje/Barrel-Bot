import math
import os
import re
import sys

import discord
from discord.ext import commands

from cogs.fun import fun as fun_cog
from cogs.barrelspam import barrelspam as barrelspam_cog

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass


# Command prefix function
def isCommand(bot: commands.Bot, message: discord.Message) -> str:
    # Allow to match with "bb " or "bb, "
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
        return m.group(0)

    # Default
    return "BarrelBot, "


# Initialize intents
Intents = discord.Intents.default()
Intents.messages = True
Intents.members = True
Intents.guild_messages = True
Intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=isCommand, intents=Intents)
bot.remove_command('help')

# Create global variables
dir_path = os.path.dirname(os.path.abspath(__file__))

# get token
TOKEN = os.environ["TOKEN"]

# prep for save functions
async def saveeverything():

    funcog = fun_cog(bot)
    spamcog = barrelspam_cog(bot)

    await funcog.saveprep()
    await spamcog.saveprep()

    await funcog.savealldata()
    await spamcog.savealldata()


# Bot events

@bot.event
async def on_ready():
    """Called when the bot starts and is ready."""
    # Load cogs
    try:
        await bot.load_extension("cogs.barrelspam")
    except:
        pass
    try:
        await bot.load_extension("cogs.fun")
    except:
        pass
    try:
        await bot.load_extension("cogs.utilities")
    except:
        pass
    try:
        await bot.load_extension("cogs.barrelnews")
    except:
        pass
    await bot.change_presence(activity=discord.Game('My name is BarrelBot!'))
    print(f"Loaded and ready! Running on {os.environ['MACHINE']}")


@bot.event
async def on_command_error(ctx: commands.Context, error):
    """Called when a command produces an error."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('You\'re missing a required argument: ' + str(error.param))
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
            await ctx.send(
                'The bot is missing the required permissions to invoke this command: ' + str(error.missing_perms))
        except commands.CommandInvokeError:
            await ctx.author.send(
                "An error occurred and I wasn't able to handle it normally. I can't send messages to the channel you entered that command in. Other permissions I'm missing are " + str(
                    error.missing_perms))
    elif isinstance(error, commands.ExtensionError):
        await ctx.send(f'The extension {str(error.name)} raised an exception.')
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'That command is on cooldown. Try again in {math.ceil(error.retry_after)} second(s).')
    else:
        await ctx.send(f'An unknown error occurred:\n{error}')


@bot.event
async def on_error(event, *args, **kwargs):
    await bot.get_user(474349369274007552).send(f'There was an error on {event}:\n{args}\n{kwargs}\n'
                                                f'Error message:\n{sys.exc_info()}')


# Bot commands

@bot.command()
@commands.is_owner()
async def olape(ctx: commands.Context):
    """Gently puts the bot to sleep, so he can rest and recover for the coming day."""
    await saveeverything()
    await ctx.send("Goodnight! See you tomorrow :)")
    quit()


@bot.command()
@commands.is_owner()
async def save_everything(ctx: commands.Context):
    await saveeverything()
    await ctx.send("success")


# Run the bot
bot.run(TOKEN)
