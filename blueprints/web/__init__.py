from quart import Blueprint, render_template, request, redirect, url_for
from quart.helpers import make_response
from quart_discord import requires_authorization, RateLimited, Unauthorized, AccessDenied
from sqlalchemy import select
from sqlalchemy.orm import Session


from lib.ormDefinitions import *
from lib.Helper import requiresAdmin, parseDashboardChoices
from lib.globals import engine, discordd, bot

blueprint = Blueprint("home", __name__)


@blueprint.route("/")
async def home():
    logged = False
    balance = 0
    if await discordd.authorized:
        logged = True
        user = await discordd.fetch_user()
        return await render_template("index.html", logged=logged, discord_url="/serverselect", logged_in=[True, user.avatar_url, user.name])
    return await render_template("index.html", logged=logged, discord_url="/serverselect", logged_in=[False])


@blueprint.route("/login/")
async def login():
    return await discordd.create_session(scope=["identify", "guilds"])


@blueprint.route("/logout/")
async def logout():
    discordd.revoke()
    return redirect(url_for(".home"))


@blueprint.route("/boringPrivacyPolicy/")
async def BoringPrivacy():
    return await render_template("boringPrivacyPolicy.html")


@blueprint.route("/callback/")
async def callback():
    await discordd.callback()
    return redirect(url_for(".home"))


@blueprint.route("/privacy/")
async def privacyPolicy():
    if await discordd.authorized:
        logged = True
        user = await discordd.fetch_user()
        return await render_template("privacyPolicy.html", logged=logged, discord_url="/serverselect", logged_in=[True, user.avatar_url, user.name])
    return await render_template("privacyPolicy.html", logged=logged, discord_url="/serverselect", logged_in=[False])


@blueprint.route("/serverselect")
@requires_authorization
async def serverselect():
    # Big ol list comprehension that produces a list of lists with the icon, name, and ownership status, and if the bot is the server for each server the user is in but only if they have the ability to add bots
    user = await discordd.fetch_user()

    # There's no good way to comment this, I'm sorry
    # TODO: Make this a function and readable
    return await render_template(
        "select.html",
        servers=[
            [
                guild.icon_url, guild.name, guild.is_owner, guild.id, True if
                any(guild.id == guildb.id for guildb in bot.guilds) else False
            ] for guild in await user.fetch_guilds() if int(guild.permissions.value) & 1 << 5 or int(guild.permissions.value) & 1 << 3],
        logged_in=[
            True, user.avatar_url, user.name
        ]
    )


@blueprint.route("/<guild>/dashboard")
@requires_authorization
@requiresAdmin
async def dashboard(guild):
    # Settings is formatted like
    user = await discordd.fetch_user()
    with Session(engine) as session:
        stmt = select(DisServer).where(DisServer.guild_id == guild)
        result = session.scalars(stmt).one()  # TODO: Make this at all work

    settings = [
        parseDashboardChoices(setting, value)
        for id, setting, value in serverSettings]
    print(settings)
    return await render_template("dashboard.html", settings=settings, logged_in=[True, user.avatar_url, user.name], server=guild
                                 )


@blueprint.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    bot.url = request.url
    return redirect(url_for(".login"))


@blueprint.errorhandler(AccessDenied)
async def access_denied(e):
    return await render_template("acessdenied.html")


@blueprint.errorhandler(RateLimited)
async def rate_limited(e):
    return ("We are currently being rate limited please wait")


@blueprint.route("/setting/<string:setting>", methods=["POST"])
async def setting(setting):
    if request.method == "POST":
        if setting == "all":
            headers = {}
        return await make_response(
            200,
        )


@blueprint.route("/support")
async def support():
    return await render_template("imagine.html", route="Support page")
