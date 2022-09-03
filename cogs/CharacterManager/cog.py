import asyncio
import datetime
import re
from contextlib import contextmanager

import google.oauth2.service_account
import gspread as gspread
from discord.ext import commands
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from cogs.Roller.utils import roll_many
from utils.config import SYSTEM_ABV
from utils.csvUtils import search_csv, edit_csv
from utils.errors import ExternalImportError, ArgumentError
from utils.functions import try_delete
from .utils import PointBuyer
from .utils import STAT_LIST

LOWERED_STAT_LIST = [stat.lower() for stat in STAT_LIST]

URL_KEY_V1_RE = re.compile(r"key=([^&#]+)")
URL_KEY_V2_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")

MAIN_POINT_BUYER = PointBuyer(SYSTEM_ABV, 10, (6, 18), (14, 16), 16)
DND_POINT_BUYER = PointBuyer("D&D", 8, (8, 15), (13,), 27)

POINT_BUY_EMOJIS = ["⬆", "⬇", "<:str:986970474087088138>", "<:dex:986970473210449960>", "<:con:986970468840005672>",
                    "<:int:986970471616634900>", "<:wis:986970470563844106>", "<:cha:986970469733400668>"]

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

SKILL_S_CELLS = ((31, 1), (31, 25))
SKILL_LENGTH = 16
SKILL_COLS = (7, 11, 16, 19)

RANGED_S_CELLS = ((50, 14),)
RANGED_LENGTH = 5
RANGED_COLS = (0, 4, 6, 10, 13, 18, 21, 23)

MELEE_S_CELLS = ((58, 1), (58, 20))
MELEE_LENGTH = 3
MELEE_COLS = (0, 4, 6, 10, 13)

STATS_S_CELL = (8, 38)
STATS_WIDTH = 2
STATS_WIDTH_SPACE = 5
STATS_HEIGHT = 3
STATS_HEIGHT_SPACE = 6

SAVES_S_CELL = (20, 3)
SAVES_WIDTH = 3
SAVES_WIDTH_SPACE = 4
SAVES_HEIGHT = 1
SAVES_HEIGHT_SPACE = 1

INFO_CELLS = ((1, 6), (5, 6), (15, 8), (15, 11), (15, 14))


def extract_gsheet_id_from_url(url):
    m2 = URL_KEY_V2_RE.search(url)
    if m2:
        return m2.group(1)
    m1 = URL_KEY_V1_RE.search(url)
    if m1:
        return m1.group(1)
    raise ExternalImportError("LINK ERROR - THIS IS NOT A VALID GOOGLE SHEETS LINK")


class CharacterManager(commands.Cog):
    g_client = None
    _client_initializing = False
    _token_expiry = None

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    @contextmanager
    def _client_lock():
        if CharacterManager._client_initializing:
            raise ExternalImportError("ERROR: STILL CONNECTING TO GOOGLE")
        CharacterManager._client_initializing = True
        yield
        CharacterManager._client_initializing = False

    @staticmethod
    async def _init_gsheet_client():
        with CharacterManager._client_lock():

            def _():
                credentials = Credentials.from_service_account_file("infactum-google.json", scopes=SCOPES)
                return gspread.authorize(credentials)

            try:
                CharacterManager.g_client = await asyncio.get_event_loop().run_in_executor(None, _)
            except Exception as e:
                CharacterManager._client_initializing = False
                raise e
        # noinspection PyProtectedMember
        CharacterManager._token_expiry = datetime.datetime.now() + datetime.timedelta(
            seconds=google.oauth2.service_account._DEFAULT_TOKEN_LIFETIME_SECS
        )
        print("Logged into Google")

    @staticmethod
    async def _refresh_google_token():
        with CharacterManager._client_lock():

            def _():
                CharacterManager.g_client.auth.refresh(request=Request())
                CharacterManager.g_client.session.headers.update(
                    {"Authorization": "Bearer %s" % CharacterManager.g_client.auth.token}
                )

            try:
                await asyncio.get_event_loop().run_in_executor(None, _)
            except Exception as e:
                CharacterManager._client_initializing = False
                raise e
        print("Refreshed Google Token")

    @staticmethod
    def _is_expired():
        return datetime.datetime.now() > CharacterManager._token_expiry

    @staticmethod
    def _cell_convert(value):
        try:
            return int(value)
        except ValueError:
            if value == "TRUE" or value == "Right":
                return 1
            if value == "FALSE" or value == "Left":
                return 0
            return value

    @staticmethod
    def _user_path(user_id):  # TODO REEEEEEEE
        pass

    @commands.command(name="gsheet", aliases=["gs"])
    async def gsheet(self, ctx, url: str):
        """"""  # TODO Add Description
        key = extract_gsheet_id_from_url(url)
        if CharacterManager.g_client is None:
            await self._init_gsheet_client()
        elif CharacterManager._is_expired():
            await self._refresh_google_token()
        doc = self.g_client.open_by_key(key)
        sheet = doc.sheet1
        values = sheet.get_all_values()

        def table(start_cells, length, columns, if_empty):
            f_table = []
            for start_cell in start_cells:
                for row in values[start_cell[0]:start_cell[0] + length]:
                    f_row = []
                    for col in columns:
                        f_row.append(self._cell_convert(row[start_cell[1] + col]))
                    if if_empty:
                        if not f_row[0]:
                            continue
                    f_table.append(f_row)
            return f_table

        def grid(start_cell, width, width_space, height, height_space):
            f_grid = []
            for col in range(0, (width - 1) * width_space + 1, width_space):
                for row in range(0, (height - 1) * height_space + 1, height_space):
                    f_grid.append([self._cell_convert(values[start_cell[0] + row][start_cell[1] + col]), '', 0, 0])
            return f_grid

        def cells(coords):
            f_cells = []
            for coord in coords:
                f_cells.append(self._cell_convert(values[coord[0]][coord[1]]))
            return f_cells

        info = cells(INFO_CELLS)
        skills = table(SKILL_S_CELLS, SKILL_LENGTH, SKILL_COLS, False)
        skills.append([self._cell_convert(values[9][12]), '', 0, 0])
        skills.append(grid(STATS_S_CELL, STATS_WIDTH, STATS_WIDTH_SPACE, STATS_HEIGHT, STATS_HEIGHT_SPACE))
        skills.append(grid(SAVES_S_CELL, SAVES_WIDTH, SAVES_WIDTH_SPACE, SAVES_HEIGHT, SAVES_HEIGHT_SPACE))
        attacks = table(RANGED_S_CELLS, RANGED_LENGTH, RANGED_COLS, True)
        attacks += table(MELEE_S_CELLS, MELEE_LENGTH, MELEE_COLS, True)
        await ctx.send(info + skills + attacks)

    @commands.command(name="randchar", aliases=["randomcharacter"])
    async def randchar(self, ctx):
        """"""  # TODO Add Description
        await roll_many(ctx, 6, "4d6kh3")

    @commands.command()
    async def pointbuy(self, ctx, *args):
        """"""  # TODO Add Description
        if "-dnd" in args:
            buyer = DND_POINT_BUYER
        else:
            buyer = MAIN_POINT_BUYER
        points = buyer.points
        for arg in args:
            if arg.startswith("-points"):
                try:
                    points = int(arg[7:])
                except ValueError:
                    raise ArgumentError("YOU MUST PUT A NUMBER AFTER THE ARGUMENT '-points'")
        await try_delete(ctx.message)
        test = await buyer.embed(ctx, points)
        [await test.add_reaction(emoji) for emoji in POINT_BUY_EMOJIS]

    @commands.Cog.listener()  # TODO: Make DMs Work, Make Other PPl adding it work
    async def on_raw_reaction_add(self, payload):
        if payload.user_id != self.bot.user.id:
            if data := search_csv(str(payload.message_id), "db/pointBuyMessages.csv"):
                if data[0] == "D&D":
                    buyer = DND_POINT_BUYER
                else:
                    buyer = MAIN_POINT_BUYER
                remove_emoji = payload.emoji
                name = payload.emoji.name
                if "⬆" == name:
                    data = buyer.change_score(data, 1)
                elif "⬇" == name:
                    data = buyer.change_score(data, -1)
                elif name in LOWERED_STAT_LIST:
                    if int(data[2]) >= 0:
                        remove_emoji = POINT_BUY_EMOJIS[int(data[2]) + 2]
                    else:
                        remove_emoji = None
                    data[2] = str(LOWERED_STAT_LIST.index(name))
                else:
                    return
                edit_csv([str(payload.message_id)] + data, "db/pointBuyMessages.csv")
                message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                embed = message.embeds[0]
                embed = buyer.update_description(data, embed)
                await message.edit(embed=embed)
                if remove_emoji:
                    await message.remove_reaction(remove_emoji, (await self.bot.fetch_user(int(data[9]))))
                if int(data[9]) != payload.user_id:
                    data[9] = str(payload.user_id)
                    edit_csv([str(payload.message_id)] + data, "db/pointBuyMessages.csv")
