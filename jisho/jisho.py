# Based on jisho-bot by hummusw

# Standard Library
from typing import Tuple
from urllib.parse import quote as urlquote
import asyncio
import logging

# External Lib
import aiohttp

# Discord
import discord

# Red
from redbot.core import commands
from redbot.core.bot import Red

# Custom imports
from .strings import *
from .constants import *
from .state import *


class JishoCog(commands.Cog):
    bot: Red
    cache: MessageCache
    session: aiohttp.ClientSession

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.cache = MessageCache(CACHE_MAXSIZE)
        self.session = aiohttp.ClientSession()

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def jisho(self, _ctx: commands.Context) -> None:
        pass

    # Command functions - lookup

    @jisho.command(aliases=["s"])
    async def search(self, ctx: commands.Context, *, query: str) -> None:
        """
        Searches jisho.org for `query`
        """

        # Communicate with jisho's beta API
        response_json = await self._api_call(query)

        found_results = bool(len(self._get_results_list(response_json)))

        # Build embed
        embed = self._command_search_embedfromjson(query, response_json, 0)

        # send message
        bot_message = await ctx.channel.send(embed=embed)

        # Add to message cache
        await self.cache.insert(
            MessageStateQuery(ctx.author, query, response_json, bot_message, 0, self._cache_cleanup)
        )

        # Add reactions, wait for interaction
        if found_results:
            await self._addreactions_search(bot_message, response_json)
            await self._wait_search(bot_message)
        else:
            await self._addreactions_xonly(bot_message)
            await self._wait_nothing(bot_message)

    def _command_search_embedfromjson(
        self,
        search_query: str,
        response_json: dict,
        start_from: int
    ) -> discord.Embed:
        """
        Builds a search results embed from a response json

        :param search_query: query for jisho.org search
        :param response_json: response from jisho.org api
        :param start_from: shows search results starting at this offset
        :return: search embed
        """

        # Build embed
        embed = discord.Embed(
            title = EMBED_SEARCH_TITLE_STEM.format(query=search_query),
            description = EMBED_SEARCH_DESCRIPTION_NORESULTS,
            url = EMBED_SEARCH_URL_STEM.format(query=urlquote(search_query, safe="")),
            color = EMBED_COLOR_JISHO
        ).set_footer(
            text = EMBED_SEARCH_FOOTER
        ).set_thumbnail(
            url = EMBED_THUMBNAIL_JISHO
        )

        # Header for search results list
        results_json = self._get_results_list(response_json)
        end_at = min(start_from + RESULTS_PER_PAGE, len(results_json))
        reply_message = EMBED_SEARCH_DESCRIPTION_STEM.format(
            start=start_from + 1,
            end=end_at,
            total=len(results_json)
        )

        # Format each line with the react emoji as well as the kanji + pronunciation (if possible)
        for i in range(start_from, end_at):
            emoji = EMOJI_NUMS[i % RESULTS_PER_PAGE + 1]
            readings = self._get_readings_list(results_json[i])
            readable_word = self._form_readable(readings[0])
            reply_message += EMBED_SEARCH_RESULT_FORMAT.format(emoji=emoji, result=readable_word)

        # Change response message if there are results
        if len(results_json) is not 0:
            embed.description = reply_message.strip()

        return embed

    @jisho.command(aliases=["d"])
    async def details(self, ctx: commands.Context, num: int, *, query: str) -> None:
        """
        Shows details for the `num`th result for `query`
        """

        number = num - 1

        # Build embed, send message
        embed, response_json = await self._command_details_embed(number, query)
        bot_message = await ctx.channel.send(embed=embed)

        # Add to message cache
        await self.cache.insert(
            MessageStateQuery(
                ctx.author,
                query,
                response_json,
                bot_message,
                number - (number % RESULTS_PER_PAGE),
                self._cache_cleanup
            )
        )

        # Add reactions, wait for interaction
        await self._addreactions_details(bot_message)
        await self._wait_details(bot_message)

    async def _command_details_embed(self, number: int, search_query: str) -> Tuple[discord.Embed, dict]:
        """
        Queries jisho.org api to shows details for a search query

        :param number: the result number to show details for (zero-indexed)
        :param search_query: query for jisho.org search
        :return: details embed, response json
        """

        # Communicate with jisho's beta API
        response_json = await self._api_call(search_query)

        # Make sure the result number we're looking for exists
        if number < 0 or number >= len(self._get_results_list(response_json)):
            raise IndexError(ERROR_INDEXERROR_STEM.format(number=number + 1, query=search_query))

        return self._command_details_embedfromjson(number, search_query, response_json), response_json

    def _command_details_embedfromjson(
        self,
        number: int,
        search_query: str,
        response_json: dict
    ) -> discord.Embed:
        """
        Builds a details embed from a response json

        :param number: the result number to show details for (zero-indexed)
        :param search_query: query for jisho.org search
        :param response_json: response from jisho.org api
        :return: details embed
        """

        details_json: dict = self._get_results_list(response_json)[number]
        readings = self._get_readings_list(details_json)

        # Get kanji (if exists) and reading
        word = self._form_readable(readings[0]) + '\n'

        # Get definitions
        definitions_truncated = False
        definitions = []
        definitions_json = details_json['senses']

        for i, def_json in enumerate(definitions_json):
            definition = ''

            # First add parts of speech, italicized if it exists
            parts_of_speech = def_json.get('parts_of_speech')
            if parts_of_speech is not None:
                definition += f'*{", ".join(parts_of_speech)}*\n'

            # Then add definitions, numbered and bolded
            definition += f'**{i + 1}. {"; ".join(def_json["english_definitions"])}** '

            # Then add extras
            extras = []

            # Used for Wikipedia definitions, don't include
            # if details_json['links']:
            #     extras += ['Links: ' + ', '.join(details_json['links'])]
            def_json_tags = def_json.get('tags')
            if def_json_tags is not None:
                extras += [', '.join(def_json_tags)]

            if def_json.get('restrictions'):
                extras += ['Only applies to ' + ', '.join(def_json['restrictions'])]
            if def_json.get('see_also'):
                extras += ['See also ' + ', '.join(def_json['see_also'])]
            if def_json.get('antonyms'):
                extras += ['Antonym: ' + ', '.join(def_json['antonyms'])]
            if def_json.get('source'):  # used for words from other languages, see 加油
                extras += ['From ' + ', '.join([f"{source['language']} {source['word']}" for source in def_json['source']])]
            if def_json.get('info'):  # used for random notes (see 行く, definition 2)
                extras += [', '.join(def_json['info'])]
            definition += ', '.join(extras)

            # Check maximum length (entries such as 行く can go over this) before adding to list
            if len('\n'.join(definitions)) + 1 + len(definition) > EMBED_FIELD_MAXLENGTH:
                definitions_truncated = True
                break
            else:
                definitions += [definition]

        definitions = '\n'.join(definitions)

        # Get tags (common, jlpt, wanikani)
        tags = []

        # Check if word is listed as common
        if details_json.get('is_common'):  # apparently some entries don't have a is_common key
            tags += [EMBED_DETAILS_TAGS_COMMON]

        # Apparently a single word can have multiple JLPT levels, choose the largest/easiest one (see 行く)
        jlpt = details_json.get('jlpt', [])
        if len(jlpt) is not 0:
            max_level = max(list(map(lambda l: l[-1], jlpt)))
            tags += [EMBED_DETAILS_TAGS_JLPTLEVEL_STEM.format(level=max_level)]

        # Get wanikani levels, assuming all tags are wanikani tags
        for entry in details_json.get('tags', []):
            if not entry.startswith('wanikani'):
                logging.debug(f'Unexpected tag: {entry}')
                continue

            wk_level = int(entry[len('wanikani'):])
            wk_query = details_json["japanese"][0]["word"]  # todo optimize search query
            tags += [EMBED_DETAILS_TAGS_WANIKANI_STEM.format(level=wk_level, query=wk_query)]

        # Default no-tags message
        if len(tags) is 0:
            tags = [EMBED_DETAILS_TAGS_NONE]

        tags = '\n'.join(tags)

        # Get other forms
        many_forms = len(readings) > 1
        other_forms = '、'.join([self._form_readable(form) for form in readings[1:]])

        # Get attribution data
        sources = [source for source, value in details_json['attribution'].items() if value]

        # Build embed
        slug = details_json["slug"]

        embed = discord.Embed(
            title = EMBED_DETAILS_TITLE_STEM.format(slug=slug),
            url = EMBED_DETAILS_URL_STEM.format(slug=slug),
            color = EMBED_COLOR_JISHO
        ).set_footer(
            text = EMBED_DETAILS_FOOTER_STEM.format(sources=', '.join(sources))
        ).set_thumbnail(
            url = EMBED_THUMBNAIL_JISHO
        )

        embed.add_field(name=EMBED_DETAILS_FIELD_WORD_NAME, value=word, inline=True)
        embed.add_field(name=EMBED_DETAILS_FIELD_TAGS_NAME, value=tags, inline=True)

        definitions_field_name = EMBED_DETAILS_FIELD_DEFINITIONSTRUNC_NAME if definitions_truncated else EMBED_DETAILS_FIELD_DEFINITIONS_NAME
        embed.add_field(name=definitions_field_name, value=definitions, inline=False)

        if many_forms:
            embed.add_field(name=EMBED_DETAILS_FIELD_OTHERFORMS_NAME, value=other_forms, inline=False)

        return embed

    @jisho.command(aliases=["l"])
    async def link(self, ctx: commands.Context, link: str) -> None:
        """
        Analyzes a jisho.org link and tries to show details
        """

        # Split link into sections, by '/'
        link_split = link.split('/')

        # Find 'jisho.org' in link, discard that and before parts
        for i, link_part in enumerate(link_split):
            if LINK_BASE in link_part.lower():
                base_index = i
                break
        else:
            raise SyntaxError(ERROR_LINK_NOTJISHO)

        link_split = link_split[base_index + 1:]

        # Make sure there's a /word or /search after jisho.org (not just the homepage)
        if len(link_split) < 2:
            raise SyntaxError(ERROR_LINK_NOQUERY)

        # Handle a search query (jisho.org/search)
        if link_split[0].lower() == LINK_SEARCH:
            # Get search query, make sure it's not a kanji details page
            query = link_split[1]
            if LINK_KANJI in query:
                raise SyntaxError(ERROR_LINK_NOKANJI)

            # Hand over to function to complete search
            await self.command_search(ctx, query)

        # Display word details (jisho.org/word)
        elif link_split[0].lower() == LINK_DETAILS:
            # Query the API directly by slug, guaranteed (?) one result, hand over to function to complete
            query = LINK_SLUGSEARCH_STEM.format(slug=link_split[1])
            await self.command_details(ctx, '1', query)

        else:
            raise SyntaxError(ERROR_LINK_NOTYPE)

    # Helper methods - wait for reactions

    async def _wait_search(self, message: discord.Message) -> None:
        """
        Waits for a reaction on a search results embed

        :param message: message to wait for a reaction to
        """

        # Wait for a reaction added to this message, by the original author, that is a valid emoji
        def check(reaction, user):
            cache_msg = self.cache[message]
            results = self._get_results_list(cache_msg.response)
            valid_reacts = [REACT_X]
            if len(results) > RESULTS_PER_PAGE:
                valid_reacts += REACTS_ARROWS
            valid_reacts += REACTS_NUMS[:min(RESULTS_PER_PAGE, len(results))]
            return reaction.message == message and user == cache_msg.author and str(reaction.emoji) in valid_reacts

        # On reaction, handle it appropriately (and clear reactions/cache on timeout)
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
            if str(reaction) == REACT_X:
                await self._action_clear(message)
            elif str(reaction) in REACTS_NUMS:
                await self._action_showdetails(message, REACTS_NUMS.index(str(reaction)))
            elif str(reaction) in REACTS_ARROWS:
                await self._action_changepage(message, reaction, user)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            await self.cache.remove(message)

    async def _wait_details(self, message: discord.Message) -> None:
        """
        Waits for a reaction on a details embed

        :param message: message to wait for a reaction to
        """

        # Wait for a reaction added to this message, by the original author, that is a valid emoji
        def check(reaction, user):
            cache_msg = self.cache[message]
            return reaction.message == message and user == cache_msg.author and str(reaction.emoji) in [REACT_RETURN, REACT_X]

        # On reaction, handle it appropriately (and clear reactions/cache on timeout)
        try:
            reaction, _user = await self.bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
            if str(reaction) == REACT_X:
                await self._action_clear(message)
            elif str(reaction) == REACT_RETURN:
                await self._action_back(message)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            await self.cache.remove(message)

    async def _wait_nothing(self, message: discord.Message) -> None:
        """
        Waits for a reaction on an embed that can only be removed

        :param message: message to wait for a reaction to
        """

        # Wait for a reaction added to this message, by the original author, that is a valid emoji
        def check(reaction, user):
            cache_msg = self.cache[message]
            return reaction.message == message and user == cache_msg.author and str(reaction.emoji) == REACT_X

        # On reaction, handle it appropriately (and clear reactions/cache on timeout)
        try:
            await self.bot.wait_for('reaction_add', timeout=TIMEOUT, check=check)
            await self._action_clear(message)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            await self.cache.remove(message)

    # Helper methods - reaction actions

    async def _action_back(self, message: discord.Message) -> None:
        """
        Goes back to search results from details

        :param message: message to go back
        """
        # Generate new embed
        messagestate = self.cache[message]
        new_embed = self._command_search_embedfromjson(messagestate.query, messagestate.response, messagestate.offset)

        # Edit message and reactions
        await message.edit(embed=new_embed)
        await self._removereactions_all(message)
        await self._addreactions_search(message, messagestate.response)

        # Wait for user interaction
        await self._wait_search(message)

    async def _action_clear(self, message: discord.Message) -> None:
        """
        Removes a message

        :param message: message to remove
        """

        await self.cache.remove(message)
        await message.delete()

    async def _action_showdetails(self, message: discord.Message, number: int) -> None:
        """
        Shows details for a search result

        :param message: message that had search results
        :param number: search result number to show details for (zero-indexed)
        """

        messagestate = self.cache[message]

        # Ignore invalid indexes
        if number + messagestate.offset >= len(self._get_results_list(messagestate.response)):
            return await self._wait_search(message)

        # Create new details embed
        new_embed = self._command_details_embedfromjson(number + messagestate.offset, messagestate.query, messagestate.response)

        # Edit message and reactions
        await message.edit(embed=new_embed)
        await self._removereactions_all(message)
        await self._addreactions_details(message)

        # Wait for user interaction
        await self._wait_details(message)

    async def _action_changepage(
        self,
        message: discord.Message,
        reaction: discord.Reaction,
        user: discord.User
    ) -> None:
        """
        Changes pages on a search results embed

        :param message: message that has search results
        :param reaction: reacted reaction
        :param user: reacting user
        """

        messagestate = self.cache[message]
        delta = (-RESULTS_PER_PAGE, RESULTS_PER_PAGE)[str(reaction) == REACT_ARROW_RIGHT]

        # Ignore page changes that would go out of bounds
        if not 0 <= messagestate.offset + delta < len(messagestate.response['data']):
            return await self._wait_search(message)

        # Create new search embed
        self.cache[message].offset += delta
        new_embed = self._command_search_embedfromjson(messagestate.query, messagestate.response, messagestate.offset)

        # Edit message and reactions
        await message.edit(embed=new_embed)
        await message.remove_reaction(reaction, user)

        # Wait for user interaction
        await self._wait_search(message)

    # Helper methods - add/remove reactions

    async def _addreactions_xonly(self, message: discord.Message) -> None:
        """
        Adds an x reaction to clear a sent embed

        :param message: Message to add reaction to
        """

        await message.add_reaction(REACT_X)

    async def _addreactions_search(self, message: discord.Message, response_json: dict) -> None:
        """
        Adds left and right arrows (if needed), numbers (as appropriate), and an x react to a search results message

        :param message: Message to add reactions to
        :param response_json: response json to find what reactions are needed
        """

        results = self._get_results_list(response_json)
        many_pages = len(results) > RESULTS_PER_PAGE

        if many_pages:
            await message.add_reaction(REACT_ARROW_LEFT)

        # Add five number reactions unless there are a fewer number of search results
        for reaction in REACTS_NUMS[:min(RESULTS_PER_PAGE, len(results))]:
            await message.add_reaction(reaction)

        if many_pages:
            await message.add_reaction(REACT_ARROW_RIGHT)

        await message.add_reaction(REACT_X)

    async def _addreactions_details(self, msg: discord.Message) -> None:
        """
        Adds return and x react to a details message
        """

        await msg.add_reaction(REACT_RETURN)
        await msg.add_reaction(REACT_X)

    async def _removereactions_all(self, msg: discord.Message) -> None:
        """
        Removes all reactions from a message
        """

        await msg.clear_reactions()

    # Until there are other things to do when removing from cache, this works todo cache is now effectively time-based, is this still needed?
    _cache_cleanup = _removereactions_all

    # Helper methods - logging  todo change to something else other than console / stdout and stderr

    async def _report_error(
        self,
        channel: discord.TextChannel,
        author: discord.User,
        error: str
    ) -> None:
        """
        Reports an error by sending an embed, as well as printing to stderr

        :param channel: channel to send error report to
        :param author: original author that caused error
        :param error_message: reported error
        """

        logging.error(error, exc_info=True, stack_info=True)

        embed_dict = {
            'title': EMBED_ERROR_TITLE,
            'description': error,
            'color': EMBED_COLOR_ERROR,
            'footer': {'text': EMBED_ERROR_FOOTER}
        }

        embed = discord.Embed.from_dict(embed_dict)

        bot_message = await channel.send(embed=embed)
        await bot_message.add_reaction(REACT_X)
        await self.cache.insert(MessageState(author, bot_message, self._cache_cleanup))

    # Helper methods - other

    async def _api_call(self, query: str) -> dict:
        """
        Helper method to do jisho.org's API call

        :param query: search query
        :return: JSON response
        :raises ValueError: status code is not 200 OK
        """

        async with self.session.get(JISHO_API_SEARCH, params={"keyword": query}) as r:
            status_code = r.status
            response_json = await r.json()

        if status_code != STATUS_OK:
            raise ValueError(ERROR_BADSTATUS_STEM.format(status=status_code))

        return response_json

    def _get_results_list(self, response_json: dict) -> list:
        """
        Helper method to get the list of search results from the response JSON (in case format changes later)

        :param response_json: response JSON returned from API
        :return: list of responses
        """

        return response_json.get('data', [])

    def _get_readings_list(self, details_json: dict) -> list:
        """
        Helper method to get the list of readings for a search result

        :param details_json: search result JSON
        :return: list of readings (dicts)
        """

        return details_json.get('japanese', [])

    def _form_readable(self, form: dict) -> str:
        """
        Helper method to return a readable version of a form: kanji with reading if both exist, otherwise whichever one does

        :param form: dictionary with key 'reading' and possibly the key 'word'
        :return: string of kanji with reading or just reading, whichever is appropriate
        """

        word = form.get('word')
        reading = form.get('reading')

        if word is not None and reading is not None:
            return f"{word}\uFF08{reading}\uFF09"
        elif word is not None:
            return word
        else:
            return reading
