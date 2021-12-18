from quart import Quart, render_template,redirect,url_for,request
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from static.bot.env import secrets
from discord.ext import commands
from bot import Razebot
import mysql.connector #sql connection
import requests
import time

# Establishing DB connection
DB = mysql.connector.connect(host=secrets["dbhost"], user=secrets["dbuname"], password=secrets["dbpassword"], database=secrets["database"])
print(DB)
cursor = DB.cursor()

# Time variables for the reconnect time thing



#Make 1 api call at the start since it doesn't change basically ever anyways
CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")

# Generates a list of the currently avaliable tiers. Should be up to date with any rank name changes as long as the api keeps up to date
valid_ranks = []
for i in CompTiers.json()["data"][0]["tiers"]:
    # Just making sure that it's not one of the unused divisions
    if not i["divisionName"].lower() in valid_ranks and i["divisionName"] != "Unused2" and i["divisionName"] != "Unused1":
        # valid_ranks should have the lowercase version of the ranks
        valid_ranks.append(i["divisionName"].lower())

print(valid_ranks)
valid_settings = ["region"]

# ----------------------------------------------------------------------------------------------------------------------
# Quart Things
# ----------------------------------------------------------------------------------------------------------------------

app = Quart(__name__)

bot=commands.Bot(help_command=None, command_prefix=">")
bot.load_extension("bot")

# This sets the secret to the secret key in binary, no super useful but kinda fun
# Probably doesn't pose a security risk but honestly no guarentees
app.secret_key = ''.join(format(ord(x),'b') for x in secrets["websecretkey"])

@app.route("/")
@app.route("/index")
async def index():
    return await render_template("index.html")

@app.route("/privacy")
async def privacy():
    return await render_template("imagine.html",route="Privacy Policy")

@app.route("/legal")
async def legal():
    return await render_template("imagine.html",route="Legal Anything")

@app.route("/about")
async def about():
    return await render_template("imagine.html",route="About Page")

@app.route("/support")
async def support():
    return await render_template("imagine.html",route="Support System")

@app.route("/contact")
async def contact():
    return await render_template("imagine.html",route="Contact Page")

@app.route("/dashboard")
async def dashboard():
    return await render_template("imagine.html",route="Dashboard")

if __name__ == '__main__':
    app.run(port="6969", host="localhost")
    bot.run(secrets["bottoken"])
    