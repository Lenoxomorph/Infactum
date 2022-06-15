import d20
import discord
from discord.ext import commands

from utils.checks import is_admin


class Customization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def prefix(self, ctx, prefix: str = None):
        """"""  # TODO Add Description
        if prefix is None:
            return await ctx.send(f"CURRENT PREFIX - {ctx.prefix}")

        is_admin(ctx.author)

        print("New Prefix" + prefix)
