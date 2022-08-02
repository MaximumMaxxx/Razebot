import logging
from os import environ

import discord
from discord.commands import option
from discord.ext import commands
from sqlalchemy import create_engine, text
import requests

from lib.Helper import avaliableSettings, validRanks,  helpMenus, avaliableSettings


engine = create_engine(
    environ.get('dburl'), echo=environ.get('echo'), future=environ.get('future'))


class Other(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

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
    async def settings(self,
                       ctx: discord.ApplicationContext,
                       setting: str = option(
                           name="settings", description="The seting to change", choices=avaliableSettings()),
                       value: str = option(name="value", description="What do you want to set the setting to?")):
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

                embed = discord.Embed(
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
    async def setroles(self, ctx: discord.ApplicationContext,
                       role: discord.Role = option(name="role", Required=True),
                       rank: str = option(name="valorant rank", Required=True, choices=validRanks())):

        valid_ranks = validRanks()
        if rank.lower() in valid_ranks:
            with engine.connect() as conn:
                # There should already be a settings table created when the bot first joined so we can just acess it here
                conn.execute(
                    text(
                        f'''REPLACE INTO rl{ctx.guild.id} (role,value) VALUES ('{rank.lower()}','{role.id}')''')
                )
                conn.commit()
                embed = discord.Embed(title=f"{role.name} successfully add or updated",
                                      description=f"The changes should take effect immediately", color=discord.Color.green())

                result = conn.execute(
                    text(f"SELECT * FROM rl{ctx.guild.id}")
                )
                guild_roles = result.all()

                if not len(guild_roles) == len(valid_ranks):
                    missingRanks = ""
                    for rank in validRanks():
                        isIn = False
                        for serverRank in guild_roles:
                            if serverRank[1].lower() == rank.lower():
                                isIn = True
                        if not isIn is True:
                            missingRanks += f"{rank} "

                    await ctx.send(embed=discord.Embed(title="You still have some roles to add",
                                                       description=f"Please rerun this command for each of the following VALORANT ranks: {missingRanks}").set_footer(text="Razebot by MaximumMaxx")
                                   )
        else:
            embed = discord.Embed(
                title="Invalid Rank", description=f"You entered {rank} but the valid options are {valid_ranks}.", color=discord.Color.red())

        embed.set_footer(text="Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="help", description="Outputs a short description of how a command works and links to Razebot.com for further reading.")
    async def help(self, ctx: discord.ApplicationContext,
                   setting: str = option(name="setting",
                                         description="What setting do you need help with?",
                                         required=False, choices=avaliableSettings())):
        setting = setting or None
        if setting is None:
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
                title="List of help menus", description=f"Current help menus: {helpMenus()}")
            image = "https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true"

        embed.set_thumbnail(url=image)
        embed.set_footer(text="Razebot by MaximumMaxx")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="test", guild_ids=[898725831164178442])
    async def test(self, ctx):
        # Make a quick api call to see if the api is up
        resp = ""

        request = requests.get("https://valorant-api.com/v1/competitivetiers",
                               headers={"user-agent": environ.get('uagentHeader')})
        if request.status_code != 200:
            resp += "Icon API is down or not responding\n"
        request = requests.get(
            "https://api.henrikdev.xyz/valorant/v1/version/na", headers={"user-agent": environ.get('uagentHeader')})
        if request.status_code != 200:
            resp += f"Rank API is down or not responding status code: {request.status_code}\n"
        if resp != "":
            embed = discord.Embed(
                title="API is down", description=resp, color=discord.Color.red())
        else:
            embed = discord.Embed(
                title="API is up", description="All systems are operational", color=discord.Color.green())
        await ctx.respond(embed=embed)

    # Link to the docs on githut
    @commands.slash_command(name="docs", description="Links to the documentation on GitHub")
    async def docs(self, ctx):
        await ctx.respond(embed=discord.Embed(
            title="Documentation", description="Docs can be found here: [Docs](github.com/MaximumMaxxx/Razebot/blob/main/docs/commands.md)", color=discord.Color.green()))


def setup(bot):
    bot.add_cog(Other(bot))
