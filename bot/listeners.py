from os import environ

import discord
from discord import commands
from discord.ext import commands
from sqlalchemy import create_engine,  select
from sqlalchemy.orm import Session
from lib.ormDefinitions import DisServer, Role


engine = create_engine(
    environ.get('dburl'), echo=bool(environ.get('echo')), future=bool(environ.get('future')))


class Listeners(commands.Cog):
    def __init__(self, bot, ):
        self.bot = bot
        self.default_region = "na"

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        with Session(engine) as session:
            session.add(
                DisServer(id=guild.id, region=self.default_region, max_self_role=None))
            session.commit()
        # Maybe remove before final release
        print(f"Joined a server with the id {guild.id}")

    @commands.Cog.listener()
    async def on_guild_leave(self, guild):
        with Session(engine) as session:
            session.query(DisServer).filter(DisServer.id == guild.id).delete()
            session.query(Role).filter(Role.server_id == guild.id).delete()
            session.commit()
        print(f"Left the server with the id {guild.id}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # This is a basic system check by pinging the bot.
        if not (self.bot.user.mentioned_in(message) and message.mention_everyone is False):
            await self.bot.process_commands(message)

        server: DisServer = select(DisServer).where(
            DisServer.id == message.guild.id)[0]

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
            )
        )

        # This line makes your other commands work.
        await self.bot.process_commands(message)


def setup(bot):
    bot.add_cog(Listeners(bot))
