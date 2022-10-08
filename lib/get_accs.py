# Because of circular imports and stuff I had to split get_accs off from accHelpers.py
# Basically AccountSelector imported accHelpers and accHelpers imported AccountSelector which is a no-no
# This is the simplest solution I could come up with

import discord
import asyncio
import aiohttp
import logging
from PIL import ImageColor

from lib.Helper import compTiers, get_jstat
from lib.rchelpers import httpStatusCheck
from lib.globals import Jstats


async def get_acc(name: str, tag: str, region: str) -> discord.Embed:
    # Getting the actual account details

    jsons = []
    # Thank god for this article: https://www.twilio.com/blog/asynchronous-http-requests-in-python-with-aiohttp
    # This whole block is kinda weird but through some async magic it works and is significantly faster than requests
    async with aiohttp.ClientSession() as session:
        tasks = []
        for link in [
            f"https://api.henrikdev.xyz/valorant/v1/account/{name}/{tag}",
            f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{name}/{tag}?filter=competitive",
            f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{name}/{tag}"
        ]:
            tasks.append(asyncio.ensure_future(
                get_jstat(session, link)))

        jsons = await asyncio.gather(*tasks)

    accountReq, MH, MMR = jsons

    puuid = accountReq.json["data"]["puuid"]

    check = httpStatusCheck(accountReq)
    if check is not None:
        return check

    kills = deaths = assists = score = mmr_change = "Unknown"

    if MMR.status == 200:
        MMR_json = MMR.json
        mmr_change = 0
        for game in MMR_json["data"]:
            mmr_change += game["mmr_change_to_last_game"]

        if len(MMR_json["data"]) == 0:
            return discord.Embed(title="ERROR", description="No data avaliable for that player. Double check your spelling and try again.", color=discord.Color.red())

        rank = MMR_json["data"][0]["currenttierpatched"]
        tiernum = MMR_json["data"][0]["currenttier"]
        elo = MMR_json["data"][0]["elo"]

        logging.debug(f"{rank} {tiernum} {elo}")

        image: str = compTiers()[tiernum]["largeIcon"]

        color = compTiers()[tiernum]["color"][:6]

        r, g, b = ImageColor.getcolor("#"+color, "RGB")
        embed = discord.Embed(
            color=discord.Color.from_rgb(r, g, b),
            description=f"The stats and rank for {name}#{tag}", title=f"{name}#{tag}"
        )

        embed.add_field(name="Rank", value=rank)
        embed.add_field(name="MMR", value=elo)

    elif MMR.status == 204:
        return (discord.Embed(title="ERROR", description="Not enough recent data or wrong region", color=discord.Color.red()))

    elif MMR.status == 429:
        return (discord.Embed(title="ERROR", description="The bot has been rate limited. Please try again in a few minutes", color=discord.Color.red()))

    else:
        logging.error(
            f"{MMR.json} error while retrieve data region: {region} username: {name} tag: {tag}"
        )
        return (
            discord.Embed(
                title="ERROR",
                description="Something went horribly wrong and we are all going to die. If the error persits please message MaximumMaxx#0001",
                color=discord.Color.red()
            ).set_footer(
                text="Razebot by MaximumMaxx"
            )
        )

    if MH.status == 200:
        MH_json = MH.json
        match_count = len(MH_json["data"])
        kills, deaths, assists, score = 0, 0, 0, 0

        for i in range(match_count):
            for j in range(len(MH_json["data"][i]["players"]["all_players"])):
                if MH_json["data"][i]["players"]["all_players"][j]["puuid"] == puuid:
                    player_index = j
                    break
            kills += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["kills"]
            deaths += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["deaths"]
            assists += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["assists"]
            score += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["score"]
        kills = round(kills/match_count, 1)
        deaths = round(deaths/match_count, 1)
        assists = round(assists/match_count, 1)
        score = round(score / match_count, 1)

        embed.add_field(name="Average stats from the last 5 games",
                        value=f"KDA: {kills} | {deaths} | {assists} \n KDR: {round(kills/deaths,2)} \n Score: {score} \n MMR Change: {mmr_change}")
    else:
        embed.add_field(
            name="ERROR", value="Error getting other stats. If the issue persists please contact me @ MaximumMaxx#0001")
        logging.error(
            f"Failure retrieving Match History data: {MH_json}")
    embed.set_image(url=image)
    embed.set_footer(text="Razebot by MaximumMaxx")
    return (embed)
