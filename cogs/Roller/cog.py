import d20
import discord
from discord.ext import commands


class Roller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="2", hidden=True)
    async def quick_roll(self, ctx, *, mod: str = "0"):
        """Quickly rolls a d20."""
        print("E")
