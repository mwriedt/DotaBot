import discord
from discord.ext import commands
import os
import random
import requests
import json
import time
import datetime
import asyncio

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='?', description=description)

NL = "\n"

discord_user_dict = {}

user_playing = False;

#_________________________________________________________________________________________________________________________

def log(id, text):
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " :: " + bot.get_user(id).name + " :: "+ text)

#_________________________________________________________________________________________________________________________

def bold(text):
    return "**" + text + "**"

#_________________________________________________________________________________________________________________________

def italics(text):
    return "_" + text + "_"

#_________________________________________________________________________________________________________________________

def underline(text):
    return "__" + text + "__"

#_________________________________________________________________________________________________________________________

async def get_match(match_id):
	url = "https://api.opendota.com/api/matches/" + str(match_id)
	response = requests.request("GET", url, timeout=None)
	if(response.status_code != 200):
		print("Broken get match!")
		return None
	result = json.loads(response.text)
	return result

#_________________________________________________________________________________________________________________________

def refresh_player(player_id):
	url = "https://api.opendota.com/api/players/" + player_id + "/refresh"
	response = requests.request("POST", url, timeout=None)
	if(response.status_code != 200):
		print("Broken refresh!")

#_________________________________________________________________________________________________________________________

async def print_game_results(match_details):
	discord_users = list(discord_user_dict.keys())
	dota_users = list(discord_user_dict.values())
	text_channel = bot.get_channel(736833195286462474)
	most_kills = -1
	most_deaths = -1
	most_assists = -1

	for player in match_details["players"]:
		try:
			user_index = dota_users.index(str(player["account_id"]))
			discord_user = discord_users[user_index]
		except ValueError:
			continue

		team_radiant = player["isRadiant"]
		if player["kills"] > most_kills:
			most_kills = player["kills"]
			most_kills_player = discord_user

		if player["deaths"] > most_deaths:
			most_deaths = player["deaths"]
			most_deaths_player = discord_user

		if player["assists"] > most_assists:
			most_assists = player["assists"]
			most_assists_player = discord_user		

			#record player stats here			
	bot_message = ""

	if team_radiant == match_details["radiant_win"]: 
		bot_message += bold("WINNER WINNER CHICKEN DINNER") + NL
	else:
		bot_message += bold("Losers") + NL

	bot_message += bot.get_user(most_kills_player).mention + " had the most kills with " + str(most_kills) + NL
	bot_message += bot.get_user(most_deaths_player).mention + " had the most deaths with " + str(most_deaths) + NL
	bot_message += bot.get_user(most_assists_player).mention + " had the most assists with " + str(most_assists) + NL

	await text_channel.send(bot_message)

#_________________________________________________________________________________________________________________________

def get_recent_game(open_dota_id):
	url = "https://api.opendota.com/api/players/"+ open_dota_id + "/recentMatches"
	response = requests.request("GET", url, timeout=None)
	if(response.status_code != 200):
		print("Broken recent games!")
		return None

	result = json.loads(response.text)

	return result

#_________________________________________________________________________________________________________________________

# def update_hero_list():
# 	url = "https://api.opendota.com/api/heroes"

# 	response = requests.request("GET", url, timeout=None)
	
# 	if(response.status_code != 200):
# 		print("Broken hero list!")
# 		return None

# 	result = json.loads(response.text)

# 	return result   

async def wait_for_game(discord_id, game_start):
	player_id = discord_user_dict[discord_id]
	log(discord_id, "Searching for finished game")

	refresh_player(player_id)
	# time.sleep(0)
	recent_games = get_recent_game(player_id)
	for game in recent_games:
		# if game["lobby_type"] == 0:
		most_recent_normal = game
		break

	if most_recent_normal["start_time"] > int(game_start): 
		log(player_id, "Found finished game: " + most_recent_normal["match_id"])
		return most_recent_normal

#_________________________________________________________________________________________________________________________

def load_user_info():
	with open("user_info.txt") as file_in:
		lines = []
		for line in file_in:
			discord_user_dict[int(line.split(':')[0])] = line.split(':')[1]
	
#_________________________________________________________________________________________________________________________

# @bot.command()
# async def updateherolist(ctx: int):
#     """Updates the list of heroes"""
#     File_object = open("hero_info.txt","w")

#     hero_list = update_hero_list()

#     File_object.write(json.dumps(hero_list))

class SearchMachine():
	discord_id_list = set([])

	def add_id(self, discord_id):
		log(discord_id, "Launched Dota 2")
		self.discord_id_list.add(discord_id)

	def remove_id(self, discord_id):
		try:
			log(discord_id, "Not Playing Dota 2")
			self.discord_id_list.remove(discord_id)
		except KeyError:
			pass

	async def run(self, launch_time):
		while(len(self.discord_id_list) > 0):
			print("Run Loop 1")
			for discord_id in self.discord_id_list:
				log(discord_id, "Run Loop 2")
				recent_game = await wait_for_game(discord_id, launch_time)
				if recent_game is not None:
					match_details = await get_match(recent_game["match_id"])
					await print_game_results(match_details)
					log(after.id, "Results sent!")
#_________________________________________________________________________________________________________________________

search_machine_instance = SearchMachine()

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	load_user_info()
	

#_________________________________________________________________________________________________________________________
@bot.command()
async def g(ctx: int):
	recent_game = await wait_for_game(ctx.author.id, time.time())
	match_details = await get_match(recent_game["match_id"])
	await print_game_results(match_details)

#_________________________________________________________________________________________________________________________

@bot.command()
async def connect(ctx: int, user_id: str):
	"""Link Discord User to OpenDota profile"""	
	if user_id not in discord_user_dict.values():
		with open("user_info.txt", "a") as myfile:
			myfile.write(str(ctx.message.author.id) + ":" + user_id + ":\n")
		discord_user_dict[ctx.message.author.id] = user_id

#_________________________________________________________________________________________________________________________


@bot.event
async def on_member_update(before, after):
#should pass the time this is called into here, so when I look at the recent matches from dota I can 
# find one that has a game time greater than this, when I do find a game, I reset this time incase they play another game
	if after.id in discord_user_dict.keys(): 
		if after.activity is None: 
			search_machine_instance.remove_id(after.id)
		elif after.activity.name == "Dota 2":
			search_machine_instance.add_id(after.id)
			if len(search_machine_instance.discord_id_list) == 1:
				asyncio.run(await search_machine_instance.run(time.time()))
	print("End event")
		                                           
#_________________________________________________________________________________________________________________________

def main():
	bot.run(os.environ['DISCORD_TOKEN'])
	search_machine_instance.run()

asyncio.run(main())