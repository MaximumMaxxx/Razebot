import time
import discord
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

class Bot(commands.Bot):

    def __init__(self, command_prefix=..., help_command=... , **options):
        super().__init__(command_prefix=command_prefix, help_command=help_command, **options)
        DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
        self.cursor = DB.cursor()

        self.timeout_time = 2700
        self.refrsh_time = time.time() + self.timeout_time

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is up")
        
        # Create the prefix table if it doesn't already exist
        sql = f"""CREATE TABLE IF NOT EXISTS prefixes (
        `id` INT NOT NULL AUTO_INCREMENT,
        `guild_id` VARCHAR(255) NULL,
        `prefix` VARCHAR(255) NULL,
        PRIMARY KEY (`id`));
        """

    @commands.Cog.listener()
    async def on_guild_join(guild):
        
