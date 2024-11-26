import math
import os
import re
import sys
import datetime as dt

import discord
from discord.ext import commands, tasks
from github import Github, InputGitTreeElement, Auth

from cogs.barrelspam import savealldata as spamsave
from cogs.fun import savealldata as funsave

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

# Command helper functions

def savealldata():
    spamsave()
    funsave()

    token = os.environ["GHT"]
    auth = Auth.Token(token)
    g = Github(auth=auth)
    repo = g.get_user().get_repo('Barrel-Bot') # repo name
    file_names = [
        'data/barrelspamdata.json',
        'data/barrelspamteamdata.json',
        'data/randomnumberscores.json'
    ]
    file_list = [dir_path + "/" + name for name in file_names]
    commit_message = 'auto update scores ' + dt.datetime.now().isoformat(sep=" ", timespec="seconds")
    master_ref = repo.get_git_ref('heads/main')
    master_sha = master_ref.object.sha
    base_tree = repo.get_git_tree(master_sha)

    element_list = list()
    for i, entry in enumerate(file_list):
        with open(entry) as input_file:
            data = input_file.read()
        element = InputGitTreeElement(file_names[i], '100644', 'blob', data)
        element_list.append(element)

    tree = repo.create_git_tree(element_list, base_tree)
    parent = repo.get_git_commit(master_sha)
    commit = repo.create_git_commit(commit_message, tree, [parent])
    master_ref.edit(commit.sha)


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
    await bot.change_presence(activity=discord.Game('My name is BarrelBot!'))


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


# Bot tasks

@tasks.loop(hours=24)
async def savedata():
    savealldata()

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
