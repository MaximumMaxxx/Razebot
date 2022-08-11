# Just define some global variables to be used across files
from collections import namedtuple
import os

Jstats = namedtuple("Jstats", ["json", "status"])

validRegions = ["AP", "BR", "EU", "KR", "NA", "LATAM"]


# Emoji
loadingEmoji = "<a:Loading:940065841402228826>"

# These are used for the past10 command
uparrow = "▲"  # "<:Upvote:909203967387516928>"  #
downarrow = "▼"  # "<:Downvote:909204210359357530>"  #
equalarrow = "<:literallydying:941523511598514186>"


# Rankcheck stuff


# I'm pretty sure I'm allowed to redistribute this font, if it's yours and you want me to stop using it just message me on discord. MaxiumMaxx#0001
discord_font = f"{os.getcwd()}/lib/whitneybook.otf"
font_end_padding = "  "
