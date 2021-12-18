from quart import Quart, render_template,redirect,url_for,request
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized
from env import secrets
import hashlib

app = Quart(__name__)

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