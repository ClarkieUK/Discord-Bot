# Imports 
from cProfile import label
from riotwatcher import LolWatcher, RiotWatcher
import riotwatcher
from unittest import result
from urllib import response
import requests
import discord
from discord.ext import commands 
from discord.ui import Button , View



# Intents for the bot
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='$', intents=intents)


# Token Setup
DISCORD_Token = "DISCORD BOT TOKEN" 
RIOT_Token = "RIOT API TOKEN" 
iconURL = "http://ddragon.leagueoflegends.com/cdn/12.18.1/img/champion/"
championsURL = "http://ddragon.leagueoflegends.com/cdn/12.18.1/data/en_US/champion.json"
RIOT_Watcher = LolWatcher(RIOT_Token) 
RIOT_Platform = "EUW1"


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


def cookedName(rawName):
    """ Sanitizes the input that the user will give and makes sure Cl a r kie -> Clarkie

    Args:
        rawName tuple: Passed in discord after the bot function is called

    Returns:
        result : string that is a complete single name for use in data display.
    """
    result = ""

    for char in rawName:
        result = result + " " + str(char)

    return result

def summonerPull(name):
    """calls the riot api for summoners, we only care about EUW so we hardcode that in with no options,
    we call a response to the from riot with our summoner name that was inputed and our token which is required 
    to access the data, we call the LolWatcher.summoner function which relates to a platform ID on the riot API and 
    helps us obtain all the data of our named player in the form of a data dictionary so we can break it down.

    Args:
        name name: this takes the fully sanitized name that went through the cookedName function.

    Returns:
        a series of strings or images : all for use in our later call of this information in the "description stage"
    """

    summoner = RIOT_Watcher.summoner.by_name(RIOT_Platform,name)
    s_Name = summoner['name']
    s_Level = "Lvl. " + str(summoner['summonerLevel'])
    s_Icon = "http://ddragon.leagueoflegends.com/cdn/12.13.1/img/profileicon/" + str(summoner['profileIconId']) + ".png"
    s_EncryptedId = summoner['id']
    print(s_EncryptedId)


    return (s_Name, s_Level, s_Icon, s_EncryptedId)

def masteryPull(name):

    summoner = summonerPull(name)

    champions = []
    ids, levels, points, names, imgs = [], [], [], [], []


    summonerChamps = RIOT_Watcher.champion_mastery.by_summoner(RIOT_Platform,summoner[3])

    for champion in summonerChamps:
        ids.append(champion['championId'])
        levels.append(champion['championLevel'])
        points.append(champion['championPoints'])

    for index in range (1,len(points)) :     # sort all my points , ids , and mastery levels through an insertion sort 
        currentvalue = points[index]
        position = index

        while position > 0 and points[position] > currentvalue :
            points[position] = points[position-1]
            ids[position],ids[position-1] = ids[position-1],ids[position]
            levels[position],levels[position-1] = levels[position-1],levels[position]   # try casting in the morning!

            position -=1

        points[position] = currentvalue

    champions_db = requests.get(championsURL).json()  

    [champions.append(champion) for champion in champions_db['data']]   

    #when wantedkey = key append 
 
    for championId in ids:
        for name in champions:
            wantedChampion = champions_db['data'][name]['key']             
            if int(wantedChampion) == int(championId): # one is str, one is int               
                names.append(name)
                imgs.append(iconURL + name + ".png")
          


    return [names, points, levels, imgs]

def ranksPull(summoner):


    summonerData = RIOT_Watcher.league.by_summoner(RIOT_Platform,summoner[3])

    calls = {0:"queueType", 1:"tier", 2:"rank", 3:"leaguePoints", 4:"wins", 5:"losses"}
    ranks = []
    try:
        for i in range(3):
            for j in range(6):
                ranks.append(summonerData[i][calls[j]])
    except:
        pass
    return ranks

def rotationPull():
    
    rotation = RIOT_Watcher.champion.rotations(RIOT_Platform)

    champions = []
    rotation_ids, names, imgs = [], [], []


    rotation_ids.append(rotation['freeChampionIds'])

    champions_db = requests.get(championsURL).json()  

    for champion in champions_db['data'] :
        champions.append(champion)

    for championId in rotation_ids:
        for name in champions:
            wantedChampion = champions_db['data'][name]['key']        
            for x in championId :
                if int(wantedChampion) == int(x): # one is str, one is int               
                    names.append(name)
                    imgs.append(iconURL + name + ".png")


    return [rotation_ids,names, imgs]


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


@bot.command()
async def profile(ctx, *rawName):
    """This displays the formatted information to our user in discord, the summoner[n] corresponds to the list we returned in the datapull we did earlier.

    Args:
        ctx (_type_): When typing the keyword into discord, it will check the function and the input it recieves after the initial command, so "info" in this case
    """

    name = cookedName(rawName)
    summoner = summonerPull(name)
    summonerRank = ranksPull(summoner)

    embed = discord.Embed(title=summoner[0], description=(summoner[1]), color=0xff91f8)
    embed.set_thumbnail(url=summoner[2])

    try:
        tmp = f"{summonerRank[1]} {summonerRank[2]} • LP:{summonerRank[3]} • Wins: {summonerRank[4]} • Losses: {summonerRank[5]}"
        embed.add_field(name=summonerRank[0], value=tmp, inline=False)
    except:
        embed.add_field(name="Not found", value="Player hasn't any ranked status.", inline=False)
    
    # solo duo
    try:
        tmp = f"{summonerRank[7]} {summonerRank[8]} • LP:{summonerRank[9]} • Wins: {summonerRank[10]} • Losses: {summonerRank[11]}"
        embed.add_field(name=summonerRank[6], value=tmp, inline=False)
    except:
        embed.add_field(name="Not found", value="Player hasn't any ranked status.", inline=False)
    
    # tft
    try:
        tmp = f"{summonerRank[13]} {summonerRank[14]} • LP:{summonerRank[15]} • Wins: {summonerRank[16]} • Losses: {summonerRank[17]}"
        embed.add_field(name=summonerRank[12], value=tmp, inline=False)
    except:
        embed.add_field(name="Not found", value="Player hasn't any ranked status.", inline=False)

    await ctx.send(embed=embed)

# Displays the most played champions of the summoner
@bot.command()
async def mastery(ctx, *rawName):
    
    name = cookedName(rawName)
    championsMastery = masteryPull(name)

    for i in range(len(championsMastery)-1) :
        tmp = f"• Points: {str(championsMastery[1][i])[:-3]} K\n• Level Mastery: {championsMastery[2][i]}" 
        embed = discord.Embed(title=championsMastery[0][i], description=tmp, color=0xff91f8)
        embed.set_thumbnail(url=championsMastery[3][i])
        await ctx.send(embed=embed)

@bot.command()
async def rotation(ctx):


    rotation = rotationPull()

    for i in range(len(rotation[1])-1) :
        embed = discord.Embed(title=rotation[1][i], description=None, color=0xff91f8)
        embed.set_thumbnail(url=rotation[2][i])
        await ctx.send(embed=embed)

# Verifies good bot launch
@bot.command()
async def clash(ctx, *rawName):

    name = cookedName(rawName) 

@bot.command()
async def button(ctx) :
    button1 = Button(style = discord.ButtonStyle.red,emoji="😎")
    button2 = Button(style = discord.ButtonStyle.red,emoji="🐱")
    button3 = Button(style = discord.ButtonStyle.red,emoji="✔")
    button4 = Button(style = discord.ButtonStyle.red,emoji="😒")
    view = View()
    view.add_item(button1)
    view.add_item(button2)
    view.add_item(button3)
    view.add_item(button4)
    await ctx.send("Test",view=view)


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#


# Runs the bot
bot.run(DISCORD_Token)


#