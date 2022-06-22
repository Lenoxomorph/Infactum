import re

import discord
from discord import Embed
from utils.csvUtils import append_csv
from utils.functions import try_delete

POINT_BUY_PIC_URL = "https://surlybikes.com/uploads/bikes/_medium_image/Lowside_BK0534_Background-2000x1333.jpg"


class PointBuyer:
    def __init__(self, name: str, base: int, min_max, increases, points: int):
        self.name = name
        self.points = points
        self.base = base
        self.min_max = min_max
        self.increases = increases

    def score_points(self, score: int):
        if self.min_max[0] <= score <= self.min_max[1]:
            return score - self.base + sum(score - x for x in self.increases if score > x)

    async def embed(self, ctx, points):
        embed = Embed(title=f"Point Buy Calculator - {self.name}", description=f"**{points}/{points}**")
        embed.set_footer(
            text=f"Min: {self.min_max[0]}, Max: {self.min_max[1]}, Increases at {', '.join(map(str, self.increases))}")
        embed.set_thumbnail(url=POINT_BUY_PIC_URL)
        data = [self.name, points, -1] + [str(self.base)] * 6
        self.update_description(data, embed)
        message = await ctx.send(embed=embed)
        append_csv([str(message.id)] + data, "db/pointBuyMessages.csv")
        return message

    def update_description(self, data: list[str], embed: Embed):
        description = f"test{self.points}"
        points = 0
        for idx, x in enumerate(data[3:]):
            pass
        embed.description = description
        return embed

    def change_score(self, data, increase):
        pass
