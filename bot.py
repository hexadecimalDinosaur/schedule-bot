import datetime
import discord
import json
import logging
import typing
from discord.ext import commands
from discord.utils import get

QUADS = [datetime.date(2020, 9, 17), datetime.date(2020, 11, 19), datetime.date(2021, 2, 8), datetime.date(2021, 4, 23)]
EXCLUDE = set(datetime.date(*date) for date in [(2020, 10, 12),  (2020, 11, 19),  (2020, 11, 20),  (2020, 12, 21),  (2020, 12, 22),  (2020, 12, 23),  (2020, 12, 24),  (2020, 12, 25),  (2020, 12, 28),  (2020, 12, 29),  (2020, 12, 30),  (2020, 12, 31),  (2021, 1, 1),  (2021, 2, 5),  (2021, 2, 12),  (2021, 2, 15),  (2021, 3, 15),  (2021, 3, 16),  (2021, 3, 17),  (2021, 3, 18),  (2021, 3, 19),  (2021, 4, 2),  (2021, 4, 5),  (2021, 5, 24),  (2021, 6, 29), (2021, 7, 1)])
WEEKDAY_FORMATS = [['mon', 'monday'], ['tue', 'tues', 'tuesday'], ['wed', 'wednesday'], ['thu', 'thur', 'thurs', 'thursday'], ['fri', 'friday'], ['sat', 'saturday'], ['sun', 'sunday']]

def getDay(date):
    if date >= datetime.date(2021, 7, 1):
        return "end"
    if date.weekday() >= 5: # Saturday or Sunday
        return "weekend"
    if date in EXCLUDE:
        return "holiday"
    start = QUADS[getQuad(date) - 1]
    day = 4
    while True:
        if start in EXCLUDE:
            start += datetime.timedelta(days=1)
            continue
        if date.weekday() >= 5: # Saturday or Sunday
            start += datetime.timedelta(days=1)
            continue
        day += 1
        if day == 5: day = 1
        if start == date:
            return day
        start += datetime.timedelta(days=1)

def getQuad(date=None):
    if not date:
        date = datetime.date.today()
    for i, quad in enumerate(QUADS[::-1]):
        if date >= quad:
            return 4 - i

class Date(commands.Converter):
    async def convert(self, ctx, arg):
        arg = arg.lower()
        date = None
        try:
            date = datetime.datetime.strptime(arg,'%Y/%m/%d').date()
        except ValueError:
            try:
                date = datetime.datetime.strptime(arg,'%Y-%m-%d').date()
            except ValueError:
                today = datetime.date.today()
                for i, f in enumerate(WEEKDAY_FORMATS):
                    if arg in f:
                        days = (i - today.weekday()) % 7
                        date = today + datetime.timedelta(days=days)
        if date:
            return date
        raise commands.BadArgument("Please specify dates in `YYYY/MM/DD`, `YYYY-MM-DD`, or days of the week.")

class Courses(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #delete once file has been updated
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def updatejson(self, ctx):
        def check(message):
            return message.content and message.author == ctx.author
        for course in data[str(ctx.guild.id)]["courses"]:
            try:
                data[str(ctx.guild.id)]["courses"][course]["role"]
            except KeyError:
                await ctx.send(f"What role would you like to give {course}?")
                message = await self.bot.wait_for('message', check=check)
                data[str(ctx.guild.id)]["courses"][course]["role"] = message.content.lower()
                role = get(ctx.guild.roles, name=data[str(ctx.guild.id)]["courses"][course]["role"])
                if not role:
                    await ctx.guild.create_role(name=data[str(ctx.guild.id)]["courses"][course]["role"], colour=discord.Colour.random())
        updateFile()
        await ctx.send("All courses have been given roles!")

    @updatejson.error
    async def updatejson_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is restricted to server admins.")
            return
        print(error)
        await ctx.send("Some roles may not have been given due to an error.")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def updateroles(self, ctx):
        for user in data[str(ctx.guild.id)]["users"].keys():
            user = ctx.guild.get_member(int(user))
            for course in data[str(ctx.guild.id)]["courses"]:
                role = get(ctx.guild.roles, name=data[str(ctx.guild.id)]["courses"][course]["role"])
                try:
                    await user.remove_roles(role)
                except AttributeError:
                    pass
            for course in data[str(ctx.guild.id)]["users"][str(user.id)]["courses"]:
                if int(data[str(ctx.guild.id)]["courses"][course]["quad"]) != getQuad():
                    continue
                role = get(ctx.guild.roles, name=data[str(ctx.guild.id)]["courses"][course]["role"])
                await user.add_roles(role)
        await ctx.send("All users enrolled in courses have been given updated roles!")

    @updateroles.error
    async def updateroles_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is restricted to server admins.")
            return
        print(error)
        await ctx.send("Please run $updatejson to ensure all courses have been given roles.")

    @commands.command(help="Displays yours or another user's courses")
    async def courses(self, ctx, *, user: typing.Optional[discord.Member]):
        if not user:
            try:
                user_attempt = " ".join(ctx.message.content.split()[1:])
                if user_attempt:
                    raise commands.BadArgument(message="**" + user_attempt + "** could not be found in the member list.")
            except IndexError:
                pass
            user = ctx.author
        try:
            quads = ["", "", "", ""]
            for course in data[str(ctx.guild.id)]['users'][str(user.id)]['courses']:
                quads[data[str(ctx.guild.id)]["courses"][course]["quad"]-1] += str(course + " - " + data[str(ctx.guild.id)]["courses"][course]["teacher"]+"\n")
            embed = discord.Embed(color=0x0160a7)
            embed.set_author(name=str(user), icon_url=user.avatar_url)
            for i in range(4):
                if len(quads[i]) > 0:
                    embed.add_field(name="Quad " + str(i + 1), value=quads[i])
            if not embed.fields:
                raise commands.BadArgument(f"**{str(user)}** does not have their courses added. To add courses, use `$join [code]` and use `$list` to see a list of available courses.")
            await ctx.send(embed=embed)
        except KeyError:
            raise commands.BadArgument(f"**{str(user)}** does not have their courses added. To add courses, use `$join [code]` and use `$list` to see a list of available courses.")

    @courses.error
    async def courses_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print (error)

    @commands.command(help="Adds a course to your schedule")
    async def join(self, ctx, course: str.upper):
        if course not in data[str(ctx.guild.id)]['courses'].keys():
            raise commands.BadArgument("Please specify a course in the course list, which can be viewed with `$list`. If your course is not listed, contact an admin.")
        if str(ctx.author.id) not in set(data[str(ctx.guild.id)]['users'].keys()):
            data[str(ctx.guild.id)]['users'][str(ctx.author.id)] = {}
            data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses'] = []
        if course in set(data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses']):
            raise commands.BadArgument(f"**{str(ctx.author)}** is already in {course}.")
        role = get(ctx.guild.roles, name=data[str(ctx.guild.id)]["courses"][course]["role"])
        if role in ctx.author.roles:
            raise commands.BadArgument(f"**{str(ctx.author)}** is already in a {role.name} course.")
        if data[str(ctx.guild.id)]["courses"][course]["quad"] == getQuad():
            await ctx.author.add_roles(role)
        data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses'].append(course)
        updateFile()
        await ctx.send(f"**{str(ctx.author)}** has been added to {course}.")

    @join.error
    async def join_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a course to join.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

    @commands.command(help="Removes a course from your schedule")
    async def leave(self, ctx, course: str.upper):
        try:
            data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses'].remove(course)
            role = get(ctx.guild.roles, name=data[str(ctx.guild.id)]["courses"][course]["role"])
            await ctx.author.remove_roles(role)
            updateFile()
            await ctx.send(f"**{ctx.author}** has been removed from {course}.")
        except KeyError:
            raise commands.BadArgument("You are not currently in any courses.")
        except ValueError:
            raise commands.BadArgument("You are not currently in {0}.".format(course) if data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses'] else "You are not currently in any courses.")

    @leave.error
    async def leave_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a course to leave.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

    @commands.command(help="Lists all joinable courses for this quad")
    async def list(self, ctx, quad: typing.Optional[int]=getQuad(), *, hidden=""):
        if quad < 1 or quad > 4:
            quad = getQuad()
        showHidden = True if "hidden" in hidden.split() else False
        output = ""
        for i in sorted(data[str(ctx.guild.id)]['courses'].keys()):
            try:
                if data[str(ctx.guild.id)]['courses'][i]['hidden'] and not showHidden:
                    continue
            except KeyError:
                pass
            if data[str(ctx.guild.id)]['courses'][i]['quad'] == quad:
                output += i
                if data[str(ctx.guild.id)]['courses'][i]['teacher']:
                    output += " ("+data[str(ctx.guild.id)]['courses'][i]['teacher'] + ")"
                output += "\n"
        if len(output) == 0:
            raise commands.BadArgument("No courses have been added for quadmester {0}.".format(str(quad)))
        embed = discord.Embed(title="Quad {0} Courses".format(str(quad)), description=output, color=0x0160a7)
        embed.set_footer(text="Use the $join command to join a course.\nIf your course is not in this list, contact an admin.")
        await ctx.send(embed=embed)

    @list.error
    async def list_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print (error)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def addcourse(self, ctx, course: str.upper, quad: int, teacher, days, hidden: typing.Optional[bool], *, role_name: str.lower):
        if quad < 1 or quad > 4:
            raise commands.BadArgument("Quadmester must be between 1 and 4.")
        if course in data[str(ctx.guild.id)]['courses'].keys():
            raise commands.BadArgument("Course {0} already exists.".format(course))
        if len(days) != 4 or days.translate({ord(i): None for i in "soi"}):
            raise commands.BadArgument("Days must be represented as a four-character string where `s` means in-school, `o` means online, and `i` means independent learning.\ne.g. `sioo`")
        data[str(ctx.guild.id)]['courses'][course] = {}
        independent = 0
        online = []
        school = 0
        for i in range(4):
            if days[i] == 's':
                school = i + 1
            if days[i] == 'o':
                online.append(i + 1)
            if days[i] == 'i':
                independent = i + 1
        data[str(ctx.guild.id)]['courses'][course]['in-school'] = school
        data[str(ctx.guild.id)]['courses'][course]['online'] = online
        data[str(ctx.guild.id)]['courses'][course]['independent'] = independent
        data[str(ctx.guild.id)]['courses'][course]['teacher'] = teacher
        data[str(ctx.guild.id)]['courses'][course]['quad'] = quad
        data[str(ctx.guild.id)]['courses'][course]['events'] = []
        data[str(ctx.guild.id)]['courses'][course]['hidden'] = hidden
        data[str(ctx.guild.id)]['courses'][course]['role'] = role_name
        role = get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.guild.create_role(name=role_name, colour=discord.Colour.random())
            role = get(ctx.guild.roles, name=role_name)
        updateFile()
        await ctx.send(f"Course **{course}** has been created.")

    @addcourse.error
    async def addcourse_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is restricted to server admins.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("This command has 4 arguments: `$addcourse [code] [quad] [teacher] [days]`.")
            return
        if isinstance(error, commands.BadArgument):
            if "Converting" in str(error):
                await ctx.send("Quadmester must be an integer.")
                return
            await ctx.send(error)
            return
        print(error)

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def delcourse(self, ctx, course: str.upper):
        if course not in data[str(ctx.guild.id)]['courses'].keys():
            raise commands.BadArgument("Course **{0}** does not exist.".format(course))
        for user in data[str(ctx.guild.id)]['users'].keys():
            try:
                data[str(ctx.guild.id)]['users'][user]['courses'].remove(course)
                user = ctx.guild.get_member(int(user))
                role = get(ctx.guild.roles, name=data[str(ctx.guild.id)]['courses'][course]["role"])
                await user.remove_roles(role)
            except ValueError:
                pass
            except AttributeError:
                pass
        del data[str(ctx.guild.id)]['courses'][course]
        await ctx.send(f"Course **{course}** has been deleted.")
        updateFile()

    @delcourse.error
    async def delcourse_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("This command is restricted to server admins.")
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a course in the format `$delcourse [course]`")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Adds an event to a course board")
    async def addevent(self, ctx, course: str.upper, date: Date, *, event_title):
        try:
            if course not in data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses']:
                raise commands.BadArgument("You are not in this class.")
        except KeyError:
            raise commands.BadArgument("You are not in any classes. Use `$join` to join a course, and `$list` to see a list of available courses.")
        try:
            if 'events' not in data[str(ctx.guild.id)]['courses'][course].keys():
                data[str(ctx.guild.id)]['courses'][course]['events'] = []
                updateFile()
        except KeyError:
            raise commands.BadArgument("This class does not exist. Contact your admin to add any new courses.")
        data[str(ctx.guild.id)]['courses'][course]['events'].append({'date':date.strftime('%Y/%m/%d'),'name':event_title})
        data[str(ctx.guild.id)]['courses'][course]['events'].sort(key=lambda e: e['date'])
        updateFile()
        await ctx.send("Event **{0}** has been created".format(event_title))

    @addevent.error
    async def addevent_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("This command has 3 arguments: `$addevent [code] [date] [event_title]`.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

    @commands.command(help="Removes an event from a course board")
    async def delevent(self, ctx, course: str.upper, date: Date, *, event_title):
        try:
            if course not in data[str(ctx.guild.id)]['users'][str(ctx.author.id)]['courses']:
                raise commands.BadArgument("You are not in this class.")
        except KeyError:
            raise commands.BadArgument("You are not in any classes. Use `$join` to join a course, and `$list` to see a list of available courses.")
        try:
            if 'events' not in data[str(ctx.guild.id)]['courses'][course].keys():
                data[str(ctx.guild.id)]['courses'][course]['events'] = []
                updateFile()
        except KeyError:
            raise commands.BadArgument("This class does not exist. Contact your admin to add any new courses.")
        try:
            data[str(ctx.guild.id)]['courses'][course]['events'].remove({'date':date.strftime('%Y/%m/%d'),'name':event_title})
            updateFile()
            await ctx.send(f"*{event_title}* was removed from the **{course}** event board.")
        except ValueError:
            raise commands.BadArgument(f"Event *{event_title}* does not exist.")

    @delevent.error
    async def delevent_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("This command has 3 arguments: `$delevent [code] [date] [event_title]`.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

    @commands.command(help="Displays a personal events board or one for a specific course")
    async def getevents(self, ctx, *, course_or_user: typing.Union[discord.Member, str.upper, None]):
        user = None
        course = None
        if isinstance(course_or_user, discord.Member):
            user = course_or_user
        elif course_or_user:
            course = course_or_user
            if course not in data[str(ctx.guild.id)]['courses']:
                raise commands.BadArgument("This class does not exist. Contact your admin to add any new courses.")
            user = ctx.author
        if not user and not course:
            if len(ctx.message.content) > 10:
                raise commands.BadArgument("**" + " ".join(ctx.message.content.split()[1:]) + "** could not be found in the member list.")
            user = ctx.author
        if course:
            try:
                if course not in data[str(ctx.guild.id)]['users'][str(user.id)]['courses']:
                    raise commands.BadArgument("**{0}** is not in course {1}.".format(str(user), course))
                courses = [course]
            except KeyError:
                raise commands.BadArgument("**{0}** is not in any classes. Use `join` to join a course, and `list` to see a list of available courses.".format(str(user)))
        else:
            try:
                courses = [course for course in data[str(ctx.guild.id)]['users'][str(user.id)]['courses']]
                if not courses:
                    raise commands.BadArgument(f"**{user}** is not in any classes. Use `join` to join a course, and `list` to see a list of available courses.")
            except KeyError:
                raise commands.BadArgument("**{0}** is not in any classes. Use `join` to join a course, and `list` to see a list of available courses.".format(str(user)))
        embed = discord.Embed(color=0x0160a7, title="Events")
        for course in courses:
            if 'events' not in data[str(ctx.guild.id)]['courses'][course].keys():
                data[str(ctx.guild.id)]['courses'][course]['events'] = []
                updateFile()
            if not data[str(ctx.guild.id)]['courses'][course]['events']:
                continue
            else:
                output = ""
                remove = []
                for i in data[str(ctx.guild.id)]['courses'][course]['events']:
                    if i['date'] < datetime.date.today().strftime('%Y/%m/%d'):
                        remove.append(i)
                        continue
                    output+=i['date'] +" : "
                    output+= i['name']
                    output += "\n "
                if remove:
                    for i in remove:
                        data[str(ctx.guild.id)]['courses'][course]['events'].remove(i)
                    updateFile()
                if output:
                    embed.add_field(name=course, value=output, inline=False)
        if embed.fields:
            embed.set_author(name=str(user),icon_url=user.avatar_url)
            embed.set_footer(text="Use the `$addevent` command to add upcoming tests, assignments, etc.")
            await ctx.send(embed=embed)
        else:
            raise commands.BadArgument(f"**{str(user)}**'s courses have no upcoming events. To add an event, use `$addevent [code] [date] [event_title]`.")

    @getevents.error
    async def getevents_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

class Schedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Displays a personal schedule for today or any specified day")
    async def schedule(self, ctx, date: typing.Optional[Date], *, user: typing.Optional[discord.Member]):
        if not date:
            date = datetime.date.today()
        if not user:
            date_specified = False
            for i in ctx.message.content.split():
                try:
                    await Date().convert(ctx, i.strip())
                    date_specified = True
                    continue
                except commands.BadArgument:
                    if "$schedule" in i.lower():
                        continue
                    if i.strip():
                        raise commands.BadArgument ("**" + " ".join(ctx.message.content.split()[(2 if date_specified else 1):]) + "** could not be found in the member list.")
            user = ctx.author
        quad = getQuad(date)
        day = getDay(date)
        header = ""
        output = ""
        if day == 'weekend':
            output = "It's the weekend! No classes!\n"
        elif day == 'holiday':
            header = "PA Day/Holiday"
        elif day == 'end':
            output = "That date is past the end of the year.\n"
        else:
            morning = ""
            afternoon = ""
            try:
                for i in data[str(ctx.guild.id)]['users'][str(user.id)]['courses']:
                    if data[str(ctx.guild.id)]['courses'][i]['quad'] == quad:
                        if 'events' not in data[str(ctx.guild.id)]['courses'][i].keys(): # check if events exist to avoid KeyError, otherwise create Key
                            data[str(ctx.guild.id)]['courses'][i]['events'] = []
                            updateFile()
                        if data[str(ctx.guild.id)]['courses'][i]['in-school'] == day or data[str(ctx.guild.id)]['courses'][i]['independent'] == day:
                            morning += i + " (" + data[str(ctx.guild.id)]['courses'][i]['teacher'] + ") - "
                            morning += "In-School\n" if data[str(ctx.guild.id)]['courses'][i]['in-school'] == day else "Independent Learning\n"
                            # append events for course on day in newline
                            for j in data[str(ctx.guild.id)]['courses'][i]['events']:
                                if datetime.datetime.strptime(j['date'], "%Y/%m/%d").date() < date: # skip all earlier events
                                    continue
                                if datetime.datetime.strptime(j['date'], "%Y/%m/%d").date() > date: # events are date-sorted
                                    break
                                morning += "*" + j['name'] + "*\n" # italics
                        else:
                            afternoon += i + " (" + data[str(ctx.guild.id)]['courses'][i]['teacher'] + ") - "
                            afternoon += "Online Afternoon Class\n"
                            # append events for course on day in newline
                            for j in data[str(ctx.guild.id)]['courses'][i]['events']:
                                if datetime.datetime.strptime(j['date'], "%Y/%m/%d").date() < date: # skip all earlier events
                                    continue
                                if datetime.datetime.strptime(j['date'], "%Y/%m/%d").date() > date: # events are date-sorted
                                    break
                                afternoon += "*" + j['name'] + "*\n" # italics
            except KeyError:
                raise commands.BadArgument(f"**{str(user)}** is not in any courses. Use `$join` to join a course and `$list` to see a list of available courses.")
            output = morning + afternoon
            if output == "":
                raise commands.BadArgument(f"**{str(user)}** is not in any classes for quad {str(quad)}. Join courses with the `$join` command, and use `$list` to find available courses.")
            header = "{0} - Quad {1} - Day {2}".format(datetime.date.strftime(date, "%Y/%m/%d"), quad, day)
        if day == 'weekend' or day == 'holiday' or day == 'end':
            # add event information
            for i in data[str(ctx.guild.id)]['users'][str(user.id)]['courses']:
                if 'events' not in data[str(ctx.guild.id)]['courses'][i].keys(): # check if events exist to avoid KeyError, otherwise create Key
                    data[str(ctx.guild.id)]['courses'][i]['events'] = []
                    updateFile()
                if len(data[str(ctx.guild.id)]['courses'][i]['events']) == 0:
                    continue
                # append events for course on day in newline
                for j in data[str(ctx.guild.id)]['courses'][i]['events']:
                    if datetime.datetime.strptime(j['date'], "%Y/%m/%d").date() < date: # skip all earlier events
                        continue
                    if datetime.datetime.strptime(j['date'], "%Y/%m/%d").date() > date: # events are date-sorted
                        break
                    output += i + ": *" + j['name'] + "*\n" # italics
        embed=discord.Embed(color=0x0160a7, title=header, description=output)
        embed.set_author(name=str(user),icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @schedule.error
    async def schedule_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)

    @commands.command(help="Displays a personalized schedule for this or any specified week")
    async def week(self, ctx, date: typing.Optional[Date], *, user: typing.Optional[discord.Member]):
        if not date:
            date = datetime.date.today()
        if not user:
            date_specified = False
            for i in ctx.message.content.split():
                try:
                    await Date().convert(ctx, i.strip())
                    date_specified = True
                    continue
                except commands.BadArgument:
                    if "$week" in i.lower():
                        continue
                    if i.strip():
                        raise commands.BadArgument (f"**{' '.join(ctx.message.content.split()[(2 if date_specified else 1):])}** could not be found in the member list.")
            user = ctx.author
        if date.weekday() == 5:
            date += datetime.timedelta(days=2)
        elif date.weekday() == 6:
            date += datetime.timedelta(days=1)
        else:
            date -= datetime.timedelta(days=date.weekday())
        quad = getQuad(date)
        embed = discord.Embed(color=0x0160a7, title="Week of {0} - Quad {1}".format(date.strftime('%Y/%m/%d'), quad))
        for i in range(5):
            output = ""
            morning = ""
            afternoon = ""
            day = getDay(date)
            if day == 'holiday':
                output = "PA Day/Holiday\n"
            else:
                try:
                    for j in data[str(ctx.guild.id)]['users'][str(user.id)]['courses']:
                        # make sure events key exists
                        events = True
                        if 'events' not in data[str(ctx.guild.id)]['courses'][j].keys(): # check if events exist to avoid KeyError, otherwise create Key
                            data[str(ctx.guild.id)]['courses'][j]['events'] = []
                            updateFile()
                        if len(data[str(ctx.guild.id)]['courses'][j]['events']) == 0:
                            events = False
                        if data[str(ctx.guild.id)]['courses'][j]['quad'] == quad:
                            if data[str(ctx.guild.id)]['courses'][j]['in-school'] == day or data[str(ctx.guild.id)]['courses'][j]['independent'] == day:
                                morning = j + " (" + data[str(ctx.guild.id)]['courses'][j]['teacher']
                                morning += ") - In School\n" if data[str(ctx.guild.id)]['courses'][j]['in-school'] == day else ") - Independent\n"
                                # append events for course on day in newline
                                if events:
                                    for k in data[str(ctx.guild.id)]['courses'][j]['events']:
                                        if k['date'] < date.strftime('%Y/%m/%d'): # skip all earlier events
                                            continue
                                        if k['date'] > date.strftime('%Y/%m/%d'): # events are date-sorted
                                            break
                                        if day == 'holiday': # only specify course on holidays
                                            morning += j + ": "
                                        morning += "*" + k['name'] + "*\n" # italics
                            else:
                                afternoon += j + " (" + data[str(ctx.guild.id)]['courses'][j]['teacher'] + ") - Online Afternoon\n"
                                # append events for course on day in newline
                                if events:
                                    for k in data[str(ctx.guild.id)]['courses'][j]['events']:
                                        if k['date'] < date.strftime('%Y/%m/%d'): # skip all earlier events
                                            continue
                                        if k['date'] > date.strftime('%Y/%m/%d'): # events are date-sorted
                                            break
                                        if day == 'holiday': # only specify course on holidays
                                            afternoon += j + ": "
                                        afternoon += "*" + k['name'] + "*\n" # italics
                    output = morning + afternoon
                except KeyError:
                    raise commands.BadArgument(f"**{str(user)}** has no courses added for this quad, to view a list of courses use `$list` and use `$join` to join the course.")
            if len(output) == 0:
                raise commands.BadArgument(f"**{str(user)}** has no courses added for this quad, to view a list of courses use `$list` and use `$join` to join the course.")
            title = date.strftime('%A')
            if day != 'holiday': title += " - Day {}".format(day)
            embed.add_field(name=title, value=output, inline=False)
            date += datetime.timedelta(days=1)
        embed.set_author(name=str(user),icon_url=user.avatar_url)
        await ctx.send(embed=embed)

    @week.error
    async def week_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(error)
            return
        print(error)


data = {}
with open("data.json") as f:
    data = json.load(f)

def updateFile():
    with open("data.json",'w') as f:
        json.dump(data,f, indent=4)

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="$", case_insensitive=True, intents=intents)
bot.add_cog(Courses(bot))
bot.add_cog(Events(bot))
bot.add_cog(Schedule(bot))

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_guild_join(guild:discord.guild):
    data[str(guild.id)] = {'courses':{},'users':{}}
    updateFile()
    print(f'Joined new server: {guild.name}\nid:{str(guild.id)}')

@bot.command(hidden=True, help="Gets latency for bot")
async def ping(ctx):
    await ctx.send ('<:ping_pong:772097617932320768> Pong! `{0}ms`'.format(int(bot.latency*1000)))

@bot.command(help="Info about this bot")
async def about(ctx):
    embed=discord.Embed(title="Schedule Bot", url="https://github.com/UserBlackBox/schedule-bot", description="Discord bot for timetable information based on the TDSB 2020 quadmester model", color=0x0160a7)
    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/771927466267770910/700c2fe2da53caf2a60041e7d2bf21b4.png?size=2048")
    await ctx.send(embed=embed)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

with open("token") as f:
    token = f.read().strip()

bot.run(token)
