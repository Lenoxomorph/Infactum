import d20

from utils import config
from utils.csvUtils import search_csv


def get_emoji(author_id):
    emoji = search_csv(author_id, "db/emojis.csv")
    if emoji is None:
        emoji = config.DEFAULT_EMOJI
    return emoji


class MainStringifier(d20.MarkdownStringifier):
    def _str_expression(self, node):
        return f"**{node.comment or 'Result'}**: {self._stringify(node.roll)}\n**Total**: {int(node.total)}"


class MultiRollContext(d20.RollContext):
    def __init__(self, max_rolls=1000, max_total_rolls=None):
        super().__init__(max_rolls)
        self.max_total_rolls = max_total_rolls or max_rolls
        self.total_rolls = 0

    def count_roll(self, n=1):
        super().count_roll(n)
        self.total_rolls += 1
        if self.total_rolls > self.max_total_rolls:
            raise d20.TooManyRolls("Too many dice rolled.")
