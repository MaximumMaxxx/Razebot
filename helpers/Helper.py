from discord import List
from quart_discord import current_app
import requests
from sqlalchemy import text
from sqlalchemy.engine.base import Engine
from quart_discord import exceptions
import functools
import logging
from discord.commands import OptionChoice


def avaliableSettings():
    return(["region", "prefix"])


def validRanks():
    return(["iron", "bronze", "silver", "gold", "platinum", "diamond", "immortal", "radiant", "none"])


def compTiers():
    return requests.get("https://valorant-api.com/v1/competitivetiers")


def helpMenus():
    return(
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
    return(
        ["rc", "quickaccs", "myaccs",
         "updaterole", "quick vs myaccs", "settings", "setroles"]
    )


def CreateAccTable(engine: Engine, id, type):
    # S signifies a saved accounts table. M signifys a Myaccounts table
    with engine.connect() as conn:
        conn.execute(
            text(f'''CREATE TABLE IF NOT EXISTS {type}{id} (
            `id` INT NOT NULL AUTO_INCREMENT,
            `note` VARCHAR(255) NULL,
            `ign` VARCHAR(255) NULL,
            `region` VARCHAR(255) NULL,
            PRIMARY KEY (`id`));
            ''')
        )


def AddAcc(engine: Engine, user, type, ign, note, region):
    with engine.connect() as conn:
        # S signifies a saved accounts table. M signifys a Myaccounts table
        result = conn.execute(
            text(f'''select * from {type}{user} where ign like '{ign}';''')
        )
        RSLT = result.all()
        if len(RSLT) != 0:
            return("duplicate")
        result = conn.execute(
            text(f"select * from {type}{user}")
        )
        RSLT = result.all()
        if len(RSLT) == 25 and type == "M":
            return("maxed")
        else:
            # Name is not in the database
            conn.execute(
                text(
                    f'''INSERT INTO {type}{user} (note,ign,region) VALUES ('{note}','{ign}','{region}')''')
            )
            conn.commit()
            return("sucess")


def RmAcc(engine: Engine, user, type, ign):
    # S signifies a saved accounts table. M signifys a Myaccounts table
    with engine.connect() as conn:
        result = conn.execute(
            text(f'''select * from {type}{user} where ign like '{ign}';''')
        )
        RSLT = result.all()
        if len(RSLT) != 0:
            # Name is not in the database
            conn.execute(
                sql=f'''DELETE FROM {type}{user} WHERE ign like '{ign}' '''
            )
            conn.commit()
            return("sucess")
        else:
            return("NIDB")


def requiresAdmin(view):
    """A simple decorator that raises `quart_discord.Unauthoirzed` if the user does not have permission to manage bots"""

    @functools.wraps(view)
    async def wrapper(*args, **kwargs):
        user = await current_app.discord.fetch_user()
        hasPermission = False
        print(kwargs["guild"])
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
    logging.warning(f"Setting {setting} and Value {value}")
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
