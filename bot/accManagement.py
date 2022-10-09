from os import environ

import discord
from discord.ext import commands
from sqlalchemy import select
import requests

from lib.Helper import validRanks
from lib.accHelpers import addHelper, removeHelper, listHelper
from lib.ormDefinitions import *
from lib.globals import engine
from lib.autoCompletes import RegionAcOption, MyAccountAcOption


class accManagement(commands.Cog):
    def __init__(self, bot: discord.bot.Bot) -> None:
        self.bot = bot

    myaccs = discord.SlashCommandGroup(
        "myaccounts", "The commands for managing your owned accounts")

    quickaccs = discord.SlashCommandGroup(
        "quickaccounts", "The commands for managing your quick accounts")

    @commands.slash_command(name="updaterole", description="Update your server role based on the ranks of the accounts saved in your myaccs list")
    async def updaterole(self, ctx: discord.ApplicationContext):
        await ctx.respond("Thinking <:loadingbutbetter:914754938175893524>")
        roles: "tuple[Role]" = select(Role).where(
            Role.server_id == ctx.guild.id)

        msg = ctx.interaction.original_message()

        # Check if the server has rank roles configured
        if not len(roles) == len(validRanks()):
            await msg.edit(embed=discord.Embed
                           (
                               title="ERROR",
                               description="Please configure your rank roles using /setroles",
                               color=discord.Color.red()
                           ))
            return

        for rank in roles:
            await ctx.author.remove_roles(
                discord.utils.get(
                    ctx.author.guild.roles,
                    id=rank.role_id
                )
            )

        owned_accs: "tuple[ValoAccount]" = select(
            ValoAccount).where(owner_id=ctx.author.id)

        if not owned_accs:
            await msg.edit(
                embed=discord.Embed
                (
                    rank="unranked",
                    name="ERROR",
                    description="In order to use this command you need atleast one account saved with `/myaccs save`."
                )
            )
            return

        # They actually have accounts in the table
        max_rank = (-1, "")
        for account in owned_accs:
            uname, tag = account[2].split('#')
            MMR = requests.get(
                f"https://api.henrikdev.xyz/valorant/v1/mmr/{account[3]}/{uname}/{tag}", headers={"user-agent": environ.get('uagentHeader')})
            # Error handling
            if MMR.status_code != 200:
                # Skip accounts that are unranked
                if MMR.status_code == 429:
                    # Rate limited
                    msg.edit(
                        embed=discord.Embed
                        (
                            name="ERROR",
                            description="Razebot has been rate limited, please try again in a few minutes"
                        ).set_footer(
                            "Razebot by MaxiumMaxx"
                        )
                    )
                    return
                continue
            MMR_json = MMR.json()
            rank = MMR_json["data"]["currenttierpatched"]

            if MMR_json["data"]["currenttier"] > max_rank[0]:
                max_rank = (MMR_json["data"]
                            ["currenttier"], account[2])
                # isolating the rank name
                rank = rank.split(' ')[0].lower()

        if max_rank[0] == -1:
            rank = "unranked"
            embed = discord.Embed(
                title="Warning",
                description="You have no valid accounts in the database. us /help myaccs for more info on adding accounts. You have been given unranked for now",
                color=discord.Color.gold()
            )
        else:
            embed = discord.Embed(
                title="Sucess",
                description=f"You have been granted the role {rank} feel free to add any other accounts you may have and run this command again.",
                color=discord.Color.green()
            )

        guild = ctx.guild
        role = discord.utils.get(  # This might be way too many levels of indentation but it looks kinda nice. if you hate it make a pr
            guild.roles,
            id=next(
                filter(
                    lambda x: x.name.lower() == rank, roles
                )
            ).role_id
        )
        await ctx.author.add_roles(role)

        embed.set_footer(text="Razebot by MaximumMaxx")
        await msg.edit(embed=embed, content=None)

    @myaccs.command()
    async def list(self, ctx):
        await ctx.respond(embed=await listHelper(
            ctx=ctx,
            type="M",
            engine=engine
        ))

    @myaccs.command()
    async def add(
        self,
        ctx,
        account: str,
        region: RegionAcOption,
        note: str
    ):
        await ctx.respond(embed=await addHelper(
            ctx=ctx,
            type="M",
            engine=engine,
            account=account,
            region=region,
            note=note
        ))

    @myaccs.command()
    async def remove(
        self,
        ctx,
        account: MyAccountAcOption
    ):
        await ctx.respond(embed=await removeHelper(
            ctx=ctx,
            type="M",
            engine=engine,
            account=account
        ))


# --------------------------------

    @quickaccs.command(name="list")
    async def list(self, ctx):
        await ctx.respond(embed=await listHelper(
            ctx=ctx,
            type="Q",
            engine=engine
        ))

    @quickaccs.command(name="add")
    async def qadd(self, ctx, account: str, note: str, region: str):
        await ctx.respond(embed=await addHelper(
            ctx=ctx,
            type="Q",
            engine=engine,
            account=account,
            region=RegionAcOption,
            note=note
        ))

    @quickaccs.command(name="remove")
    async def qremove(self, ctx, account: str):
        await ctx.respond(embed=await removeHelper(
            ctx=ctx,
            type="Q",
            engine=engine,
            account=account
        ))


def setup(bot):
    bot.add_cog(accManagement(bot))
