# Original source of reaction-based menu idea from
# https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py
#
# Ported to Red V3 by Palm\_\_ (https://github.com/palmtree5)
# Modified from RedBot to use state
import asyncio
import contextlib
import functools
from typing import Any, Awaitable, Callable, Iterable, Optional, Dict, Union

import discord

from redbot.core.commands import Context
from redbot.core.utils.predicates import ReactionPredicate

_ReactableEmoji = Union[str, discord.Emoji]
_SMenuFn = Callable[[Context, discord.Embed, dict, discord.Message, Any, float, str], Awaitable[None]]

async def smenu(
    ctx: Context,
    embed: discord.Embed,
    controls: Dict[str, _SMenuFn],
    message: Optional[discord.Message] = None,
    state: Any = None,
    timeout: float = 30.0,
):
    """
    An emoji-based menu with a state

    .. note:: All functions for handling what a particular emoji does
              should be coroutines (i.e. :code:`async def`). Additionally,
              they must take all of the parameters of this function, in
              addition to a string representing the emoji reacted with.
              This parameter should be the last one, and none of the
              parameters in the handling functions are optional

    Parameters
    ----------
    ctx: Context
        The command context
    embed: discord.Embed
        The current page of the menu.
    controls: dict
        A mapping of emoji to the function which handles the action for the
        emoji.
    message: Optional[discord.Message]
        The message representing the menu. Usually :code:`None` when first opening
        the menu
    state: Any
        The current state of the menu
    timeout: float
        The time (in seconds) to wait for a reaction


    Raises
    ------
    RuntimeError
        If either of the notes above are violated
    """

    for key, value in controls.items():
        maybe_coro = value
        if isinstance(value, functools.partial):
            maybe_coro = value.func
        if not asyncio.iscoroutinefunction(maybe_coro):
            raise RuntimeError("Function must be a coroutine")

    current_page = embed

    if not message:
        message = await ctx.send(embed=current_page)
        # Don't wait for reactions to be added (GH-1797)
        # noinspection PyAsyncCall
        start_adding_reactions(message, controls.keys())
    else:
        try:
            await message.edit(embed=current_page)
        except discord.NotFound:
            return

    try:
        predicates = ReactionPredicate.with_emojis(tuple(controls.keys()), message, ctx.author)
        tasks = [
            asyncio.ensure_future(ctx.bot.wait_for("reaction_add", check=predicates)),
            asyncio.ensure_future(ctx.bot.wait_for("reaction_remove", check=predicates)),
        ]
        done, pending = await asyncio.wait(
            tasks, timeout=timeout, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

        if len(done) == 0:
            raise asyncio.TimeoutError()
        react, user = done.pop().result()
    except asyncio.TimeoutError:
        if not ctx.me:
            return
        try:
            if message.channel.permissions_for(ctx.me).manage_messages:
                await message.clear_reactions()
            else:
                raise RuntimeError
        except (discord.Forbidden, RuntimeError):  # cannot remove all reactions
            for key in controls.keys():
                try:
                    await message.remove_reaction(key, ctx.bot.user)
                except discord.Forbidden:
                    return
                except discord.HTTPException:
                    pass
        except discord.NotFound:
            return
    else:
        return await controls[react.emoji](
            ctx, embed, controls, message, state, timeout, react.emoji
        )


async def do_something(
    ctx: Context,
    embed: discord.Embed,
    controls: dict,
    message: discord.Message,
    state: Any,
    timeout: float,
    emoji: str,
):
    return await smenu(ctx, embed, controls, message=message, state=state, timeout=timeout)

async def close_menu(
    ctx: Context,
    embed: discord.Embed,
    controls: dict,
    message: discord.Message,
    state: Any,
    timeout: float,
    emoji: str,
):
    with contextlib.suppress(discord.NotFound):
        await message.delete()


def start_adding_reactions(
    message: discord.Message,
    emojis: Iterable[_ReactableEmoji]
) -> asyncio.Task:
    """Start adding reactions to a message.

    This is a non-blocking operation - calling this will schedule the
    reactions being added, but the calling code will continue to
    execute asynchronously. There is no need to await this function.

    This is particularly useful if you wish to start waiting for a
    reaction whilst the reactions are still being added - in fact,
    this is exactly what `menu` uses to do that.

    Parameters
    ----------
    message: discord.Message
        The message to add reactions to.
    emojis : Iterable[Union[str, discord.Emoji]]
        The emojis to react to the message with.

    Returns
    -------
    asyncio.Task
        The task for the coroutine adding the reactions.

    """

    async def task():
        # The task should exit silently if the message is deleted
        with contextlib.suppress(discord.NotFound):
            for emoji in emojis:
                await message.add_reaction(emoji)

    return asyncio.create_task(task())
