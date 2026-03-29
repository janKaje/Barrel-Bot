import json
import math
import os
import random as rand
import re
import asyncio
from copy import deepcopy
import sys
import io
from typing import Callable
from datetime import timedelta as td

import discord
from discord.ext import commands, tasks
from chatterbot import ChatBot
from chatterbot.filters import get_recent_repeated_responses
from chatterbot.conversation import Statement

dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.append(os.path.join(dir_path, "base"))

from checks import Checks
from extra_exceptions import *
from env import BBGLOBALS


async def setup(bot):
    await bot.add_cog(chat(bot))

async def temp_bot_send(ctx: commands.Context, content: str = None, embed: discord.Embed = None, file: discord.File = None):
    pass


class chat(commands.Cog, name="Chatbot"):
    """Chatbot module"""

    def __init__(self, bot:commands.Bot):
        self.bot = bot
        self.bot_send = temp_bot_send
        self.chatbot = ChatBot(
            "BarrelBot hyper advanced AI wizardry",
            logic_adapters=[
                'chatterbot.logic.BestMatch',
                {
                    'import_path': 'chatterbot.logic.SpecificResponseAdapter',
                    'input_text': 'good bot',
                    'output_text': ':3'
                }
            ],
            database_uri='sqlite:///data/chatbot.sqlite3',
            filters=[get_recent_repeated_responses]
        )

    def set_bot_send(self, bot_send:Callable):
        self.bot_send = bot_send

    async def cog_load(self):

        # print loaded
        print(f"cog: {self.qualified_name} loaded")

    @commands.command()
    @commands.is_owner()
    async def message_history_to_csv(self, ctx: commands.Context):

        csv = io.StringIO("datetime,name,content")
        async for msg in ctx.channel.history(limit=None,oldest_first=True):
            if msg.content != "":
                csv.write(f'\n{msg.created_at.timestamp()},{msg.author.name},"{msg.content}"')
        csv.seek(0)
        with open(f"{ctx.channel.name}.csv", "w", encoding='utf-16') as file:
            file.write(csv.getvalue())
        
        await self.bot_send(ctx, f"File saved to {ctx.channel.name}.csv")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called whenever a message is sent that the bot can see."""
        # don't interact with bots
        if message.author.bot:
            # unless it's bb in the chatbot channel,
            # then add checkmark so people can give feedback
            if message.author.id == self.bot.user.id and \
                message.channel.id == BBGLOBALS.CHATBOT_CHANNEL_ID:
            
                await message.add_reaction("✅")
                await message.add_reaction("🗑️")
            return
        
        if message.channel.id != BBGLOBALS.CHATBOT_CHANNEL_ID:
            return
        
        async with message.channel.typing():
            # learn user's response
            if message.type == discord.MessageType.reply:
                try:
                    prevmsgref = message.reference
                    prevmsg = await message.channel.fetch_message(prevmsgref.message_id)
                    self.learn_response(message, prevmsg)
                except discord.HTTPException:
                    pass
            # eh, not really needed
            # else:
            #     async for prevmsg in message.channel.history(before=message.created_at, limit=1):
            #         break
            #     # if more than 12 hours, don't count as continuation of conversation
            #     if (prevmsg.created_at - message.created_at) <= td(hours=12):
            #         self.learn_response(message, prevmsg)

            # get response
            msg = Statement(text=self.sanitize_input(message.content))
            response:Statement = self.chatbot.generate_response(msg)

            if response.text == '':
                return

            responsetxt = f"{response.text}\n-# ✅ to tell the bot good job, 🗑️ to remove"

            ctx = await self.bot.get_context(message)

        await self.bot_send(ctx, responsetxt)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.channel_id != BBGLOBALS.CHATBOT_CHANNEL_ID:
            return
        
        if payload.message_author_id == self.bot.user.id and \
            str(payload.emoji) in ["✅", "🗑️"] and \
            payload.user_id != self.bot.user.id:

            chnl = await self.bot.fetch_channel(payload.channel_id)
            message = await chnl.fetch_message(payload.message_id)

            if str(payload.emoji) == "✅":
                async for prevmsg in chnl.history(before=message.created_at, limit=1):
                    break

                self.learn_response(message, prevmsg)

            elif str(payload.emoji) == "🗑️":
                await message.delete()

    def sanitize_input(self, message:str) -> str:

        message = message.replace("-# ✅ to tell the bot good job, 🗑️ to remove", "").strip("\n ")

        for m in re.finditer(r"<a?(:\w+:)\d+>", message):
            message = message.replace(m.group(0), m.group(1)) # clean emoji inputs
        
        return message
        

    def learn_response(self, message:discord.Message, prevmsg:discord.Message):

        msg = self.sanitize_input(message.content)
        prevmsg = self.sanitize_input(prevmsg.content)

        if msg == '' or prevmsg == '':
            return

        self.chatbot.learn_response(Statement(msg), 
                                    Statement(prevmsg))

        print(f"LEARNED: {prevmsg} -> {msg}")