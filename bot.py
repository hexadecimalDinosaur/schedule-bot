import discord
import json
import datetime

def getDay(year,month,day):
    date = datetime.datetime(year,month,day)
    exclude = set(['2020-10-12','2020-11-20','2020-12-21','2020-12-22','2020-12-23','2020-12-24','2020-12-25','2020-12-28','2020-12-29','2020-12-30','2020-12-31','2021-01-01','2021-02-05','2021-02-12','2021-02-15','2021-03-15','2021-03-16','2021-03-17','2021-03-18','2021-03-19','2021-04-02','2021-04-05','2021-05-24','2021-06-29','2021-07-01'])
    if date.strftime("%a") == "Sun" or date.strftime("%a") == "Sat":
        return "weekend"
    if date.strftime("%Y-%m-%d") in exclude:
        return "holiday"
    quad1 = datetime.datetime(2020,9,17)
    quad2 = datetime.datetime(2020,11,23)
    quad3 = datetime.datetime(2021,2,8)
    quad4 = datetime.datetime(2021,4,23)
    start = None
    day = 4
    if date > quad4:
        start = quad4
    elif date > quad3:
        start = quad3
    elif date > quad2:
        start = quad2
    elif date > quad1:
        start = quad1
    while True:
        if start.strftime("%Y-%m-%d") in exclude:
            start += datetime.timedelta(days=1)
            continue
        if start.strftime("%a") == "Sun" or start.strftime("%a") == "Sat":
            start += datetime.timedelta(days=1)
            continue
        day += 1
        if day == 5: day = 1
        if start == date:
            return day
        start += datetime.timedelta(days=1)

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
            embed=discord.Embed(color=0x0160a7)
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
        
        embed = discord.Embed(title="Courses", description=output, color=0x0160a7)
        embed.set_footer(text="Use the $join command to join a course")
        await message.channel.send(embed=embed)
            

client.run('TOKEN')
