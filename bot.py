from datetime import timedelta
import discord
import logging
import json
import datetime

def getDay(year,month,day):
    date = datetime.datetime(year,month,day)
    exclude = set(['2020-10-12','2020-11-19','2020-11-20','2020-12-21','2020-12-22','2020-12-23','2020-12-24','2020-12-25','2020-12-28','2020-12-29','2020-12-30','2020-12-31','2021-01-01','2021-02-05','2021-02-12','2021-02-15','2021-03-15','2021-03-16','2021-03-17','2021-03-18','2021-03-19','2021-04-02','2021-04-05','2021-05-24','2021-06-29','2021-07-01'])
    if date >= datetime.datetime(2021,7,1):
        return "end"
    if date.strftime("%a") == "Sun" or date.strftime("%a") == "Sat":
        return "weekend"
    if date.strftime("%Y-%m-%d") in exclude:
        return "holiday"
    quad1 = datetime.datetime(2020,9,17)
    quad2 = datetime.datetime(2020,11,19)
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

def getQuad(year=datetime.datetime.today().year,month=datetime.datetime.today().month,day=datetime.datetime.today().day):
    quad1 = datetime.datetime(2020,9,17)
    quad2 = datetime.datetime(2020,11,19)
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

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_guild_join(guild:discord.guild):
    data[str(guild.id)] = {'courses':{},'users':{}}
    updateFile()
    print('Joined new server: {0}\nid:{1}'.format(guild.name,str(guild.id)))

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
        helpMessage = "`$list` - list all joinable courses for this quad\n`$list [quad]` - list joinable courses for specific quad\n`$join [code]` - add a course to your schedule\n`$leave [code]` - remove a course from your schedule\n`$courses` - view your courses\n`$courses [user]` - view another user's courses\n`$schedule` - view your schedule for today\n`$schedule YYYY/MM/DD` - view your schedule on a specific day\n`$week` - view your schedule for the week\n`$week [user]` - view weekly schedule of another user\n`$getevents [code]` - view assignment board for course\n`addevent [code] [yyyy/mm/dd] [event_name]` - add assignment to board\n`delevent [code] [yyyy/mm/dd] [event_name]` - remove event from board"
        embed=discord.Embed(title="Commands", description=helpMessage, color=0x0160a7)
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('$courses'):
        user = message.author
        if len(message.mentions) >= 1:
            user = message.mentions[0]
        elif len(message.content.split()) > 1:
            content = message.content.split()
            if content[1].isdigit() and message.channel.guild.get_member(int(content[1])) != None:
                    user = message.channel.guild.get_member(int(content[1]))
            else:
                user = message.channel.guild.get_member_named(" ".join(content[1:]))
                if user == None:
                    await message.channel.send("**"+" ".join(content[1:])+"** could not be found in the member list")
                    return
        if str(user.id) in list(data[str(message.channel.guild.id)]['users'].keys()) and len(data[str(message.channel.guild.id)]['users'][str(user.id)]['courses']) > 0:
            quads = ["","","",""]
            for i in data[str(message.channel.guild.id)]['users'][str(user.id)]['courses']:
                quads[data[str(message.channel.guild.id)]["courses"][i]["quad"]-1] += str(i+" - "+data[str(message.channel.guild.id)]["courses"][i]["teacher"]+"\n")
            embed=discord.Embed(color=0x0160a7)
            embed.set_author(name=str(user), icon_url=user.avatar_url)
            for i in range(4):
                if len(quads[i]) > 0:
                    embed.add_field(name="Quad "+str(i+1), value=quads[i])
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("**" + str(user)+"** does not have their courses added to the bot")

    elif message.content.lower().startswith('$list'):
        content = message.content.split()
        showHidden = False
        quad = getQuad()
        if len(content) >= 2 and content[1].isdigit() and content[1] in ["1","2","3","4"]:
            quad = int(content[1])
        if 'hidden' in content:
            showHidden = True
        output = ""
        for i in sorted(list(data[str(message.channel.guild.id)]['courses'].keys())):
            if 'hidden' in data[str(message.channel.guild.id)]['courses'][i].keys() and data[str(message.channel.guild.id)]['courses'][i]['hidden'] and not showHidden:
                continue
            if data[str(message.channel.guild.id)]['courses'][i]['quad'] == quad:
                output += i
                if data[str(message.channel.guild.id)]['courses'][i]['teacher']:
                    output += " ("+data[str(message.channel.guild.id)]['courses'][i]['teacher']+")"
                output += "\n"
        if len(output) == 0:
            output += "No courses have been added for quadmester {0} yet".format(str(quad))
        embed = discord.Embed(title="Quad {0} Courses".format(str(quad)), description=output, color=0x0160a7)
        embed.set_footer(text="Use the $join command to join a course\nIf your course is not in this list contact an admin")
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('$join'):
        content = message.content.split()
        if len(content) < 2:
            await message.channel.send("Please specify a course to join")
        elif content[1].upper() not in set(data[str(message.channel.guild.id)]['courses'].keys()):
            await message.channel.send("Please specify a course in the course list which can be viewed with `$list`. If your course is not there contact an admin")
        else:
            if str(message.author.id) not in set(data[str(message.channel.guild.id)]['users'].keys()):
                data[str(message.channel.guild.id)]['users'][str(message.author.id)] = {}
                data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses'] = []
            if content[1].upper() in set(data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']):
                await message.channel.send(str(message.author)+" is already in "+content[1].upper())
                return
            data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses'].append(content[1].upper())
            updateFile()
            await message.channel.send(str(message.author)+" has been added to " + content[1].upper())

    elif message.content.lower().startswith('$leave'):
        content = message.content.split()
        if len(content) < 2:
            await message.channel.send("Please specify a course to leave")
        elif str(message.author.id) not in set(data[str(message.channel.guild.id)]['users'].keys()):
            await message.channel.send("You are not in any courses currently")
        elif len(data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']) == 0:
            await message.channel.send("You are not in any courses currently")
        elif content[1].upper() not in set(data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']):
            await message.channel.send("You are not in "+content[1].upper())
        else:
            data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses'].remove(content[1].upper())
            updateFile()
            await message.channel.send(str(message.author)+" has left "+content[1].upper())

    elif message.content.lower().startswith('$schedule'):
        if str(message.author.id) not in set(data[str(message.channel.guild.id)]['users'].keys()):
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
                    if content[1].lower() in ('sun', 'sunday', 'sat', 'saturday'):
                        await message.channel.send("It's the weekend! No classes!")
                        return
                    elif content[1].lower() in ('mon', 'monday', 'tue', 'tues', 'tuesday', 'wed', 'wednesday', 'thu', 'thur', 'thursday', 'fri', 'friday'):
                        date = datetime.datetime.today()
                        if date.weekday() == 5:
                            date += datetime.timedelta(days=2)
                        elif date.weekday() == 6:
                            date += datetime.timedelta(days=1)
                        else:
                            date -= datetime.timedelta(days=date.weekday())
                        if content[1].lower() in ('mon', 'monday'):
                            if datetime.datetime.today().strftime('%Y/%m/%d') > date.strftime('%Y/%m/%d'):
                                date += datetime.timedelta(days=7)
                        if content[1].lower() in ('tue', 'tues', 'tuesday'):
                            date += datetime.timedelta(days=1)
                            if datetime.datetime.today().strftime('%Y/%m/%d') > date.strftime('%Y/%m/%d'):
                                date += datetime.timedelta(days=7)
                        if content[1].lower() in ('wed', 'wednesday'):
                            date += datetime.timedelta(days=2)
                            if datetime.datetime.today().strftime('%Y/%m/%d') > date.strftime('%Y/%m/%d'):
                                date += datetime.timedelta(days=7)
                        if content[1].lower() in ('thu', 'thur', 'thursday'):
                            date += datetime.timedelta(days=3)
                            if datetime.datetime.today().strftime('%Y/%m/%d') > date.strftime('%Y/%m/%d'):
                                date += datetime.timedelta(days=7)
                        if content[1].lower() in ('fri', 'friday'):
                            date += datetime.timedelta(days=4)
                            if datetime.datetime.today().strftime('%Y/%m/%d') > date.strftime('%Y/%m/%d'):
                                date += datetime.timedelta(days=7)
                        date = [date.year,date.month,date.day]
                    else:
                        await message.channel.send("Please specify dates in `YYYY/MM/DD`, `YYYY-MM-DD`, or days of the week")
                        return
        quad = getQuad(date[0],date[1],date[2])
        day = getDay(date[0],date[1],date[2])
        if day == 'weekend':
            header = ""
            output = "It's the weekend! No classes!\n"
        elif day == 'holiday':
            header = "PA Day/Holiday"
            output = ""
        elif day == 'end':
            header = ""
            output = "That date is past the end of the year.\n"
        else:
            output = ""
            morning = ""
            afternoon = ""
            for i in data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']:
                if data[str(message.channel.guild.id)]['courses'][i]['quad'] == quad:
                    if 'events' not in data[str(message.channel.guild.id)]['courses'][i].keys(): # check if events exist to avoid KeyError, otherwise create Key
                        data[str(message.channel.guild.id)]['courses'][i]['events'] = []
                        updateFile()
                    if data[str(message.channel.guild.id)]['courses'][i]['in-school'] == day:
                        morning += i + " (" + data[str(message.channel.guild.id)]['courses'][i]['teacher'] + ") - "
                        morning += "In-School\n"
                        # append events for course on day in newline
                        for j in data[str(message.channel.guild.id)]['courses'][i]['events']:
                            if datetime.datetime.strptime(j['date'], "%Y/%m/%d") < datetime.datetime(*date): # skip all earlier events
                                continue
                            if datetime.datetime.strptime(j['date'], "%Y/%m/%d") > datetime.datetime(*date): # events are date-sorted
                                break
                            morning += "*" + j['name'] + "*\n" # italics
                    elif data[str(message.channel.guild.id)]['courses'][i]['independent'] == day:
                        morning += i + " (" + data[str(message.channel.guild.id)]['courses'][i]['teacher'] + ") - "
                        morning += "Independent Learning\n"
                        # append events for course on day in newline
                        for j in data[str(message.channel.guild.id)]['courses'][i]['events']:
                            if datetime.datetime.strptime(j['date'], "%Y/%m/%d") < datetime.datetime(*date): # skip all earlier events
                                continue
                            if datetime.datetime.strptime(j['date'], "%Y/%m/%d") > datetime.datetime(*date): # events are date-sorted
                                    break
                            morning += "*" + j['name'] + "*\n" # italics
                    else:
                        afternoon += i + " (" + data[str(message.channel.guild.id)]['courses'][i]['teacher'] + ") - "
                        afternoon += "Online Afternoon Class\n"
                        # append events for course on day in newline
                        for j in data[str(message.channel.guild.id)]['courses'][i]['events']:
                            if datetime.datetime.strptime(j['date'], "%Y/%m/%d") < datetime.datetime(*date): # skip all earlier events
                                continue
                            if datetime.datetime.strptime(j['date'], "%Y/%m/%d") > datetime.datetime(*date): # events are date-sorted
                                break
                            afternoon += "*" + j['name'] + "*\n" # italics
            output = morning+afternoon
            if output == "":
                await message.channel.send("<@"+str(message.author.id)+"> you are not in any classes for quad "+str(quad)+". Join your courses using the `$join` command")
                return
            if len(str(date[1])) < 2:
                date[1] = "0"+str(date[1])
            if len(str(date[2])) < 2:
                date[2] = "0"+str(date[2])
            header = "{}/{}/{} - Quad {} - Day {}".format(date[0],date[1],date[2],quad, day)
        if day == 'weekend' or day == 'holiday' or day == 'end':
            # add event information
            for i in data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']:
                if 'events' not in data[str(message.channel.guild.id)]['courses'][i].keys(): # check if events exist to avoid KeyError, otherwise create Key
                    data[str(message.channel.guild.id)]['courses'][i]['events'] = []
                    updateFile()
                if len(data[str(message.channel.guild.id)]['courses'][i]['events']) == 0:
                    continue
                # append events for course on day in newline
                for j in data[str(message.channel.guild.id)]['courses'][i]['events']:
                    if datetime.datetime.strptime(j['date'], "%Y/%m/%d") < datetime.datetime(*date): # skip all earlier events
                        continue
                    if datetime.datetime.strptime(j['date'], "%Y/%m/%d") > datetime.datetime(*date): # events are date-sorted
                        break
                    output += i + ": *" + j['name'] + "*\n" # italics
        embed=discord.Embed(color=0x0160a7, title=header, description=output)
        embed.set_author(name=str(message.author),icon_url=message.author.avatar_url)
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('$week'): # return's users' schedule for the week. if someone else is mentioned, returned their schedule for the week
        user = message.author
        if len(message.mentions) >= 1:
            user = message.mentions[0]
        elif len(message.content.split()) > 1:
            content = message.content.split()
            if content[1].isdigit() and message.channel.guild.get_member(int(content[1])) != None:
                    user = message.channel.guild.get_member(int(content[1]))
            else:
                user = message.channel.guild.get_member_named(" ".join(content[1:]))
                if user == None:
                    await message.channel.send("**"+" ".join(content[1:])+"** could not be found in the member list")
                    return
        date = datetime.datetime.today()
        if date.weekday() == 5:
            date += datetime.timedelta(days=2)
        elif date.weekday() == 6:
            date += datetime.timedelta(days=1)
        else:
            date -= datetime.timedelta(days=date.weekday())
        quad = getQuad(date.year,date.month,date.day)
        embed = discord.Embed(color=0x0160a7, title="Week of {} - Quad {}".format(date.strftime('%Y/%m/%d'), quad))
        if str(user.id) not in set(data[str(message.channel.guild.id)]['users'].keys()):
            await message.channel.send("**"+str(user)+"** has no courses added for this quad, to view a list of courses use `$list` and use `$join` to join the course")
            return
        for i in range(5):
            output = ""
            morning = ""
            afternoon = ""
            day = getDay(date.year,date.month,date.day)
            if day == 'holiday':
                output = "PA Day/Holiday\n"
            else:
                for j in data[str(message.channel.guild.id)]['users'][str(user.id)]['courses']:
                    # make sure events key exists
                    if 'events' not in data[str(message.channel.guild.id)]['courses'][j].keys(): # check if events exist to avoid KeyError, otherwise create Key
                        data[str(message.channel.guild.id)]['courses'][j]['events'] = []
                        updateFile()
                    if len(data[str(message.channel.guild.id)]['courses'][j]['events']) == 0:
                        continue
                    if data[str(message.channel.guild.id)]['courses'][j]['quad'] == quad:
                        if data[str(message.channel.guild.id)]['courses'][j]['in-school'] == day:
                            morning = j + " (" + data[str(message.channel.guild.id)]['courses'][j]['teacher'] + ") - In School\n" + output
                            # append events for course on day in newline
                            for k in data[str(message.channel.guild.id)]['courses'][j]['events']:
                                if k['date'] < date.strftime('%Y/%m/%d'): # skip all earlier events
                                    continue
                                if k['date'] > date.strftime('%Y/%m/%d'): # events are date-sorted
                                    break
                                if day == 'holiday': # only specify course on holidays
                                    morning += j + ": "
                                morning += "*" + k['name'] + "*\n" # italics
                        elif data[str(message.channel.guild.id)]['courses'][j]['independent'] == day:
                            morning = j + " (" + data[str(message.channel.guild.id)]['courses'][j]['teacher'] + ") - Independent\n" + output
                            # append events for course on day in newline
                            for k in data[str(message.channel.guild.id)]['courses'][j]['events']:
                                if k['date'] < date.strftime('%Y/%m/%d'): # skip all earlier events
                                    continue
                                if k['date'] > date.strftime('%Y/%m/%d'): # events are date-sorted
                                    break
                                if day == 'holiday': # only specify course on holidays
                                    morning += j + ": "
                                morning += "*" + k['name'] + "*\n" # italics
                        else:
                            afternoon += j + " (" + data[str(message.channel.guild.id)]['courses'][j]['teacher'] + ") - Online Afternoon\n"
                            # append events for course on day in newline
                            for k in data[str(message.channel.guild.id)]['courses'][j]['events']:
                                if k['date'] < date.strftime('%Y/%m/%d'): # skip all earlier events
                                    continue
                                if k['date'] > date.strftime('%Y/%m/%d'): # events are date-sorted
                                    break
                                if day == 'holiday': # only specify course on holidays
                                    afternoon += j + ": "
                                afternoon += "*" + k['name'] + "*\n" # italics
                output = morning + afternoon
            if len(output) == 0:
                await message.channel.send("**"+str(user)+"** has no courses added for this quad, to view a list of courses use `$list` and use `$join` to join the course")
                return
            title = date.strftime('%A')
            if day != 'holiday': title += " - Day {}".format(day)
            embed.add_field(name=title, value=output, inline=False)
            date += datetime.timedelta(days=1)
        embed.set_author(name=str(user),icon_url=user.avatar_url)
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
                if content[1].upper() in set(data[str(message.channel.guild.id)]['courses'].keys()):
                    await message.channel.send(content[1].upper() + " already exists")
                    return
                if not content[2].isdigit():
                    await message.channel.send("Quadmester must be an integer")
                    return
                if len(content[4]) != 4:
                    await message.channel.send("Days should be for letters, `s` for in school, `o` for online, `i` for independent")
                hidden = False
                if len(content) > 5 and content[5].lower() == 'true':
                    hidden = True
                data[str(message.channel.guild.id)]['courses'][content[1].upper()] = {}
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
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['in-school'] = school
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['online'] = online
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['independent'] = independent
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['teacher'] = content[3]
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['quad'] = int(content[2])
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'] = []
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['hidden'] = hidden
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
            if content[1].upper() not in set(data[str(message.channel.guild.id)]['courses'].keys()):
                await message.channel.send(content[1].upper() + " does not exist")
                return
            del data[str(message.channel.guild.id)]['courses'][content[1].upper()]
            for i in data[str(message.channel.guild.id)]['users'].keys():
                try:
                    data[str(message.channel.guild.id)]['users'][i]['courses'].remove(content[1].upper())
                except ValueError:
                    pass
            await message.channel.send(content[1].upper() + " has been deleted")
            updateFile()

    elif message.content.lower().startswith('$addevent'):
        content = message.content.split()
        try:
            if len(content) < 4:
                await message.channel.send("This command has 3 argument `$addevent [code] [date] [event_title]`")
            elif content[1].upper() not in set(data[str(message.channel.guild.id)]['courses'].keys()):
                await message.channel.send("This class does not exist. Contact your admin to add any new courses.")
            elif str(message.author.id) not in data[str(message.channel.guild.id)]['users'].keys() or content[1].upper() not in set(data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']):
                await message.channel.send("You are not in this class")
        except TypeError:
            await message.channel.send("You are not in this class")
        else:
            if 'events' not in set(data[str(message.channel.guild.id)]['courses'][content[1].upper()].keys()):
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'] = []
                updateFile()
            if len(content) > 4:
                content[3] = " ".join(content[3:])
            if len(content[2]) > 1:
                try:
                    date = datetime.datetime.strptime(content[2],'%Y-%m-%d')
                    data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'].append({'date':date.strftime('%Y/%m/%d'),'name':content[3]})
                    data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'].sort(key=lambda e: e['date'])
                    updateFile()
                    await message.channel.send("Event `{0}` has been created".format(content[3]))
                except ValueError:
                    try:
                        date = datetime.datetime.strptime(content[2],'%Y/%m/%d')
                        data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'].append({'date':date.strftime('%Y/%m/%d'),'name':content[3]})
                        data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'].sort(key=lambda e: e['date'])
                        updateFile()
                        await message.channel.send("Event `{0}` has been created".format(content[3]))
                    except ValueError:
                        await message.channel.send("Please specify dates in `YYYY/MM/DD` or `YYYY-MM-DD`")
                        return

    elif message.content.lower().startswith('$getevents'):
        content = message.content.split()
        user = message.author
        courses = []
        if len(message.mentions) >= 1:
            user = message.mentions[0]
        elif len(content) > 1:
            if content[1].isdigit() and message.channel.guild.get_member(int(content[1])) != None:
                    user = message.channel.guild.get_member(int(content[1]))
            else:
                user = message.channel.guild.get_member_named(" ".join(content[1:]))
                if user == None:
                    user = message.author
                    try:
                        if content[1].upper() not in set(data[str(message.channel.guild.id)]['courses'].keys()):
                            await message.channel.send("This class does not exist. Contact your admin to add any new courses.")
                            return
                        elif str(user.id) not in data[str(message.channel.guild.id)]['users'].keys() or content[1].upper() not in set(data[str(message.channel.guild.id)]['users'][str(user.id)]['courses']):
                            await message.channel.send("This user is not in this class.")
                            return
                    except TypeError:
                        await message.channel.send("This user is not in this class.")
                    courses = [content[1].upper()]
        if not courses:
            try:
                courses = [course for course in data[str(message.channel.guild.id)]['users'][str(user.id)]['courses']]
            except KeyError:
                await message.channel.send("This user is not in any classes. Use `$join` to join classes, and `$list` to see available classes.")
                return
            if len(courses) < 1:
                await message.channel.send("This user is not in any classes. Use `$join` to join classes, and `$list` to see available classes.")
                return
        embed = discord.Embed(color=0x0160a7, title="Events")
        for course in courses:
            if 'events' not in set(data[str(message.channel.guild.id)]['courses'][course].keys()):
                data[str(message.channel.guild.id)]['courses'][course]['events'] = []
                updateFile()
            if len(data[str(message.channel.guild.id)]['courses'][course]['events']) == 0:
                await message.channel.send("There are no events for this course, add an event using `$addevent [code] [date] [event_title]`")
            else:
                output =""
                remove = []
                for i in data[str(message.channel.guild.id)]['courses'][course]['events']:
                    if i['date'] < datetime.datetime.today().strftime('%Y/%m/%d'):
                        remove.append(i)
                        continue
                    output+=i['date'] +" : "
                    output+= i['name']
                    output += "\n "
                if len(remove)>=1:
                    for i in remove:
                        data[str(message.channel.guild.id)]['courses'][course]['events'].remove(i)
                    updateFile()
                embed.add_field(name=course, value=output, inline=False)
        embed.set_author(name=str(user),icon_url=user.avatar_url)
        embed.set_footer(text="Use the `$addevent` command to add upcoming tests, assignments, etc")
        await message.channel.send(embed=embed)

    elif message.content.lower().startswith('$delevent'):
        content = message.content.split()
        if len(content) < 4:
            await message.channel.send("This command has 3 argument `$delevent [code] [date] [event_title]`")
        elif content[1].upper() not in set(data[str(message.channel.guild.id)]['courses'].keys()):
            await message.channel.send("This class does not exist. Contact your admin to add any new courses.")
        elif content[1].upper() not in set(data[str(message.channel.guild.id)]['users'][str(message.author.id)]['courses']):
            await message.channel.send("You are not in this class")
        else:
            if 'events' not in set(data[str(message.channel.guild.id)]['courses'][content[1].upper()].keys()):
                data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'] = []
                updateFile()
            if len(content) > 4:
                content[3] = " ".join(content[3:])
            if len(content[2]) > 1:
                date = None
                try:
                    date = datetime.datetime.strptime(content[2],'%Y-%m-%d')
                except ValueError:
                    try:
                        date = datetime.datetime.strptime(content[2],'%Y/%m/%d')
                    except ValueError:
                        await message.channel.send("Please specify dates in `YYYY/MM/DD` or `YYYY-MM-DD`")
                        return
                try:
                    data[str(message.channel.guild.id)]['courses'][content[1].upper()]['events'].remove({'date':date.strftime('%Y/%m/%d'),'name':content[3]})
                    updateFile()
                    await message.channel.send("`{0}` was removed from the {1} event board".format(content[3], content[1].upper()))
                except ValueError:
                    await message.channel.send("The specified event was not found")
                    return

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

token = ""
with open("token") as f:
    token = f.read().strip()

client.run(token)
