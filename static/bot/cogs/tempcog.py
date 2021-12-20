from discord.ext import commands
import discord

class testing(commands.Cog):
    """Epic Gamer testing cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="Ping")
    async def ping(self,ctx):

        await ctx.send(f"The current ping is {round(self.bot.latency * 1000)}ms")


def setup(bot):
    bot.add_cog(testing(bot))