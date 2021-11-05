from typing import Any, Optional, Literal, List
import discord

import aiohttp

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
import json
import os
from os import path

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]

WANI_COG_ID = 4669677326061720122

RADICAL_COLOR = 0x01A4F6
KANJI_COLOR = 0xF400A3
VOCAB_COLOR = 0x9E00ED
BURNED_COLOR = 0x4D4D4D


def error_embed(title="", description="") -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=BURNED_COLOR)


def radical_embed(radical_entry: dict) -> discord.Embed:
    character: str = radical_entry["character"]
    name: str = radical_entry["name"]
    level: int = radical_entry["level"]

    return discord.Embed(
        title=f"Radical: {character} | {name}",
        description=f"Level: {level}",
        color=RADICAL_COLOR
    )


def kanji_embed(kanji_entry: dict) -> discord.Embed:
    character: str = kanji_entry["character"]
    primary: str = kanji_entry["name"]
    alternatives: list[str] = kanji_entry["meaning"]["alternatives"]
    onyomi: list[str] = kanji_entry["readings"]["onyomi"]
    kunyomi: list[str] = kanji_entry["readings"]["kunyomi"]
    level: int = kanji_entry["level"]

    return discord.Embed(
        title=f"Kanji: {character} | {primary}",
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


def vocab_embed(vocab_entry: dict) -> discord.Embed:
    vocab: str = vocab_entry["vocab"]
    level: int = vocab_entry["level"]
    reading: str = vocab_entry["reading"]["reading"]
    primary: str = vocab_entry["meaning"]["primary"]
    alternatives: list[str] = vocab_entry["meaning"]["alternatives"]

    return discord.Embed(
        title=f"Vocab: {vocab} | {reading}",
        description=(
            f"""
            Level: {level}
            Primary: {primary}{f"{os.linesep}{', '.join(alternatives) if len(alternatives) > 0 else ''}"}
            """
        ),
        color=VOCAB_COLOR
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

    @commands.group()
    async def wani(self, ctx: commands.Context) -> None:
        pass

    @wani.command(aliases=["r"])
    async def radical(self, ctx: commands.Context, *, radical: str) -> None:
        """
        Get information for `radical`
        Search by radical if query length is 1, else search by name
        """
        embed: Optional[discord.Embed] = None
        if len(radical) < 1:
            embed = error_embed("Invalid query", "No radical provided")
        else:
            try:
                if len(radical) > 1:
                    embed = radical_embed(next(
                        r for r in self.radicals if r["name"].lower() == radical.lower()
                    ))
                else:
                    embed = radical_embed(next(
                        r for r in self.radicals if r["character"] == radical
                    ))
            except Exception as e:
                print(e)
                embed = error_embed(f"{radical} not found")
        await ctx.send(embed=embed)

    @wani.command(aliases=["k"])
    async def kanji(self, ctx: commands.Context, *, kanji: str) -> None:
        """
        Get information for `kanji`
        Will only get info for the first character
        """
        embed: Optional[discord.Embed] = None
        if len(kanji) < 1:
            embed = error_embed("Invalid query", "No kanji provided")
        else:
            if len(kanji) > 1:
                kanji = kanji[0]
            try:
                embed = kanji_embed(next(
                    k for k in self.kanji if k["character"] == kanji))
            except Exception as e:
                print(e)
                embed = error_embed(f"{kanji} not found")

        await ctx.send(embed=embed)

    @wani.command(aliases=["v"])
    async def vocab(self, ctx: commands.Context, *, vocab: str) -> None:
        """
        Get information for `kanji`
        """
        embed: Optional[discord.Embed] = None
        if len(vocab) == 0:
            embed = error_embed("Invalid query", "No vocab provided")
        else:
            try:
                embed = vocab_embed(next(
                    v for v in self.vocab if v["vocab"] == vocab
                ))
            except Exception as e:
                print(e)
                embed = error_embed(f"{vocab} not found")

        await ctx.send(embed=embed)
