# Code slightly stolen from here: https://replit.com/@cooljames1610/economybot I still modified it a bunch but the bot to app communication is not me
import time
import os
import asyncio
import logging

import discord
from discord.ext import commands
from quart.helpers import make_response
from quart import Quart, redirect, url_for, render_template, request
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized, AccessDenied
import requests
from sqlalchemy import create_engine
from quart_csrf import CSRFProtect

from helpers.Helper import requiresAdmin
from secrets.secrets import Secrets

logging.basicConfig(level=logging.WARNING,
                    encoding="utf-8", filename="Logs.log")
app = Quart(__name__)
CSRFProtect(app)

engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=True, future=True)

# Refreshes the SQL connection whever called to prevent sql timeout errors which are annoying
timeout_time = 2700
refresh_time = time.time() + timeout_time


CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")
# Generates a list of the currently avaliable tiers. Should be up to date with any rank name changes as long as the api keeps up to date
valid_ranks = []
for i in CompTiers.json()["data"][0]["tiers"]:
    # Just making sure that it's not one of the unused divisions
    if not i["divisionName"].lower() in valid_ranks and i["divisionName"] != "Unused2" and i["divisionName"] != "Unused1":
        # valid_ranks should have the lowercase version of the ranks
        valid_ranks.append(i["divisionName"].lower())


app.secret_key = Secrets.websecretkey

# Remove this when going into production
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
app.config["DISCORD_CLIENT_ID"] = Secrets.dscclientid
app.config["DISCORD_CLIENT_SECRET"] = Secrets.dscclientsecret
app.config["DISCORD_REDIRECT_URI"] = Secrets.dscredirecturi
app.config["DISCORD_BOT_TOKEN"] = Secrets.bottoken

discordd = DiscordOAuth2Session(app)


@app.route("/")
async def home():
    logged = False
    balance = 0
    if await discordd.authorized:
        logged = True
        user = await discordd.fetch_user()
        return await render_template("index.html", logged=logged, discord_url="/serverselect", logged_in=[True, user.avatar_url, user.name])
    return await render_template("index.html", logged=logged, discord_url="/serverselect", logged_in=[False])


@app.route("/login/")
async def login():
    return await discordd.create_session(scope=["identify", "guilds"])


@app.route("/logout/")
async def logout():
    discordd.revoke()
    return redirect(url_for(".home"))


@app.route("/callback/")
async def callback():
    await discordd.callback()
    return redirect(url_for(".home"))


@app.route("/serverselect")
@requires_authorization
async def serverselect():
    user = await discordd.fetch_user()
    # Big ol list comprehension that produces a list of lists with the icon, name, and ownership status, and if the bot is the server for each server the user is in but only if they have the ability to add bots
    if await discordd.authorized:
        user = await discordd.fetch_user()
        return await render_template("select.html", servers=[[guild.icon_url, guild.name, guild.is_owner, guild.id, True if guild.id in bot.guilds else False] for guild in await user.fetch_guilds() if int(guild.permissions.value) & 1 << 5 or int(guild.permissions.value) & 1 << 3], logged_in=[True, user.avatar_url, user.name])
    return await render_template("select.html", servers=[[guild.icon_url, guild.name, guild.is_owner, guild.id, True if guild.id in bot.guilds else False] for guild in await user.fetch_guilds() if int(guild.permissions.value) & 1 << 5 or int(guild.permissions.value) & 1 << 3], logged_in=[False])


@app.route("/<guild>/dashboard")
@requires_authorization
@requiresAdmin
async def dashboard(guild):
    # Settings is formatted like
    user = await discordd.fetch_user()
    return await render_template("dashboard.html", settings=[
        # The formatting here is important
        # * means can be repeated as many times as you wants
        # For the select is setup like ["select","Name/address it will be posted to", [*["Select option","nothing or default"]]]
        # For text input it's ["string","name","default value"]

        ["select", "Region", [["NA", ""], ["EU", "default"]]],
        ["string", "Prefix", ">"]], logged_in=[True, user.avatar_url, user.name]
    )


@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    bot.url = request.url
    return redirect(url_for(".login"))


@app.errorhandler(AccessDenied)
async def access_denied(e):
    return await render_template("acessdenied.html")


@app.route("/setting/<string:setting>", methods=["POST"])
async def setting(setting):
    if request.method == "POST":
        if setting == "all":
            headers = {}
        return await make_response(
            200,
        )


@app.route("/support")
async def support():
    return await render_template("imagine.html", route="Support page")

bot = commands.Bot(command_prefix=">",
                   description="Razebot, the ultimate discord bot for VALORANT", help_command=None)

Globalextensions = ["bot.accManagement",
                    "bot.listeners", "bot.other", "bot.rankCheck"]

# Some bot code that I don't feel like abstracting


@bot.event
async def on_ready():
    print('--------------------------------------')
    print('Bot is ready.')
    print('Razebot by MaximumMaxx')
    print(bot.user.name)
    print(bot.user.id)
    print('--------------------------------------')
    await status_task()


async def status_task():
    await bot.change_presence(activity=discord.Game('VALORANT or something'))


@bot.command()
@commands.is_owner()
async def goodnight(ctx):
    await ctx.channel.send("Sleep well")
    await bot.logout()


@bot.command()
@commands.is_owner()
async def load(ctx, extension):
    try:
        bot.load_extension(extension)
        print('{} loaded sucessfully.'.format(extension))
        embed = discord.Embed(
            title='{} loaded sucessfully.'.format(extension),
            color=ctx.author.color
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as error:
        print('{} raised an exception during loading. [{}]'.format(
            extension, error))
        embed = discord.Embed(
            title='{} raised an exception during loading. [{}]'.format(
                extension, error),
            color=ctx.author.color
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()


@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    try:
        bot.unload_extension(extension)
        print('{} Extension unloaded.'.format(extension))
        embed = discord.Embed(
            title='{} Successfully unloaded.'.format(extension),
            color=ctx.author.color
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()
    except Exception as error:
        print('{} raised an exception during unloading. [{}]'.format(
            extension, error))
        embed = discord.Embed(
            title='{} rasied an exception during unloading. [{}]'.format(
                extension, error),
            color=ctx.author.color
        )
        msg = await ctx.channel.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()


@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    try:
        bot.unload_extension(extension)
        bot.load_extension(extension)
        await ctx.channel.send('{} raided an exception while reloading'.format(extension))
    except Exception as error:
        await ctx.channel.send('{} raised an exception while reloading. [{}]'.format(extension, error))


@bot.command()
@commands.is_owner()
async def loaded(ctx: discord.ApplicationContext):
    embed = discord.Embed(
        title="Loaded Extensions",
        description=" "
    )
    extensions = bot.extensions.items()
    for extension in extensions:
        embed.add_field(name=extension[0], value="✅", inline=False)
    await ctx.send(embed=embed)


def run():
    bot.loop.create_task(app.run_task(
        host=Secrets.webhost, port=Secrets.webport, debug=True))
    for extension in Globalextensions:
        try:
            bot.load_extension(extension)
        except Exception as error:
            print('{} failed to load [{}]'.format(
                extension, error))
    bot.run(Secrets.bottoken)


if __name__ == "__main__":
    run()
