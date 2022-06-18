import re

import d20
import discord

from utils.dice import MultiRollContext, get_emoji
from utils.functions import try_delete

ADV_WORD_RE = re.compile(r"(?:^|\s+)(adv|dis)(?:\s+|$)")


def string_search_adv(dice_str: str):
    adv = d20.AdvType.NONE
    if (match := ADV_WORD_RE.search(dice_str)) is not None:
        adv = d20.AdvType.ADV if match.group(1) == "adv" else d20.AdvType.DIS
        dice_str = dice_str[: match.start(1)] + dice_str[match.end():]
    return dice_str, adv


def mention_user(author):
    return f"{author.mention}  {get_emoji(str(author.id))}"  # TODO Add Custom Emojis


async def roll_many(ctx, iterations, roll_str, dc=None, adv=None):
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
    await ctx.send(f"{mention_user(ctx.author)}"
                   f"\n{out}", allowed_mentions=discord.AllowedMentions(users=[ctx.author]))
