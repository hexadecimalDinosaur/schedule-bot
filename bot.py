import discord
import json
import datetime

def getDay(year,month,day):
    date = datetime.datetime(year,month,day)
    exclude = set(['2020-10-12','2020-11-20','2020-12-21','2020-12-22','2020-12-23','2020-12-24','2020-12-25','2020-12-28','2020-12-29','2020-12-30','2020-12-31','2021-01-01','2021-02-05','2021-02-12','2021-02-15','2021-03-15','2021-03-16','2021-03-17','2021-03-18','2021-03-19','2021-04-02','2021-04-05','2021-05-24','2021-06-29','2021-07-01'])
    if date >= datetime.datetime(2021,7,1):
        return "end"
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
    if date >= quad4:
        start = quad4
    elif date >= quad3:
        start = quad3
    elif date >= quad2:
        start = quad2
    elif date >= quad1:
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

def getQuad(year,month,day):
    quad1 = datetime.datetime(2020,9,17)
    quad2 = datetime.datetime(2020,11,23)
    quad3 = datetime.datetime(2021,2,8)
    quad4 = datetime.datetime(2021,4,23)
    date = datetime.datetime(year,month,day)
    if date >= quad4:
        return 4
    elif date >= quad3:
        return 3
    elif date >= quad2:
        return 2
    elif date >= quad1:
        return 1

data = {}
with open("data.json") as f:
    data = json.load(f)

def updateFile():
    with open("data.json",'w') as f:
        json.dump(data,f, indent=4)

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.lower().startswith('$ping'):
        await message.channel.send('<:ping_pong:772097617932320768> Pong! `{0}ms`'.format(int(client.latency*1000)))
    
    elif message.content.lower().startswith('$about'):
        embed=discord.Embed(title="Schedule Bot", url="https://github.com/UserBlackBox/schedule-bot", description="Discord bot for timetable information based on the TDSB 2020 quadmester model", color=0x0160a7)
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/771927466267770910/700c2fe2da53caf2a60041e7d2bf21b4.png?size=2048")
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('$help'):
        helpMessage = "`$list` - list all joinable courses\n`$join [code]` - add a course to your schedule\n`$leave [code]` - remove a course from your schedule\n`$courses` - view your courses\n`$schedule` - view your schedule for today\n`$schedule YYYY/MM/DD` - view your schedule on a specific day"
        embed=discord.Embed(title="Commands", description=helpMessage, color=0x0160a7)
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('$courses'):
        if str(message.author.id) in list(data['users'].keys()) and len(data['users'][str(message.author.id)]['courses']) > 0:
            quads = ["","","",""]
            for i in data['users'][str(message.author.id)]['courses']:
                quads[data["courses"][i]["quad"]-1] += str(i+" - "+data["courses"][i]["teacher"]+"\n")
            embed=discord.Embed(color=0x0160a7)
            embed.set_author(name=str(message.author), icon_url=message.author.avatar_url)
            for i in range(4):
                if len(quads[i]) > 0:
                    embed.add_field(name="Quad "+str(i+1), value=quads[i])
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("**" + str(message.author)+"** does not have their courses added to the bot")
    
    elif message.content.lower().startswith('$list'):
        output = ""
        for i in sorted(list(data['courses'].keys())):
            output += i
            if data['courses'][i]['teacher']:
                output += " ("+data['courses'][i]['teacher']+")"
            output += "\n"
        
        embed = discord.Embed(title="Courses", description=output, color=0x0160a7)
        embed.set_footer(text="Use the $join command to join a course\nIf your course is not in this list contact an admin")
        await message.channel.send(embed=embed)
    
    elif message.content.lower().startswith('$join'):
        content = message.content.split()
        if len(content) < 2:
            await message.channel.send("Please specify a course to join")
        elif content[1].upper() not in set(data['courses'].keys()):
            await message.channel.send("Please specify a course in the course list which can be viewed with `$list`. If your course is not there contact an admin")
        else:
            if str(message.author.id) not in set(data['users'].keys()):
                data['users'][str(message.author.id)] = {}
                data['users'][str(message.author.id)]['courses'] = []
            if content[1].upper() in set(data['users'][str(message.author.id)]['courses']):
                await message.channel.send(str(message.author)+" is already in "+content[1].upper())
                return
            data['users'][str(message.author.id)]['courses'].append(content[1].upper())
            updateFile()
            await message.channel.send(str(message.author)+" has been added to " + content[1].upper())
    
    elif message.content.lower().startswith('$leave'):
        content = message.content.split()
        if len(content) < 2:
            await message.channel.send("Please specify a course to leave")
        elif str(message.author.id) not in set(data['users'].keys()):
            await message.channel.send("You are not in any courses currently")
        elif len(data['users'][str(message.author.id)]['courses']) == 0:
            await message.channel.send("You are not in any courses currently")
        elif content[1].upper() not in set(data['users'][str(message.author.id)]['courses']):
            await message.chennel.send("You are not in "+content[1].upper())
        else:
            data['users'][str(message.author.id)]['courses'].remove(content[1].upper())
            updateFile()
            await message.channel.send(str(message.author)+" has left "+content[1].upper())
    
    elif message.content.lower().startswith('$schedule'):
        if str(message.author.id) not in set(data['users'].keys()):
            await message.channel.send('<@'+str(message.author.id)+'> you are not in any courses, to view a list of courses use `$list` and use `$join` to join the course')
            return
        content = message.content.split()
        date = datetime.datetime.today()
        date = [date.year,date.month,date.day]
        if len(content) > 1:
            try:
                date = datetime.datetime.strptime(content[1],'%Y-%m-%d')
                date = [date.year,date.month,date.day]
            except ValueError:
                try:
                    date = datetime.datetime.strptime(content[1],'%Y/%m/%d')
                    date = [date.year,date.month,date.day]
                except ValueError:
                    await message.channel.send("Please specify dates in `YYYY/MM/DD` or `YYYY-MM-DD`")
                    return
        quad = getQuad(date[0],date[1],date[2])
        day = getDay(date[0],date[1],date[2])
        if day == 'weekend':
            await message.channel.send("It's the weekend! No classes!")
        elif day == 'holiday':
            await message.channel.send("It's a PA day or holiday! No classes!")
        elif day == 'end':
            await message.channel.send("That date is past the end of the year")
        else:
            output = ""
            for i in data['users'][str(message.author.id)]['courses']:
                if data['courses'][i]['quad'] == quad:
                    output += i + " (" + data['courses'][i]['teacher'] + ") - "
                    if data['courses'][i]['in-school'] == day:
                        output += "In-School\n"
                    elif data['courses'][i]['independent'] == day:
                        output += "Independent Learning\n"
                    else:
                        output += "Online Afternoon Class\n"
            if output == "":
                await message.channel.send("<@"+str(message.author.id)+"> you are not in any classes for quad "+str(quad)+". Join your courses using the `$join` command")
                return
            if len(str(date[1])) < 2:
                date[1] = "0"+str(date[1])
            if len(str(date[2])) < 2:
                date[2] = "0"+str(date[2])
            embed=discord.Embed(color=0x0160a7, title="{}/{}/{} - Quad {} - Day {}".format(date[0],date[1],date[2],quad, day), description=output)
            embed.set_author(name=str(message.author),icon_url=message.author.avatar_url)
            await message.channel.send(embed=embed)
        
    elif message.content.lower().startswith('$addcourse'):
        if not message.author.permissions_in(message.channel).administrator:
            await message.channel.send("<@"+str(message.author.id)+"> this command is restricted to server admins")
        else:
            content = message.content.split()
            if len(content) < 5:
                await message.channel.send("This command has 4 arguments `$addcourse [code] [quad] [teacher] [days]`")
                return
            else:
                if content[1].upper() in set(data['courses'].keys()):
                    await message.channel.send(content[1].upper() + " already exists")
                    return
                if not content[2].isdigit():
                    await message.channel.send("Quadmester must be an integer")
                    return
                if len(content[4]) != 4:
                    await message.channel.send("Days should be for letters, `s` for in school, `o` for online, `i` for independent")
                data['courses'][content[1].upper()] = {}
                independent = 0
                online = []
                school = 0
                for i in range(4):
                    if content[4][i] == 's':
                        school = i+1
                    if content[4][i] == 'o':
                        online.append(i+1)
                    if content[4][i] == 'i':
                        independent = i+1
                data['courses'][content[1].upper()]['in-school'] = school
                data['courses'][content[1].upper()]['online'] = online
                data['courses'][content[1].upper()]['independent'] = independent
                data['courses'][content[1].upper()]['teacher'] = content[3]
                data['courses'][content[1].upper()]['quad'] = int(content[2])
                updateFile()
                await message.channel.send(content[1].upper() + " has been created")

    elif message.content.lower().startswith('$delcourse'):
        if not message.author.permissions_in(message.channel).administrator:
            await message.channel.send("<@"+str(message.author.id)+"> this command is restricted to server admins")
        else:
            content = message.content.split()
            if len(content) != 2:
                await message.channel.send("This command has 1 argument: `$delcourse [code]`")
                return
            if content[1].upper() not in set(data['courses'].keys()):
                await message.channel.send(content[1].upper() + " does not exist")
                return
            del data['courses'][content[1].upper()]
            for i in data['users'].keys():
                try:
                    data['users'][i]['courses'].remove(content[1].upper())
                except ValueError:
                    pass
            await message.channel.send(content[1].upper() + " has been deleted")
            updateFile()
    elif message.content.lower().startswith('$addevent'):
        content = message.content.split()
        await message.channel.send("Bad bitch")
        # if len(content) < 6:
        #     await message.channel.send("This command has 3 argument `$addevent [code] [quad] [teacher] [date] [event_title]")
        # elif content[1].upper() not in set(data['users'][str(message.author.id)]['courses'].values()):
        #     await message.channel.send("You are not in this class")
        # else: 
        #     date = datetime.datetime.today()
        # date = [date.year,date.month,date.day]
        # if len(content[3]) == 1:
        #     try:
        #         date = datetime.datetime.strptime(content[1],'%Y-%m-%d')
        #         date = [date.year,date.month,date.day]
        #     except ValueError:
        #         try:
        #             date = datetime.datetime.strptime(content[1],'%Y/%m/%d')
        #             date = [date.year,date.month,date.day]
        #         except ValueError:
        #             await message.channel.send("Please specify dates in `YYYY/MM/DD` or `YYYY-MM-DD`")
        #             return
    

token = ""
with open("token") as f:
    token = f.read().strip()

client.run(token)
