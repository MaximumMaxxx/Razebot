import discord
from .globals import validRegions, Jstats
from typing import Union


def regionAutoComplete(ctx: discord.AutocompleteContext):
    """Returns the regions that start with what you've typed"""
    return list(filter(lambda x: x.startswith(ctx.value.lower()), validRegions))


def httpStatusCheck(jstat: Jstats) -> Union[discord.Embed, None]:
    """Checks the status of the http request and returns an embed if there is an error"""
    if jstat.status == 200:
        return None

    if jstat.status == 403:
        return discord.Embed(
            title="Error",
            description="The Riot servers are currently not up, please try again later. If this error persists please contact MaxiumMaxx#0001",
            color=discord.Color.red()
        )

    if jstat.status == 429:
        return discord.Embed(
            title="Error",
            description="Razebot is currently being rate limited. Please try again later."
        )

    else:
        err = jstat.json["errors"][0]
        return discord.Embed(
            title="Error",
            description=f"There was an error with the request. Status code: {jstat.status}\nmsg: {err['message']}| code: {err['code']}| details: {err['details']}"
        )
