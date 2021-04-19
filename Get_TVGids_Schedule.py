

import requests, re
from urllib.parse import urljoin
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup as soup
import pandas as pd
from os import remove
import subprocess
import time
from datetime import datetime, timedelta
import pytz


def ConvertDate(Date_Input):
    Date_Input = Date_Input.split(" ")
    dfMonth = pd.read_csv("Months.csv", sep=";")
    return datetime.strptime("-".join([Date_Input[2], str(dfMonth[dfMonth['Month_NL'] == Date_Input[1]].reset_index(drop=True)['Month_Number'][0]).zfill(2), Date_Input[0]]), "%Y-%m-%d")


while True:
    Channel_URL = "espn"
    Channel_Real = "ESPN"

    DateList_URL = ['/eergisteren', '/gisteren', '', '/1', '/2', '/3', '/4', '/5', '/6']
    DateList_Real = [(datetime.today() + timedelta(days=-2)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=-1)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=0)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=3)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=4)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=5)).replace(hour=0, minute=0, second=0, microsecond=0), (datetime.today() + timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)]


    dfSchedule = pd.DataFrame()

    for i in range(len(DateList_URL)):
        Date_URL = DateList_URL[i]
        Date_Real = DateList_Real[i]

        URL = "https://www.tvgids.tv/zenders/{}{}".format(Channel_URL, Date_URL)

        req = Request(URL, headers={"User-Agent":"Mozilla/5.0"})

        page_html = urlopen(req).read()
        page_soup = soup(page_html, "html.parser")

        AllItems_URL = page_soup.find("div",{"class":"section-content"}).findAll("a",{"class":"section-item posible-progress-bar"})

        for x in range(len(AllItems_URL)):
            URL = "https://www.tvgids.tv" + AllItems_URL[x]['href']

            req = Request(URL, headers={"User-Agent":"Mozilla/5.0"})

            page_html = urlopen(req).read()
            page_soup = soup(page_html, "html.parser")

            Text = str(page_soup.find("dl",{"class":"dl-horizontal program-details"})).split("<dt>")

            Date = Text[1].strip().split("<dd>")[1].strip().replace("\n", "").replace("\t", "").replace("\r", "").replace("</dd>", "")
            Date = Date[Date.find(" ")+1:].strip()
            Date = ConvertDate(Date)

            Time = Text[2].strip().split("<dd>")[1].strip().replace("\n", "").replace("\t", "").replace("\r", "").replace("</dd>", "")
            Time = Time.split(" tot ")

            TimeStart = pytz.timezone("Europe/Amsterdam").localize(Date + timedelta(hours=int(Time[0].strip().split(":")[0]), minutes=int(Time[0].strip().split(":")[1])))
            TimeStart_UTC = TimeStart.astimezone(pytz.timezone("UTC"))
            TimeStart = TimeStart_UTC.strftime("%Y%m%d%H%M%S")

            TimeEnd = pytz.timezone("Europe/Amsterdam").localize(Date + timedelta(hours=int(Time[1].strip().split(":")[0]), minutes=int(Time[1].strip().split(":")[1])))
            TimeEnd_UTC = TimeEnd.astimezone(pytz.timezone("UTC"))
            TimeEnd = TimeEnd_UTC.strftime("%Y%m%d%H%M%S")

            Program = page_soup.find("head").find("title").text.strip()
            Program = Program[:Program.rfind(" - TV Gids")].strip()
            ProgramDesc = page_soup.find("div",{"class":"section-item gray"}).find("p").text.replace("\r", "").replace("\n\n\n", "\n\n").split("\n\n")
            ProgramDesc = ProgramDesc[0].strip() + "\n\n" + ProgramDesc[1].strip()

            dfSchedule = pd.concat([dfSchedule, pd.DataFrame([TimeStart, TimeEnd, Channel_Real, Program, ProgramDesc]).transpose()]).reset_index(drop=True)

    dfSchedule.columns = ['StartTime', 'EndTime', 'Channel', 'Program', 'ProgramDesc']
    dfSchedule = dfSchedule.sort_values(['StartTime']).drop_duplicates().reset_index(drop=True)


    dfSchedule.insert(3, "Channel_ID", 1)
    dfSchedule.insert(4, "Icon", "https://logodownload.org/wp-content/uploads/2015/05/espn-logo.png")


    XML_Base = open("XML_base_Overig.txt", "r+", encoding="latin1").read()
    XML_Text = XML_Base
    XML_End = """\n</tv>"""

    TemplateProgramming = """\n    <programme start="{} +0000" stop="{} +0000" channel="{}">
            <title lang="en">{}</title>
            <previously-shown/>
            <icon src="{}"/>
            <desc lang="en">{}</desc>
        </programme>"""


    for i in range(len(dfSchedule)):
        StartTime = dfSchedule.iloc[i,0]
        EndTime = dfSchedule.iloc[i,1]
        HomeChannel = dfSchedule.iloc[i,3]
        HomeTitle = dfSchedule.iloc[i,5]
        HomeIcon = dfSchedule.iloc[i,4]
        ProgramDesc = dfSchedule.iloc[i,6]

        Program = TemplateProgramming.format(StartTime, EndTime, HomeChannel, HomeTitle, HomeIcon, ProgramDesc)

        XML_Text = XML_Text + Program



    XML_Text = XML_Text + XML_End

    remove("Overig.xml")
    NewFile = open("Overig.xml", "w+", encoding="UTF-8") # , encoding="latin1"
    NewFile.write(XML_Text.encode().decode('latin1').encode('utf8').decode().replace("&", "en"))
    NewFile.close()

    dfSchedule.to_csv("Schedule_Overig.csv", index=False, sep=";")

    PushToGit = subprocess.run('git init')
    PushToGit = subprocess.run('git add *')
    PushToGit = subprocess.run('''git commit -a -m "Update of the 'Overig' schedule"''')
    PushToGit = subprocess.run("git push")

    print("Schedule updated.")

    time.sleep(24*60*60)

