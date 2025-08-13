import os
import re

import discord
from discord.ext import commands

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def setup(bot):
    await bot.add_cog(utilities(bot))


class utilities(commands.Cog, name="Utilities"):
    """Random other stuff"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.bot_send = None

    def set_bot_send(self, bot_send):
        self.bot_send = bot_send

    @commands.command()
    async def github(self, ctx: commands.Context):
        """Provides a link to my github page."""
        await self.bot_send(ctx, "https://github.com/janKaje/Barrel-Bot")

    @commands.command()
    @commands.is_owner()
    async def debuginfo(self, ctx: commands.Context):
        print(os.environ)
        await self.bot_send(ctx, "All environment variables printed in console.")

    # Custom Help command
    @commands.command()
    async def help(self, ctx: commands.Context, *, cmd=None):
        """Displays the help command. `<cmd>` can be the name of a command or category, and if given, displays the
        long help text for that command or category. If `<cmd>` is 'commands' or not specified, lists the commands."""
        # displays all commands if cmd is not given
        if cmd is None or cmd == 'commands':
            command_msg = discord.Embed(title='Commands', color=discord.Color.blue(),
                                        description='Type `barrelbot, help [command]` or `barrelbot, help [category]` '
                                                    'for more information.')

            cmds = []

            async def addcommands(cog: commands.Cog, add=[]):
                nonlocal command_msg, cmds
                cog_info = ''
                for i in cog.walk_commands():
                    checks = True
                    for j in i.checks:
                        try:
                            try:
                                await j(ctx)
                            except commands.CheckFailure:
                                checks = False
                        except:
                            try:
                                j(ctx)
                            except commands.CheckFailure:
                                checks = False
                    if checks:
                        cog_info += f'***{i.name}***  -  '
                        cmds.append(i.name)
                for cmd in add:
                    i = self.bot.get_command(cmd)
                    checks = True
                    for j in i.checks:
                        try:
                            try:
                                await j(ctx)
                            except commands.CheckFailure:
                                checks = False
                        except:
                            try:
                                j(ctx)
                            except commands.CheckFailure:
                                checks = False
                    if checks:
                        cog_info += f'***{i.name}***  -  '
                        cmds.append(i.name)
                if cog_info != '':
                    command_msg.add_field(name=f'__{cog.qualified_name}__', value=re.sub(r'  \-  \Z', '', cog_info),
                                          inline=False)

            for cog_name in [
                'Utilities',
                'Economy',
                'Research',
                'Fun',
                'Barrel Spam',
                'Barrel News',
                'Analytics',
            ]:
                cog = self.bot.get_cog(cog_name)
                if cog is not None:
                    await addcommands(cog)

            if await self.bot.is_owner(ctx.author):
                info = ''
                for command in self.bot.commands:
                    if command.name not in cmds:
                        checks = True
                        for j in command.checks:
                            try:
                                try:
                                    await j(ctx)
                                except commands.CheckFailure:
                                    checks = False
                            except:
                                try:
                                    j(ctx)
                                except commands.CheckFailure:
                                    checks = False
                        if checks:
                            info += f'***{command.name}***  -  '
                            cmds.append(command.name)
                if info != '':
                    command_msg.add_field(name='__Owner Only__', value=re.sub(r'  \-  \Z', '', info), inline=False)

            await self.bot_send(ctx, embed=command_msg)

        # for when a certain command or cog is specified
        else:
            for cog in self.bot.cogs:
                if cmd.lower() == cog.lower():
                    embed = discord.Embed(title=cog, color=discord.Color.blue(), description=self.bot.get_cog(cog).__doc__)
                    cog_info = ''
                    for i in self.bot.get_cog(cog).walk_commands():
                        checks = True
                        for j in i.checks:
                            try:
                                try:
                                    await j(ctx)
                                except commands.CheckFailure:
                                    checks = False
                            except:
                                try:
                                    j(ctx)
                                except commands.CheckFailure:
                                    checks = False
                        if checks:
                            cog_info += f'***{i.name}***  -  '
                    if cog_info != '':
                        embed.add_field(name=f'__Commands__', value=re.sub(r'  \-  \Z', '', cog_info),
                                            inline=False)
                    await self.bot_send(ctx, embed=embed)
                    return
            comd = ''
            alia = 'Aliases: '
            # iterates through commands
            for c in self.bot.walk_commands():
                if c.name == cmd or cmd in c.aliases:  # if search term matches command or any of the aliases
                    title = c.name  # adds name
                    comd = c.help  # adds help
                    # adds aliases
                    for a in c.aliases:
                        alia += f'{a}, '
                    # adds parameters
                    for b in c.clean_params:
                        title += f' <{b}>'
                    break
            # if the command wasn't found
            if comd == '':
                await self.bot_send(ctx, 'That command was not found.')
                return
            helpmsg = discord.Embed(title=title, color=discord.Color.blue(), description=comd)  # creates embed
            # if the command has aliases, add them to the footer
            if not alia == 'Aliases: ':
                alia = re.sub(r', \Z', '', alia)
                helpmsg.set_footer(text=alia)
            await self.bot_send(ctx, embed=helpmsg)

    @commands.command()
    async def feedback(self, ctx:commands.Context):
        """Feedback form for bugs or feature requests"""
        await self.bot_send(ctx, "https://docs.google.com/forms/d/e/1FAIpQLScoy5MqeEZAo9UxhbrTH_zI93DSeGsAc-Sf4gsp634VRosg6A/viewform?usp=header")
    
    @commands.command()
    async def is_in_dev_mode(self, ctx:commands.Context):
        """Returns whether the bot is in dev mode or not"""
        from base import env
        if env._BBGLOBALS.IS_IN_DEV_MODE:
            await self.bot_send(ctx, "The bot is currently in development mode.")
        else:
            await self.bot_send(ctx, "The bot is currently running in production mode.")