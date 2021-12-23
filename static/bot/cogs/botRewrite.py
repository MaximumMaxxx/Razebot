import time
import discord
from discord import message
from discord.commands import option
from discord.ext import commands
import requests
from PIL import ImageColor
import logging
from asyncio import exceptions
import mysql.connector
from app import refresh

# Local Imports
from help_menus import help_menus,avaliable_help_menus
from secrets import secrets

# Welcome to self land the land of self. 
class Razebot(commands.Bot):

    def __init__(self, command_prefix=..., help_command=... , **options):
        super().__init__(command_prefix=command_prefix, help_command=help_command, **options)
        self.DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
        self.cursor = self.DB.cursor()

        self.default_prefix = ">"
        self.timeout_time = 2700
        self.refresh_time = time.time() + self.timeout_time

    # ----------------------------------------------------------------------------------------------------------------------
    # Helper Functions
    # ----------------------------------------------------------------------------------------------------------------------

    def refresh(self):
        if time.time() > self.refresh_time:
            self.DB.close()
            self.DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
            self.cursor = self.DB.cursor()
            print("Refreshed")
        self.refresh_time = time.time()+self.timeout_time

    def CreateAccTable(self,id,type):
        # S signifies a saved accounts table. M signifys a Myaccounts table
        sql = f'''CREATE TABLE IF NOT EXISTS {type}{id} (
        `id` INT NOT NULL AUTO_INCREMENT,
        `note` VARCHAR(255) NULL,
        `ign` VARCHAR(255) NULL,
        PRIMARY KEY (`id`));
        '''
        self.cursor.execute(sql)
        # Doesn't seem to be required but I'll leave it here anyways
        self.DB.commit()

    def AddAcc(self,user, type, ign, note):
        # S signifies a saved accounts table. M signifys a Myaccounts table
        sql = f'''select * from {type}{user} where ign like '{ign}';'''
        self.cursor.execute(sql)
        RSLT = self.cursor.fetchall()
        if len(RSLT) != 0:
            return("Name Already In Database")
        else:
            # Name is not in the database
            sql = f'''INSERT INTO {type}{user} (note,ign) VALUES (%s,%s)'''
            values = (note,ign)
            self.cursor.execute(sql,values)
            self.DB.commit()
            return("sucess")


    def RmAcc(self,user, type, ign):
        # S signifies a saved accounts table. M signifys a Myaccounts table
        sql = f'''select * from {type}{user} where ign like '{ign}';'''
        self.cursor.execute(sql)
        RSLT = self.cursor.fetchall()
        if len(RSLT) != 0:
            # Name is not in the database
            sql = f'''DELETE FROM {type}{user} WHERE ign like '{ign}' '''
            self.cursor.execute(sql)
            self.DB.commit()
            return("sucess")
        else:
            return("Name not In Database")

    # ----------------------------------------------------------------------------------------------------------------------
    # Listeners
    # ----------------------------------------------------------------------------------------------------------------------

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog is up")
        
        # Create the prefix table if it doesn't already exist
        sql = f"""CREATE TABLE IF NOT EXISTS prefixes (
        `id` INT NOT NULL AUTO_INCREMENT,
        `guild_id` VARCHAR(255) NULL UNIQUE,
        `prefix` VARCHAR(255) NULL,
        PRIMARY KEY (`id`));
        """
        self.cursor.execute(sql)
        self.DB.commit()

    # Setup a server's initial prefix
    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        sql = f"REPLACE INTO prefixes (guid_id,prefix) VALUES ({str(guild.id())},{self.default_prefix})"
        self.cursor.execute(sql)
        self.DB.commit()
        # Maybe remove before final release
        print(f"Joined a server with the id {guild.id()}")

    # Remove a server's prefix and settings data when the bot leaves the server
    @commands.Cog.listener()
    async def on_guild_leave(self,guild):
        sql = f"DELETE FROM prefixes WHERE guild_id MATCHES {guild.id()}"
        self.cursor.execute(sql)
        sql = f"DROP TABLE set{guild.id()}"
        self.cursor.execute(sql)
        self.DB.commit()
        print(f"Left the server with the id {guild.id()}")

    # ----------------------------------------------------------------------------------------------------------------------
    # Commands
    # ----------------------------------------------------------------------------------------------------------------------

    @commands.slash_command(name="Credits")
    async def credits(self,ctx):
        embed = discord.Embed(title = "Credits", description=None)
        embed.add_field(name="Loading Icon",value="Icon by Krishprakash24gmail via Wikicommons under CC Atribution-sharalike 4.0 International")
        embed.add_field(name="Wrapper",value="Pycord by the pycord development team")
        ctx.respond(embed=embed)

    