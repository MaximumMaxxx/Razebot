# Code largely stolen from here: https://replit.com/@cooljames1610/economybot I still modified it a bunch but the bot to app communication is not me
from discord.ext import commands
from quart import Quart, redirect, url_for, render_template, request
import mysql.connector
import time
import os
import requests

from static.bot.cogs.secrets import secrets
from static.bot.cogs.botRewrite import Razebot

app = Quart(__name__)

DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
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
        DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
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



app.secret_key = secrets["websecuritykey"]

# Remove this when going into production
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"
app.config["DISCORD_CLIENT_ID"] = secrets["dscclientid"]
app.config["DISCORD_CLIENT_SECRET"] = secrets["dscclientsecret"]
app.config["DISCORD_REDIRECT_URI"] = secrets["dscredirecturi"]
app.config["DISCORD_BOT_TOKEN"] = secrets["bottoken"]

@app.route("/")
async def home():
  logged = False
  balance = 0
  if await discordd.authorized:
    logged = True
  return await render_template("index.html", logged=logged, discord_url="/dashboard")


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
  try:
    return redirect(bot.url)
  except:
    return redirect(url_for(".me"))

@app.route("/dashboard")
async def dashboard():
  return await render_template("dashboard.html")

#@app.errorhandler(Unauthorized)
#async def redirect_unauthorized(e):
  bot.url = request.url
  return redirect(url_for(".login"))

def get_prefix(client, message):
  global cursor
  refresh()
  sql = f"SELECT 1 FROM prefixes WHERE guild_id = {str(message.guild.id)}"
  cursor.execute(sql)
  return cursor.fetchall()



bot = commands.Bot(command_prefix=(get_prefix), description="Simple economy bot", help_command=None)

def run():
  bot.loop.create_task(app.run_task('0.0.0.0'))
  bot.add_cog(Razebot(bot))
  bot.run(secrets["bottoken"])

def runWebOnly():
  app.run(host="localhost",port="6969",debug=True)

if __name__ == "__main__":
  #run()
  runWebOnly()