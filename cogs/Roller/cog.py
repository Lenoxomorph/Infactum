import d20
import discord
from discord.ext import commands

from .utils import string_search_adv


class Roller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["r"])
    async def roll(self, ctx, *, dice: str = "1d20"):
        """Quickly rolls a d20."""
        print(d20.roll(dice))
