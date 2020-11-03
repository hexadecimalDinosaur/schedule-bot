# schedule-bot
Discord bot for timetable information based on the TDSB 2020 quadmester model

## Instructions
Install the `discord` module using pip, run `bot.py` using python3 with the `data.json` in the working directory

Only one instance of the bot should be used per server as the json database is shared among all servers the bot is present in

## Usage
`$list` - list all joinable courses

`$join [code]` - add a course to your schedule

`$leave [code]` - remove a course from your schedule

`$courses` - view your courses

`$schedule` - view your schedule for today

`$schedule [YYYY/MM/DD]` - view your schedule on a specific day

### Admin Commands
`addcourse [code] [quad] [teacher] [day]` - create a joinable course

Day argument should be 4 letters long with `o` representing online afternoon class, `i` representing independent learning, `s` representing in school. Ex. `oois` is day 1 and 2 online, day 3 independent, and day 4 in school.

`delcourse [code]` - delete a course