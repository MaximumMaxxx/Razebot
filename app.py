from quart import Quart, render_template,redirect,url_for,request, session
from quart_discord import DiscordOAuth2Session
from static.bot.cogs.secrets import secrets

app = Quart(__name__)
app.config["SECRET_KEY"] = secrets["websecretkey"]
app.config["DISCORD_CLIENT_ID"] = secrets["dscclientid"]
app.config["DISCORD_CLIENT_SECRET"] = secrets["dscclientsecret"]
app.config["DISCORD_REDIRECT_URI"] = secrets["dscredirecturi"]

discord = DiscordOAuth2Session(app)

@app.route("/")
async def home():
    return await render_template("index.html",discord_url="/login")

@app.route("/dashboard")
async def dashboard():
    return await render_template("imagine.html", route="Dashboard")

@app.route("/login")
async def login():
    return await discord.create_session()

@app.route("/callback")
async def callback():
    try:
        await discord.callback()
    except:
        return redirect(url_for("login"))
    
    user = await discord.fetch_user()
    return await render_template("imagine.html",route=f"{user.name} # {user.discriminator}")


if __name__ == '__main__':
    app.run(debug=True, port=6969)