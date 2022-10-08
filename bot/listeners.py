from http import server
from os import environ

import discord
from discord import commands
from discord.ext import commands
from sqlalchemy.orm import Session
from lib.ormDefinitions import DisServer, Role
from lib.globals import engine


class Listeners(commands.Cog):
    def __init__(self, bot, ):
        self.bot = bot
        self.default_region = "na"

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with Session(engine) as session:
            session.add(
                DisServer(
                    server_id=str(guild.id),
                    region=self.default_region,
                    max_self_role=None
                )
            )
            session.commit()
        # Maybe remove before final release
        print(f"Joined a server with the id {guild.server_id}")

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        with Session(engine) as session:
            session.query(
                DisServer
            ).filter(
                DisServer.server_id == str(guild.id)
            ).delete()
            session.query(
                Role
            ).where(
                Role.server_id == str(guild.id)
            ).delete()
            session.commit()
        print(f"Left the server with the id {guild.id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # This is a basic system check by pinging the bot.
        if not (self.bot.user.mentioned_in(message) and message.mention_everyone is False):
            await self.bot.process_commands(message)
            return

        with Session(engine) as session:
            server: DisServer = session.query(
                DisServer
            ).filter(
                DisServer.server_id == str(message.guild.id)
            ).one_or_none()

        await message.channel.send(
            embed=discord.Embed
            (
                title="Razebot info",
                description=" ", color=discord.Color.red()
            ).add_field(
                name="Default region",
                value=server.region
            ).add_field(
                name="Latency",
                value=f"{round(self.bot.latency,2)}ms"
            ).set_footer(
                text="Razebot by MaximumMaxx"
            )
        )

        # This line makes your other commands work.
        await self.bot.process_commands(message)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.sync_commands(guild_ids=[898725831164178442], force=True)
        print('--------------------------------------')
        print('Bot is ready.')
        print('Razebot by MaximumMaxx')
        print(self.bot.user.name)
        print(self.bot.user.id)
        print('--------------------------------------')
        await self.bot.change_presence(activity=discord.Game(environ.get("playing_note")))


def setup(bot):
    bot.add_cog(Listeners(bot))
