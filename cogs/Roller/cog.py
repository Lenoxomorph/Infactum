import d20
import discord
from discord.ext import commands

from utils.dice import MainStringifier, MultiRollContext
from utils.functions import try_delete
from .utils import string_search_adv, mention_user


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

    @staticmethod
    async def _roll_many(ctx, iterations, roll_str, dc=None, adv=None):
        if iterations < 1 or iterations > 100:
            return await ctx.send("Too many or too few iterations.")
        if adv is None:
            adv = d20.AdvType.NONE
        results = []
        successes = 0
        ast = d20.parse(roll_str, allow_comments=True)
        roller = d20.Roller(context=MultiRollContext())

        for _ in range(iterations):
            res = roller.roll(ast, advantage=adv)
            if dc is not None and res.total >= dc:
                successes += 1
            results.append(res)

        if dc is None:
            header = f"**Results:** *Rolling {iterations} iterations*"
            footer = f"**Total:** {sum(o.total for o in results)}"
        else:
            header = f"Rolling {iterations} iterations, DC {dc}..."
            footer = f"{successes} successes, {sum(o.total for o in results)} total."

        if ast.comment:
            header = f"{ast.comment}: {header}"

        result_strs = "\n".join(str(o) for o in results)

        out = f"{header}\n{result_strs}\n{footer}"

        if len(out) > 1500:
            one_result = str(results[0])
            out = f"{header}\n{one_result}\n[{len(results) - 1} results omitted for output size.]\n{footer}"

        await try_delete(ctx.message)
        await ctx.send(f"{mention_user(ctx.author)}\n{out}", allowed_mentions=discord.AllowedMentions(users=[ctx.author]))
