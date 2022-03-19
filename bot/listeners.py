import time

import discord
from discord import commands
from discord.ext import commands
from sqlalchemy import create_engine, text
from app import setting

from secrets.secrets import Secrets

engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=Secrets.echo, future=Secrets.future)


class Listeners(commands.Cog):
    def __init__(self, bot, ):
        self.bot = bot
        self.default_region = "na"

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with engine.connect() as conn:
            conn.execute(
                # Settings table
                text(f'''CREATE TABLE IF NOT EXISTS set{guild.id} (
                `id` INT NOT NULL AUTO_INCREMENT,
                `setting` VARCHAR(255) NULL UNIQUE,
                `value` VARCHAR(255) NULL,
                PRIMARY KEY (`id`));
                ''')
            )
            conn.execute(
                # server role table
                text(f'''CREATE TABLE IF NOT EXISTS rl{guild.id} (
                `id` INT NOT NULL AUTO_INCREMENT,
                `role` VARCHAR(255) NULL UNIQUE,
                `value` VARCHAR(255) NULL,
                PRIMARY KEY (`id`));
                ''')
            )
            conn.execute(
                # Creating some default settings values
                text(
                    f"REPLACE INTO set{guild.id} (setting,value) VALUES ('region','{self.default_region}')")
            )
            conn.execute(
                text(
                    f"REPLACE INTO set{guild.id} (setting,value) VALUES ('max_self_role','None')")
            )
            conn.commit()
        # Maybe remove before final release
        print(f"Joined a server with the id {guild.id}")

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        with engine.connect() as conn:
            conn.execute(
                text(f"DROP TABLE set{guild.id()}")
            )
        print(f"Left the server with the id {guild.id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.bot.user.mentioned_in(message) and message.mention_everyone is False:
            with engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT * FROM set{message.guild.id}")
                )
                settings = result.all()
            # Converting the cursor output to a dictionary
            setDict = {}
            for i in range(len(settings)):
                setDict[settings[i][1]] = settings[i][2]

            embed = discord.Embed(title="Razebot info",
                                  description=" ", color=discord.Color.red())
            embed.add_field(name="Default region", value=setDict["region"])
            embed.add_field(
                name="Latency", value=f"{round(self.bot.latency,2)}ms")

            await message.channel.send(embed=embed)

        # This line makes your other commands work.
        await self.bot.process_commands(message)


def setup(bot):
    bot.add_cog(Listeners(bot))
