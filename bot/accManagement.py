import discord
from discord.commands import option, OptionChoice
from discord.ext import commands
from sqlalchemy import create_engine, text
import requests

from secrets.secrets import Secrets
from helpers.Helper import CreateAccTable, regions, AddAcc, RmAcc, regionsChoice


engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=True, future=True)


class accManagement(commands.Cog):
    def __init__(self, bot: discord.bot.Bot) -> None:
        self.bot = bot
    myaccs = discord.SlashCommandGroup(
        "MyAccounts", "The commands for managing your owned accounts")

    quickaccs = discord.SlashCommandGroup(
        "QuickAccounts", "The commands for managing your quick accounts")

    @commands.slash_command(name="updaterole", description="Update your server role based on the ranks of the accounts saved in your myaccs list")
    async def updaterole(self, ctx):
        await ctx.respond("Thinking <:loadingbutbetter:914754938175893524>")
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM rl{ctx.author.guild.id}")
            )
            guild_roles = result.all()
            # Check if the server has rank roles configured
            if len(guild_roles) == len(self.valid_ranks()):

                # Convert roles into a dictionary
                roleDict = {}
                for i in range(len(guild_roles)):
                    roleDict[guild_roles[i][1]] = guild_roles[i][2]

                for rank in roleDict:
                    await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, id=int(roleDict[rank])))

                CreateAccTable(engine, ctx.message.author.id, "M")
                result = conn.execute(
                    text(f"select * from M{ctx.author.id}")
                )
                author_accs = result.all()
                if len(author_accs) != 0:  # They actually have accounts in the table
                    max_rank = (-1, "")
                    for account in author_accs:
                        uname, tag = account[2].split('#')
                        MMR = requests.get(
                            f"https://api.henrikdev.xyz/valorant/v1/mmr/{account[3]}/{uname}/{tag}")
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
        CreateAccTable(engine, ctx.author.id, "M")
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM M{ctx.author.id}")
            )
            author_accs = result.all()

            if len(author_accs) == 0:
                embed = discord.Embed(
                    title="ERROR", description="You have not accounts to list. Use /myaccs to add an account", color=discord.Color.red())
            else:
                embed = discord.Embed(
                    title="Your Accounts", color=discord.Color.dark_red())
                for account in author_accs:
                    embed.add_field(name=account[2], value=account[1])
        await ctx.respond(embed)

    @myaccs.command()
    async def add(self, ctx, account: str, region: str, note: str):
        CreateAccTable(engine, ctx.author.id, "M")
        account, tag = account.split("#") if account != None else None
        if region != None:
            if account != None:
                if note == None:
                    note = "No note"
                returned = AddAcc(
                    engine, ctx.author.id, "M", f"{account}#{tag}", note)
                if returned == "duplicate":
                    embed = discord.Embed(
                        title="ERROR", description="That account has already been saved by you", color=discord.Color.red())
                elif returned == "maxed":
                    embed = discord.Embed(title="ERROR", description="Listen man, you have 25 accounts saved. there is no reason you should have that many accounts. You should seriously reconsider whatever life decisions brought you here. Sorry but this is an intervention. If you got here by adding a bunch of other accounts then you're using this wrong. Alrigt rant over, have a good night or afternoon or day or whatever.",  color=discord.Color.red())
                elif returned == "sucess":
                    embed = discord.Embed(
                        title="Sucess", description="Your account has successfully been added to the database", color=discord.Color.green())

            else:
                embed = discord.Embed(
                    title="Error", description="Please specify a VALORANT account", color=discord.Color.red())

        else:
            embed = discord.Embed(
                title="Error", description="Please specify a region", color=discord.Color.red())
        await ctx.respond(embed)

    @myaccs.command()
    async def remove(self, ctx, account: str):
        CreateAccTable(engine, ctx.author.id, "M")
        account, tag = account.split("#") if account != None else None
        returned = RmAcc(engine, ctx.author.id,
                         "M", f"{account}#{tag}")
        if returned == "sucess":
            embed = discord.Embed(
                title="Sucess", description="You account has successfully been removed from the database", color=discord.Color.green())
        elif returned == "NIDB":
            embed = discord.Embed(
                title="ERROR", description="That account isn't in the database. You likely misspelled something", color=discord.Color.red())
        await ctx.respond(embed)


# --------------------------------

    @quickaccs.command(name="list")
    async def list(self, ctx):
        CreateAccTable(engine, ctx.author.id, "Q")
        with engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM Q{ctx.author.id}")
            )
            author_accs = result.all()

        if len(author_accs) == 0:
            embed = discord.Embed(
                title="ERROR", description="You have not accounts to list. Use /quickaccs to add an account", color=discord.Color.red())
        else:
            embed = discord.Embed(
                title="Your Quick Accounts", color=discord.Color.dark_red())
            for account in author_accs:
                embed.add_field(name=account[2], value=account[1])
        await ctx.respond(embed)

    @quickaccs.command(name="add")
    async def qadd(self, ctx, account: str, note: str, region: str):
        account, tag = account.split("#") if account != None else None
        if region != None:
            if account != None:
                if note == None:
                    note = "No note"
                returned = AddAcc(
                    ctx.author.id, "Q", f"{account}#{tag}", note)
                if returned == "duplicate":
                    embed = discord.Embed(
                        title="ERROR", description="That account has already been saved by you", color=discord.Color.red())
                elif returned == "sucess":
                    embed = discord.Embed(
                        title="Sucess", description="Your account has successfully been added to the database", color=discord.Color.green())

            else:
                embed = discord.Embed(
                    title="Error", description="Please specify a VALORANT account", color=discord.Color.red())

        else:
            embed = discord.Embed(
                title="Error", description="Please specify a region", color=discord.Color.red())
        await ctx.respond(embed)

    @quickaccs.command(name="remove")
    async def qremove(self, ctx, account: str):
        account, tag = account.split("#") if account != None else None
        returned = RmAcc(engine, ctx.author.id,
                         "Q", f"{account}#{tag}")
        if returned == "sucess":
            embed = discord.Embed(
                title="Sucess", description="You account has successfully been removed from the database", color=discord.Color.green())
        elif returned == "NIDB":
            embed = discord.Embed(
                title="ERROR", description="That account isn't in the database. You likely misspelled something", color=discord.Color.red())
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(accManagement(bot))
