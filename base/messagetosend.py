from discord import Embed, File
from discord.ext.commands import Context

class UnsentMessage:

    def __init__(self, ctx:Context, content:str=None, embed:Embed=None, file:File=None):
        self.ctx = ctx
        self.content = content
        self.embed = embed
        self.file = file

    async def send(self):
        await self.ctx.send(self.content, embed=self.embed, file=self.file)
