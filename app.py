# Code largely stolen from here: https://replit.com/@cooljames1610/economybot I still modified it a bunch but the bot to app communication is not me
from discord.ext import commands
from quart import Quart, redirect, url_for, render_template, request
import mysql.connector
import time
import os

from discord.ext import commands
from quart.helpers import make_response
from quart import Quart, redirect, url_for, render_template, request
import requests

from .static.bot.cogs.secrets import Secrets 
# from static.bot.cogs.botRewrite import Razebot 
app = Quart(__name__)

DB = mysql.connector.connect(host=Secrets["dbhost"],user=Secrets["dbuname"],password=Secrets["dbpassword"],database=Secrets["database"])
cursor = DB.cursor()

# Refreshes the SQL connection whever called to prevent sql timeout errors which are annoying
timeout_time = 2700
refresh_time = time.time() + timeout_time

def refresh():
    global refresh_time
    global DB
    global cursor
    if time.time() > refresh_time:
        DB.close()
        DB = mysql.connector.connect(host=Secrets["dbhost"],user=Secrets["dbname"],password=Secrets["dbpassword"],database=Secrets["database"])
        cursor = DB.cursor()
        print("Refreshed")
    refresh_time = time.time()+timeout_time


CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")
# Generates a list of the currently avaliable tiers. Should be up to date with any rank name changes as long as the api keeps up to date
valid_ranks = []
for i in CompTiers.json()["data"][0]["tiers"]:
    # Just making sure that it's not one of the unused divisions
    if not i["divisionName"].lower() in valid_ranks and i["divisionName"] != "Unused2" and i["divisionName"] != "Unused1":
        # valid_ranks should have the lowercase version of the ranks
        valid_ranks.append(i["divisionName"].lower())



app.secret_key = Secrets["websecretkey"]

# Remove this when going into production
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
app.config["DISCORD_CLIENT_ID"] = Secrets["dscclientid"]
app.config["DISCORD_CLIENT_SECRET"] = Secrets["dscclientsecret"]
app.config["DISCORD_REDIRECT_URI"] = Secrets["dscredirecturi"]
app.config["DISCORD_BOT_TOKEN"] = Secrets["bottoken"]

@app.route("/")
async def home():
  logged = False
  balance = 0
  if await discordd.authorized:
    logged = True
    user = await discordd.fetch_user()
    return await render_template("index.html", logged=logged, discord_url="/serverselect", logged_in=[True,user.avatar_url,user.name])
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
    logged = True
    user = await discordd.fetch_user()
    return await render_template("select.html",servers=[[guild.icon_url,guild.name,guild.is_owner,guild.id,True if guild.id in bot.guilds else False] for guild in await user.fetch_guilds() if int(guild.permissions.value) & 1 << 5 or int(guild.permissions.value) & 1 << 3], logged_in=[True,user.avatar_url,user.name])
  return await render_template("select.html",servers=[[guild.icon_url,guild.name,guild.is_owner,guild.id,True if guild.id in bot.guilds else False] for guild in await user.fetch_guilds() if int(guild.permissions.value) & 1 << 5 or int(guild.permissions.value) & 1 << 3], logged_in = [False])

@app.route("/<guild>/dashboard")
@requires_authorization
async def dashboard(guild):
  # Settings is formatted like
  user = await discordd.fetch_user()
  return await render_template("dashboard.html", settings=[
    # The formatting here is important
    # * means can be repeated as many times as you wants
    # For the select is setup like ["select","Name/address it will be posted to", [*["Select option","nothing or default"]]]
    # For text input it's ["string","name","default value"]

    ["select","Region",[["NA",""],["EU","default"]]], 
    ["string","Prefix",">"]]
    ,logged_in=[True,user.avatar_url,user.name]
    )

#@app.errorhandler(Unauthorized)
#async def redirect_unauthorized(e):
  bot.url = request.url
  return redirect(url_for(".login"))

# Temp route for testing
@app.route("/me/")
@requires_authorization
async def me():
    user = await discordd.fetch_user()
    return f"""
    <html>
        <head>
            <title>{user.name}</title>
        </head>
        <body>
            <img src='{user.avatar_url}' />
        </body>
    </html>"""

@app.route("/setting/<string:setting>",methods=["POST"])
@requires_authorization
async def setting(setting):
  if request.method == "POST":
    if setting == "all": headers = {}
    return await make_response(
      200,
      )

@app.route("/support")
async def support():
  return await render_template("imagine.html", route = "Support page")

def get_prefix(client, message):
  global cursor
  refresh()
  sql = f"SELECT 1 FROM prefixes WHERE guild_id = {str(message.guild.id)}"
  cursor.execute(sql)
  return cursor.fetchall()

bot = commands.Bot(command_prefix=(get_prefix), description="Razebot, the ultimate discord bot for VALORANT", help_command=None)

def run():
  bot.loop.create_task(app.run_task(host="localhost",port="6969",debug=True))
  bot.add_cog(Razebot(bot))
  bot.run(Secrets["bottoken"])

def runWebOnly():
  app.run(host="0.0.0.0",port="6969",debug=True)

if __name__ == "__main__":
  # run()
  runWebOnly()