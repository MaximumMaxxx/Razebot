from code import interact
from unicodedata import name
import discord
from sqlalchemy.orm import Session
from sqlalchemy import select

from lib.globals import validRegions, engine
from lib.ormDefinitions import *


def regionAutoComplete(ctx: discord.AutocompleteContext):
    """Returns the regions that start with what you've typed"""
    # Filter all the regions that start with what you've typed
    filtered = list(
        filter(
            lambda x: x.lower().startswith(
                ctx.value.lower()
            ),
            validRegions
        )
    )
    return filtered


def myAccountAutoComplete(ctx: discord.AutocompleteContext):
    """
    Returns the account names that start with what you've typed.
    This is mostly used for accounts relating to `myaccs` and `myaccsdel`
    the output pulls from the database so it's user specific
    """

    # Grab the user's accounts
    inter = ctx.interaction
    with Session(engine) as session:
        accounts: "list[ValoAccount]" = session.query(
            ValoAccount
        ).filter(
            ValoAccount.owner_id == inter.user.id
        ).filter(
            ValoAccount.acctype == "M"
        ).all()

    # Functional programming is cool
    # This filters out all the accounts that don't start with what you've typed
    # This should be faster than a pure python loop because C moment
    filtered = list(
        filter(
            lambda x: x.lower().startswith(
                ctx.value.lower()
            ),
            map(
                lambda x: f"{x.username}#{x.tag}",
                accounts
            )
        )
    )

    return filtered


def quickAccountAutoComplete(ctx: discord.AutocompleteContext):
    """
    Returns the account names that start with what you've typed.
    This is mostly used for accounts relating to `myaccs` and `myaccsdel`
    the output pulls from the database so it's user specific
    """

    # Grab the user's accounts
    inter = ctx.interaction
    with Session(engine) as session:
        accounts: "list[ValoAccount]" = session.query(
            ValoAccount
        ).filter(
            ValoAccount.owner_id == inter.user.id
        ).filter(
            ValoAccount.acctype == "Q"
        ).all()

    # Functional programming is cool
    # This filters out all the accounts that don't start with what you've typed
    # This should be faster than a pure python loop because C moment
    filtered = list(
        filter(
            lambda x: x.lower().startswith(
                ctx.value.lower()
            ),
            map(
                lambda x: f"{x.username}#{x.tag}",
                accounts
            )
        )
    )

    return filtered


# --------------------------------


RegionAcOption = discord.Option(
    str,
    name="region",
    description=f"The region the account is in. If not specified will default to the server's default region.",
    required=False,
    autocomplete=regionAutoComplete
)

MyAccountAcOption = discord.Option(
    str,
    name="account",
    description=f"The account you want to operate on.",
    required=True,
    autocomplete=myAccountAutoComplete
)

QuickAccountAcOption = discord.Option(
    str,
    name="account",
    description=f"The account you want to operate on.",
    required=True,
    autocomplete=quickAccountAutoComplete
)

# -------------------------------
# -- Not really auto completes --
# -------------------------------

NotesOptions = discord.Option(
    str,
    name="note",
    description="The note you want to add to the account",
    required=False,
    max_length=255
)

AccountOptions = discord.Option(
    str,
    name="accounts",
    description="The accounts you want to add to the list",
    required=True,
    max_length=22
)
