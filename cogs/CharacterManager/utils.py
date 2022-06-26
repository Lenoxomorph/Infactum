from typing import List

from discord import Embed

from utils.csvUtils import append_csv, edit_csv

POINT_BUY_PIC_URL = "https://surlybikes.com/uploads/bikes/_medium_image/Lowside_BK0534_Background-2000x1333.jpg"

STAT_LIST = ["Str", "Dex", "Con", "Int", "Wis", "Cha"]


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
        data = [self.name, points, -1] + [str(self.base)] * 6 + [ctx.author.id]
        self.update_description(data, embed)
        message = await ctx.send(embed=embed)
        append_csv([str(message.id)] + data, "db/pointBuyMessages.csv")
        return message

    def update_description(self, data: List[str], embed: Embed):
        description = ""
        points = 0
        for i, score in enumerate(data[3:9]):
            temp_points = self.score_points(int(score))
            points += temp_points
            header_footer = '**' if str(i) == data[2] else ''
            description += f"{header_footer}{STAT_LIST[i]}:  {score}  (*{temp_points}*)" \
                           f"{header_footer}\n"
        description = f"**{points}**/**{int(data[1])}**\n" + description
        embed.description = description
        return embed

    def change_score(self, data, increase):
        temp_data = data.copy()
        if int(temp_data[2]) >= 0:
            temp_data[int(temp_data[2]) + 3] = str(int(temp_data[int(temp_data[2]) + 3]) + increase)
            total_points = 0
            for score in temp_data[3:9]:
                points = self.score_points(int(score))
                if points is not None:
                    total_points += points
                else:
                    break
            else:
                if total_points <= int(temp_data[1]):
                    data = temp_data
        return data
