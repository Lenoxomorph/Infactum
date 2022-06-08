import d20
import discord
from discord.ext import commands

from utils.dice import MainStringifier
from utils.functions import try_delete
from .utils import string_search_adv


class Roller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["r"])
    async def roll(self, ctx, *, dice: str = "1d20"):
        """"""  # TODO Add Description
        dice, adv = string_search_adv(dice)

        res = d20.roll(dice, advantage=adv, allow_comments=True, stringifier=MainStringifier())
        header = f"{ctx.author.mention}  :game_die:\n"  # TODO Add Custom Emojis
        out = header + str(res)
        if len(out) > 1999:
            out = f"{header} + {str(res)[:100]} + ...\n**Total**: {res.total}"
        await try_delete(ctx.message)
        await ctx.send(out, allowed_mentions=discord.AllowedMentions(users=[ctx.author]))
