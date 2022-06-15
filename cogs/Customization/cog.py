import d20
import discord
from discord.ext import commands

from .utils import is_admin
from utils.functions import edit_csv


class Customization(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def prefix(self, ctx, prefix: str = None):
        """"""  # TODO Add Description

        guild_id = str(ctx.guild.id)
        if prefix is None:
            return await ctx.send(f"CURRENT PREFIX - {ctx.prefix}")

        is_admin(ctx.author)

        self.bot.prefixes[guild_id] = prefix

        edit_csv((guild_id, prefix), "db/prefixes.csv")

        await ctx.send(f"```ini\n[CHANGED SERVER PREFIX TO: {prefix}]\n```")
