from .globals import validRegions, Jstats
from typing import Union

from sqlalchemy.orm import Session
import discord

from lib.ormDefinitions import DisServer
import aiohttp
import lib.rchelpers as rchelpers
from lib.Helper import porpotionalAlign, compTiers
from lib.globals import engine


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


async def past10(ctx, account, region):
    name, tag = account.split("#")

    if type(region) is None:
        with Session(engine) as session:
            session.query(
                DisServer
            ).where(
                DisServer.server_id == str(ctx.guild.id)
            ).one_or_none().region

    await ctx.respond(f"Working on that ... {globals.loadingEmoji}")

    matches = None
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{name}/{tag}") as r:
            matches = Jstats(await r.json(), r.status)

    check = rchelpers.httpStatusCheck(matches)
    if check is not None:
        await ctx.respond(check)
        return

    tier = matches.json["data"][0]["currenttier"]

    matchesString = ""  # "```"
    for match in matches.json["data"]:
        emoji = ""

        if match["mmr_change_to_last_game"] > 0:
            emoji = globals.uparrow

        elif match["mmr_change_to_last_game"] < 0:
            emoji = globals.downarrow
        else:
            emoji = globals.equalarrow

        elomod = match['elo'] % 100

        nextRankSection = ""
        if match["currenttierpatched"] != "Radiant":  # You can't rank up past radiant
            nextRankSection = f"- {str(elomod).rjust(2, ' ')}/100"

        matchesString += f"\n{match['currenttierpatched']} {nextRankSection} - {emoji} {'+' if match['mmr_change_to_last_game'] >= 0 else ''}{match['mmr_change_to_last_game']} - {match['elo']}"
    # matchesString += "```"

    matchesString = porpotionalAlign(matchesString)

    embed = discord.Embed(
        title=f"{name}#{tag}",
        description=matchesString
    ).add_field(
        name=matches.json["data"][0]["currenttierpatched"],
        value=matches.json["data"][0]["elo"]
    )

    embed.set_thumbnail(url=compTiers()[tier]["largeIcon"])

    await ctx.edit(content=None, embed=embed)
