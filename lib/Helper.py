import json
from multiprocessing.spawn import import_main_path

from quart_discord import current_app
from sqlalchemy.orm import Session
from sqlalchemy.engine.base import Engine
from quart_discord import exceptions
import functools
import logging
from discord.commands import OptionChoice
from PIL import ImageFont

from lib.ormDefinitions import *
from lib.globals import Jstats


def avaliableSettings():
    return (["region", "prefix"])


def validRanks():
    return (["iron", "bronze", "silver", "gold", "platinum", "diamond", "immortal", "radiant", "none"])


def compTiers():
    with open("lib/valorant_ranks.json") as f:
        return json.load(f)


def porpotionalAlign(text: str) -> str:
    """
    Takes in a string and returns a new string with spacing for alignment in in it

    The string must be split by newlines, each word must be split by spaces, and each line must have the same number of words/sets of characters w/no spaces.

    for example:
    ```
    Hello World\\n
    Hi Mom
    ```
    would return:
    ```
    Hello World\\n
    Hi    Mom
    ```

    Designed to work with non-monospaced fonts
    """
    text = text[1:]
    font = ImageFont.truetype(globals.discord_font, 16)

    # Define some whitespace characters
    characters = [
        " ",
        " ",
        " ",
        " ",
        " ",
        "　",
        " ",
    ]

    # Size and sort the characters
    Whitespacesizes = [
        (c, font.getlength(c))
        for c in characters
    ]

    Whitespacesizes.sort(
        key=lambda x: x[1]
    )

    # Turn the string into a list of words
    lines = text.split("\n")
    words: "list(list(str))" = [i.split(" ") for i in lines]

    # Main loop
    for index in range(len(words[0])):
        # Get the longest word in the line

        temp = []
        for line in words:
            temp.append(font.getlength(line[index]))

        longestWord = max(temp)

        for li in range(len(words)):
            length = 0
            while (font.getlength(words[li][index])) < longestWord:
                length = font.getlength(words[li][index])
                different = longestWord - length

                if different < Whitespacesizes[0][1]:
                    print(f"{words[li][index]} is complete")
                    break

                biggest_whitespace = ""
                for whitespace in Whitespacesizes:
                    if whitespace[1] > different:
                        break
                    biggest_whitespace = whitespace[0]

                words[li][index] += biggest_whitespace

    # Turn the list back into a string
    newString = "\n".join([" ".join(i) for i in words])
    return newString


def helpMenus():
    return (
        {
            "rc": ["https://static.wikia.nocookie.net/valorant/images/2/24/TX_CompetitiveTier_Large_24.png", "Rank Check", f"Allows you to check the rank of any player. Usage: the base command is '>rc'. If no account is specified it will pull from your quick accounts list. If you ping someone, it will pull from their accounts list. If you put a username like 'rc name#tag' it will check that player's rank. Finally you can add a region like 'na' if the person is in a different region than the server owner has set."],
            "quickaccs": ["https://upload.wikimedia.org/wikipedia/commons/a/a8/Lightning_bolt_simple.png", "Quick Accounts", f"A command to interact with a database of saved quick accounts. Quick accounts are used to check the ranks of certain people or accounts without having to memorize their tags. Syntax: All uses start with >quickaccs followed by something. To view a list of your saved accounts use '>quickaccs'. To add an account use '>quickaccs add Name#tag note' If the name or note has spaces you don't have to do anything special. To remove an account use '>quickaccs del Name#tag' Again nothing special has to happen if the name has spaces"],
            "myaccs": ["https://pngimg.com/uploads/smurf/smurf_PNG34.png", "My accounts", f"A command to interact with a database of saved quick accounts. My accounts is used to manage a list of accounts you own. Syntax: All uses start with >myaccs followed by something. To view a list of your saved accounts use '>myaccs'. To add an account use '>myaccs add Name#tag note' If the name or note has spaces you don't have to do anything special. To remove an account use '>myaccs del Name#tag' Again nothing special has to happen if the name has spaces"],
            "updaterole": ["https://static.wikia.nocookie.net/valorant/images/7/7f/TX_CompetitiveTier_Large_3.png/revision/latest/scale-to-width-down/250?cb=20200623203005", ">updaterole", f"A command to automatically update your role based on what accounts you have linked to >myaccs."],
            "quick vs myaccs": ["https://static.wikia.nocookie.net/valorant/images/7/7f/TX_CompetitiveTier_Large_3.png/revision/latest/scale-to-width-down/250?cb=20200623203005", "Quick accounts Vs My Accounts", f"The distinction between quickaccs and myaccs is a small but important one. myaccs is a list of all accounts you personally own. myaccs is thus pulled from in a situation where you are the subject, the prime examples of these are rank updating, and when you're pinged for a rank check. constrasting that is quickaccs. quickaccs is a list of accounts you want to check without having to memorize tags, this might be a friend's account, or it might be a youtuber's account. You can put whatever accounts you want in quickaccs and it won't affect anything"],
            "settings": ["https://static.thenounproject.com/png/1524589-200.png", "settings", f"Allows you to change the settings for the bot. formatting: '>settings setting:value' use '>settings list' for a list of avaliable settings"],
            "setroles": ["https://static.wikia.nocookie.net/valorant/images/7/7f/TX_CompetitiveTier_Large_3.png/revision/latest/scale-to-width-down/250?cb=20200623203005", "Set roles", f"Allows you to set the roles for each rank. All ranks must be set before updateroles or rankcheck can be used. Format: '>setroles role:@role' note: you may have to add a space, type the @, then remove the space. The command will also tell you what role links you are missing."]
        }
    )


def avaliableHelpMenus():
    return (
        ["rc", "quickaccs", "myaccs",
         "updaterole", "quick vs myaccs", "settings", "setroles"]
    )


def AddAcc(engine: Engine, user_id: int, type, ign, note, region):
    with Session(engine) as session:
        # S signifies a saved accounts table. M signifys a Myaccounts table
        result = session.query(
            ValoAccount
        ).filter(
            ValoAccount.username == ign.split("#")[0]
        ).filter(
            ValoAccount.owner_id == str(user_id)
        ).one_or_none()

        if result is not None:
            return ("duplicate")

        result = session.query(
            ValoAccount
        ).filter(
            ValoAccount.owner_id == str(user_id)
        ).where(
            ValoAccount.acctype == type
        ).all()

        if len(result) >= 25 and type == "M":
            return ("maxed")
        else:
            # Name is not in the database
            name, tag = ign.split("#")
            valoAcc = ValoAccount(
                username=name,
                tag=tag,
                note=note,
                acctype=type,
                region=region,
                owner_id=str(user_id)
            )

            session.add(valoAcc)
            session.commit()
            return ("success")


def RmAcc(engine: Engine, user, type, ign):
    # S signifies a saved accounts table. M signifys a Myaccounts table
    acc, tag = ign.split("#")
    with Session(engine) as session:
        result = session.query(
            ValoAccount
        ).filter(
            ValoAccount.username == acc
        ).filter(
            ValoAccount.owner_id == str(user)
        ).filter(
            ValoAccount.acctype == type
        ).filter(
            ValoAccount.tag == tag
        ).one_or_none()

    if result is None:
        return ("NIDB")

    session.delete(result)
    session.commit()

    return ("sucess")


def requiresAdmin(view):
    """A simple decorator that raises `quart_discord.Unauthoirzed` if the user does not have permission to manage bots"""

    @ functools.wraps(view)
    async def wrapper(*args, **kwargs):
        user = await current_app.discord.fetch_user()
        hasPermission = False
        for guild in await user.fetch_guilds():
            if int(guild.permissions.value) & 1 << 5 and guild.id == int(kwargs["guild"]):
                hasPermission = True
                break
        if not hasPermission:
            raise exceptions.AccessDenied
        logging.info(f"User {user} has passed the permission check")
        return await view(*args, **kwargs)

    return wrapper


def parseDashboardChoices(setting: str, value: str):
    # The formatting here is important
    # * means can be repeated as many times as you wants
    # For the select is setup like ["select","Name/address it will be posted to", [*["Select option","nothing or default"]]]
    # For text input it's ["string","name","default value"]

    lookupTable = {
        "region": ["select", "_", [["NA", False], ["EU", False], ["AP", False], ["KR", False]]],
        "max_self_role": ["select", "_", [[Value, False if Value != value else True] for Value in validRanks()]]
    }
    formatted = lookupTable[setting]
    formatted[1] = setting
    if formatted[0] == "select":
        for setting in formatted[2]:
            if setting[0].lower() == value.lower():
                setting[1] = True
    elif formatted[0] == "string":
        formatted[2] = value
    return formatted


def regions():
    return ["kr", "na", "eu", "ap"]


def regionsChoice():
    return [OptionChoice(name=i, value=i) for i in regions()]


def rankChoices():
    return [OptionChoice(name=i, value=i) for i in validRanks()]


def settingChoices():
    return [OptionChoice(name=i, value=i) for i in avaliableSettings()]


def helpmenuChoice():
    return [OptionChoice(name=i, value=i) for i in helpMenus()]


async def get_jstat(session, url):
    """
    A little helper function for the http requests
    """
    async with session.get(url) as resp:
        return Jstats(await resp.json(), resp.status)


def parseTrueFalse(value):
    trueValues = ["true", "yes", "y", "1"]
    falseValues = ["false", "no", "n", "0"]
    if value.lower() in trueValues:
        return True
    elif value.lower() in falseValues:
        return False
    else:
        print("Unable to parse true false value")
        return None
