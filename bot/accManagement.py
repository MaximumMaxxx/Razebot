from os import environ

import discord
from discord.commands import option, OptionChoice
from discord.ext import commands
from sqlalchemy import create_engine, text
import requests

from lib.Helper import CreateAccTable, validRanks
from lib.accHelpers import addHelper, removeHelper, listHelper


engine = create_engine(
    f"mysql+pymysql://{environ.get('dbuname')}:{environ.get('dbpassword')}@{environ.get('dbhost')}/{environ.get('database')}", echo=environ.get('echo'), future=environ.get('future'))


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
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM rl{ctx.author.guild.id}")
            )
            guild_roles = result.all()
            # Check if the server has rank roles configured
            if len(guild_roles) == len(validRanks()):

                # Convert roles into a dictionary
                roleDict = {}
                for i in range(len(guild_roles)):
                    roleDict[guild_roles[i][1]] = guild_roles[i][2]

                for rank in roleDict:
                    await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, id=int(roleDict[rank])))

                CreateAccTable(engine, ctx.author.id, "M")
                result = conn.execute(
                    text(f"select * from M{ctx.author.id}")
                )
                author_accs = result.all()
                if len(author_accs) != 0:  # They actually have accounts in the table
                    max_rank = (-1, "")
                    for account in author_accs:
                        uname, tag = account[2].split('#')
                        MMR = requests.get(
                            f"https://api.henrikdev.xyz/valorant/v1/mmr/{account[3]}/{uname}/{tag}", headers={"user-agent": environ.get('uagentHeader')})
                        # Error handling
                        if MMR.status_code != 200:
                            # Skip accounts that are unranked
                            if MMR.status_code == 429:
                                # Rate limited
                                embed = discord.Embed(
                                    name="ERROR", description="Razebot has been rate limited, please try again in a few minutes")
                                break
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
                            title="Warning", description="You have no valid accounts in the database. us >help myaccs for more info on adding accounts. You have been given unranked for now", color=discord.Color.gold())
                    else:
                        embed = discord.Embed(
                            title="Sucess", description=f"You have been granted the role {rank} feel free to add any other accounts you may have and run this command again.", color=discord.Color.green())

                else:
                    embed = discord.Embed(
                        name="ERROR", description="In order to use this command you need atleast one account saved with `/myaccs save`.")
                    rank = "unranked"
                guild = ctx.guild
                role = discord.utils.get(guild.roles, id=int(roleDict[rank]))
                await ctx.author.add_roles(role)

            else:
                embed = discord.Embed(
                    title="ERROR", description="Please configure your rank roles using /setroles", color=discord.Color.red())

            embed.set_footer(text="Razebot by MaximumMaxx")
            msg = await ctx.interaction.original_message()  # gets the message from response
            # edits message from response
        await msg.edit(embed=embed, content=None)

    @myaccs.command()
    async def list(self, ctx):
        await ctx.respond(embed=await listHelper(
            ctx=ctx,
            type="M",
            engine=engine
        ))

    @myaccs.command()
    async def add(self, ctx, account: str, region: str, note: str):
        await ctx.respond(embed=await addHelper(
            ctx=ctx,
            type="M",
            engine=engine,
            account=account,
            region=region,
            note=note
        ))

    @myaccs.command()
    async def remove(self, ctx, account: str):
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
            region=region,
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
