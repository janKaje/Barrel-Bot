import math
import os
import re
import sys

import discord
from discord.ext import commands

from cogs.barrelspam import savealldata as spamsave
from cogs.fun import savealldata as funsave


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

# Open saved data
with open("token.txt") as file:
    TOKEN = file.read()


# Command helper functions

def savealldata():
    spamsave()
    funsave()


# Bot events

@bot.event
async def on_ready():
    """Called when the bot starts and is ready."""
    # Load cogs
    await bot.load_extension("cogs.barrelspam")
    await bot.load_extension("cogs.fun")
    await bot.load_extension("cogs.utilities")
    await bot.change_presence(activity=discord.Game('My name is barrelbot!'))


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
    savealldata()
    await ctx.send("Goodnight! See you tomorrow :)")
    quit()


@bot.command()
@commands.is_owner()
async def save_all_data(ctx: commands.Context):
    """Saves all data."""
    savealldata()
    await ctx.send("Done!")


# Run the bot
bot.run(TOKEN)
