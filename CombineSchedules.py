

import pandas as pd
from os import remove
import subprocess


MLB_m3u = open("MLB.m3u", "r+", encoding="latin1").read()

Overig_m3u = open("Overig.m3u", "r+", encoding="latin1").read()

Combined_m3u = [MLB_m3u.split("\n")[0]]
Combined_m3u_temp = [MLB_m3u.split("\n")[0]] + MLB_m3u.split("\n")[1:-1] + Overig_m3u.split("\n")[1:-1]


for i in range(1, len(Combined_m3u_temp), 2):
    ChannelID = str(int((i-1)/2+1))
    Channel = "\n".join(Combined_m3u_temp[i:i+1+1])
    Channel = '#EXTINF:0 tvg-id="{}" CUID="{}" tvg-chno="{}" '.format(ChannelID, ChannelID, ChannelID) + Channel[Channel.find("tvg-name="):]

    Combined_m3u.append(Channel)

Combined_m3u = "\n".join(Combined_m3u)

remove("Combined.m3u")
NewFile = open("Combined.m3u", "w+", encoding="UTF-8") # , encoding="latin1"
NewFile.write(Combined_m3u)
NewFile.close()


dfSchedule_MLB = pd.read_csv("Schedule_MLB.csv", sep=";")
dfSchedule_Overig = pd.read_csv("Schedule_Overig.csv", sep=";")

dfSchedule_Combined = pd.DataFrame()

for i in range(len(dfSchedule_MLB)):
    StartTime = str(dfSchedule_MLB.iloc[i,0]).replace("&", "en")
    EndTime = str(dfSchedule_MLB.iloc[i,1]).replace("&", "en")
    Channel_ID = int(dfSchedule_MLB.iloc[i,2])
    Icon = str(dfSchedule_MLB.iloc[i,4]).replace("&", "en")
    Program = str(dfSchedule_MLB.iloc[i,3]).replace("&", "en")
    ProgramDesc = str(dfSchedule_MLB.iloc[i,9]).replace("&", "en")
    dfSchedule_Combined = pd.concat([dfSchedule_Combined, pd.DataFrame([StartTime, EndTime, Channel_ID, Icon, Program, ProgramDesc]).transpose()]).reset_index(drop=True)

for i in range(len(dfSchedule_Overig)):
    StartTime = str(dfSchedule_Overig.iloc[i,0]).replace("&", "en")
    EndTime = str(dfSchedule_Overig.iloc[i,1]).replace("&", "en")
    Channel_ID = int(dfSchedule_Overig.iloc[i,3])
    Icon = str(dfSchedule_Overig.iloc[i,4]).replace("&", "en")
    Program = str(dfSchedule_Overig.iloc[i,5]).replace("&", "en")
    ProgramDesc = str(dfSchedule_Overig.iloc[i,6]).replace("&", "en")
    dfSchedule_Combined = pd.concat([dfSchedule_Combined, pd.DataFrame([StartTime, EndTime, Channel_ID, Icon, Program, ProgramDesc]).transpose()]).reset_index(drop=True)

dfSchedule_Combined.columns = ['StartTime', 'EndTime', 'Channel_ID', 'Icon', 'Program', 'ProgramDesc']
dfSchedule_Combined = dfSchedule_Combined.sort_values(['Channel_ID', 'StartTime']).drop_duplicates().reset_index(drop=True)


XML_Base = open("XML_base_Combined.txt", "r+", encoding="latin1").read()
XML_Text = XML_Base
XML_End = """\n</tv>"""

TemplateProgramming = """\n    <programme start="{} +0000" stop="{} +0000" channel="{}">
        <title lang="en">{}</title>
        <previously-shown/>
        <icon src="{}"/>
        <desc lang="en">{}</desc>
    </programme>"""


for i in range(len(dfSchedule_Combined)):
    StartTime = dfSchedule_Combined.iloc[i,0]
    EndTime = dfSchedule_Combined.iloc[i,1]
    HomeChannel = dfSchedule_Combined.iloc[i,2]
    HomeTitle = dfSchedule_Combined.iloc[i,4]
    HomeIcon = dfSchedule_Combined.iloc[i,3]
    ProgramDesc = dfSchedule_Combined.iloc[i,5]

    Program = TemplateProgramming.format(StartTime, EndTime, HomeChannel, HomeTitle, HomeIcon, ProgramDesc)

    XML_Text = XML_Text + Program


remove("Combined.xml")
NewFile = open("Combined.xml", "w+", encoding="UTF-8") # , encoding="latin1"
NewFile.write(XML_Text)
NewFile.close()



PushToGit = subprocess.run('git init')
PushToGit = subprocess.run('git add *')
PushToGit = subprocess.run('''git commit -a -m "Update of the combined schedule"''')
PushToGit = subprocess.run("git push")

