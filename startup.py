import discord
from discord.ext import commands
import os
import random
import requests
import json
import time

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='?', description=description)

discord_user_dict = {}

#_________________________________________________________________________________________________________________________

# def get_match(match_id):
# 	url = "https://api.opendota.com/api/matches/" + match_id

# 	response = requests.request("GET", url, timeout=None)
	
# 	if(response.status_code != 200):
# 		print("Broken get match!")
# 		return None

# 	result = json.loads(response.text)

# 	return result

#_________________________________________________________________________________________________________________________

def get_word_cloud(player_id):
	url = "https://api.opendota.com/api/players/" + player_id + "/wordcloud"
	response = requests.request("GET", url, timeout=None)
	if(response.status_code != 200):
		print("Broken word cloud!")
		return None

	result = json.loads(response.text)

	return result

#_________________________________________________________________________________________________________________________

def get_ward_count(player_id):
	url = "https://api.opendota.com/api/players/" + player_id + "/totals"
	response = requests.request("GET", url, timeout=None)
	if(response.status_code != 200):
		print("Broken word cloud!")
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

#_________________________________________________________________________________________________________________________

def load_user_info():
	with open("user_info.txt") as file_in:
		lines = []
		for line in file_in:
			discord_user_dict[int(line.split(':')[0])] = line.split(':')[1]

#_________________________________________________________________________________________________________________________

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    load_user_info()

#_________________________________________________________________________________________________________________________

# @bot.command()
# async def match(ctx: int, match_id: str):
#     """Returns match history"""
#     data = get_match(match_id)

#     chat_log = [x["key"] for x in data["chat"] if x["type"] == "chat"]

#     await ctx.send(chat_log)   

#_________________________________________________________________________________________________________________________

@bot.command()
async def wordcloud(ctx: int, discord_user: discord.User):
    """Returns most used words"""
    data = get_word_cloud(discord_user_dict[discord_user.id])

    word_list = []
    for word, count in data["my_word_counts"].items(): 
        if (count > 10):
            word_list.append(word)
        
    await ctx.send(word_list)  
    
#_________________________________________________________________________________________________________________________

@bot.command()
async def wardcount(ctx: int, discord_user: discord.User):
    """Returns most used words"""
    data = get_ward_count(discord_user_dict[discord_user.id])

    count = [x["sum"] for x in data if x["field"] == "purchase_ward_observer"][0]
    count += [x["sum"] for x in data if x["field"] == "purchase_ward_sentry"][0]
        
    await ctx.send(discord_user.mention + " has placed a total of " + str(count) + " wards in Dota")  

#_________________________________________________________________________________________________________________________

# @bot.command()
# async def updateherolist(ctx: int):
#     """Updates the list of heroes"""
#     File_object = open("hero_info.txt","w")

#     hero_list = update_hero_list()

#     File_object.write(json.dumps(hero_list))

#_________________________________________________________________________________________________________________________

@bot.command()
async def connect(ctx: int, user_id: str):
	"""Link Discord User to OpenDota profile"""	
	if user_id not in discord_user_dict.values():
		with open("user_info.txt", "a") as myfile:
			myfile.write(str(ctx.message.author.id) + ":" + user_id + ":\n")
		discord_user_dict[ctx.message.author.id] = user_id

#_________________________________________________________________________________________________________________________
		

#_________________________________________________________________________________________________________________________

# @bot.command()
# async def roll(ctx, dice: str):
#     """Rolls a dice in NdN format."""
#     try:
#         rolls, limit = map(int, dice.split('d'))
#     except Exception:
#         await ctx.send('Format has to be in NdN!')
#         return

#     result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
#     await ctx.send(result)

#_________________________________________________________________________________________________________________________

# @bot.group()
# async def cool(ctx):
#     """Says if a user is cool.

#     In reality this just checks if a subcommand is being invoked.
#     """
#     if ctx.invoked_subcommand is None:
#         await ctx.send('No, {0.subcommand_passed} is not cool'.format(ctx))

# #_________________________________________________________________________________________________________________________

# @cool.command(name='bot')
# async def _bot(ctx):
#     """Is the bot cool?"""
#     await ctx.send('Yes, the bot is cool.')

#_________________________________________________________________________________________________________________________

bot.run(os.environ['DISCORD_TOKEN'])