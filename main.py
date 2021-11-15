import time # Error logging
import discord # All bot functionality 
from discord.ext import commands # Commands for said discord integration
from discord.utils import get # Used for rank assignment
import requests # Api Calls
from PIL import ImageColor # Converting Hex to RGB
import logging # Error Logging

# The setting dictionary. Won't store across restarts but this is more meant for if you change the source code to have
# an easy place to keep all the essential settings. Also this approach doesn't require SQL which was partly my goal.
settings = {"assumed region":"na","prefix":">"}

# Command:[embed,ImageLink]
help_menus = {"rc":["https://static.wikia.nocookie.net/valorant/images/2/24/TX_CompetitiveTier_Large_24.png","RC aka Rank Check", f"Takes in 0,1, or 2 parameters and searches the valorant api for a player's stats. If it finds a valid player it returns an with the player's rank and MMR. With one argument it takes in the Valorant name formatted like Name#Tag and pulls from the default region in settings. If no arguments are provided it prompts the user with questions instead. If you want to specify region you can either use 2 arguments like >rc Vname#tag region or no arguments"],
"quickaccs":["https://upload.wikimedia.org/wikipedia/commons/a/a8/Lightning_bolt_simple.png","Quick Accounts",f"A command to interact with a database of saved quick accounts. Quick accounts are used to check the ranks of certain people or accounts without having to memorize their tags. Syntax: All uses start with >quickaccs followed by something. To view a list of your saved accounts use '>quickaccs'. To add an account use '>quickaccs add Name#tag note' If the name or note has spaces you don't have to do anything special. To remove an account use '>quickaccs del Name#tag' Again nothing special has to happen if the name has spaces"],
"myaccs":["https://pngimg.com/uploads/smurf/smurf_PNG34.png","My accounts",f"A command to interact with a database of saved quick accounts. My accounts is used to manage a list of accounts you own. Syntax: All uses start with >myaccs followed by something. To view a list of your saved accounts use '>myaccs'. To add an account use '>muaccs add Name#tag note' If the name or note has spaces you don't have to do anything special. To remove an account use '>myaccs del Name#tag' Again nothing special has to happen if the name has spaces"]}# Obviously only 

# Modify the second item in each set with the name of the role. Ex: unranked role called "Cringe" "unranked":"Unranked" -> "unranked":"Cringe"
role_names= {"unranked":"Unranked","iron":"⁎ Iron ⁎","bronze":"⁑ Bronze ⁑","silver":"✼ Silver ✼","gold":"Gold","platnium":"Platinum","diamond":"Diamond","immortal":"Immortal","radiant":"Radiant"}

# Obviously only enable SQL if you have a database setup
UseSQL = True
if UseSQL == True:
    import mysql.connector
    # In the parenthesis put the things to connect to your Database. Ex: host = "localhost", user = "sudo", password = "My very secure password", database = "Razebot"
    DB = mysql.connector.connect()

    print(DB)
    cursor = DB.cursor()

#Make 1 api call at the start since it doesn't change basically ever anyways
CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")

# initialize the bot
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

# ----------------------------------------------------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------------------------------------------------

@bot.command()
async def updaterole(ctx):
    if UseSQL:
        try:
            # A really hacky solution to remove all the rank roles someone has
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["unranked"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["iron"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["bronze"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["silver"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["gold"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["platnium"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["diamond"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["immortal"]))
            await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, name=role_names["radiant"]))
    
            sql = f"select * from M{ctx.message.author.id}"
            cursor.execute(sql)
            Result = cursor.fetchall()
    
            if len(Result) != 0:
                # if they have something in the database
                max_rank = (-1,"") # if the person is unranked then 0 > -1
                region = settings["assumed region"]
                for i in range(len(Result)):
                    split = Result[i][2].split('#')
                    MMR= requests.get(f"https://api.henrikdev.xyz/valorant/v1/mmr/{region}/{split[0]}/{split[1]}")
                    if MMR.status_code != 200:
                        continue
                    MMR_json = MMR.json()
                    rank=MMR_json["data"]["currenttierpatched"]
                    if MMR_json["data"]["currenttier"] > max_rank[0]:
                        max_rank = (MMR_json["data"]["currenttier"],Result[i][2])
                        rank_split = rank.split(' ')[0].lower()
            
                if max_rank[0] == -1:
                    rank_split = "unranked"
                    embed = discord.Embed(title="Warning", description="You have no valid accounts in the database. us >help myaccs for more info on adding accounts. You have been given unranked for now", color=discord.Color.gold())
                else:
                    embed = discord.Embed(title="Sucess", description=f"You have been granted the role {rank_split} feel free to add any other accounts you may have and run this command again.", color=discord.Color.green())
            else:
                # They don't have anything in the database
                embed = discord.Embed(title="ERROR", description="You have no items in the database us >help myaccs for more info. You have been given unranked for now", color=discord.Color.red())
                rank_split = "unranked"
            guild = ctx.message.guild
    
            print(f":{rank_split}:")
            role = get(guild.roles, name=role_names[rank_split])
            await ctx.author.add_roles(role)
        except:
            embed = discord.Embed(title="Nope", description=f"Something did a big ol break...", color=discord.Color.red())
            print(logging.exception(''))

    else:
        embed=discord.Embed(title="ERROR", description="Please setup, connect, and enable a SQL database to use this feature", color=discord.Color.red())
    embed.set_footer(text="Razebot by MaximumMaxx")    
    await ctx.send(embed=embed)



@bot.command()
async def myaccs(ctx,*arg):
    if UseSQL == True:
        try:
            # Take in args to modify and create saved data for the User's account
            arg = list(arg)
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
                
                # Compress the note into arg[3] so you don't have to use quotes
                while len(arg) > 3:
                    arg[2] = arg[2] +" "+arg[3]
                    arg.pop(3)
 
 
                if arg[0] == "add":
                    if len(arg) == 2:
                        arg.append("No note")
 
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
        except:
            embed=discord.Embed(title="haha get errored", description="Something broke lol", color=discord.Color.red())
            print(logging.exception(''))
    else:
        embed=discord.Embed(title="ERROR", description="Please Setup and enable a SQL server to use this feature", color=discord.Color.red())
    embed.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed=embed)



@bot.command()
async def quickaccs(ctx,*arg):
    if UseSQL == True:
        try:
            # Take in args to modify and create saved data for the User's account
            
            # Create table for the user that called the command 
            Create_TB(ctx.message.author.id,"S")
 
            if len(arg) == 0:
                # return an embed with a of their accounts
                sql = f"select * from S{ctx.message.author.id}"
                cursor.execute(sql)
                Result = cursor.fetchall()
                print(Result)
 
                if len(Result) == 0:
                    Output = "You have no accounts use '>quickaccs add User#tag note' to add your account(s)"
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
 
                # Compress the note into arg[3] so you don't have to use quotes
                while len(arg) > 3:
                    arg[2] = arg[2] +" "+arg[3]
                    arg.pop(3)
 
                if arg[0] == "add":
                    # Take all data after and add to myaccs db
                    if arg[0] == "add":
                        if len(arg) == 2:
                            arg.append("No note")
                    Output = AddTo_TB(ctx.message.author.id,"S",arg[1],arg[2])
                elif arg[0] == "del":
                    # Delete the specified account for the db
                    Output = RmFrom_TB(ctx.message.author.id,"S",arg[1])
                else:
                    # Invalid arguement
                    Output = "Invalid argument us >help for help"
            
            if Output =="sucess":
                embed=discord.Embed(title="Sucess", description="Operation Completed Sucessfully", color=discord.Color.green())
            elif Output !="display":
                embed=discord.Embed(title="ERROR", description=Output, color=discord.Color.red())
        except:
            embed=discord.Embed(title="ERROR", description="Something broke lol get rekt", color=discord.Color.red())
    else:
        embed=discord.Embed(title="ERROR", description="Please Setup and enable a SQL server to use this feature", color=discord.Color.red())
    embed.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx,*arg):
    # Getting the prefix here so that it can vary based on settings
    prefix = settings["prefix"]
    helps = help_menus
    if len(arg) == 0:
        # Return the default help menu
        embed = discord.Embed(title = "List of help menus",description = f"Current help menus: {prefix}help rc, {prefix}help myaccs, {prefix}help quickaccs")
        image = "https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true"
    else:
        # Return the specified help menu
        if arg[0] in helps:
            embed = discord.Embed(title = helps[arg[0]][1], description = helps[arg[0]][2], color = discord.Color.dark_green())
            image = helps[arg[0]][0]
        else:
            # Invalid help menu
            image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
            embed =  embed = discord.Embed(title="Setting not found", description=f"{prefix}help for a general list of help menus" ,color=discord.Color.red())
 
    # return the help menu
    embed.set_thumbnail(url=image)
    embed.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed = embed)

@bot.command()
async def rc(ctx,*arg):  
    try:
        Preembed = False
        arg = list(arg)
        # allows support for the original call setup
        if len(arg)== 0:
            if UseSQL == True:
                # If SQL is enabled pull a list of accounts from Quickaccs
                try:
                    sql = f"SELECT * FROM S{ctx.message.author.id}"
                    cursor.execute(sql)
                    Result = cursor.fetchall()
                except:
                    item = discord.Embed(title="No accounts in quickaccs", description=f"Use >help quickaccs for more info" ,color=discord.Color.red())
                    Preembed = True
 
                if len(Result) == 0:
                    # Not Quick accounts
                    item = discord.Embed(title="No accounts in quickaccs", description=f"Use >help quickaccs for more info" ,color=discord.Color.red())
                    Preembed = True
                else:
                    # Atleast 1 quick account
                    
                    # Generating the embed with counting starting from 1
                    item =discord.Embed(title="Your Quick Accounts", color=discord.Color.dark_red())
                    for i in range(len(Result)):
                        item.add_field(name=f"{i+1}). {Result[i][2]}",value=Result[i][1])
                    
                    # User input validation
                    def check(msg):
                        return msg.author == ctx.author and msg.channel == ctx.channel
                    
                    # User input
                    await ctx.send("What account number would you like to check? Use 'Cancel' to cancel the command")
                    await ctx.send(embed=item)
                    acc = await bot.wait_for("message", check=check, timeout=30)
                    if acc.content =="Cancel":
                        Preembed = True
                        item = discord.Embed(title="Operation Cancelled" ,color=discord.Color.green())
                    elif len(Result) < int(acc.content) -1 or int(acc.content)<= 0:
                        Preembed = True
                        item = discord.Embed(title="Invalid account number" ,color=discord.Color.red())
                    else:
                        # Account number should be valid here
                        name = Result[int(acc.content)-1][2]
                        region = settings["assumed region"]
 
            else:
                # Just uses the legacy rank checking system with message and response if SQL isn't enabled
 
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
            # return an embed with a list of their accounts
            if "<" in arg[0]:
                # Pinging Someone
                # Removeing all the special characters to isolate the uuid of the ping
                to_rem = ["<",">","!","@"]
                arg = list(arg)
                for i in to_rem:
                    arg[0] = arg[0].replace(i,'')
                
                # Getting the accounts owned by that uuid
                sql = f"select * from M{arg[0]}"
                cursor.execute(sql)
                Result = cursor.fetchall()
                print(Result)
                
                # Possibly working line of code to get the uname of the 
                user = bot.get_user(arg[0])

                # User input validation
                def check(msg):
                    return msg.author == ctx.author and msg.channel == ctx.channel
                
                # Embed for the pinged person's accounts
                await ctx.send("What account number would you like to check? Use 'Cancel' to cancel the command")
                embed=discord.Embed(title=f"{user}'s accounts", color=discord.Color.dark_red())
                for i in range(len(Result)):
                    embed.add_field(name=f"{i+1}) {Result[i][2]}",value=Result[i][1])
                embed.set_footer(text="Razebot by MaximumMaxx")
                await ctx.send(embed=embed)
                
                # User input
                acc = await bot.wait_for("message", check=check, timeout=30)
                if acc.content =="Cancel":
                    Preembed = True
                    item = discord.Embed(title="Operation Cancelled" ,color=discord.Color.green())
                elif len(Result) < int(acc.content) -1 or int(acc.content)<= 0:
                    Preembed = True
                    item = discord.Embed(title="Invalid account number" ,color=discord.Color.red())
                else:
                    # Account number should be valid here
                    name = Result[int(acc.content)-1][2]
                    region = settings["assumed region"]

            else:
                # Work around to allow the use of non-quoted spaced names
                while not '#' in arg[0]:
                    arg[0] = arg[0] +" "+arg[1]
                    arg.pop(1)
                if len(arg) == 1:
    
                    print(arg)
                    name = arg[0]
                    region = settings["assumed region"]
                else: 
                    print(arg)
                    name= arg[0]
                    region = arg[1]
            
        # Skip all the api calls if there isn't anything in quickaccs
        if not Preembed:
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

bot.run()
