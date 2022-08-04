import discord
from discord.ext import commands
from discord.commands import option
from sqlalchemy import create_engine, select
from os import environ

from lib.Helper import compTiers as ct, regionsChoice
from lib.accHelpers import getAccFromList, get_acc
from lib.ormDefinitions import *

engine = create_engine(
    environ.get('dburl'), echo=bool(environ.get('echo')), future=bool(environ.get('future')))


class Rankcheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CompTiers = ct()

    rclist = discord.SlashCommandGroup(
        "rclist", "Check the rank of someone from either your quick accounts list of your my accounts list")

    @rclist.command(name="myaccounts", description="Check an account that you own")
    async def mylist(self, ctx: discord.ApplicationContext):
        embed, msg = await getAccFromList(
            ctx=ctx,
            bot=self.bot,
            operation="M",
            engine=engine)
        await msg.edit(content=None, embed=embed)

    @rclist.command(name="quickaccounts", description="Check an account that you own")
    async def quicklist(self, ctx: discord.ApplicationContext):
        returned = await getAccFromList(
            ctx=ctx,
            bot=self.bot,
            operation="Q",
            engine=engine)
        embed, msg = returned
        await msg.edit(content=None, embed=embed)

    @commands.slash_command(name="rankcheckaccount", description="Get the stats for a specific VALORANT account")
    async def rcacc(
            self, ctx: discord.ApplicationContext, account: str = option(name="Account", description="The VALORANT account you would like to check the rank of"), region: str = option(name="Region", description=f"The region the account is in. If not specified will default to the server's default region.", choices=regionsChoice())):
        # The formatting is a little wack but it does the thing hopefully and it's one line so I'll take the jank
        # Accounts is expected to be a list of tuples but you can just pass in a one item list and 0 and it acomplishes the same thing

        await ctx.respond("Working on that ... please wait")
        if type(region) is not str:
            with engine.connect() as conn:
                result = select(DisServer).where(DisServer.id == ctx.guild.id).where(
                    DisServer.default_region == region)
                # Pull the region from the settings
                region = result[0].default_region

        msg = await ctx.interaction.original_message()
        await msg.edit(content=None, embed=get_acc((None, None, account, region)))

    @commands.slash_command(name="rankcheckuser", description="Get the stats of an account owned by a discord user")
    async def rcuser(self, ctx: discord.ApplicationContext, user: discord.User, region: str = option(name="Region", description=f"The region the account is in. If not specified will default to the server's default region.", choices=regionsChoice())):\
            # The formatting is a little wack but it does the thing hopefully and it's one line so I'll take the jank

        if type(region) is not str:
            with engine.connect() as conn:
                result = select(DisServer).where(DisServer.id == ctx.guild.id).where(
                    DisServer.default_region == region)
                # Pull the region from the settings
                region = result[0].default_region

        returned = await getAccFromList(
            ctx=ctx,
            bot=self.bot,
            operation="M",
            engine=engine,
            id=user.id,
            ownerShip=f"{user.name}'s"
        )
        embed, msg = returned
        await msg.edit(content=None, embed=embed)


def setup(bot):
    bot.add_cog(Rankcheck(bot))
