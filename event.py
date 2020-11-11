import datetime

class Event:
    name = ""
    event_type = ""
    date = datetime.datetime()

    def __init__(self, name:str, event_type:str, date:datetime.datetime=datetime.datetime.today()):
        self.name = name
        self.event_type = event_type
        self.date = date
    
    def getDateStr(self):
        return self.date.strftime("%Y/%m/%d")
    
