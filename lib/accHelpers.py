import asyncio

import discord
from sqlalchemy import engine
from sqlalchemy.orm import Session
import logging
import aiohttp
from PIL import ImageColor

from lib.Helper import AddAcc, RmAcc, compTiers
from lib.ormDefinitions import ValoAccount
from bot.views.accountSelector import accountSelectorFactory
from lib.get_accs import get_acc


async def addHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine,  account: str, region: str, note: str) -> discord.Embed:
    try:
        account, tag = account.split("#") if account != None else None
    except ValueError:
        return (discord.Embed(title="ERROR", description="Your account is missing a tag", color=discord.Color.red()))
    if region != None:
        if account != None:
            if note == None:
                note = "No note"
            returned = AddAcc(
                engine, ctx.author.id, type, f"{account}#{tag}", note, region)
            if returned == "duplicate":
                return (discord.Embed(
                    title="ERROR", description="That account has already been saved by you", color=discord.Color.red()))
            elif returned == "maxed":
                return (discord.Embed(title="ERROR", description="Listen man, you have 25 accounts saved. Sorry but this is an intervention. Please reconsider your life choices leading up to here.",  color=discord.Color.red()))
            elif returned == "success":
                return (discord.Embed(
                    title="Success", description="Your account has successfully been added to the database", color=discord.Color.green()))

        else:
            return (discord.Embed(
                title="Error", description="Please specify a VALORANT account", color=discord.Color.red()))

    else:
        return (discord.Embed(
            title="Error", description="Please specify a region", color=discord.Color.red()))


async def removeHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine, account: str):
    try:
        account, tag = account.split("#") if account != None else None
    except ValueError:
        return (discord.Embed(title="ERROR", description="Your account is missing a tag", color=discord.Color.red()))
    returned = RmAcc(engine, ctx.author.id,
                     type, f"{account}#{tag}")
    if returned == "sucess":
        return (discord.Embed(
            title="Sucess", description="You account has successfully been removed from the database", color=discord.Color.green()))
    elif returned == "NIDB":
        return (discord.Embed(
            title="ERROR", description="That account isn't in the database. You likely misspelled something", color=discord.Color.red()))


async def listHelper(ctx: discord.ApplicationContext, type: str, engine: engine.Engine):
    with Session(engine) as session:
        author_accs: "list[ValoAccount]" = session.query(
            ValoAccount
        ).filter(
            ValoAccount.owner_id == ctx.author.id
        ).filter(
            ValoAccount.acctype == type
        ).all()

    if not author_accs:
        embed = discord.Embed(
            title="ERROR", description=f"You have not accounts to list. Use /{'myaccs' if type != 'Q' else 'quickaccs'} to add an account", color=discord.Color.red())
    else:
        embed = discord.Embed(
            title="Your Accounts" if type != "Q" else "Your Quick Accounts", color=discord.Color.dark_red())
        for account in author_accs:
            embed.add_field(
                name=f"{account.username}#{account.tag}", value=account.note, inline=False)
    return (embed)


async def getAccFromList(ctx: discord.ApplicationContext, operation: str, engine: engine.Engine, callback: "callable" = get_acc, id=-1):
    # https://docs.pycord.dev/en/master/ext/pages/index.html <- good
    """Displays a list of accounts to the user and allows them to select one to get the stats of"""
    if id == -1:
        id = ctx.author.id

    await ctx.respond(f"1 second please... {globals.loadingEmoji}")

    with Session(engine) as session:
        accounts: "list[ValoAccount]" = session.query(
            ValoAccount
        ).filter(
            ValoAccount.owner_id == id
        ).filter(
            ValoAccount.acctype == operation
        ).all()

    if not accounts:  # This is a little cursed
        await ctx.edit(
            content=None,
            embed=discord.Embed(
                title="ERROR",
                description=f"You have not accounts to list. Use /{'myaccs' if operation != 'Q' else 'quickaccs'} to add an account",
                color=discord.Color.red()
            )
        )
        return

    # Construct the region dictionary
    region_dict = {}
    for account in accounts:
        region_dict[f"{account.username}#{account.tag}"] = account.region

    # Construct the select element
    options = []
    for account in accounts:
        options.append(
            discord.SelectOption(
                label=f"{account.username}#{account.tag}",
                value=f"{account.username}#{account.tag}",
                description=account.note
            )
        )

    # Send the select menu
    await ctx.edit(content=None, view=accountSelectorFactory(options=options, region=region_dict, callback=callback))
