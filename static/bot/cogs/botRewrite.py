import math
import asyncio
import time

import discord
from discord.commands import option
from discord.ext import commands
import requests
from PIL import ImageColor
import mysql.connector

from .helps import avaliable_help_menus, avaliable_settings
from .secrets import secrets
from ..Helper import CompTiers, valid_ranks


# Welcome to self land the land of self. 
class Razebot(commands.Bot):

	def __init__(self, command_prefix=">", help_command=None , **options):
		super().__init__(command_prefix=command_prefix, help_command=help_command, **options)
		self.DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
		self.cursor = self.DB.cursor()

		self.default_prefix = ">"
		self.default_region = "NA"
		self.timeout_time = 2700
		self.refresh_time = time.time() + self.timeout_time
		self.start_time = time.time()

		

	# ----------------------------------------------------------------------------------------------------------------------
	# Helper Functions
	# ----------------------------------------------------------------------------------------------------------------------

	def refresh(self):
		if time.time() > self.refresh_time:
			self.DB.close()
			self.DB = mysql.connector.connect(host=secrets["dbhost"],user=secrets["dbname"],password=secrets["dbpassword"],database=secrets["database"])
			self.cursor = self.DB.cursor()
			print("Refreshed")
		self.refresh_time = time.time()+self.timeout_time

	def CreateAccTable(self,id,type):
		# S signifies a saved accounts table. M signifys a Myaccounts table
		sql = f'''CREATE TABLE IF NOT EXISTS {type}{id} (
		`id` INT NOT NULL AUTO_INCREMENT,
		`note` VARCHAR(255) NULL,
		`ign` VARCHAR(255) NULL,
		PRIMARY KEY (`id`));
		'''
		self.cursor.execute(sql)
		# Doesn't seem to be required but I'll leave it here anyways
		self.DB.commit()

	def AddAcc(self,user, type, ign, note):
		# S signifies a saved accounts table. M signifys a Myaccounts table
		sql = f'''select * from {type}{user} where ign like '{ign}';'''
		self.cursor.execute(sql)
		RSLT = self.cursor.fetchall()
		if len(RSLT) != 0: return("duplicate")
		sql = f"secect * from {type}{user}"
		account_count = len(self.cursor.execute(sql).fetchall())
		if account_count == 25 and type=="M": return("maxed")
		else:
			# Name is not in the database
			sql = f'''INSERT INTO {type}{user} (note,ign) VALUES (%s,%s)'''
			values = (note,ign)
			self.cursor.execute(sql,values)
			self.DB.commit()
			return("sucess")


	def RmAcc(self,user, type, ign):
		# S signifies a saved accounts table. M signifys a Myaccounts table
		sql = f'''select * from {type}{user} where ign like '{ign}';'''
		self.cursor.execute(sql)
		RSLT = self.cursor.fetchall()
		if len(RSLT) != 0:
			# Name is not in the database
			sql = f'''DELETE FROM {type}{user} WHERE ign like '{ign}' '''
			self.cursor.execute(sql)
			self.DB.commit()
			return("sucess")
		else:
			return("NIDB")

	def get_acc(self,accounts, account_index):
		# Getting the actual account details
		region, acc, tag = accounts[account_index][2], accounts[account_index][1], accounts[account_index][3]
		MH= requests.get(f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{acc}/{tag}?filter=competitive")
		MMR = requests.get(f"https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{acc}/{tag}")

		kills, deaths, assists, score, mmr_change = "Unkown"

		if MMR.status_code == 200:
			MMR_json = MMR.json()
			mmr_change = 0
			for game in MMR_json["data"]:
				mmr_change += game["mmr_change_to_last_game"]
			
			rank = MMR_json["data"][0]["currenttierpatched"]
			tiernum = MMR_json["data"][0]["currenttier"]
			elo = MMR_json["data"][0]["elo"]
			image=CompTiers.json()["data"][0]["tiers"][tiernum]["largeIcon"]
			color = CompTiers.json()["data"][0]["tiers"][tiernum]["color"][:6]
			embed = discord.Embed(color=discord.Color.from_rgb(ImageColor.getcolor("#"+color,"RGB")[0],ImageColor.getcolor("#"+color,"RGB")[1],ImageColor.getcolor("#"+color,"RGB")[2]),description=f"The stats and rank for {acc}",title=acc)
			embed.add_field(name="Rank", value = rank)
			embed.add_field(name="MMR",value=elo)
		elif MMR.status_code == 204: return(discord.Embed(title="ERROR",description="Not enough recent data or wrong region",color= discord.Color.red()))
		elif MMR.status_code == 429: return(discord.Embed(title="ERROR", description="The bot has been rate limited. Please try again in a few minutes", color=discord.Color.red()))
		# Python devs be like:
		else: return(discord.embed(title="ERROR",description= "User not found", color=discord.Color.red())) if MMR.json()["message"] == "User not found" else discord.embed(title="ERROR",description= "Something went horribly wrong and we are all going to die.", color=discord.Color.red())
				
		if MH.status_code == 200:
			MH_json = MH.json()
			match_count = len(MH_json["data"])
			kills, deaths, assists, score = 0
			uuid = MH_json["puuid"]

			for i in range(match_count):
				for j in range(len(MH_json["data"][i]["players"]["all_players"])):
					if  MH_json["data"][i]["players"]["all_players"][j]["puuid"] == uuid:
						player_index = j
						break
				kills += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["kills"]
				deaths += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["deaths"]
				assists += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["assists"]
				score += MH_json["data"][i]["players"]["all_players"][player_index]["stats"]["score"]
			kills = round(kills/match_count,1)
			deaths = round(deaths/match_count,1)
			assists = round(assists/match_count,1)
			score = round(score / match_count,1)

			embed.add_field(name="Stats from the last 5 gmaes",value=f"KDA: {kills}|{deaths}|{assists} \n KDR: {kills/deaths} \n Score: {score} \n MMR Change: {mmr_change}")
		else:
			embed.add_field(name="ERROR", value="Error getting other stats. If the issue persists please contact me @ MaximumMaxx#0001")
		embed.set_image(image)
		embed.set_footer("Razebot by MaximumMaxx")
		return(embed)

	# ----------------------------------------------------------------------------------------------------------------------
	# Listeners
	# ----------------------------------------------------------------------------------------------------------------------

	@commands.Cog.listener()
	async def on_ready(self):
		print("Cog is up")


	# Setup a server's initial sql tables
	@commands.Cog.listener()
	async def on_guild_join(self,guild):
		# Settings table
		sql = f'''CREATE TABLE IF NOT EXISTS set{guild.id} (
		`id` INT NOT NULL AUTO_INCREMENT,
		`setting` VARCHAR(255) NULL UNIQUE,
		`value` VARCHAR(255) NULL,e
		PRIMARY KEY (`id`));
		'''
		self.cursor.execute(sql)

		# server role table
		sql = f'''CREATE TABLE IF NOT EXISTS rl{guild.id} (
		`id` INT NOT NULL AUTO_INCREMENT,
		`role` VARCHAR(255) NULL UNIQUE,
		`value` VARCHAR(255) NULL,
		`region` VARCHAR(255) NULL,
		PRIMARY KEY (`id`));
		'''
		self.cursor.execute(sql)

		# Creating some default settings values
		sql = f"REPLACE INTO set{guild.id} (setting,value) VALUES (prefix,{self.default_prefix})"
		self.cursor.execute(sql)
		sql = f"REPLACE INTO set{guild.id} (setting,value) VALUES (region,{self.default_region})"
		self.cursor.execute(sql)
		sql = f"REPLACE INTO set{guild.id} (setting,value) VALUES (max_self_role,None)"
		self.cursor.execute(sql)

		self.DB.commit()
		# Maybe remove before final release
		print(f"Joined a server with the id {guild.id()}")


	# Remove a server's prefix and settings data when the bot leaves the server
	@commands.Cog.listener()
	async def on_guild_leave(self,guild):
		sql = f"DROP TABLE set{guild.id()}"
		self.cursor.execute(sql)
		self.DB.commit()
		print(f"Left the server with the id {guild.id()}")


	# Print out some info when pinged
	@commands.Cog.listener()
	async def on_message(self,message):
		if self.user.mentioned_in(message) and message.mention_everyone is False:
			sql = f"SELECT * FROM set{message.guild.id}"
			self.cursor.execute(sql)
			settings = self.cursor.fetchall()

			# Converting the cursor output to a dictionary
			setDict = {}
			for i in range(len(settings)):
				setDict[settings[i][1]] = settings[i][2]

			embed = discord.Embed(title="Razebot info", description=None, color=discord.Color.red())
			embed.add_field(name="Prefix", value=setDict["prefix"])
			embed.add_field(name="Default region", value=setDict["region"])
			embed.add_field(name="Latency", value=self.latency)
			embed.add_field(name="Uptime", value=f"{round(self.start_time-time.time(),0)}s")

			
			await message.channel.send(embed=embed)

		await self.process_commands(message) # This line makes your other commands work.

	# ----------------------------------------------------------------------------------------------------------------------
	# Commands
	# ----------------------------------------------------------------------------------------------------------------------

	@commands.slash_command(name="credits")
	@commands.command()
	async def credits(self,ctx: discord.context):
		embed = discord.Embed(title = "Credits", description=None, url="https://Razebot.com/dashboard")
		embed.add_field(name="Loading Icon by",value="Krishprakash24gmail via Wikicommons under CC Atribution-sharalike 4.0 International")
		embed.add_field(name="Wrapper by",value="The Pycord development team")
		embed.add_field(name="Design inspiration from",value="Discord developer portal, Mee6, Carl-bot, and many more.", )
		embed.set_footer(text="Razebot by MaximumMaxx")
		await ctx.respond(embed=embed)


	@commands.slash_command(name="settings")
	@commands.command()
	async def settings(self, ctx: discord.context, setting: str, value: str):
		if setting == None:
			if setting.lower() in avaliable_settings:
				self.refresh()
				
				# There should already be a settings table created when the bot first joined so we can just acess it here
				sql = f"REPLACE set{ctx.author.guild.id} (setting,value) VALUES ({setting.lower()},{value})"
				self.cursor.execute(sql)
				self.DB.commit()
				embed = embed=discord.Embed(title=f"{setting} successfully updated", description=f"The changes should take effect immediately", color=discord.Color.green())
			else:
				embed = discord.Embed(title= "Invalid Setting", description=f"The avaliable settings are {avaliable_settings}", color=discord.Color.red())
		
		else:
			embed=discord.Embed(title="Avaliable settings", description=f"The avaliable help menus are {avaliable_settings}", color=discord.Color.green())
		
		embed.set_footer(text="Razebot by MaximumMaxx")
		ctx.respond(embed=embed)


	@commands.slash_command(name="set roles", description="Set the role for each VALORANT comp rank")
	@commands.command()
	async def setroles(self, ctx, role: discord.role.Role = option(name="Role",Required=True), rank: str = option(name="Valorant Rank",Required=True)):
		if rank.lower() in valid_ranks:
			self.refresh()
			# There should already be a settings table created when the bot first joined so we can just acess it here
			sql = f'''REPLACE INTO rl{ctx.author.guild.id} (role,value) VALUES ({role.name},{rank})'''            
			self.cursor.execute(sql)
			self.DB.commit()
			embed = embed=discord.Embed(title=f"{role.name} successfully updated", description=f"The changes should take effect immediately", color=discord.Color.green())

			sql = f"SELECT * FROM rl{ctx.author.guild.id}"
			self.cursor.execute(sql)
			guild_roles = self.cursor.fetchall()

			if not len(guild_roles) == len(valid_ranks):
				ctx.send(embed=discord.Embed(title="You still have some roles to add", description=f"Please rerun this command for each of the following VALORANT ranks: {[i for i in valid_ranks if i not in guild_roles[1]]}"))
		else:
			embed = discord.Embed(title= "Invalid Rank", description=f"You entered {rank} but the valid options are {valid_ranks}.", color=discord.Color.red())
	
		embed.set_footer(text="Razebot by MaximumMaxx")
		ctx.respond(embed=embed)


	@commands.slash_command(name = "update role", description = "Update your server role based on the ranks of the accounts saved in your myaccs list")
	@commands.command()
	async def updaterole(self,ctx):
		await ctx.respond("Thinking <:loading:something>")
		self.refresh()

		sql = f"SELECT * FROM rl{ctx.author.guild.id}"
		self.cursor.execute(sql)
		guild_roles = self.cursor.fetchall()
		if len(guild_roles) == len(valid_ranks): # Check if the server has rank roles configured
			
			# Convert roles into a dictionary
			roleDict = {}
			for i in range(len(guild_roles)):
				roleDict[guild_roles[i][1]] = guild_roles[i][2]

			for rank in roleDict:
				await ctx.author.remove_roles(discord.utils.get(ctx.author.guild.roles, id=int(roleDict[rank])))
			
			self.CreateAccTable(ctx.message.author.id,"M")
			sql = f"select * from M{ctx.author.id}"
			self.cursor.execute(sql)
			author_accs = self.cursor.fetchall()
			if len(author_accs) != 0: # They actually have accounts in the table
				max_rank = (-1,"")
				for account in author_accs:
					uname,tag = account[2].split('#')
					MMR = requests.get(f"https://api.henrikdev.xyz/valorant/v1/mmr/{account[3]}/{uname}/{tag}")
					# Error handling
					if MMR.status_code != 200:
						# Skip accounts that are unranked
						if MMR.status_code == 429:
							# Rate limited
							embed= discord.Embed(name="ERROR", description="Razebot has been rate limited, please try again in a few minutes")
							break
						continue
					MMR_json = MMR.json()
					rank=MMR_json["data"]["currenttierpatched"]

					if MMR_json["data"]["currenttier"] > max_rank[0]:
						max_rank = (MMR_json["data"]["currenttier"],account[2])
						# isolating the rank name
						rank = rank.split(' ')[0].lower()
				
				if max_rank[0] == -1:
					rank = "unranked"
					embed = discord.Embed(title="Warning", description="You have no valid accounts in the database. us >help myaccs for more info on adding accounts. You have been given unranked for now", color=discord.Color.gold())
				else:
					embed = discord.Embed(title="Sucess", description=f"You have been granted the role {rank} feel free to add any other accounts you may have and run this command again.", color=discord.Color.green())

			else: 
				embed = discord.Embed(name="ERROR", description="In order to use this command you need atleast one account saved with `/myaccs save`.")
				rank = "unranked"
			guild = ctx.guild
			role = discord.utils.get(guild.roles, id=int(roleDict[rank]))
			await ctx.author.add_roles(role)

		else: embed = discord.Embed(name="ERROR", description="Please configure your rank roles using /setroles", color = discord.Color.red())

		embed.set_footer(text="Razebot by MaximumMaxx")
		msg = await ctx.interaction.original_message()  #gets the message from response
		await msg.edit(embed=embed,content= None) #edits message from response


	@commands.slash_command(name = "myaccs", description = "Interact with the list of your account (accounts you actually own).")
	@commands.command()
	async def myaccs(self,ctx, 
	operation: str = option(name="operation",Required=True), 
	account: str = option(name="account",Required=False, description = "Formatted as name#tag"),
	region: str = option(name="region",Required=False),
	note: str = option(name="note",Required=False, description = "short note (255 characters)")):
		
		account = account or None

		self.CreateAccTable(ctx.message.author.id, "M")
		account,tag = account.split("#") if account != None else None
		note = note or None
		region = region or None

		if operation.lower() == "list":
			self.refresh()
			sql = f"SELECT * FROM M{ctx.message.author.id}"
			self.cursor.execute(sql)
			author_accs = self.cursor.fetchall()

			if len(author_accs) == 0:
				embed = discord.Embed(title="ERROR",description="You have not accounts to list. Use /myaccs to add an account" ,color=discord.Color.red())
			else:
				embed=discord.Embed(title="Your Accounts", color=discord.Color.dark_red())
				for account in author_accs:
					embed.add_field(name=account[2],value=account[1])
		
		elif operation.lower() == "add":


			if region != None:
				if account != None:
					if note == None: note= "No note"
					returned = self.AddAcc(ctx.message.author.id,"M",f"{account}#{tag}",note)
					if returned == "duplicate": embed= discord.Embed(title="ERROR", description="That account has already been saved by you", color=discord.Color.red())
					elif returned == "maxed": embed = discord.Embed(title="ERROR", description="Listen man, you have 25 accounts saved. there is no reason you should have that many accounts. You should seriously reconsider whatever life decisions brought you here. Sorry but this is an intervention. If you got here by adding a bunch of other accounts then you're using this wrong. Alrigt rant over, have a good night or afternoon or day or whatever.",  color=discord.Color.red())
					elif returned == "sucess": embed = discord.Embed(title="Sucess", description="Your account has successfully been added to the database", color=discord.Color.green())

				else: embed=discord.Embed(title="Error", description = "Please specify a VALORANT account",color=discord.Color.red())

			else:embed=discord.Embed(title="Error", description = "Please specify a region",color=discord.Color.red())

		elif operation.lower() == "remove" or operation.lower() == "delete":
			returned = self.RmAcc(ctx.message.author.id,"M",f"{account}#{tag}")
			if returned == "sucess": embed = discord.Embed(title="Sucess", description="You account has successfully been removed from the database", color=discord.Color.green())
			elif returned == "NIDB": embed= discord.Embed(title="ERROR", description="That account isn't in the database. You likely misspelled something", color=discord.Color.red())

		embed.set_footer(text="Razebot by MaximumMaxx")
		ctx.respond(embed=embed)


	@commands.slash_command(name="quick accounts", description = "Used to interact with the quick accounts database")
	@commands.command()
	# More or less a 1 - 1 copy of myaccs
	async def quickaccs(self,ctx,
	operation: str = option(name="operation",Required=True), 
	account: str = option(name="account",Required=False, description = "Formatted as name#tag"),
	region: str = option(name="region",Required=False),
	note: str = option(name="note",Required=False, description = "short note (255 characters)")):
		
		account = account or None

		self.CreateAccTable(ctx.message.author.id, "Q")
		account,tag = account.split("#") if account != None else None
		note = note or None
		region = region or None

		if operation.lower() == "list":
			self.refresh()
			sql = f"SELECT * FROM Q{ctx.message.author.id}"
			self.cursor.execute(sql)
			author_accs = self.cursor.fetchall()

			if len(author_accs) == 0:
				embed = discord.Embed(title="ERROR",description="You have not accounts to list. Use /quickaccs to add an account" ,color=discord.Color.red())
			else:
				embed=discord.Embed(title="Your Quick Accounts", color=discord.Color.dark_red())
				for account in author_accs:
					embed.add_field(name=account[2],value=account[1])
		
		elif operation.lower() == "add":


			if region != None:
				if account != None:
					if note == None: note= "No note"
					returned = self.AddAcc(ctx.message.author.id,"Q",f"{account}#{tag}",note)
					if returned == "duplicate": embed= discord.Embed(title="ERROR", description="That account has already been saved by you", color=discord.Color.red())
					elif returned == "sucess": embed = discord.Embed(title="Sucess", description="Your account has successfully been added to the database", color=discord.Color.green())

				else: embed=discord.Embed(title="Error", description = "Please specify a VALORANT account",color=discord.Color.red())

			else:embed=discord.Embed(title="Error", description = "Please specify a region",color=discord.Color.red())

		elif operation.lower() == "remove" or operation.lower() == "delete":
			returned = self.RmAcc(ctx.message.author.id,"Q",f"{account}#{tag}")
			if returned == "sucess": embed = discord.Embed(title="Sucess", description="You account has successfully been removed from the database", color=discord.Color.green())
			elif returned == "NIDB": embed= discord.Embed(title="ERROR", description="That account isn't in the database. You likely misspelled something", color=discord.Color.red())

		embed.set_footer(text="Razebot by MaximumMaxx")
		ctx.respond(embed=embed)


	@commands.slash_command(name="help",description = "Outputs a short description of how a command works and links to Razebot.com for further reading.")
	@commands.command()
	async def help(self,ctx,setting: str = option(avaliable_help_menus,None,required=False)):
		setting = setting or None

		if setting != None:
			if setting in avaliable_help_menus:
				embed = discord.Embed(title = avaliable_help_menus[setting][1], description = avaliable_help_menus[setting][2], color = discord.Color.dark_green())
				image = avaliable_help_menus[setting][0]
			else:
				image = "https://lh3.googleusercontent.com/proxy/_c_wrpevgis34jEBvd9uRPxYueZbavIRTtU9zNuZJ-FMRw-yo8XHX6n-tSeiJc7ZipzFB3snxw35LnIwCVrxku3cpoMAY1U"
				embed =  embed = discord.Embed(title="Setting not found", description=f"/help for a general list of help menus" ,color=discord.Color.red())
		else:
			# Return the default help menu
			embed = discord.Embed(title = "List of help menus",description = f"Current help menus: /help rc, /help myaccs, /help quickaccs, /help updaterole, /help quick vs myaccs, /help settings, /help setroles")
			image = "https://github.com/MaximumMaxxx/Razebot/blob/main/assets/Valobot%20logo%20raze%20thicckened.png?raw=true"

		embed.set_thumbnail(url=image)
		embed.set_footer(text="Razebot by MaximumMaxx")
		await ctx.respond(embed = embed)


	@commands.command( name="rclist", description = "Check the Rank of an account from either your Quick accounts or My accounts list")
	@commands.slash_command( name="Rank Check List", description = "Check the Rank of an account from either your Quick accounts or My accounts list")
	async def rclist(self, ctx, list: str = option(name="List", description = "The list that you want to pull the accounts from. (my | quick)", Required=True)):
		self.refresh()
		list = list.lower()
		operation = ""
		if list == "quick": operation = "Q"
		elif list == "my": operation = "M"
		else: 
			embed = discord.Embed(title="ERROR", description="Please provide a valid list type")
			embed.set_footer(text="Razebot by MaximumMaxx")
			ctx.respond(embed=  embed)
			return
		
		accounts = self.cursor.execute(f"SELECT * FROM {operation}{ctx.message.author.id}").fetchall()
		# 5 accounts per page with a left and right arrow
		page = 1
		max_page_count = math.ceil(len(accounts)/5)
		
		embed=discord.Embed(title=f"Your {list}accounts list", color=discord.Color.red(), description=None)
		embed.set_footer(text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
		await ctx.respond( embed=embed)
		message = await ctx.interaction.original_message()
		# getting the message object for editing and reacting

		await message.add_reaction("◀️")
		# Just a bunch of unicode recycling signs rn
		await message.add_reaction("\u2673") 
		await message.add_reaction("\u2674") 
		await message.add_reaction("\u2675")
		await message.add_reaction("\u2676")
		await message.add_reaction("\u2677")
		await message.add_reaction("▶️")
		number_reactions = ["\u2673","\u2674","\u2675","\u2676","\u2677"]

		def check(reaction, user):
			return user == ctx.author
			# This makes sure nobody except the command sender can interact with the "menu"


		# Getting which account the user wants
		while True:
			try:
				reaction, user = await self.wait_for("reaction_add", timeout=60, check=check)
				# waiting for a reaction to be added - times out after x seconds, 60 in this
				# example

				if str(reaction.emoji) == "▶️" and page != max_page_count:
					page += 1
					embed=discord.Embed(title=f"Your {list}accounts list", color=discord.Color.red(), description=None)
					embed.set_footer(text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
					for i in range(5):
						j = page*5 + i
						if not j > len(accounts):
							embed.add_field(embed.add_field(name=f"{j+1}) {accounts[j][2]}",value=accounts[j][1]))
					await message.edit(embed=embed)
					await message.remove_reaction(reaction, user)

				elif str(reaction.emoji) == "◀️" and page > 1:
					page -= 1
					embed=discord.Embed(title=f"Your {list}accounts list", color=discord.Color.red(), description=None)
					embed.set_footer(text=f"Page {page} / {max_page_count} \n Razebot by MaximumMaxx")
					for i in range(5):
						j = page*5 + i
						if not j > len(accounts):
							embed.add_field(embed.add_field(name=f"{j+1}) {accounts[j][2]}",value=accounts[j][1]))
					await message.edit(embed=embed)
					await message.remove_reaction(reaction, user)
				
				elif str(reaction.emoji) in number_reactions:
					account_index = page*5 + number_reactions.index(str(reaction.emoji))
					if account_index > len(accounts):
						await message.remove_reaction(reaction, user)
					else:
						break


				else:
					await message.remove_reaction(reaction, user)
					# removes reactions if the user tries to go forward on the last page or
					# backwards on the first page
			except asyncio.TimeoutError:
				embed=discord.Embed(title=f"ERROR", color=discord.Color.red(), description="Your time to select an items has timed out. Please try again.")
				embed.set_footer(text="Razebot by MaximumMaxx")
				await message.edit(embed=embed)
				return
				# ending the loop if user doesn't react after x seconds
		ctx.respond(embed=self.get_acc(accounts,account_index))


	@commands.command(name = "rcacc", description = "Get the stats for a specific VALORANT account")
	@commands.slash_command(name = "Rank Check Account", description = "Get the stats for a specific VALORANT account")
	async def rcacc(self, ctx, account: str = option(name="Account", description = "The VALORANT account you would like to check the rank of"), region: str = option(name="Region",description = f"The region the account is in. If not specified will default to the server's default region.")):
		# The formatting is a little wack but it does the thing hopefully and it's one line so I'll take the jank
		# Accounts is expected to be a list of tuples but you can just pass in a one item list and 0 and it acomplishes the same thing
		ctx.respond(embed=self.get_acc([(None,account,None,region)],0))