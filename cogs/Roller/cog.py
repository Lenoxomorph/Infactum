import d20
import discord
from discord.ext import commands

from utils.dice import MainStringifier
from utils.functions import try_delete
from .utils import string_search_adv, mention_user, roll_many


class Roller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["r"])
    async def roll(self, ctx, *, dice: str = "1d20"):
        """"""  # TODO Add Description
        dice, adv = string_search_adv(dice)

        res = d20.roll(dice, advantage=adv, allow_comments=True, stringifier=MainStringifier())
        out = f"{mention_user(ctx.author)}\n{str(res)}"
        if len(out) > 1999:
            out = f"{mention_user(ctx.author)}\n{str(res)[:100]}...\n**Total**: {res.total}"
        await try_delete(ctx.message)
        await ctx.send(out, allowed_mentions=discord.AllowedMentions(users=[ctx.author]))

    @commands.command(name="multiroll", aliases=["rr"])
    async def rr(self, ctx, iterations: int, *, dice):
        """"""  # TODO Add Description
        dice, adv = string_search_adv(dice)
        await roll_many(ctx, iterations, dice, adv=adv)

    @commands.command(name="iterroll", aliases=["rrr"])
    async def rrr(self, ctx, iterations: int, dice, dc: int = None, *, args=""):
        """"""  # TODO Add Description
        _, adv = string_search_adv(args)
        await roll_many(ctx, iterations, dice, dc, adv)
