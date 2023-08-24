import asyncio
import datetime
import math
import os
import re
from contextlib import contextmanager
from pathlib import Path

import discord
import google.oauth2.service_account
import gspread as gspread
import random
from d20 import roll
from discord.ext import commands
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from cogs.Roller.utils import roll_many, string_search_adv
from utils.config import SYSTEM_ABV
from utils.csvUtils import search_csv, edit_csv, write_csv, read_line, read_csv, read_keys
from utils.dice import adv_dis_to_roll
from utils.errors import ExternalImportError, ArgumentError, UserDatabaseError, make_success, InputMatchError
from utils.functions import try_delete, search_list, format_mod
from utils.lists import skills
from .utils import PointBuyer
from .utils import STAT_LIST

LOWERED_STAT_LIST = [stat.lower() for stat in STAT_LIST]

URL_KEY_V1_RE = re.compile(r"key=([^&#]+)")
URL_KEY_V2_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")

ADV_DIS_RE = re.compile(r"(-(?:adv|advantage)\s?(-?\d+))")
KNOWLEDGE_RE = re.compile(r"(-(?:know|knowledge)\s?(.*))")
RANGE_RE = re.compile(r"(-(?:ran|range)\s?(\d+))")
MOD_RE = re.compile(r"([+-]\s*\d+)")

MAIN_POINT_BUYER = PointBuyer(SYSTEM_ABV, 10, (6, 18), (14, 16), 16)
DND_POINT_BUYER = PointBuyer("D&D", 8, (8, 15), (13,), 27)

POINT_BUY_EMOJIS = ["⬆", "⬇", "<:str:986970474087088138>", "<:dex:986970473210449960>", "<:con:986970468840005672>",
                    "<:int:986970471616634900>", "<:wis:986970470563844106>", "<:cha:986970469733400668>"]

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

VOWELS = ['a', 'e', 'i', 'o', 'u']

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

ATTACKS_S_CELL = (51, 1)
ATTACKS_WIDTH = 3
ATTACKS_WIDTH_SPACE = 4
ATTACKS_HEIGHT = 1
ATTACKS_HEIGHT_SPACE = 1

NAME_CELL = ((1, 6),)
INFO_CELLS = ((5, 6), (15, 8), (15, 11), (15, 14), (58, 39), (60, 39))

SANITY_CELL = (8, 27)


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
            raise ExternalImportError("STILL CONNECTING TO GOOGLE")
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
            raise UserDatabaseError("NO ACTIVE CHARACTER")

    @staticmethod
    def _set_user_character(user_id, char_name):
        path = CharacterManager._user_path(user_id)
        Path(path).mkdir(parents=True, exist_ok=True)
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
    def _get_character_knowledge_dictionary(path):
        skill_dict = CharacterManager._get_character_skill_dictionary(path)
        bad_keys = []
        for key in skill_dict:
            if 11 < skill_dict[key] < 18:
                continue
            bad_keys.append(key)
        for key in bad_keys:
            skill_dict.pop(key)
        return skill_dict

    @staticmethod
    def _blank_char_embed(path):
        lines = read_csv(f"{path}/info.csv")
        embed = discord.Embed(colour=discord.Colour(int(lines[5][0], 16)))
        if url := lines[6][0]:
            embed.set_thumbnail(url=url)
        return embed

    @staticmethod
    def _extract_argument(re_str, input_str, on_fail=""):
        if match := re_str.search(input_str):
            input_str = input_str[: (match.start(1))] + input_str[match.end():]
        elif on_fail:
            raise InputMatchError(on_fail)
        return input_str, match

    @staticmethod
    def _a_an(input_str):
        return f"{'an' if input_str[0] in VOWELS else 'a'} {input_str}"

    @staticmethod
    def _get_char_key(path):
        lines = read_csv(f"{path}/info.csv")
        return lines[0][0]

    async def _get_char_doc(self, key):
        if CharacterManager.g_client is None:
            await self._init_gsheet_client()
        elif CharacterManager._is_expired():
            await self._refresh_google_token()
        try:
            return self.g_client.open_by_key(key)
        except gspread.exceptions.APIError:
            raise ExternalImportError("Make sure your sheet is set to viewing privileges")

    async def _update_char(self, key, author_id):
        doc = await self._get_char_doc(key)
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
                    f_grid.append(
                        [CharacterManager._cell_convert(values[start_cell[0] + row][start_cell[1] + col]), '', 0])
            return f_grid

        def cells(coords):
            f_cells = []
            for coord in coords:
                f_cells.append([CharacterManager._cell_convert(values[coord[0]][coord[1]])])
            return f_cells

        name = cells(NAME_CELL)[0][0]
        info = [[key]] + cells(INFO_CELLS)
        skills = table(SKILL_S_CELLS, SKILL_LENGTH, SKILL_COLS, False)
        skills.append([CharacterManager._cell_convert(values[9][12]), '', 0])
        skills.extend(grid(STATS_S_CELL, STATS_WIDTH, STATS_WIDTH_SPACE, STATS_HEIGHT, STATS_HEIGHT_SPACE))
        skills.extend(grid(SAVES_S_CELL, SAVES_WIDTH, SAVES_WIDTH_SPACE, SAVES_HEIGHT, SAVES_HEIGHT_SPACE))
        skills.extend(grid(ATTACKS_S_CELL, ATTACKS_WIDTH, ATTACKS_WIDTH_SPACE, ATTACKS_HEIGHT, ATTACKS_HEIGHT_SPACE))
        attacks = table(RANGED_S_CELLS, RANGED_LENGTH, RANGED_COLS, True)
        attacks.extend(table(MELEE_S_CELLS, MELEE_LENGTH, MELEE_COLS, True))

        path = CharacterManager._set_user_character(author_id, name)

        Path(path + name).mkdir(parents=True, exist_ok=True)

        CharacterManager._write_char_file(path, info, "info")
        CharacterManager._write_char_file(path, skills, "skills")
        CharacterManager._write_char_file(path, attacks, "attacks")

        return name

    @commands.command(name="gsheet", aliases=["gs"])
    async def gsheet(self, ctx, url: str):
        """"""  # TODO Add Description
        key = extract_gsheet_id_from_url(url)

        name = await self._update_char(key, ctx.author.id)

        await ctx.send(make_success(f"{name} HAS BEEN CREATED"))
        await ctx.send(make_success(f"{name} IS NOW YOUR ACTIVE CHARACTER"))

    @commands.command(name="update", aliases=["up"])
    async def update(self, ctx):
        """"""  # TODO Add Description
        path, name = self._char_path(ctx.author.id)
        key = self._get_char_key(path)
        await self._update_char(key, ctx.author.id)

        await ctx.send(make_success(f"{name} HAS BEEN UPDATED"))

    @commands.command(name="link", aliases=["lk"])
    async def link(self, ctx):
        """"""  # TODO Add Description
        path, name = self._char_path(ctx.author.id)
        key = self._get_char_key(path)

        embed = self._blank_char_embed(path)
        embed.title = f"{name}'s Link Is:"
        embed.description = f"https://docs.google.com/spreadsheets/d/{key}/"

        await ctx.send(embed=embed)

    @commands.command(name="character", aliases=["char"])
    async def character(self, ctx, name: str):
        """"""  # TODO Add Description
        path = self._user_path(ctx.author.id)
        if match := search_list(name, next(os.walk(path))[1]):
            self._set_user_character(ctx.author.id, match[1])
            embed = self._blank_char_embed(path + match[1])
            embed.title = f"{match[1]} is now your active character!"
            await try_delete(ctx.message)
            await ctx.send(embed=embed)
        else:
            raise InputMatchError("NOT A CHARACTER")

    @commands.command(name="check", aliases=["chk", "czech"])
    async def check(self, ctx, *, input_skill):
        """"""  # TODO Add Description
        # region Easter Eggs
        easter_string = input_skill.strip().lower()
        if easter_string == "piss":
            await ctx.send(file=discord.File("db/easter_eggs/piss-i-cant-talk.gif"))
            return
        elif easter_string == "beef":
            await ctx.send(file=discord.File("db/easter_eggs/b96de9fc-6c91-490a-b08a-d74b728dec49.png"))
            return
        elif easter_string == "dyslexia":
            await ctx.send(file=discord.File("db/easter_eggs/funny-cant-see.gif"))
            return
        elif easter_string == "erection":
            randNum = random.random()
            print(f"ER CHECK: {randNum}")
            if randNum <= 0.01:
                await ctx.send(file=discord.File("db/easter_eggs/fail.gif"))
            else:
                await ctx.send(file=discord.File("db/easter_eggs/neco-arc-erection.gif"))
            return
        elif easter_string == "backpack":
            await ctx.invoke(self.bot.get_command('rr'), iterations=20, dice="d100")
            return
        elif easter_string == "rat":
            await ctx.send(file=discord.File("db/easter_eggs/rat.gif"))
            return
        # endregion

        adv_num = 0
        if match := ADV_DIS_RE.search(input_skill):
            adv_num += int(match.group(2))
            input_skill = input_skill[: (match.start(1))] + input_skill[match.end():]
        input_skill, adv = string_search_adv(input_skill)
        adv_num += int(adv)
        path, name = self._char_path(ctx.author.id)
        skill_path = f"{path}/skills.csv"
        extra_skill_dict = self._get_character_skill_dictionary(skill_path)

        mods = []

        if match := MOD_RE.search(input_skill):
            mods.append(format_mod(int(match.group(1))))
            input_skill = input_skill[: (match.start(1))] + input_skill[match.end():]

        if match := KNOWLEDGE_RE.search(input_skill):
            knowledge_dict = self._get_character_knowledge_dictionary(skill_path)
            if kno_match := search_list(match.group(2), [key for key in knowledge_dict]):
                knowledge_line = read_line(knowledge_dict[kno_match[1]], skill_path)
                mods.append(format_mod(int(int(knowledge_line[0]) / 2)))
                if int(knowledge_line[2]):
                    mods.append(format_mod(3))
            else:
                raise InputMatchError("NOT A KNOWLEDGE")
            input_skill = input_skill[: (match.start(1))] + input_skill[match.end():]

        if match := search_list(input_skill, skills + [key for key in extra_skill_dict]):
            line_num = match[0]
            if line_num >= len(skills):
                line_num = extra_skill_dict[match[1]]
            if line_num == len(skills) - 1:
                key = self._get_char_key(path)
                doc = await self._get_char_doc(key)
                sanity = int(doc.sheet1.cell(9, 28).value)
                res = roll("1d100")
                succeed = sanity > int(res)
                description = f"{str(res)}\n`{int(res)}` *{'<' if succeed else '>'}* `{sanity}` : ***{'Success' if succeed else 'Failure'}***"
            else:
                line = read_line(line_num, skill_path)
                mods = [format_mod(int(line[0]))] + mods
                mod_str = " ".join(mods)
                res = roll(f"{adv_dis_to_roll(adv_num + int(line[2]))}{mod_str}")
                description = str(res)
            embed = self._blank_char_embed(path)
            embed.title = f"{name} makes a {match[1]} check!"
            embed.description = description
            print(f"{name} makes a {match[1]} check! ------- {description}")
            await try_delete(ctx.message)
            await ctx.send(embed=embed)
        else:
            raise InputMatchError("NOT A SKILL")

    @commands.command(name="attack", aliases=["atk"])
    async def attack(self, ctx, *, input_attack):
        """"""  # TODO Add Description
        adv_num = 0
        input_attack, match = self._extract_argument(ADV_DIS_RE, input_attack)
        if match:
            adv_num += int(match.group(2))
        input_attack, adv = string_search_adv(input_attack)
        adv_num += int(adv)
        path, name = self._char_path(ctx.author.id)
        attack_path = f"{path}/attacks.csv"

        mods = []

        input_attack, match = self._extract_argument(MOD_RE, input_attack)
        if match:
            mods.append(format_mod(int(match.group(1))))

        atk_range = None
        input_attack, match = self._extract_argument(RANGE_RE, input_attack)
        if match:
            atk_range = int(match.group(2))

        input_attack, match = self._extract_argument(KNOWLEDGE_RE, input_attack)
        if match:
            knowledge_dict = self._get_character_knowledge_dictionary(f"{path}/skills.csv")
            if kno_match := search_list(match.group(2), [key for key in knowledge_dict]):
                mods.append(format_mod(int(int(read_line(knowledge_dict[kno_match[1]], f"{path}/skills.csv")[0]) / 2)))
            else:
                raise InputMatchError("NOT A KNOWLEDGE")

        if match := search_list(input_attack, read_keys(attack_path)):
            line = read_line(match[0], attack_path)

            atk_name = line[0]
            atk_dice = line[3]
            atk_type = line[4]

            if atk_range:
                if len(line) > 5:
                    mods.append(format_mod(math.floor(atk_range / int(line[5])) * int(line[6])))

            mods = [format_mod(int(line[1]))] + mods
            mod_str = " ".join(mods)

            adv_num += int(line[2]) - 1

            to_hit = roll(f"{adv_dis_to_roll(adv_num)}{mod_str}")
            damage = roll(atk_dice)

            embed = self._blank_char_embed(path)
            embed.title = f"{name} attacks with {self._a_an(atk_name)}"
            embed.description = f"**To Hit:** {str(to_hit)}\n**Damage:** {str(damage)} ***{atk_type}***"
            await try_delete(ctx.message)
            await ctx.send(embed=embed)
        else:
            raise InputMatchError("NOT A ATTACK")

    # @commands.command(name="funny", aliases=["fun"])
    # async def funny(self, ctx):
    #     embed = discord.Embed(colour=discord.Colour(int("2A2A2A", 16)))
    #     embed.set_image(url="https://i.ytimg.com/vi/oGl38onQJf0/maxresdefault.jpg")
    #     embed.title = f"Scoir | Download and Buy Today - Epic Games Store"
    #     embed.url = "https://www.scoir.com/"
    #     embed.description = "Download and play Submerged: Hidden Depths at the Epic Games Store. Check for platform availability and price!"
    #     embed.set_author(name="Epic Games Store", url="https://store.epicgames.com/en-US/")
    #     # embed.description = f"**To Hit:** {str(to_hit)}\n**Damage:** {str(damage)}"
    #     await try_delete(ctx.message)
    #     await ctx.send("**Scoir is free on the Epic Games Store until November 1, 2022 1:55 PM!**", embed=embed)

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
