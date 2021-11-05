from typing import Any, Optional, Literal, List
import discord

import aiohttp

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import json
from os import path

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

WANI_COG_ID = 4669677326061720122

RADICAL_COLOR = 0x01A4F6
KANJI_COLOR = 0xF400A3
VOCAB_COLOR = 0x9E00ED
BURNED_COLOR = 0x4D4D4D

status_ok = 200
request_type = "GET"
parser = "html.parser"


def error_embed(title="", description="") -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=BURNED_COLOR)


def kanji_embed(kanji_entry: dict) -> discord.Embed:
    character: str = kanji_entry["character"]
    primary: str = kanji_entry["name"]
    alternatives: list[str] = kanji_entry["alternatives"]
    onyomi: list[str] = kanji_entry["onyomi"]
    kunyomi: list[str] = kanji_entry["kunyomi"]
    level: int = kanji_entry["level"]

    return discord.Embed(
        title=f"{character} | {primary}",
        description=(
            f"""
            Level: {level}
            Alternative Meanings: {', '.join(alternatives)}
            On’yomi: {', '.join(onyomi)}
            Kun’yomi: {', '.join(kunyomi)}
            """
        ),
        color=KANJI_COLOR
    )


class WaniCog(commands.Cog):
    def __init__(self, bot: Red) -> None:
        self.bot = Red
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self,
            identifier=WANI_COG_ID,
            force_registration=True
        )
        cog_path = path.realpath(path.dirname(__file__))
        with open(path.join(cog_path, "radicals.json")) as f:
            self.radicals = json.loads(f.read())
        with open(path.join(cog_path, "kanji.json")) as f:
            self.kanji = json.loads(f.read())
        with open(path.join(cog_path, "vocab.json")) as f:
            self.vocab = json.loads(f.read())

    def cofg_unload(self) -> None:
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    @ commands.group()
    async def wani(self, ctx: commands.Context) -> None:
        pass

    @ wani.command(aliases=["k"])
    async def kanji(self, ctx: commands.Context, *, kanji: str) -> None:
        """
        Get information for `kanji`
        Will only get info for first character
        """
        embed: Optional[discord.Embed] = None
        if len(kanji) < 1:
            embed = error_embed("Invalid query", "No query provieded")
        else:
            if len(kanji) > 1:
                kanji = kanji[0]
            try:
                embed = kanji_embed(
                    k for k in self.kanji if k["character"] == kanji)
            except:
                embed = error_embed(f"{kanji} not found")

        await ctx.send(embed=embed)
