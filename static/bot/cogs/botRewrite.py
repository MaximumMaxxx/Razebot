from os import name
import time
import discord
from discord import message
from discord.commands import option
from discord.ext import commands
from discord.ext.commands.core import has_permissions
import requests
from PIL import ImageColor
import logging
from asyncio import exceptions
from app import valid_ranks
import mysql.connector

# Local Imports
from help_menus import help_menus, avaliable_help_menus, avaliable_settings
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
        self.start_time = time.time()

        

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
        # Might want to move to app.py instead of in a cog
        sql = f"""CREATE TABLE IF NOT EXISTS prefixes (
        `id` INT NOT NULL AUTO_INCREMENT,
        `guild_id` VARCHAR(255) NULL UNIQUE,
        `prefix` VARCHAR(255) NULL,
        PRIMARY KEY (`id`));
        """
        self.cursor.execute(sql)
        self.DB.commit()

    # Setup a server's initial prefix and 
    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        # Settings table
        sql = f'''CREATE TABLE IF NOT EXISTS set{guild.id} (
        `id` INT NOT NULL AUTO_INCREMENT,
        `setting` VARCHAR(255) NULL UNIQUE,
        `value` VARCHAR(255) NULL,
        PRIMARY KEY (`id`));
        '''
        self.cursor.execute(sql)

        # Adding to prefixes table
        sql = f"REPLACE INTO set{guild.id} (setting,value) VALUES (prefix,{self.default_prefix})"
        self.cursor.execute(sql)

        self.DB.commit()
        # Maybe remove before final release
        print(f"Joined a server with the id {guild.id()}")

    # Remove a server's prefix and settings data when the bot leaves the server
    @commands.Cog.listener()
    async def on_guild_leave(self,guild):
        sql = f"DROP TABLE set{guild.id()}"
        self.cursor.execute(sql)
        self.DB.commit()
        print(f"Left the server with the id {guild.id()}")

    # Print out some info when pinged
    @commands.Cog.listener
    async def on_message(self,message):
        if self.user.mentioned_in(message) and message.mention_everyone is False:
            sql = f"SELECT * FROM set{message.guild.id}"
            self.cursor.execute(sql)
            settings = self.cursor.fetchall()

            # Converting the cursor output to a dictionary
            setDict = {}
            for i in range(len(settings)):
                setDict[settings[i][1]] = settings[i][2]

            embed = discord.Embed(title="Razebot info", description=None, color=discord.Color.red())
            embed.add_field(name="Prefix", value=setDict["prefix"])
            embed.add_field(name="Default region", value=setDict["region"])
            embed.add_field(name="Latency", value=self.latency)
            embed.add_field(name="Uptime", value=f"{round(self.start_time-time.time(),0)}s")

            
            await message.channel.send(embed=embed)

        await self.process_commands(message) # This line makes your other commands work.


    # ----------------------------------------------------------------------------------------------------------------------
    # Commands
    # ----------------------------------------------------------------------------------------------------------------------

    @commands.slash_command(name="Credits")
    @commands.command()
    async def credits(self,ctx):
        embed = discord.Embed(title = "Credits", description=None)
        embed.add_field(name="Loading Icon by",value="Krishprakash24gmail via Wikicommons under CC Atribution-sharalike 4.0 International")
        embed.add_field(name="Wrapper by",value="The Pycord development team")
        embed.add_field(name="Design inspiration from",value="Discord developer portal, Mee6, Carl-bot, and many more.", )
        ctx.respond(embed=embed)

    @commands.slash_command(name="Settings")
    @commands.command()
    async def settings(self, ctx, setting, value):
        if setting == None:
            if setting in avaliable_settings:
                self.refresh()
                
                # There should already be a settings table created when the bot first joined so we can just acess it here
                sql = f"REPLACE set{ctx.guild.id} (setting,value) VALUES ({setting},{value})"
            else:
                embed = discord.Embed(title= "Invalid Setting", description=f"The avaliable settings are {avaliable_settings}", color=discord.Color.red())
        
        else:
            embed=discord.Embed(title="Avaliable settings", description=f"The avaliable help menus are {avaliable_settings}", color=discord.Color.green())
        
        ctx.respond(embed=embed)