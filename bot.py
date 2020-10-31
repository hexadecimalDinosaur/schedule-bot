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
        await message.channel.send('<:ping_pong:772097617932320768> Pong! `{0}ms`'.format(int(client.latency*1000)))
    
    elif message.content.startswith('$schedule'):
        if str(message.author) in list(data['users'].keys()) and len(data['users'][str(message.author)]['courses']) > 0:
            quads = ["","","",""]
            for i in data['users'][str(message.author)]['courses']:
                quads[data["courses"][i]["quad"]-1] += str(i+" - "+data["courses"][i]["teacher"]+"\n")
            embed=discord.Embed()
            embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
            for i in range(4):
                if len(quads[i]) > 0:
                    embed.add_field(name="Quad "+str(i+1), value=quads[i])
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("**" + str(message.author)+"** does not have their courses added to the bot")
    
    elif message.content.startswith('$list'):
        output = ""
        for i in sorted(list(data['courses'].keys())):
            output += i
            if data['courses'][i]['teacher']:
                output += " ("+data['courses'][i]['teacher']+")"
            output += "\n"
        
        embed = discord.Embed(title="Courses", description=output)
        embed.set_footer(text="Use the $join command to join a course")
        await message.channel.send(embed=embed)
            

client.run('TOKEN')
