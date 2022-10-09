from os import environ

from discord.ext import commands
from sqlalchemy import select
from sqlalchemy.orm import Session
import discord

from lib.globals import engine
from lib.Helper import compTiers as ct
from lib.accHelpers import getAccFromList, get_acc
from lib.ormDefinitions import *
from lib.rchelpers import past10
from lib.autoCompletes import RegionAcOption, AccountOptions


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
            operation="Q",
            engine=engine
        )

    @commands.slash_command(name="rankcheckaccount", description="Get the stats for a specific VALORANT account")
    async def rcacc(
            self, ctx: discord.ApplicationContext,
            account:  AccountOptions,
            region: RegionAcOption
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
        region: RegionAcOption
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
            operation="M",
            engine=engine,
            id=user.id,
        )

    @commands.slash_command(name="quickpast5", description="Get the stats of the last 5 matches for an account from your my accounts list")
    async def qpast5(
            self,
            ctx: discord.ApplicationContext,
    ):
        await getAccFromList(
            ctx=ctx,
            operation="Q",
            engine=engine,
            callback=past10,
        )

    @commands.slash_command(name="mypast5", description="Get the stats of the last 5 matches for an account from your quick accounts list")
    async def mpast5(
            self,
            ctx
    ):
        await getAccFromList(
            ctx=ctx,
            operation="M",
            engine=engine,
            callback=past10,
        )


def setup(bot):
    bot.add_cog(Rankcheck(bot))
