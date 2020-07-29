import discord
from discord.ext import commands
import os
import random
import requests
import json
import time
import datetime
import asyncio
import os

TOKEN = os.environ['DISCORD_TOKEN']
CHANNEL_ID = 736833195286462474
NL = "\n"

bot = commands.Bot(command_prefix='?')

discord_user_dict = {}
processed_matches = set([])
dota_players = set([])

#_________________________________________________________________________________________________________________________

def log(discord_id, log_text):
	print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " :: " + bot.get_user(int(discord_id)).name + " :: "+ log_text)

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
	text_channel = bot.get_channel(CHANNEL_ID)
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

def get_recent_game(player_id):
	url = "https://api.opendota.com/api/players/"+ player_id + "/recentMatches"
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

async def wait_for_game(player_info, lobby_type=[0]):
	player_id = discord_user_dict[player_info.discord_id]
	log(player_info.discord_id, "Searching for finished game")

	refresh_player(player_id)
	await asyncio.sleep(3)
	recent_games = get_recent_game(player_id)
	most_recent_normal = None
	for game in recent_games:
		if game["lobby_type"] in lobby_type:
			if game["match_id"] not in processed_matches:
				most_recent_normal = game
				break
			else: #TODO: Fix temp code
				player_info.launch_time = 0#time.time() # reset most recent game time (for other players that loop here)

	#probably have a access issue here if a recent game cannot be found
	if most_recent_normal is not None: 
		if most_recent_normal["start_time"] > int(player_info.launch_time): 
			log(player_info.discord_id, "Found finished game: " + str(most_recent_normal["match_id"]))
			player_info.launch_time = time.time() # reset most recent game time (for first player to loop here)
			processed_matches.add(most_recent_normal["match_id"])
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
#_________________________________________________________________________________________________________________________

class id_info():
	def __init__(self, discord_id, launch_time):    
		self.discord_id = discord_id
		self.launch_time = launch_time

	def __eq__(self, other):
		return self.discord_id == other.discord_id

	def __ne__(self, other):
		return self.discord_id != other.discord_id

	def __hash__(self):
		return hash(self.discord_id)

#_________________________________________________________________________________________________________________________

async def run_search():
	while len(dota_players) > 0:
		player_set = dota_players.copy()
		for player_info in player_set:
			log(player_info.discord_id, "Begin search")
			recent_game = await wait_for_game(player_info)
			if recent_game is not None:
				match_details = await get_match(recent_game["match_id"])
				await print_game_results(match_details)
				log(player_info.discord_id, "Results sent!")
			else: 
				await asyncio.sleep(3) #let other events get through if no match is found
			log(player_info.discord_id, "End search")
			
#_________________________________________________________________________________________________________________________

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')
	load_user_info()
	game = discord.Game("League of Legends")
	await bot.change_presence(status=discord.Status.online, activity=game)

#_________________________________________________________________________________________________________________________

@bot.command()
async def g(ctx: int):
	recent_game = await wait_for_game(player_info=id_info(ctx.author.id, 0), lobby_type=[0,1,2,3,4,5,6,7,8,9])
	match_details = await get_match(recent_game["match_id"])
	await print_game_results(match_details)

#_________________________________________________________________________________________________________________________

@bot.command()
async def connect(ctx: int, player_id: str):
	"""Link Discord User to OpenDota profile"""	
	if player_id not in discord_user_dict.values():
		with open("user_info.txt", "a") as myfile:
			myfile.write(str(ctx.message.author.id) + ":" + player_id + ":\n")
		discord_user_dict[ctx.message.author.id] = player_id

#_________________________________________________________________________________________________________________________

loop = asyncio.get_event_loop()

@bot.event
async def on_member_update(before, after):
	if after.id in discord_user_dict.keys(): 
		log(after.id, "start om_member_update")
		if after.activity is None: 
			try:
				dota_players.remove(id_info(after.id, 0))
			except KeyError:
				pass	
		elif after.activity.name == "Dota 2":
			dota_players.add(id_info(after.id, time.time()))
			if len(dota_players) == 1:
				loop.create_task(run_search())
		log(after.id, "end om_member_update")
		                                           
#_________________________________________________________________________________________________________________________

def main():
	bot.run(TOKEN)

main()