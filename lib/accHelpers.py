from collections import namedtuple
import asyncio
import time

import discord
from lib.Helper import AddAcc, RmAcc, compTiers
from sqlalchemy import engine
from sqlalchemy.orm import Session
import requests
import logging
import aiohttp
from PIL import ImageColor

from lib.ormDefinitions import ValoAccount
from bot.views.accountSelector import accountSelectorFactory


async def addHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine,  account: str, region: str, note: str) -> discord.Embed:
    try:
        account, tag = account.split("#") if account != None else None
    except ValueError:
        return(discord.Embed(title="ERROR", description="Your account is missing a tag", color=discord.Color.red()))
    if region != None:
        if account != None:
            if note == None:
                note = "No note"
            returned = AddAcc(
                engine, ctx.author.id, type, f"{account}#{tag}", note, region)
            if returned == "duplicate":
                return(discord.Embed(
                    title="ERROR", description="That account has already been saved by you", color=discord.Color.red()))
            elif returned == "maxed":
                return(discord.Embed(title="ERROR", description="Listen man, you have 25 accounts saved. Sorry but this is an intervention. Please reconsider your life choices leading up to here.",  color=discord.Color.red()))
            elif returned == "success":
                return(discord.Embed(
                    title="Success", description="Your account has successfully been added to the database", color=discord.Color.green()))

        else:
            return(discord.Embed(
                title="Error", description="Please specify a VALORANT account", color=discord.Color.red()))

    else:
        return(discord.Embed(
            title="Error", description="Please specify a region", color=discord.Color.red()))


async def removeHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine, account: str):
    try:
        account, tag = account.split("#") if account != None else None
    except ValueError:
        return(discord.Embed(title="ERROR", description="Your account is missing a tag", color=discord.Color.red()))
    returned = RmAcc(engine, ctx.author.id,
                     type, f"{account}#{tag}")
    if returned == "sucess":
        return(discord.Embed(
            title="Sucess", description="You account has successfully been removed from the database", color=discord.Color.green()))
    elif returned == "NIDB":
        return(discord.Embed(
            title="ERROR", description="That account isn't in the database. You likely misspelled something", color=discord.Color.red()))


async def listHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine):
    with Session(engine) as session:
        author_accs: "list[ValoAccount]" = session.query(ValoAccount).filter(
            ValoAccount.owner_id == ctx.author.id).filter(ValoAccount.acctype == type).all()

    if not author_accs:
        embed = discord.Embed(
            title="ERROR", description=f"You have not accounts to list. Use /{'myaccs' if type != 'Q' else 'quickaccs'} to add an account", color=discord.Color.red())
    else:
        embed = discord.Embed(
            title="Your Accounts" if type != "Q" else "Your Quick Accounts", color=discord.Color.dark_red())
        for account in author_accs:
            embed.add_field(
                name=f"{account.username}#{account.tag}", value=account.note, inline=False)
    return(embed)


async def getAccFromList(ctx: discord.ApplicationContext, bot: discord.bot.Bot, operation: str, engine: engine.Engine, id=-1, ownerShip="Your"):  # Rewrite this
    # https://docs.pycord.dev/en/master/ext/pages/index.html <- good
    """Displays a list of accounts to the user and allows them to select one to get the stats of"""
    if id == -1:
        id = ctx.author.id

    await ctx.respond(f"1 second please...")

    with Session(engine) as session:
        accounts: "list[ValoAccount]" = session.query(
            ValoAccount
        ).filter(
            ValoAccount.owner_id == id
        ).filter(
            ValoAccount.acctype == operation
        ).all()

    if not accounts:  # This is a little cursed
        await ctx.edit(
            content=None,
            embed=discord.Embed(
                title="ERROR",
                description=f"You have not accounts to list. Use /{'myaccs' if operation != 'Q' else 'quickaccs'} to add an account",
                color=discord.Color.red()
            )
        )
        return

    # Construct the region dictionary
    region_dict = {}
    for account in accounts:
        region_dict[f"{account.username}#{account.tag}"] = account.region

    # Construct the select element
    options = []
    for account in accounts:
        options.append(
            discord.SelectOption(
                label=f"{account.username}#{account.tag}",
                value=f"{account.username}#{account.tag}",
                description=account.note
            )
        )

    # Send the select menu
    await ctx.edit(content=None, view=accountSelectorFactory(options=options, region=region_dict))


async def get_jstat(session, url, Jstats):
    """
    A little helper function for the http requests
    """
    async with session.get(url) as resp:
        return Jstats(await resp.json(), resp.status)


async def get_acc(name: str, tag: str, region: str) -> discord.Embed:
    # Getting the actual account details

    jsons = []
    Jstats = namedtuple("Jstats", ["json", "status"])
    start_time = time.time()
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
                get_jstat(session, link, Jstats)))

        jsons = await asyncio.gather(*tasks)

    accountReq, MH, MMR = jsons

    puuid = accountReq.json["data"]["puuid"]

    if accountReq.status == 403:
        logging.debug(f"Api is being rate limited")
        return(
            discord.Embed(
                title="ERROR",
                color=discord.Color.red(),
                description="The API is being rate limited. Please try again later."
            ).set_footer(
                text="Razebot by MaximumMaxx"
            )
        )

    if accountReq.status != 200:
        logging.debug(
            f"Account not found: {name}#{tag} Error code {accountReq.status}"
        )
        return(
            discord.Embed(
                title="ERROR",
                description=f"Account not found: {name}#{tag}"
            ).set_footer(
                text="Razebot by MaximumMaxx"
            )
        )

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
        return(discord.Embed(title="ERROR", description="Not enough recent data or wrong region", color=discord.Color.red()))

    elif MMR.status == 429:
        return(discord.Embed(title="ERROR", description="The bot has been rate limited. Please try again in a few minutes", color=discord.Color.red()))

    else:
        logging.error(
            f"{MMR.json} error while retrieve data region: {region} username: {name} tag: {tag}"
        )
        return(
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
    return(embed)
