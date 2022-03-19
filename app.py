# Code slightly stolen from here: https://replit.com/@cooljames1610/economybot I still modified it a bunch but the bot to app communication is not me
import time
import os
import logging

import discord
from discord.ext import commands
from quart.helpers import make_response
from quart import Quart, redirect, url_for, render_template, request
from quart_discord import DiscordOAuth2Session, RateLimited, requires_authorization, Unauthorized, AccessDenied
import requests
from sqlalchemy import create_engine, text
from quart_csrf import CSRFProtect

from helpers.Helper import requiresAdmin, validRanks, parseDashboardChoices
from secrets.secrets import Secrets
from blueprints.api import blueprint

logging.basicConfig(level=logging.WARNING, filename="Logs.log")
app = Quart(__name__)
# Load in the pages
app.register_blueprint(blueprint, url_prefix="/api")

CSRFProtect(app)

engine = create_engine(
    f"mysql+pymysql://{Secrets.dbuname}:{Secrets.dbpassword}@{Secrets.dbhost}/{Secrets.database}", echo=Secrets.echo, future=Secrets.future)

# Refreshes the SQL connection whever called to prevent sql timeout errors which are annoying
timeout_time = 2700
refresh_time = time.time() + timeout_time


CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")
# Generates a list of the currently avaliable tiers. Should be up to date with any rank name changes as long as the api keeps up to date
valid_ranks = validRanks()


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


@app.route("/privacy/")
async def privacy():
    return await render_template("privacyPolicy.html")


@app.route("/callback/")
async def callback():
    await discordd.callback()
    return redirect(url_for(".home"))


@app.route("/serverselect")
@requires_authorization
async def serverselect():
    # Big ol list comprehension that produces a list of lists with the icon, name, and ownership status, and if the bot is the server for each server the user is in but only if they have the ability to add bots
    user = await discordd.fetch_user()

    return await render_template("select.html", servers=[[guild.icon_url, guild.name, guild.is_owner, guild.id, True if any(guild.id == guildb.id for guildb in bot.guilds) else False] for guild in await user.fetch_guilds() if int(guild.permissions.value) & 1 << 5 or int(guild.permissions.value) & 1 << 3], logged_in=[True, user.avatar_url, user.name])


@app.route("/<guild>/dashboard")
@requires_authorization
@requiresAdmin
async def dashboard(guild):
    # Settings is formatted like
    user = await discordd.fetch_user()
    with engine.connect() as conn:
        rslt = conn.execute(text(f"SELECT * FROM set{guild}"))
    serverSettings = rslt.all()
    settings = [parseDashboardChoices(setting, value)
                for id, setting, value in serverSettings]
    print(settings)
    return await render_template("dashboard.html", settings=settings, logged_in=[True, user.avatar_url, user.name], server=guild
                                 )


@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    bot.url = request.url
    return redirect(url_for(".login"))


@app.errorhandler(AccessDenied)
async def access_denied(e):
    return await render_template("acessdenied.html")


@app.errorhandler(RateLimited)
async def rate_limited(e):
    return ("We are currently being rate limited please wait")


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


def run():
    bot.loop.create_task(app.run_task(
        host=Secrets.webhost, port=Secrets.webport, debug=True))
    for extension in Globalextensions:
        try:
            bot.load_extension(extension)
        except Exception as error:
            print('{} failed to load [{}]'.format(
                extension, error))
            logging.error(
                f"{extension} failed to load [{error}]")
    bot.run(Secrets.bottoken)


if __name__ == "__main__":
    run()
