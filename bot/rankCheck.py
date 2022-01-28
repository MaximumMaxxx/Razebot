import math
import asyncio
import logging
from random import choice

import discord
from discord.ext import commands
from discord.commands import option
import requests
from PIL import ImageColor
from sqlalchemy import create_engine, text

from helpers.Helper import compTiers as ct
from secrets.secrets import Secrets

engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=True, future=True)


class Rankcheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CompTiers = ct()

    # Helper function for all the logic with rank checking
    def get_acc(self, account: str) -> discord.Embed:
        # Getting the actual account details
        region, acc, tag = account[2], account[1], account[3]
        try:
            accountReq = requests.get(
                f"https://api.henrikdev.xyz/valorant/v1/account/{acc}/{tag}")
            if accountReq.status_code != 200:
                return(discord.Embed(title="ERROR", description="Account not found"))
            else:
                puuid = accountReq.json()["data"]['puuid']
        except discord.ApplicationCommandInvokeError or KeyError as exception:
            logging.exception(
                f"Failed to retrieve account details with url: https://api.henrikdev.xyz/valorant/v1/account/{acc}/{tag} produces error: {exception}")
            return(discord.Embed(title="ERROR", description="Account not found", color=discord.Color.red()))
        MH = requests.get(
            f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{acc}/{tag}?filter=competitive")
        MMR = requests.get(
            f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{acc}/{tag}")

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
            image: str = self.CompTiers.json(
            )["data"][0]["tiers"][tiernum]["largeIcon"]
            print(image)
            print(type(image))

            color = self.CompTiers.json(
            )["data"][0]["tiers"][tiernum]["color"][:6]
            embed = discord.Embed(color=discord.Color.from_rgb(ImageColor.getcolor("#"+color, "RGB")[0], ImageColor.getcolor(
                "#"+color, "RGB")[1], ImageColor.getcolor("#"+color, "RGB")[2]), description=f"The stats and rank for {acc}", title=acc)
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

    @commands.slash_command(name="rankchecklist", description="Check the Rank of an account from either your Quick accounts or My accounts list")
    async def rclist(self, ctx: discord.ApplicationContext, list: str = option(name="List", description="The list that you want to pull the accounts from. (my | quick)", Required=True)):
        list = list.lower()
        operation = ""
        if list == "quick":
            operation = "Q"
        elif list == "my":
            operation = "M"
        else:
            embed = discord.Embed(
                title="ERROR", description="Please provide a valid list type")
            embed.set_footer(text="Razebot by MaximumMaxx")
            ctx.respond(embed=embed)
            return

        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {operation}{ctx.author.id}"))
            accounts = result.all()  # 5 accounts per page with a left and right arrow
        page = 1
        max_page_count = math.ceil(len(accounts)/5)

        embed = discord.Embed(
            title=f"Your {list}accounts list", color=discord.Color.red(), description=None)
        embed.set_footer(
            text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)
        message = await ctx.interaction.original_message()
        # getting the message object for editing and reacting

        await message.add_reaction("◀️")
        # Just a bunch of unicode recycling signs rn
        await message.add_reaction("\u2673")
        await message.add_reaction("\u2674")
        await message.add_reaction("\u2675")
        await message.add_reaction("\u2676")
        await message.add_reaction("\u2677")
        await message.add_reaction("▶️")
        number_reactions = ["\u2673", "\u2674", "\u2675", "\u2676", "\u2677"]

        def check(reaction, user):
            return user == ctx.author
            # This makes sure nobody except the command sender can interact with the "menu"

        # Getting which account the user wants
        while True:
            try:
                reaction, user = await self.wait_for("reaction_add", timeout=60, check=check)
                # waiting for a reaction to be added - times out after x seconds, 60 in this
                # example

                if str(reaction.emoji) == "▶️" and page != max_page_count:
                    page += 1
                    embed = discord.Embed(
                        title=f"Your {list}accounts list", color=discord.Color.red(), description=None)
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
                        title=f"Your {list}accounts list", color=discord.Color.red(), description=None)
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
                    if account_index > len(accounts):
                        await message.remove_reaction(reaction, user)
                    else:
                        break

                else:
                    await message.remove_reaction(reaction, user)
                    # removes reactions if the user tries to go forward on the last page or
                    # backwards on the first page
            except asyncio.TimeoutError:
                embed = discord.Embed(title=f"ERROR", color=discord.Color.red(
                ), description="Your time to select an items has timed out. Please try again.")
                embed.set_footer(text="Razebot by MaximumMaxx")
                await message.edit(embed=embed)
                return
                # ending the loop if user doesn't react after x seconds
        await ctx.respond("Working on that ... please wait")
        msg = await ctx.interaction.original_message()
        await msg.edit(content=None, embed=self.get_acc(accounts[account_index]))

    @commands.slash_command(name="rankcheckaccount", description="Get the stats for a specific VALORANT account")
    async def rcacc(self, ctx: discord.ApplicationContext, account: str = option(name="Account", description="The VALORANT account you would like to check the rank of"), region: str = option(name="Region", description=f"The region the account is in. If not specified will default to the server's default region.", choices=[discord.OptionChoice(name="North America", value="na"), discord.OptionChoice(name="Europe", value="eu"), discord.OptionChoice(name="Korea", value="kr"), discord.OptionChoice(name="Asia Pacific", value="ap")])):
        # The formatting is a little wack but it does the thing hopefully and it's one line so I'll take the jank
        # Accounts is expected to be a list of tuples but you can just pass in a one item list and 0 and it acomplishes the same thing

        await ctx.respond("Working on that ... please wait")
        if type(region) is not str:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        f"SELECT * FROM set{ctx.guild.id} WHERE setting = 'region'")
                )
                region = result.all()[0][2]

        msg = await ctx.interaction.original_message()
        await msg.edit(content=None, embed=self.get_acc((None, account.split("#")[0], region,  account.split("#")[1])))


def setup(bot):
    bot.add_cog(Rankcheck(bot))
