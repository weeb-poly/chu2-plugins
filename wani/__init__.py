import json
from pathlib import Path

from redbot.core.bot import Red

from .wani import WaniCog

with open(Path(__file__).parent / "info.json") as fp:
    __read_end_user_data_statement_ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    bot.add_cog(WaniCog(bot))
