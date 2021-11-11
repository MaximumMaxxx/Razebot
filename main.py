
from asyncio.tasks import current_task
import time # Error logging
import discord
from discord import message
from discord import embeds # Discord Integration
from discord.ext import commands # Commands for said discord integration
from discord.utils import get
import requests # Api Calls
from PIL import ImageColor # Converting Hex to RGB
import logging # Error Logging

# The setting dictionary. Won't store across restarts but this is more meant for if you change the source code to have
# an easy place to keep all the essential settings. Also this approach doesn't require SQL which was partly my goal.
settings = {"assumed region":"na","prefix":">"}

# Command:[embed,ImageLink]
help_menus = {"rc":["https://static.wikia.nocookie.net/valorant/images/2/24/TX_CompetitiveTier_Large_24.png","RC aka Rank Check", f"Takes in 0,1, or 2 parameters and searches the valorant api for them. If it finds a valid player it returns an with the player's rank and MMR. With one argument it takes in the Valorant name formatted like Name#Tag and pulls from the default region in settings. If no arguments are provided it prompts the user with questions instead. If you want to specify region you can either use 2 arguments like >rc Vname#tag region or no arguments"]}
# Obviously only 
UseSQL = True
if UseSQL == True:
    import mysql.connector
    DB = mysql.connector.connect()
    print(DB)
    cursor = DB.cursor()

#Make 1 api call at the start since it doesn't change basically ever anyways

CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")

bot = commands.Bot(command_prefix=settings["prefix"], help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Activity(name=">help", type=2))


def Create_TB(user,type):
    # S signifies a saved accounts table. M signifys a Myaccounts table


    sql = f'''CREATE TABLE IF NOT EXISTS {type}{user} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `note` VARCHAR(255) NULL,
    `ign` VARCHAR(255) NULL,
    PRIMARY KEY (`id`));
    '''
    cursor.execute(sql)

def AddTo_TB(user, type, ign, note):
    # S signifies a saved accounts table. M signifys a Myaccounts table

    sql = f'''select * from {type}{user} where ign like '{ign}';'''
    cursor.execute(sql)
    RSLT = cursor.fetchall()
    if len(RSLT) != 0:
        return("Name Already In Database")
    else:
        # Name is not in the database
        sql = f'''INSERT INTO {type}{user} (note,ign) VALUES (%s,%s)'''
        values = (note,ign)
        cursor.execute(sql,values)
        DB.commit()
        return("sucess")

def RmFrom_TB(user, type, ign):
    # S signifies a saved accounts table. M signifys a Myaccounts table

    sql = f'''select * from {type}{user} where ign like '{ign}';'''
    cursor.execute(sql)
    RSLT = cursor.fetchall()
    if len(RSLT) != 0:
        # Name is not in the database
        sql = f'''DELETE FROM {type}{user} WHERE ign like '{ign}' '''
        cursor.execute(sql)
        DB.commit()
        return("sucess")

    else:
        return("Name not In Database")



        



def UpdateRole():
    # Gives users a role based on what accs they have saved
    pass

# ----------------------------------------------------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------------------------------------------------



@bot.command()
async def updaterole(ctx):
    roleId = 904582610775322664
    guild = ctx.message.guild
    role = get(guild.roles,id=roleId)
    await ctx.author.add_roles(role)



@bot.command()
async def myaccs(ctx,*arg):
    if UseSQL == True:
        # Take in args to modify and create saved data for the User's account
        
        # Create table for the user that called the command 
        Create_TB(ctx.message.author.id,"M")

        if len(arg) == 0:
            # return an embed with a of their accounts
            sql = f"select * from M{ctx.message.author.id}"
            cursor.execute(sql)
            Result = cursor.fetchall()
            print(Result)

            if len(Result) == 0:
                Output = "You have no accounts us '>myaccs add User#tag note' to add your account(s)"
            else:
                Output = "display"
                embed=discord.Embed(title="Your Accounts", color=discord.Color.dark_red())
                for i in range(len(Result)):
                    embed.add_field(name=Result[i][2],value=Result[i][1])

        else:
            # Atleast one argument passed in

            # In Case of a name with a space(s) compress it so that everything still works fine
            while not '#' in arg[1]:
                arg[1] = arg[1] +" "+arg[2]
                arg.pop(2)


            if arg[0] == "add":
                # Take all data after and add to myaccs db
                Output = AddTo_TB(ctx.message.author.id,"M",arg[1],arg[2])
            elif arg[0] == "del":
                # Delete the specified account for the db
                Output = RmFrom_TB(ctx.message.author.id,"M",arg[1])
            else:
                # Invalid arguement
                Output = "Invalid argument us >help for help"
        
        if Output =="sucess":
            embed=discord.Embed(title="Sucess", description="Operation Completed Sucessfully", color=discord.Color.green())
        elif Output !="display":
            embed=discord.Embed(title="ERROR", description=Output, color=discord.Color.red())
    else:
        embed=discord.Embed(title="ERROR", description="Please Setup and enable a SQL server to use this feature", color=discord.Color.red())
    await ctx.send(embed=embed)
        



@bot.command()
async def quickaccs(ctx,*arg):
    # Take in args to modify and create saved account data 

    # Create table for the user that called the command 
    Create_TB(ctx.message.author.id,"S")

    if len(arg) == 0:
        # Return embed with the list of accounts that they have saved
        pass
    else:
        # They passed in atleast one argument
        if arg[0] == "del":
            # Delete the username after that from their database
            pass
        elif arg[0] == "add":
            # Add the username after type to database
            pass
        else:
            # Return error embed
            pass


@bot.command()
async def help(ctx,*arg):
    # Getting the prefix here so that it can vary based on settings
    prefix = settings["prefix"]
    helps = help_menus
    if len(arg) == 0:
        # Return the default help menu
        embed = discord.Embed(title = "General Help Settings",description = f"Current help menus: {prefix}help rc")
        image = "https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true"
    else:
        if arg[0] in helps:
            embed = discord.Embed(title = helps[arg[0]][1], description = helps[arg[0]][2], color = discord.Color.dark_green())
            image = helps[arg[0]][0]
        else:
            image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
            embed =  embed = discord.Embed(title="Setting not found", description=f"{prefix}help for a general list of help menus" ,color=discord.Color.red())

        # Return the specific help menu
    embed.set_thumbnail(url=image)
    await ctx.send(embed = embed)



@bot.command()
async def rc(ctx,*arg):  
    try:
        cache = False
        arg = list(arg)
        # allows support for the original call setup
        if len(arg)== 0:
            # Input validation
            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            # Input from the user
            await ctx.send("What region? na,eu,ap,kr")
            region = await bot.wait_for("message", check=check, timeout=30)
            region =region.content
            
            await ctx.send("What Username and tag? Ex: Bob#6969")
            name= await bot.wait_for("message", check=check, timeout=30)
            name = name.content

            
        else:
            
            if arg[0] == "cache":
                # Do some stuff 
                cache = True
                pass
            # Work around to allow the use of non-quoted spaced names
            while not '#' in arg[0] and not cache:
                arg[0] = arg[0] +" "+arg[1]
                arg.pop(1)
            if len(arg) == 1 and not cache:

                print(arg)
                name = arg[0]
                region = settings["assumed region"]
            elif not cache:
                # Bassically an else statement just skips if chache 
                print(arg)
                name= arg[0]
                region = arg[1]
            
        if cache:
            # Get user input based on their cached results i.e request their most used/most recent item from the DB
            pass  
        
        split = name.split('#')
        
        
        

        # Api calls, using formatted strings

        MMR= requests.get(f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{split[0]}/{split[1]}")

        # Some default values in case a 200 isn't recieved
        default_color = False

        # Setting the output based on the result of the api call
        if MMR.status_code==200:
            MMR_json = MMR.json()
            
            rank=MMR_json["data"]["currenttierpatched"]
            tiernum=MMR_json["data"]["currenttier"]
            elo=MMR_json["data"]["elo"]
            image = CompTiers.json()["data"][0]["tiers"][tiernum]["largeIcon"]
            color = CompTiers.json()["data"][0]["tiers"][tiernum]["color"][:6]

        elif MMR.status_code == 204:
            output = "Not enough recent data. Play the game more. Also might be wrong region."
            image = "https://pics.me.me/git-gud-19872304.png"
            color = "34ebb1"
        elif MMR.status_code == 429:
            output = "Rate Limited. Wait a few minutes and try again."
            image = "https://streamsentials.com/wp-content/uploads/sadge-png.png"
            color = "34ebb1"
        else:
            image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
            if MMR.json()["message"] == "User not found":
                output = "User not found"
            else:
                output = "Something broke. Oh no!"
                # Not sure how actually useful this is, but it exists
                with open('log.txt','w') as f:
                    f.write(f"Error in rc function {MMR.status_code} | {time.ctime(time.time())} | {region}/{split[0]}/{split[1]} | {MMR.json()} \n")
            EMB_color = discord.Color.red()
            default_color = True
            
            # Convert the hex colors to rgb
        
        # if default_color is true then we don't need to convert from hex to rgb
        if default_color == False:
            color_rgb = ImageColor.getcolor("#"+color, "RGB")
            # Discord won't accept a tuple so I just am storing them in variables
            red = color_rgb[0]
            blue = color_rgb[1]
            green = color_rgb[2]
            EMB_color = discord.Color.from_rgb(red,green,blue)

        if MMR.status_code==200:
            #add some stuff that we couldn't make before because of being required to make the embed
            item = discord.Embed(title=name, description=f"The stats and rank for {name}" ,color=EMB_color)
            item.add_field(name="Rank",value=rank,inline=True)
            item.add_field(name="MMR",value=elo,inline=True)
        else:
            item = discord.Embed(title=name, description=output, color=EMB_color)

        item.set_thumbnail(url=image)
        item.set_footer(text="Razebot by MaximumMaxx")
        await ctx.send(embed = item)
        # Upon successful completion aka getting the embed output

    except TimeoutError:
        embed = discord.Embed(title="Timeout, took too long", description=f"A 30 second timeout ran out." ,color=discord.Color.red())
        await ctx.send(embed = embed)
    except:
        embed = discord.Embed(title="Something broke in a very bad way", description=f"Please send help" ,color=discord.Color.red())
        await ctx.send(embed = embed)
        print(logging.exception(''))

bot.run('')
