import time
import discord
from discord import embeds
from discord.ext import commands
import random
from mysql.connector import connect
import requests
import re
from PIL import ImageColor
import logging

# A very overkill solution to caching common usernames however, it works and is good SQL practice.
# Obviously only 
UseSQL = False
if UseSQL == True:
    import mysql.connector
    DB = mysql.connector.connect("Your DB connection")
    print(DB)

settings = {"assumed region":"na",}

bot = commands.Bot(command_prefix='>')

def save_to_DB(user, username):

    print(user)
    print(username)

    cursor = DB.cursor()
    sql = f"CREATE TABLE IF NOT EXISTS {user} (id INT, username TEXT, quantity INT, ign VARCHAR(255))"
    cursor.execut(sql)
    sql = f"SELECT * FROM {user} WHERE text LIKE {username} LIMIT 1"
    cursor.execute(sql)

    Result = cursor.fetchall()
    
    print(Result)

    if len(Result) == 0:
        sql = f"INSERT INTO {user} (quantity, ign)"
        values = (1,username)
        cursor.execute(sql,values)
    else:
        sql = f"UPDATE {user} SET {Result} quantity = 2"


@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def rand(ctx):
    await ctx.send(str(random.randint(0,100)))


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
            print("2 args")
            name= arg[0]
            region = arg[1]
            
            
        split = name.split('#')
        
        

        # Api calls, using formatted strings
        CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")
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

bot.run('Bot Token')
