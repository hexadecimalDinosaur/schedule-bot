import discord
import json

data = {}
with open("data.json") as f:
    data = json.load(f)

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith('$ping'):
        await message.channel.send('Pong! {0}ms'.format(int(client.latency*1000)))
    
    elif message.content.startswith('$schedule'):
        if str(message.author) in list(data['users'].keys()):
            output = ""
            output += "**"+str(message.author)+"'s Courses:**\n"
            for i in data['users'][str(message.author)]['courses']:
                output += str(i+" - "+data["courses"][i]["teacher"])
                output += "\n"
            await message.channel.send(output)
            

client.run('TOKEN')
