import asyncio
import datetime
import re
from contextlib import contextmanager
from pathlib import Path

import discord
import google.oauth2.service_account
import gspread as gspread
from d20 import roll
from discord.ext import commands
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from cogs.Roller.utils import roll_many, string_search_adv, mention_user
from utils.config import SYSTEM_ABV
from utils.csvUtils import search_csv, edit_csv, write_csv, read_line, read_csv
from utils.dice import MainStringifier, adv_dis_to_roll
from utils.errors import ExternalImportError, ArgumentError, UserDatabaseError, make_success, InputMatchError
from utils.functions import try_delete, search_list
from utils.lists import skills
from .utils import PointBuyer
from .utils import STAT_LIST

LOWERED_STAT_LIST = [stat.lower() for stat in STAT_LIST]

URL_KEY_V1_RE = re.compile(r"key=([^&#]+)")
URL_KEY_V2_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")

ADV_DIS_RE = re.compile(r"(-adv\s?(-?\d+))")

MAIN_POINT_BUYER = PointBuyer(SYSTEM_ABV, 10, (6, 18), (14, 16), 16)
DND_POINT_BUYER = PointBuyer("D&D", 8, (8, 15), (13,), 27)

POINT_BUY_EMOJIS = ["⬆", "⬇", "<:str:986970474087088138>", "<:dex:986970473210449960>", "<:con:986970468840005672>",
                    "<:int:986970471616634900>", "<:wis:986970470563844106>", "<:cha:986970469733400668>"]

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

SKILL_S_CELLS = ((31, 1), (31, 25))
SKILL_LENGTH = 16
SKILL_COLS = (7, 11, 16)

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

NAME_CELL = ((1, 6),)
INFO_CELLS = ((5, 6), (15, 8), (15, 11), (15, 14), (58, 39), (60, 39))


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
        print("BREACHED INTO GOOGLE")

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
        print("REFRESHED TUNNELS TO GOOGLE")

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
    def _user_path(user_id):
        return f"db/Users/{user_id}/"

    @staticmethod
    def _char_path(user_id):
        path = CharacterManager._user_path(user_id)
        try:
            with open(path + "user_id.txt", "r") as f:
                name = f.readline()
                return path + name, name
        except FileNotFoundError:
            raise UserDatabaseError("ERROR: NO ACTIVE CHARACTER")

    @staticmethod
    def _set_user_character(user_id, char_name):
        path = CharacterManager._user_path(user_id)
        Path(path + char_name).mkdir(parents=True, exist_ok=True)
        with open(path + "user_id.txt", "w") as f:
            f.write(char_name)
        return path + char_name + "/"

    @staticmethod
    def _write_char_file(path, data, name):
        write_csv(data, path + name + ".csv")

    @staticmethod
    def _get_character_skill_dictionary(path):
        return_dict = {}
        for index, a in enumerate(read_csv(path)):
            if name := a[1]:
                return_dict[name] = index
        return return_dict

    @staticmethod
    def _blank_char_embed(path):
        lines = read_csv(f"{path}/info.csv")
        embed = discord.Embed(colour=discord.Colour(int(lines[4][0], 16)))
        embed.set_thumbnail(url=lines[5][0])
        return embed

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
                    f_grid.append([self._cell_convert(values[start_cell[0] + row][start_cell[1] + col]), '', 0])
            return f_grid

        def cells(coords):
            f_cells = []
            for coord in coords:
                f_cells.append([self._cell_convert(values[coord[0]][coord[1]])])
            return f_cells

        name = cells(NAME_CELL)[0][0]
        info = cells(INFO_CELLS)
        skills = table(SKILL_S_CELLS, SKILL_LENGTH, SKILL_COLS, False)
        skills.append([self._cell_convert(values[9][12]), '', 0])
        skills.extend(grid(STATS_S_CELL, STATS_WIDTH, STATS_WIDTH_SPACE, STATS_HEIGHT, STATS_HEIGHT_SPACE))
        skills.extend(grid(SAVES_S_CELL, SAVES_WIDTH, SAVES_WIDTH_SPACE, SAVES_HEIGHT, SAVES_HEIGHT_SPACE))
        attacks = table(RANGED_S_CELLS, RANGED_LENGTH, RANGED_COLS, True)
        attacks.extend(table(MELEE_S_CELLS, MELEE_LENGTH, MELEE_COLS, True))

        path = self._set_user_character(ctx.author.id, name)
        await ctx.send(make_success(f"{name} IS NOW YOUR ACTIVE CHARACTER"))

        self._write_char_file(path, info, "info")
        self._write_char_file(path, skills, "skills")
        self._write_char_file(path, attacks, "attacks")

        await ctx.send(make_success(f"{name} HAS BEEN CREATED"))

    @commands.command(name="check", aliases=["chk"])
    async def check(self, ctx, *, input_skill):
        """"""  # TODO Add Description, Add Knowledge Adding, Extra ADVS
        adv_num = 0
        if match := ADV_DIS_RE.search(input_skill):
            adv_num += int(match.group(2))
            input_skill = input_skill[: (match.start(1))] + input_skill[match.end():]
        input_skill, adv = string_search_adv(input_skill)
        input_skill = input_skill.strip()
        adv_num += int(adv)
        path, name = self._char_path(ctx.author.id)
        skill_path = f"{path}/skills.csv"
        extra_skill_dict = self._get_character_skill_dictionary(skill_path)

        if match := search_list(input_skill, skills + [key for key in extra_skill_dict]):
            line_num = match[0]
            if line_num >= len(skills):
                line_num = extra_skill_dict[match[1]]
            line = read_line(line_num, skill_path)
            mod = f"+{line[0]}" if int(line[0]) >= 0 else f"{line[0]}"
            res = roll(f"{adv_dis_to_roll(adv_num+int(line[2]))}{mod}")
            embed = self._blank_char_embed(path)
            embed.title = f"{name} makes a {match[1]} check!"
            embed.description = str(res)
            await try_delete(ctx.message)
            await ctx.send(embed=embed)
        else:
            raise InputMatchError("ERROR: NOT A SKILL")

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
