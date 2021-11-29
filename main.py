# External imports
import time # Error logging
import discord
from discord.commands.commands import option # All bot functionality 
from discord.ext import commands # Commands for said discord integration
from discord.utils import get # Used for rank assignment
import requests # Api Calls
from PIL import ImageColor # Converting Hex to RGB
import logging # Error Logging
from asyncio import exceptions # Should already be included with pycord
import mysql.connector #sql connection

# Local Imports
from help_menus import help_menus,avaliable_help_menus
from bot_token import bot_token, connection

# Establishing DB connection
# In the parenthesis put the things to connect to your Database. Ex: host = "localhost", user = "sudo", password = "My very secure password", database = "Razebot"
DB = mysql.connector.connect(connection)
print(DB)
cursor = DB.cursor()

# Time variables for the reconnect time thing
timeout_time = 2700
refresh_time = time.time() + timeout_time


#Make 1 api call at the start since it doesn't change basically ever anyways
CompTiers = requests.get("https://valorant-api.com/v1/competitivetiers")

# Generates a list of the currently avaliable tiers. Should be up to date with any rank name changes as long as the api keeps up to date
valid_ranks = []
for i in CompTiers.json()["data"][0]["tiers"]:
    # Just making sure that it's not one of the unused divisions
    if not i["divisionName"].lower() in valid_ranks and i["divisionName"] != "Unused2" and i["divisionName"] != "Unused1":
        # valid_ranks should have the lowercase version of the ranks
        valid_ranks.append(i["divisionName"].lower())

print(valid_ranks)
valid_settings = ["region"]

# initialize the bot
bot = commands.Bot(command_prefix=">", help_command=None)

@bot.event
async def on_ready():
    await bot.change_presence(activity = discord.Activity(name=">help", type=2))

# ----------------------------------------------------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------------------------------------------------

def refresh():
    global refresh_time
    global DB
    global cursor
    if time.time() > refresh_time:
        DB.close()
        DB = mysql.connector.connect(host="localhost",user="root",password="root",database="Razebot")
        cursor = DB.cursor()
        print("Refreshed")
    refresh_time = time.time()+timeout_time
    
def Acc_TB(id,type):
    # S signifies a saved accounts table. M signifys a Myaccounts table
    sql = f'''CREATE TABLE IF NOT EXISTS {type}{id} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `note` VARCHAR(255) NULL,
    `ign` VARCHAR(255) NULL,
    PRIMARY KEY (`id`));
    '''
    cursor.execute(sql)

def Add_ACCS(user, type, ign, note):
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
async def settings(ctx, *arg):
    refresh()
    invalidDated = False

    arg= list(arg)
    guild = ctx.author.guild.id
    sql = f'''CREATE TABLE IF NOT EXISTS set{guild} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `setting` VARCHAR(255) NULL UNIQUE,
    `value` VARCHAR(255) NULL,
    PRIMARY KEY (`id`));
    '''

    cursor.execute(sql)

    if arg[0] == "list":
        nice_string = ""
        for set in valid_settings:
            nice_string += f"{set} "
        embed = embed = discord.Embed(title="Avaliable Settings", description=f"List of avaliable settings: {nice_string}", color=discord.Color.light_gray())

    else:
        # getting and converting the list of settings into a dictionary for easier code writing
        sql = f"select * from set{guild}"
        cursor.execute(sql)
        settings = cursor.fetchall()

        settingsDict = {}
        for i in range(len(settings)):
            # Key is the role and the value for the key in the value
            settingsDict[settings[i][1]] = settings[i][2]
        
        for item in arg:
            split = item.split(':')
            if split[0] in valid_settings:
                continue
            else:
                index = arg.index(item)
                arg.pop(index)
                invalidDated = True



        if len(arg) == 0 and invalidDated:
            # put in args, just not valid ones
            embed = embed = discord.Embed(title="Error", description="No valid arguements passed in. Use '>help settings' for more info", color=discord.Color.red())
        elif len(arg) == 0 and invalidDated == False:
            # No args
            embed = embed = discord.Embed(title="Error", description="No arguments passed in", color=discord.Color.red())
        else:
            # Valid args
            for setting in arg:
                split = setting.split(":")
                if split[0] in valid_settings:
                    # Replace into a is a great command
                    sql = f'''REPLACE INTO set{guild} (setting,value) VALUES (%s,%s)'''
                    values = (split[0],split[1])
                    cursor.execute(sql,values)
                    DB.commit()
            embed = embed = discord.Embed(title="Success", description="Settings have sucessfully been updated", color=discord.Color.green())

    await ctx.send(embed = embed)

# ----------------------------------------------------------------------------------------------------------------------

@bot.command()
async def setroles(ctx, *arg):
    refresh()
    missing_roles = []
    arg= list(arg)
    guild = ctx.author.guild.id
    # New table prefix, rl
    sql = f'''CREATE TABLE IF NOT EXISTS rl{guild} (
    `id` INT NOT NULL AUTO_INCREMENT,
    `role` VARCHAR(255) NULL UNIQUE,
    `value` VARCHAR(255) NULL,
    PRIMARY KEY (`id`));
    '''
    cursor.execute(sql)

    invalidDated = False

    # Remove any invalid roles
    for item in arg:
        split = item.split(':')
        if split[0] in valid_ranks:
            continue
        else:
            index = arg.index(item)
            arg.pop(index)
            print("Invalid")
            invalidDated = True

    if len(arg) == 0 and invalidDated == False:
        embed = embed = discord.Embed(title="Warning", description="No arguements passed in. Use '>help setroles' for more info", color=discord.Color.gold())
    elif invalidDated == True and len(arg) == 0:
        embed = embed = discord.Embed(title="Warning", description="No valid arguements passed in. Use '>help setroles' for more info", color=discord.Color.gold())
    else:
        for item in arg:
            split = item.split(':')
            to_rem = ["<",">","!","@","&"]
            for i in to_rem:
                split[1] = split[1].replace(i,'')
            # So I know this implementation is kinda slow, but it will work fine enough for now. If I need to make this faster in the future I can
            sql = f'''REPLACE INTO rl{guild} (role,value) VALUES (%s,%s)'''
            values = (split[0],split[1])
            cursor.execute(sql, values)
            DB.commit()
        embed = embed = discord.Embed(title="Success", description="Roles have sucessfully been updated", color=discord.Color.green())
    
    await ctx.send(embed=embed)
    sql = f"select * from rl{guild}"
    cursor.execute(sql)
    in_db = cursor.fetchall()

    rsltDict = {}
    for i in range(len(in_db)):
        # Key is the role and the value for the key in the value
        rsltDict[in_db[i][1]] = in_db[i][2]

    missing_roles = []
    if not len(in_db) == len(valid_ranks):
        for key in valid_ranks:
            # A kinda hacky way to append if it's not in the dictionary
            try:
                rsltDict[key]
            except:
                missing_roles.append(key)



    if missing_roles != []:
        embed = discord.Embed(title="Warning", description=f"You are still missing the following roles {missing_roles}. You may enouncer errors while these are not properly configured use '>help setroles'", color=discord.Color.gold())
        await ctx.send(embed=embed)

# ----------------------------------------------------------------------------------------------------------------------

@bot.slash_command(nane="Update Role",description="Update your role based on you accounts save in Myaccounts", guild_ids=[898725831164178442])
async def updaterole(ctx):
    refresh()
    guild = ctx.author.guild.id
    has_roles = False
    has_region = True
    set = []
    try:
        sql = f"select * from rl{guild}"
        cursor.execute(sql)
        roles = cursor.fetchall()

        print(roles)
        print(len(valid_ranks))
        if len(roles) == len(valid_ranks):
            has_roles = True
    except:
        pass

    try:
        sql = f"select * from set{guild}"
        cursor.execute(sql)
        set = cursor.fetchall()
        print(set)
    except:
        has_region = False
    
    try:
        setDict = {}
        for i in range(len(set)):
            # Key is the role and the value for the key in the value
            setDict[set[i][1]] = set[i][2]
        region = setDict["region"]
        has_region= True
    except:
        has_region = False

    print(has_roles)
    print(has_region)

    if has_region and has_roles:
        try:
            # A less hacky solution to role removal
            roleDict = {}
            for i in range(len(roles)):
                # Key is the role and the value for the key in the value
                roleDict[roles[i][1]] = roles[i][2]

            for rank in roleDict:
                await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, id=int(roleDict[rank])))


            sql = f"select * from M{ctx.author.id}"
            cursor.execute(sql)
            Result = cursor.fetchall()
            if len(Result) != 0:
                # if they have something in the database
                max_rank = (-1,"") # if the person is unranked then 0 > -1

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
            guild = ctx.guild

            role = get(guild.roles, name="diamond")
            print(role)
            await ctx.author.add_roles(role)
        except:
            embed = discord.Embed(title="Nope", description=f"Something did a big ol break...", color=discord.Color.red())
            print(logging.exception(''))
    else:
        embed = discord.Embed(title="Error", description=f"Please configure a default region region and/or setup default roles. use '>help settings' and '>help setroles'", color=discord.Color.red())
    embed.set_footer(text="Razebot by MaximumMaxx")    
    await ctx.respond(embed=embed)

# ----------------------------------------------------------------------------------------------------------------------

@bot.command()
async def myaccs(ctx,*arg):
    refresh()
    try:
        # Take in args to modify and create saved data for the User's account
        arg = list(arg)
        # Create table for the user that called the command 
        Acc_TB(ctx.message.author.id,"M")

        if len(arg) == 0:
            # return an embed with a of their accounts
            sql = f"select * from M{ctx.message.author.id}"
            cursor.execute(sql)
            Result = cursor.fetchall()
            print(Result)

            if len(Result) == 0:
                Output = "You have no accounts use '>myaccs add User#tag note' to add your account(s)"
            elif len(Result) > 25:
                Output = "You have reached the account limit. No clue why you would prossibly own 25 accounts but ok. Use '/help' for more info on managing your accounts"
            else:
                embed=discord.Embed(title="Your Accounts", color=discord.Color.dark_red())
                for i in range(len(Result)):
                    embed.add_field(name=Result[i][2],value=Result[i][1])

        elif len(arg) == 1:
            # Only 1 perameter was passed in so it won't do anything except error
            embed=discord.Embed(title="Error", description = "Invalid argument count. Use '>help myaccs' for more info",color=discord.Color.red())

        else:
            # Atleast two arguments passed in
            if arg[0] == "add":    
                # This is not super clean code but functions were being weird so I can't do that solution
                while not '#' in arg[1]:
                    arg[1] = arg[1] +" "+arg[2]
                    arg.pop(2)

                while len(arg) > 3:
                    arg[2] = arg[2] +" "+arg[3]
                    arg.pop(3)

                if len(arg) == 2:
                    arg.append("No note")

                Output = Add_ACCS(ctx.message.author.id,"M",arg[1],arg[2])
            elif arg[0] == "del":

                while not '#' in arg[1]:
                    arg[1] = arg[1] +" "+arg[2]
                    arg.pop(2)

                while len(arg) > 3:
                    arg[2] = arg[2] +" "+arg[3]
                    arg.pop(3)

                # Delete the specified account for the db
                Output = RmFrom_TB(ctx.message.author.id,"M",arg[1])

            else:
                # Invalid arguement
                Output = "Invalid argument use >help for help"
        
        if Output =="sucess":
            embed=discord.Embed(title="Sucess", description="Operation Completed Sucessfully", color=discord.Color.green())
        elif Output == "maxed":
            embed=discord.Embed(title="ERROR", description="You have reached the accounts limit. Not sure why you own more than 25 accounts but ok. use '/help' for help removing accounts", color=discord.Color.red())            
        elif Output !="display":
            embed=discord.Embed(title="ERROR", description=Output, color=discord.Color.red())
    except:
        embed=discord.Embed(title="haha get errored", description="Something broke lol", color=discord.Color.red())
        print(logging.exception(''))

    embed.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed=embed)

# ----------------------------------------------------------------------------------------------------------------------

@bot.command()
async def quickaccs(ctx,*arg):
    refresh()
    try:
        arg = list(arg)
        # Take in args to modify and create saved data for the User's account
        
        # Create table for the user that called the command 
        Acc_TB(ctx.message.author.id,"S")

        if len(arg) == 0:
            # return an embed with a of their accounts
            sql = f"select * from S{ctx.message.author.id}"
            cursor.execute(sql)
            Result = cursor.fetchall()
            print(Result)

            if len(Result) == 0:
                Output = "You have no accounts use '>quickaccs add User#tag note' to add your account(s)"
            elif len(Result) > 25:
                Output = "You have reached the account limit. You either have a lot of friends and/or watch too much Valorant youtube. Either way until I feel like working around the field limit you're a little screwed. Use '/help' for more info on managing your accounts"
            else:
                Output = "display"
                embed=discord.Embed(title="Your Accounts", color=discord.Color.dark_red())
                for i in range(len(Result)):
                    embed.add_field(name=Result[i][2],value=Result[i][1])

        else:
            # Atleast one argument passed in

            if arg[0] == "add":
                while not '#' in arg[1]:
                    arg[1] = arg[1] +" "+arg[2]
                    arg.pop(2)

                while len(arg) > 3:
                    arg[2] = arg[2] +" "+arg[3]
                    arg.pop(3)
                # Take all data after and add to myaccs db
                if len(arg) == 2:
                    arg.append("No note")
                Output = Add_ACCS(ctx.message.author.id,"S",arg[1],arg[2])
            elif arg[0] == "del":
                while not '#' in arg[1]:
                    arg[1] = arg[1] +" "+arg[2]
                    arg.pop(2)

                while len(arg) > 3:
                    arg[2] = arg[2] +" "+arg[3]
                    arg.pop(3)
                # Delete the specified account for the db
                Output = RmFrom_TB(ctx.message.author.id,"S",arg[1])
            else:
                # Invalid arguement
                Output = "Invalid argument us >help for help"
        
        if Output =="sucess":
            embed=discord.Embed(title="Sucess", description="Operation Completed Sucessfully", color=discord.Color.green())
        elif Output == "maxed":
            embed=discord.Embed(title="ERROR", description="While it is understamdable that you would want more than 25 saved accounts, until due time when I feel like working around the field limit you'll just have to priotatize", color=discord.Color.red())
        elif Output !="display":
            embed=discord.Embed(title="ERROR", description=Output, color=discord.Color.red()) 
    except:
        embed=discord.Embed(title="ERROR", description="Something broke lol get rekt", color=discord.Color.red())
        print(logging.exception(''))

    embed.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed=embed)

# ----------------------------------------------------------------------------------------------------------------------

@bot.slash_command()
async def help(ctx,setting: str = option(avaliable_help_menus,None,required=False)):
    setting = setting or None

    print(type(setting))

    helps = help_menus
    if type(setting) != str:
        # Return the default help menu
        embed = discord.Embed(title = "List of help menus",description = f"Current help menus: /help rc, /help myaccs, /help quickaccs, /help updaterole, /help quick vs myaccs, /help settings, /help setroles")
        image = "https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true"
    else:
        # Return the specified help menu
        if setting in helps:
            embed = discord.Embed(title = helps[setting][1], description = helps[setting][2], color = discord.Color.dark_green())
            image = helps[setting][0]
        else:
            # Invalid help menu
            image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
            embed =  embed = discord.Embed(title="Setting not found", description=f"/help for a general list of help menus" ,color=discord.Color.red())
 
    # return the help menu
    embed.set_thumbnail(url=image)
    embed.set_footer(text="Razebot by MaximumMaxx")
    await ctx.respond(embed = embed)

# ----------------------------------------------------------------------------------------------------------------------

@bot.command()
async def rc(ctx,*arg):
    refresh()
    has_region = True
    guild = ctx.author.guild.id
    try:
        sql = f"select * from set{guild}"
        cursor.execute(sql)
        set = cursor.fetchall()
        
        setDict = {}
        for i in range(len(set)):
            # Key is the role and the value for the key in the value
            setDict[set[i][1]] = set[i][2]
        region = setDict["region"]
    except:
        print("the second one got ya")
        has_region = False
        print(logging.exception(''))
    if has_region:
        # Welcome to If hell, how may I take your order?
        # Yeah I'll take sketchy code with a side of uncertinty and maybe an 5L unneccesary variable to drink
        # Alright, coming right up:  
        try:
            Preembed = False
            arg = list(arg)
            # allows support for the original call setup
            if len(arg)== 0:
            
                try_succeed = False
                # If SQL is enabled pull a list of accounts from Quickaccs
                try:
                    sql = f"SELECT * FROM S{ctx.message.author.id}"
                    cursor.execute(sql)
                    Result = cursor.fetchall()
                    try_succeed = True
                except:
                    item = discord.Embed(title="No accounts in quickaccs", description=f"Use >help quickaccs for more info" ,color=discord.Color.red())
                    Preembed = True
                # know this is a stupid way to implement this but I also don't care enough to fix it.
                # There's a tiny bit of logic becuase I want that try to just effect that SQL statement 
                # But there's still absolutely a cleaner way to do it. 
                if try_succeed:

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
                    
                    print(arg[0])
                    # https://www.reddit.com/r/Discord_Bots/comments/quyrbk/get_username_from_uuid/
                    user = await bot.fetch_user(arg[0])

                    username = user.name

                    # User input validation
                    def check(msg):
                        return msg.author == ctx.author and msg.channel == ctx.channel
                    
                    # Embed for the pinged person's accounts
                    await ctx.send("What account number would you like to check? Use 'Cancel' to cancel the command")
                    embed=discord.Embed(title=f"{username}'s accounts", color=discord.Color.dark_red())
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

                else:
                    # Work around to allow the use of non-quoted spaced names
                    while not '#' in arg[0]:
                        arg[0] = arg[0] +" "+arg[1]
                        arg.pop(1)
                    if len(arg) == 1:
        
                        print(arg)
                        name = arg[0]
                    else: 
                        print(arg)
                        name= arg[0]
                        region = arg[1]
                
            # Skip all the api calls if there isn't anything in quickaccs
            if not Preembed:
                split = name.split('#')
    
                # Api calls, using formatted strings
                MH= requests.get(f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{split[0]}/{split[1]}?filter=competitive")
                MMR = requests.get(f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{split[0]}/{split[1]}")
                # Some default values in case a 200 isn't recieved
                default_color = False
    
                kills = "Unkown"
                deaths = "Unknown"
                assists = "Unknown"
                score = "Unknown"
                mmr_change = "Unknown"


                # Setting the output based on the result of the api call
                if MMR.status_code==200:
                    MMR_json = MMR.json()
                
                    # Match history data  
                    if MH.status_code == 200:
                        # Variables n stuff
                        MH_json = MH.json()
                        match_count = len(MH_json["data"])
                        kills = 0
                        deaths = 0
                        assists = 0
                        score = 0
                        uuid = MH_json["puuid"]
                        # for all the matches in the match history, add them to the the variables
                        for i in range(match_count):
                            j = 0
                            while True:
                                if MH_json["data"][i]["players"]["all_players"][j]["puuid"] == uuid:
                                    player_index = j
                                    break
                                else:
                                    j+=1
                            kills += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["kills"]
                            deaths += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["deaths"]
                            assists += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["assists"]
                            score += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["score"]
                        # Averaging the data
                        kills = round(kills/match_count,1)
                        deaths = round(deaths/match_count,1)
                        assists = round(assists/match_count,1)
                        score = round(score / match_count,1)

                    mmr_change = 0
                    for game in MMR_json["data"]:
                        mmr_change += game["mmr_change_to_last_game"]
                    # Extracting some other data from the mmr api
                    rank=MMR_json["data"][0]["currenttierpatched"]
                    tiernum=MMR_json["data"][0]["currenttier"]
                    elo=MMR_json["data"][0]["elo"]
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

                if MH.status_code == 200:
                    item.add_field(name="KDA",value=f"{kills}|{deaths}|{assists}",inline=True)
                    item.add_field(name="Average Score",value=score,inline=True)
                    item.add_field(name="MMR change", value = mmr_change)
                elif MH.status_code == 429:
                    item.add_field(name="KDA",value=("Rate limited"),inline=True)
                else:
                    item.add_field(name="KDA",value="Something went wrong. Try again in a few minutes. If the problem persists contact a server admin",inline=True)
            
        except exceptions.TimeoutError:
            # If the user input times out
            item = discord.Embed(title="Timeout, took too long", description=f"A 30 second timeout ran out." ,color=discord.Color.red())
        except:
            # Something else broke. Should hopefully never be displayed
            item = discord.Embed(title="Something broke in a very bad way", description=f"Please send help" ,color=discord.Color.red())
            print(logging.exception(''))

    else: 
        item = discord.Embed(title="Error", description=f"Please configure a default region. use '>help settings' for more info" ,color=discord.Color.red())

    item.set_footer(text="Razebot by MaximumMaxx")
    await ctx.send(embed = item)

bot.run(bot_token)
