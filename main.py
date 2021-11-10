
import time
import discord
from discord import embeds
from discord.activity import CustomActivity
from discord.ext import commands
import random
from mysql.connector import connect
import requests
import re
from PIL import ImageColor
import logging

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

#Make 1 api call at the start since it doen't change basically ever anyways

CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")

bot = commands.Bot(command_prefix=settings["prefix"], help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Activity(name=" Minecraft", type=1))


def save_to_DB(user, username):


    cursor = DB.cursor()
    sql = f'''CREATE TABLE IF NOT EXISTS U{user} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `quantity` INT NULL,
    `ign` VARCHAR(255) NULL,
    PRIMARY KEY (`id`));
    '''
    cursor.execute(sql)
    sql = f"Select * from U{user} WHere ign like '{username}'"
    
    cursor.execute(sql)

    Result = cursor.fetchall()
   

    if len(Result) == 0:
        print("not in db")
        #sql = f"INSERT INTO U{user} (quantity, ign) VALUES (%s,%s)"
        #values = (1,username)

        sql = f"INSERT INTO  U{user} (quantity, ign) VALUES (1,'{username}');"
        cursor.execute(sql)
        
        DB.commit()
        



    else:

        sql = f"Select * from U{user}"
        cursor.execute(sql)
        rslt = cursor.fetchall()
        count = rslt[0][1]
        count += 1
        sql = f"UPDATE U{user} SET quantity = {count} where ign like '{username}';"
        cursor.execute(sql)
        DB.commit()

        sql = f"Select * from U{user}"
        cursor.execute(sql)
        rslt = cursor.fetchall()




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

            # Weird Regex thing to split all non letters and numbers
        elif len(arg) == 1:
            name = arg[0]
            region = settings["assumed region"]
            
        else:

            name= arg[0]
            region = arg[1]
            
            
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

        if UseSQL == True:
            save_to_DB(ctx.author.id,name)

    except TimeoutError:
        embed = discord.Embed(title="Timeout, took too long", description=f"A 30 second timeout ran out." ,color=discord.Color.red())
        await ctx.send(embed = embed)
    except:
        embed = discord.Embed(title="Something broke in a very bad way", description=f"Please send help" ,color=discord.Color.red())
        await ctx.send(embed = embed)
        print(logging.exception(''))

bot.run('')
