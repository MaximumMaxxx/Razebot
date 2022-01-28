import logging
import discord
from discord.commands import option
from discord.ext import commands
from sqlalchemy import create_engine, text

from secrets.secrets import Secrets
from helpers.Helper import avaliableSettings, validRanks, avaliableHelpMenus, helpMenus

engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=True, future=True)


class Other(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.avaliableHelpMenus = avaliableHelpMenus()
        self.helpMenus = helpMenus()

    @commands.slash_command(name="credits")
    async def credits(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title="Credits", description=" ",)
        embed.add_field(name="Loading Icon by",
                        value="Krishprakash24gmail via Wikicommons under CC Atribution-sharalike 4.0 International")
        embed.add_field(name="Wrapper by", value="The Pycord development team")
        embed.add_field(name="Design inspiration from",
                        value="Discord developer portal, Mee6, Carl-bot, and many more.", )
        embed.set_footer(text="Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="settings")
    async def settings(self, ctx: discord.ApplicationContext, setting: str, value: str):
        if setting != None:
            if setting.lower() in avaliableSettings():

                # There should already be a settings table created when the bot first joined so we can just acess it here
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            f"REPLACE set{ctx.guild.id} (setting,value) VALUES ('{setting.lower()}','{value}')")
                    )
                    conn.commit()
                    logging.info(
                        f"Updated the setting {setting.lower()} in guild {ctx.guild.id} to {value}")

                embed = embed = discord.Embed(
                    title=f"{setting} successfully updated", description=f"The changes should take effect immediately", color=discord.Color.green())
            else:
                embed = discord.Embed(
                    title="Invalid Setting", description=f"The avaliable settings are {avaliableSettings()}", color=discord.Color.red())

        else:
            embed = discord.Embed(
                title="Avaliable settings", description=f"The avaliable help menus are {avaliableSettings()}", color=discord.Color.green())

        embed.set_footer(text="Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="setroles", description="Set the role for each VALORANT comp rank")
    async def setroles(self, ctx: discord.ApplicationContext, role: discord.role.Role = option(name="role", Required=True), rank: str = option(name="valorant rank", Required=True)):
        valid_ranks = validRanks()
        if rank.lower() in valid_ranks:
            with engine.connect() as conn:
                # There should already be a settings table created when the bot first joined so we can just acess it here
                conn.execute(
                    text(
                        f'''REPLACE INTO rl{ctx.guild.id} (role,value) VALUES ('{role.id}','{rank}')''')
                )
                conn.commit()
                embed = discord.Embed(title=f"{role.name} successfully updated",

                                      description=f"The changes should take effect immediately", color=discord.Color.green())

                result = conn.execute(
                    text(f"SELECT * FROM rl{ctx.guild.id}")
                )
                guild_roles = result.all()

                if not len(guild_roles) == len(valid_ranks):
                    if len(guild_roles) != 0:
                        ctx.send(embed=discord.Embed(title="You still have some roles to add",
                                                     description=f"Please rerun this command for each of the following VALORANT ranks: {[i for i in valid_ranks if i not in guild_roles[1]]}").set_footer(text="Razebot by MaximumMaxx")
                                 )
                    else:
                        ctx.send(embed=discord.Embed(title="You still have some roles to add",
                                                     description=f"Please rerun this command for each of the following VALORANT ranks: {[i for i in valid_ranks]}").set_footer(text="Razebot by MaximumMaxx")
                                 )

                return
        else:
            embed = discord.Embed(
                title="Invalid Rank", description=f"You entered {rank} but the valid options are {valid_ranks}.", color=discord.Color.red())

        embed.set_footer(text="Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="help", description="Outputs a short description of how a command works and links to Razebot.com for further reading.")
    async def help(self, ctx: discord.ApplicationContext, setting: str = option(avaliableHelpMenus(), None, required=False)):
        setting = setting or None

        if setting != None:
            if setting in self.avaliableHelpMenus:
                embed = discord.Embed(
                    title=self.helpMenus[setting][1], description=self.HelpMenus[setting][2], color=discord.Color.dark_green())
                image = self.helpMenus[setting][0]
            else:
                image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
                embed = embed = discord.Embed(
                    title="Setting not found", description=f"/help for a general list of help menus", color=discord.Color.red())
        else:
            # Return the default help menu
            embed = discord.Embed(
                title="List of help menus", description=f"Current help menus: /help rc, /help myaccs, /help quickaccs, /help updaterole, /help quick vs myaccs, /help settings, /help setroles")
            image = "https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true"

        embed.set_thumbnail(url=image)
        embed.set_footer(text="Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Other(bot))
