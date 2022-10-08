# Just define some global variables to be used across files
from collections import namedtuple
import imp
import os

from quart import Quart
from quart_discord import DiscordOAuth2Session
from quart_csrf import CSRFProtect
from sqlalchemy import create_engine
from discord.ext import commands

Jstats = namedtuple("Jstats", ["json", "status"])

validRegions = ["AP", "BR", "EU", "KR", "NA", "LATAM"]


# Emoji
loadingEmoji = "<a:Loading:940065841402228826>"

# These are used for the past10 command
uparrow = "▲"  # "<:Upvote:909203967387516928>"  #
downarrow = "▼"  # "<:Downvote:909204210359357530>"  #
equalarrow = "<:literallydying:941523511598514186>"


# I'm pretty sure I'm allowed to redistribute this font, if it's yours and you want me to stop using it just message me on discord. MaxiumMaxx#0001
discord_font = f"{os.getcwd()}/lib/whitneybook.otf"
font_end_padding = "  "

# Setup variables for auth, these should be shared across all files that import this file
app = Quart(__name__)
CSRFProtect(app)  # Wacky stuff to make the site more secure
discordd = DiscordOAuth2Session(app)

bot = commands.Bot(
    command_prefix=">",
    description="Razebot, the ultimate discord bot for VALORANT",
    help_command=None
)

engine = create_engine(
    os.environ.get('dburl'), echo=bool(os.environ.get('echo')), future=bool(os.environ.get('future')))
