from os import environ
import os

from discord.ext import commands
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
import discord
import aiohttp
from lib import rchelpers

from lib.Helper import compTiers as ct, porpotionalAlign
from lib.accHelpers import getAccFromList, get_acc
from lib.globals import Jstats
from lib.ormDefinitions import *
from lib.rchelpers import regionAutoComplete
import lib.globals as globals

engine = create_engine(
    environ.get('dburl'), echo=bool(environ.get('echo')), future=bool(environ.get('future')))


class Rankcheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CompTiers = ct()

    rclist = discord.SlashCommandGroup(
        "rclist", "Check the rank of someone from either your quick accounts list of your my accounts list")

    @rclist.command(name="myaccounts", description="Check an account that you own")
    async def mylist(
        self,
        ctx: discord.ApplicationContext
    ):
        await getAccFromList(
            ctx=ctx,
            bot=self.bot,
            operation="M",
            engine=engine
        )

    @rclist.command(name="quickaccounts", description="Check an account that you own")
    async def quicklist(
        self,
        ctx: discord.ApplicationContext
    ):
        await getAccFromList(
            ctx=ctx,
            bot=self.bot,
            operation="Q",
            engine=engine
        )

    @commands.slash_command(name="rankcheckaccount", description="Get the stats for a specific VALORANT account")
    async def rcacc(
            self, ctx: discord.ApplicationContext,
            account:  discord.Option(
                str,
                name="account",
                description="The VALORANT account you would like to check the rank of"
            ),
            region: discord.Option(
                str,
                name="region",
                description=f"The region the account is in. If not specified will default to the server's default region.",
                autocomplete=regionAutoComplete
            )
    ):
        # The formatting is a little wack but it does the thing hopefully and it's one line so I'll take the jank
        # Accounts is expected to be a list of tuples but you can just pass in a one item list and 0 and it acomplishes the same thing

        await ctx.respond("Working on that ... please wait")
        if type(region) is not str:
            with Session(engine) as session:
                stmt = select(DisServer).where(DisServer.id == ctx.guild.id)
                # Pull the region from the settings
                region = session.schalars(stmt).one().default_region

        msg = await ctx.interaction.original_message()
        name, tag = account.split("#")
        await msg.edit(content=None, embed=await get_acc(name, tag, region))

    @commands.slash_command(name="rankcheckuser", description="Get the stats of an account owned by a discord user")
    async def rcuser(
        self,
        ctx: discord.ApplicationContext,
        user: discord.User,
        region: discord.Option(
            str,
            name="region",
            description=f"The region the account is in. If not specified will default to the server's default region.",
            autocomplete=regionAutoComplete,
            required=False
        )
    ):
        # The formatting is a little wack but it does the thing hopefully and it's one line so I'll take the jank

        if type(region) is not str:
            with Session(engine) as session:

                # Pull the region from the settings
                region = session.query(
                    DisServer
                ).filter(
                    DisServer.server_id == str(ctx.guild.id)
                ).one_or_none().region

        await getAccFromList(
            ctx=ctx,
            bot=self.bot,
            operation="M",
            engine=engine,
            id=user.id,
            ownerShip=f"{user.name}'s"
        )

    @commands.slash_command(name="past10", description="Get the stats of the last 5 matches for a specific VALORANT account")
    async def past10(
            self,
            ctx: discord.ApplicationContext,
            account: discord.Option(
                str,
                name="account",
                description="The account#tag that you want to see",
                required=True
            ),
            region: discord.Option(
                str,
                name="region",
                description="The region that you want to check the account in; Defaults to the server's default region.",
                autocomplete=regionAutoComplete,
                requied=False
            )
    ):
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

        embed.set_thumbnail(url=ct()[tier]["largeIcon"])

        await ctx.edit(content=None, embed=embed)


def setup(bot):
    bot.add_cog(Rankcheck(bot))
