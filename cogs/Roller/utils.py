import re

import d20

ADV_WORD_RE = re.compile(r"(?:^|\s+)(adv|dis)(?:\s+|$)")


def string_search_adv(dice_str: str):
    adv = d20.AdvType.NONE
    if (match := ADV_WORD_RE.search(dice_str)) is not None:
        adv = d20.AdvType.ADV if match.group(1) == "adv" else d20.AdvType.DIS
        dice_str = dice_str[: match.start(1)] + dice_str[match.end():]
    return dice_str, adv
