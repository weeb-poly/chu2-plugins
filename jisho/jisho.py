# Based on jisho-bot by hummusw

# Standard Library
from typing import Literal
from urllib.parse import quote as urlquote

# External Lib
import aiohttp

# Discord
import discord

# Red
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils import menus
from redbot.core.utils.predicates import ReactionPredicate

RequestType = Literal["discord_deleted_user", "owner", "user", "user_strict"]


JISHO_COG_ID = 3245301569410685578 # Random 64 bit number
JISHO_API_SEARCH = "http://jisho.org/api/v1/search/words"


EMBED_COLOR_JISHO = 0x3edd00
EMBED_THUMBNAIL_JISHO = 'https://assets.jisho.org/assets/touch-icon-017b99ca4bfd11363a97f66cc4c00b1667613a05e38d08d858aa5e2a35dce055.png'


class JishoCog(commands.Cog):    
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self,
            identifier=JISHO_COG_ID,
            force_registration=True,
        )
        default_global = {
            "results_per_page": 5
        }
        self.config.register_global(**default_global)

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, *, requester: RequestType, user_id: int) -> None:
        super().red_delete_data_for_user(requester=requester, user_id=user_id)

    async def _command_search_pages(self, query: str, results: list) -> list:
        """
        Builds a search results embed from a response json
        :param query: query for jisho.org search
        :param results: response from jisho.org api
        :return: list of embeds
        """

        def _form_readable(form: dict) -> str:
            """
            Helper method to return a readable version of a form: kanji with reading if both exist, otherwise whichever one does
            :param form: dictionary with key 'reading' and possibly the key 'word'
            :return: string of kanji with reading or just reading, whichever is appropriate
            """
            if form.get('word') and form.get('reading'):
                return f'{form["word"]}（{form["reading"]}）'
            elif form.get('word'):
                return form['word']
            else:
                return form['reading']

        results_per_page = await self.config.results_per_page()

        pages = []

        default_embed = discord.Embed(
            title = 'jisho.org search results for {query}'.format(query=query),
            description = '*Sorry, no results were found*',
            url = 'https://jisho.org/search/{query}'.format(query=urlquote(query, safe="")),
            color = EMBED_COLOR_JISHO
        ).set_footer(
            text = 'Use the reacts for more actions\nPowered by jisho.org\'s beta API'
        ).set_thumbnail(
            url = EMBED_THUMBNAIL_JISHO
        )

        embed = None

        for (idx, result) in enumerate(results):
            if idx % results_per_page == 0:
                if embed is not None:
                    pages.append(embed)

                embed = default_embed.copy()
                end_at = min(idx + results_per_page, len(results))
                embed.description = '*Showing results {start} to {end} (out of {total})*'.format(start=idx+1, end=end_at, total=len(results))

            emoji = ReactionPredicate.NUMBER_EMOJIS[idx % results_per_page + 1]
            readings = result.get('japanese', [])
            readable_word = _form_readable(readings[0])

            embed.add_field(name=emoji, value=readable_word, inline=False)

        if embed is None:
            embed = default_embed.copy()
        
        pages.append(embed)

        return pages

    @commands.group()
    async def jisho(self, ctx: commands.Context) -> None:
        pass

    @jisho.command(aliases=["s"])
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """
        Searches jisho.org for `query`
        """
        # Build embed, send message, add reactions
        results = []
        async with self.session.get(JISHO_API_SEARCH, params={"keyword": query}) as r:
            results = (await r.json()).get('data', [])

        pages = await self._command_search_pages(query, results)

        await menus.menu(ctx, pages, menus.DEFAULT_CONTROLS)

    @jisho.command(aliases=["d"])
    async def details(self, ctx: commands.Context, idx: int, *, query: str) -> None:
        """
        Shows details for the `num`th result for `query`
        """
        # Build embed, send message, add reactions
        results = []
        async with self.session.get(JISHO_API_SEARCH, params={"keyword": query}) as r:
            results = (await r.json()).get('data', [])

        pages = await self._command_search_pages(query, results)

        await menus.menu(ctx, pages, menus.DEFAULT_CONTROLS, page=idx)

    @jisho.command(aliases=["l"])
    async def link(self, ctx: commands.Context, url: str) -> None:
        """
        Analyzes a jisho.org link and tries to show details
        """
        pass
