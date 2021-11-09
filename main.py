import time
import discord
from discord.ext import commands
import random
import requests
import re
from PIL import ImageColor

bot = commands.Bot(command_prefix='>')

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def rand(ctx):
    await ctx.send(str(random.randint(0,100)))

@bot.command()
async def rc(ctx):    
    # Input validation
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    # Input from the user
    await ctx.send("What region? na,eu,ap,kr")
    region = await bot.wait_for("message", check=check, timeout=30)
    
    await ctx.send("What Username and tag? Ex: Bob#6969")
    name= await bot.wait_for("message", check=check, timeout=30)

    # Weird Regex thing to split all non letters and numbers
    split = re.findall(r"[\w']+", name.content)

    # Api calls, using formatted strings
    CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")
    MMR= requests.get(f"https://api.henrikdev.xyz/valorant/v1/mmr/{region.content}/{split[0]}/{split[1]}")
    profile = requests.get(f"https://api.henrikdev.xyz/valorant/v1/account/{split[0]}/{split[1]}")

    # Some default values in case a 200 isn't recieved
    

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
        output = "Either something is very broken, or you miss typed something"
        # Not sure how actually useful this is, but it exists
        with open('log.txt','w') as f:
            f.write(f"Error in rc function {MMR.status_code} | {time.ctime(time.time())} | {region.content}/{split[0]}/{split[1]} | {MMR.json()}")
        color = discord.Color.red()
        image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
    
    # Convert the hex colors to rgb
    color_rgb = ImageColor.getcolor("#"+color, "RGB")
    # Discord won't accept a tuple so I just am storing them in variables
    red = color_rgb[0]
    blue = color_rgb[1]
    green = color_rgb[2]

    if MMR.status_code==200:
        #add some stuff that we couldn't make before because of being required to make the embed
        item = discord.Embed(title=name.content, description=f"The stats and rank for {name.content}" ,color=discord.Color.from_rgb(red,green,blue))
        item.add_field(name="Rank",value=rank,inline=True)
        item.add_field(name="MMR",value=elo,inline=True)
    else:
        item = discord.Embed(title=name.content, description=output, color=discord.Color.from_rgb(red,green,blue))

    item.set_thumbnail(url=image)
    item.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed = item)

bot.run('')
