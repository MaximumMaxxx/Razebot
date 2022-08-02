import discord
from lib.Helper import CreateAccTable, AddAcc, RmAcc, compTiers
from sqlalchemy import engine, text
import math
import requests
import logging
import asyncio
from PIL import ImageColor

from secrets.secrets import Secrets


async def addHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine,  account: str, region: str, note: str) -> discord.Embed:
    CreateAccTable(engine, ctx.author.id, type)
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
            elif returned == "sucess":
                return(discord.Embed(
                    title="Sucess", description="Your account has successfully been added to the database", color=discord.Color.green()))

        else:
            return(discord.Embed(
                title="Error", description="Please specify a VALORANT account", color=discord.Color.red()))

    else:
        return(discord.Embed(
            title="Error", description="Please specify a region", color=discord.Color.red()))


async def removeHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine, account: str):
    CreateAccTable(engine, ctx.author.id, type)
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
    CreateAccTable(engine, ctx.author.id, type)
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT * FROM {type}{ctx.author.id}")
        )
        author_accs = result.all()

        if len(author_accs) == 0:
            embed = discord.Embed(
                title="ERROR", description="You have not accounts to list. Use /myaccs to add an account", color=discord.Color.red())
        else:
            embed = discord.Embed(
                title="Your Accounts" if type != "Q" else "Your Quick Accounts", color=discord.Color.dark_red())
            for account in author_accs:
                embed.add_field(name=account[2], value=account[1])
        return(embed)


async def getAccFromList(ctx: discord.ApplicationContext, bot: discord.bot.Bot, operation: str, engine: engine.Engine, id=-1, ownerShip="Your"):
    if id == -1:
        id = ctx.author.id
    with engine.connect() as conn:
        result = conn.execute(
            text(f"SELECT * FROM {operation}{id}"))
        accounts = result.all()  # 5 accounts per page with a left and right arrow
        page = 1
        max_page_count = math.ceil(len(accounts)/5)
        niceType = "quick" if operation == "Q" else "my"

        embed = discord.Embed(
            title=f"{ownerShip} {niceType}accounts list", color=discord.Color.red(), description=None)

        for i in range(5):
            j = (page-1)*5 + i
            if j < len(accounts):
                embed.add_field(
                    name=f"{j+1}) {accounts[j][2]}", value=accounts[j][1])

        embed.set_footer(
            text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)
        message = await ctx.interaction.original_message()
        # getting the message object for editing and reacting

        await message.add_reaction("◀️")
        await message.add_reaction("1️⃣")
        await message.add_reaction("2️⃣")
        await message.add_reaction("3️⃣")
        await message.add_reaction("4️⃣")
        await message.add_reaction("5️⃣")
        await message.add_reaction("▶️")
        number_reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

        def check(reaction, user):
            return user == ctx.author
            # This makes sure nobody except the command sender can interact with the "menu"

        # Getting which account the user wants
        try:
            while True:
                reaction, user = await bot.wait_for("reaction_add", timeout=60, check=check)
                # waiting for a reaction to be added - times out after 60 seconds

                if str(reaction.emoji) == "▶️" and page != max_page_count:
                    page += 1
                    embed = discord.Embed(
                        title=f"{ownerShip} {list}accounts list", color=discord.Color.red(), description=None)
                    embed.set_footer(
                        text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
                    for i in range(5):
                        j = page*5 + i
                        if not j > len(accounts):
                            embed.add_field(embed.add_field(
                                name=f"{j+1}) {accounts[j][2]}", value=accounts[j][1]))
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) == "◀️" and page > 1:
                    page -= 1
                    embed = discord.Embed(
                        title=f"{ownerShip} {list}accounts list", color=discord.Color.red(), description=None)
                    embed.set_footer(
                        text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
                    for i in range(5):
                        j = page*5 + i
                        if not j > len(accounts):
                            embed.add_field(embed.add_field(
                                name=f"{j+1}) {accounts[j][2]}", value=accounts[j][1]))
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)

                elif str(reaction.emoji) in number_reactions:
                    account_index = page*5 + \
                        number_reactions.index(str(reaction.emoji)) + 1
                    number_reactions.index(str(reaction.emoji))
                    if account_index - 5 > len(accounts):
                        await message.remove_reaction(reaction, user)
                    else:
                        break

                else:
                    await message.remove_reaction(reaction, user)
                    # removes reactions if the user tries to go forward on the last page or
                    # backwards on the first page

            # The -6 is really arbitary and honestly I have no idea why it's needed but it makes it work
            await ctx.edit(content="Working on that ... please wait", embed=None)
            return((get_acc(accounts[account_index-6]), message))

        # If the user doens't respond withing 60 seconds
        except asyncio.TimeoutError:
            embed = discord.Embed(title=f"ERROR", color=discord.Color.red(
            ), description="Your time to select an items has timed out. Please try again.")
            embed.set_footer(text="Razebot by MaximumMaxx")
            return(embed, message)


def get_acc(account: str) -> discord.Embed:
    # Getting the actual account details
    acc, tag = account[2].split("#")
    region = account[3]

    try:
        accountReq = requests.get(
            f"https://api.henrikdev.xyz/valorant/v1/account/{acc}/{tag}", headers={"user-agent": Secrets.uagentHeader})

        if accountReq.status_code == 403:
            logging.info(f"Api is being rate limited")
            embed = discord.Embed(title="ERROR", color=discord.Color.red(
            ), description="The API is being rate limited. Please try again later.")
            embed.set_footer(text="Razebot by MaximumMaxx")
            return(embed)

        if accountReq.status_code != 200:
            logging.info(
                f"Account not found: {acc}#{tag} Error code {accountReq.status_code}")
            return(discord.Embed(title="ERROR", description=f"Account not found: {acc}#{tag}"))

        puuid = accountReq.json()["data"]['puuid']
    except discord.ApplicationCommandInvokeError or KeyError as exception:
        logging.exception(
            f"Failed to retrieve account details with url: https://api.henrikdev.xyz/valorant/v1/account/{acc}/{tag} produces error: {exception}")
        return(discord.Embed(title="ERROR", description="Account not found (something went really wrong)", color=discord.Color.red()))

    mhRequest = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{acc}/{tag}?filter=competitive"
    MH = requests.get(mhRequest, headers={"user-agent": Secrets.uagentHeader})
    mmrRequest = f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{acc}/{tag}"
    MMR = requests.get(mmrRequest, headers={
                       "user-agent": Secrets.uagentHeader})

    logging.info(
        f"Made a request for {acc}#{tag} to \n{mhRequest}\n and \n{mmrRequest}\n got status code {MH.status_code} and {MMR.status_code}")

    kills = deaths = assists = score = mmr_change = "Unknown"

    if MMR.status_code == 200:
        MMR_json = MMR.json()
        mmr_change = 0
        for game in MMR_json["data"]:
            mmr_change += game["mmr_change_to_last_game"]
        if len(MMR_json["data"]) == 0:
            return discord.Embed(title="ERROR", description="No data avaliable for that player. Double check your spelling and try again.", color=discord.Color.red())
        rank = MMR_json["data"][0]["currenttierpatched"]
        tiernum = MMR_json["data"][0]["currenttier"]
        elo = MMR_json["data"][0]["elo"]
        image: str = compTiers().json(
        )["data"][0]["tiers"][tiernum]["largeIcon"]
        color = compTiers().json(
        )["data"][0]["tiers"][tiernum]["color"][:6]
        embed = discord.Embed(color=discord.Color.from_rgb(ImageColor.getcolor("#"+color, "RGB")[0], ImageColor.getcolor(
            "#"+color, "RGB")[1], ImageColor.getcolor("#"+color, "RGB")[2]), description=f"The stats and rank for {acc}#{tag}", title=f"{acc}#{tag}")
        embed.add_field(name="Rank", value=rank)
        embed.add_field(name="MMR", value=elo)
    elif MMR.status_code == 204:
        return(discord.Embed(title="ERROR", description="Not enough recent data or wrong region", color=discord.Color.red()))
    elif MMR.status_code == 429:
        return(discord.Embed(title="ERROR", description="The bot has been rate limited. Please try again in a few minutes", color=discord.Color.red()))
    else:
        logging.error(
            f"{MMR.json()} error while retrieve data region: {region} username: {acc} tag: {tag}")
        return(discord.Embed(title="ERROR", description="Something went horribly wrong and we are all going to die.", color=discord.Color.red()))

    if MH.status_code == 200:
        MH_json = MH.json()
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
            f"Failure retrieving Match History data: {MH.json()}")
    embed.set_image(url=image)
    embed.set_footer(text="Razebot by MaximumMaxx")
    return(embed)
