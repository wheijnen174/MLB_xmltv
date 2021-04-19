

import pandas as pd
from os import remove
import requests
import json
from datetime import datetime, timedelta
from dateutil import tz
import subprocess
import time




while True:
    dfTeams_1 = pd.read_csv("Teams.csv", sep=";")
    dfTeams_2 = pd.read_csv("TeamNames.csv", sep=",")

    #---------------------------------------------------------------------------------

    M3U_Base = """#EXTM3U\n"""

    Template = """#EXTINF:0 tvg-id="{}" CUID="{}" tvg-chno="{}" tvg-name="{}" tvg-logo="{}" group-title="MLB",{}\n{}\n"""


    M3U_Text = M3U_Base

    for i in range(len(dfTeams_1)):
        ChannelID = dfTeams_1.iloc[i,1]
        ChannelName = dfTeams_1.iloc[i,2]
        ChannelLogo = dfTeams_1.iloc[i,3]
        StreamLink = "http://192.168.2.23:71{}/".format(str(dfTeams_1.iloc[i,0]).zfill(2))
        
        M3U_Text = M3U_Text + Template.format(ChannelID, ChannelID, ChannelID, ChannelName, ChannelLogo, ChannelName, StreamLink)


    remove("MLB.m3u")
    NewFile = open("MLB.m3u", "w+", encoding="latin1")
    NewFile.write(M3U_Text)
    NewFile.close()

    #---------------------------------------------------------------------------------

    XML_Base = open("XML_base_MLB.txt", "r+", encoding="latin1").read()
    XML_Text = XML_Base
    XML_End = """\n</tv>"""

    TemplateProgramming = """\n    <programme start="{} +0000" stop="{} +0000" channel="{}">
            <title lang="en">{}</title>
            <previously-shown/>
            <icon src="{}"/>
            <desc lang="en">{}</desc>
        </programme>"""


    dfSchedule_temp = pd.DataFrame()

    Schedule_StartDate = (datetime.today() - timedelta(days=2)).strftime("%Y-%m-%d")
    Schedule_EndDate = (datetime.today() + timedelta(days=10)).strftime("%Y-%m-%d")

    Schedule = json.loads(requests.get("http://statsapi.mlb.com/api/v1/schedule/games/?sportId=1&startDate={}&endDate={}".format(Schedule_StartDate, Schedule_EndDate)).text)

    for i in range(len(Schedule['dates'])):
        ScheduleDate = Schedule['dates'][i]

        Games = ScheduleDate['games']

        for Game in Games:
            if Game['status']['detailedState'] != "Postponed":
                StartTime = datetime.strptime(Game['gameDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()) - timedelta(hours=2) - timedelta(minutes=45)
                EndTime = StartTime + timedelta(hours=5, minutes=15)

                StartTime = StartTime.strftime("%Y%m%d%H%M%S")
                EndTime = EndTime.strftime("%Y%m%d%H%M%S")

                OfficialDate = datetime.strptime(Game['officialDate'], "%Y-%m-%d").strftime("%B %d, %Y")

                HomeTeam_Full = Game['teams']['home']['team']['name']
                HomeTeam_Abbr = dfTeams_2[dfTeams_2['TeamID'] == dfTeams_1[dfTeams_1['FullName'] == HomeTeam_Full].reset_index(drop=True)['TeamID'][0]].reset_index(drop=True)['TeamAbbrev'][0].upper()
                HomeTeam_Short = dfTeams_2[dfTeams_2['TeamID'] == dfTeams_1[dfTeams_1['FullName'] == HomeTeam_Full].reset_index(drop=True)['TeamID'][0]].reset_index(drop=True)['TeamName'][0]
                AwayTeam_Full = Game['teams']['away']['team']['name']
                AwayTeam_Abbr = dfTeams_2[dfTeams_2['TeamID'] == dfTeams_1[dfTeams_1['FullName'] == AwayTeam_Full].reset_index(drop=True)['TeamID'][0]].reset_index(drop=True)['TeamAbbrev'][0].upper()
                AwayTeam_Short = dfTeams_2[dfTeams_2['TeamID'] == dfTeams_1[dfTeams_1['FullName'] == AwayTeam_Full].reset_index(drop=True)['TeamID'][0]].reset_index(drop=True)['TeamName'][0]

                Venue = Game['venue']['name']

                GameType = Game['dayNight']
                GameNumber = str(Game['seriesGameNumber']) + "/" + str(Game['gamesInSeries'])

                FirstPitchTime = datetime.strptime(Game['gameDate'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=tz.tzutc()).astimezone(tz.tzlocal()).strftime("%H:%M")

                ProgramDesc = "Live streaming of a {} game ({} of the series) of the {} at the {}. First pitch is at {}. This game is played at {} on {}".format(GameType.lower(), GameNumber, AwayTeam_Full, HomeTeam_Full, FirstPitchTime, Venue, OfficialDate)

                HomeChannel = dfTeams_1[dfTeams_1['FullName'] == HomeTeam_Full].reset_index(drop=True)['Channel Number'][0]
                HomeIcon = dfTeams_1[dfTeams_1['FullName'] == HomeTeam_Full].reset_index(drop=True)['LogoURL'][0]
                HomeTitle = HomeTeam_Short + " vs " + AwayTeam_Short + " ({})".format(FirstPitchTime)

                AwayChannel = dfTeams_1[dfTeams_1['FullName'] == AwayTeam_Full].reset_index(drop=True)['Channel Number'][0]
                AwayIcon = dfTeams_1[dfTeams_1['FullName'] == AwayTeam_Full].reset_index(drop=True)['LogoURL'][0]
                AwayTitle = AwayTeam_Short + " @ " + HomeTeam_Short + " ({})".format(FirstPitchTime)


                dfSchedule_temp = pd.concat([dfSchedule_temp, pd.DataFrame([StartTime, EndTime, HomeChannel, HomeTitle, HomeIcon, "", AwayChannel, AwayTitle, AwayIcon, ProgramDesc]).transpose(), pd.DataFrame([StartTime, EndTime, AwayChannel, AwayTitle, AwayIcon, "@", HomeChannel, HomeTitle, HomeIcon, ProgramDesc]).transpose()]).reset_index(drop=True)

    dfSchedule_temp.columns = ["StartTime", "EndTime", "HomeChannel", "HomeTitle", "HomeIcon", "HomeAway", "AwayChannel", "AwayTitle", "AwayIcon", "ProgramDesc"]
    dfSchedule_temp = dfSchedule_temp.sort_values(["HomeChannel", "StartTime"]).reset_index(drop=True)


    dfSchedule = pd.DataFrame()

    for i in range(30):
        dfSchedule_team = dfSchedule_temp[dfSchedule_temp['HomeChannel'] == i+1].reset_index(drop=True)

        NoOfGames = len(dfSchedule_team)

        for x in range(NoOfGames):
            if x == 0:
                NoStream_start = datetime.strptime(Schedule_StartDate, "%Y-%m-%d").strftime("%Y%m%d%H%M%S")
                NoStream_end = dfSchedule_team.iloc[x,0]
                NoStream_channel = dfSchedule_team.iloc[x,2]
                NoStream_title = "No streaming"
                NoStream_icon = "https://upload.wikimedia.org/wikipedia/en/thumb/a/a6/Major_League_Baseball_logo.svg/1920px-Major_League_Baseball_logo.svg.png"
                NoStream_desc = "At this time, there is no game available."
                HomeAway = ""
                AwayChannel = ""
                AwayTitle = ""
                AwayIcon = ""

                dfSchedule_team_nostream = pd.DataFrame([NoStream_start, NoStream_end, NoStream_channel, NoStream_title, NoStream_icon, HomeAway, AwayChannel, AwayTitle, AwayIcon, NoStream_desc]).transpose()
                dfSchedule_team_nostream.columns = ["StartTime", "EndTime", "HomeChannel", "HomeTitle", "HomeIcon", "HomeAway", "AwayChannel", "AwayTitle", "AwayIcon", "ProgramDesc"]

                dfSchedule_team = dfSchedule_team.append(dfSchedule_team_nostream).reset_index(drop=True)

            if x != NoOfGames-1:
                NoStream_start = dfSchedule_team.iloc[x,1]
                NoStream_end = dfSchedule_team.iloc[x+1,0]
                NoStream_channel = dfSchedule_team.iloc[x,2]
                NoStream_title = "No streaming"
                NoStream_icon = "https://upload.wikimedia.org/wikipedia/en/thumb/a/a6/Major_League_Baseball_logo.svg/1920px-Major_League_Baseball_logo.svg.png"
                NoStream_desc = "At this time, there is no game available."
                HomeAway = ""
                AwayChannel = ""
                AwayTitle = ""
                AwayIcon = ""

                dfSchedule_team_nostream = pd.DataFrame([NoStream_start, NoStream_end, NoStream_channel, NoStream_title, NoStream_icon, HomeAway, AwayChannel, AwayTitle, AwayIcon, NoStream_desc]).transpose()
                dfSchedule_team_nostream.columns = ["StartTime", "EndTime", "HomeChannel", "HomeTitle", "HomeIcon", "HomeAway", "AwayChannel", "AwayTitle", "AwayIcon", "ProgramDesc"]

                dfSchedule_team = dfSchedule_team.append(dfSchedule_team_nostream).reset_index(drop=True)

            if x == NoOfGames-1:
                NoStream_start = dfSchedule_team.iloc[x,1]
                NoStream_end = (datetime.strptime(Schedule_EndDate, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y%m%d%H%M%S")
                NoStream_channel = dfSchedule_team.iloc[x,2]
                NoStream_title = "No streaming"
                NoStream_icon = "https://upload.wikimedia.org/wikipedia/en/thumb/a/a6/Major_League_Baseball_logo.svg/1920px-Major_League_Baseball_logo.svg.png"
                NoStream_desc = "At this time, there is no game available."
                HomeAway = ""
                AwayChannel = ""
                AwayTitle = ""
                AwayIcon = ""

                dfSchedule_team_nostream = pd.DataFrame([NoStream_start, NoStream_end, NoStream_channel, NoStream_title, NoStream_icon, HomeAway, AwayChannel, AwayTitle, AwayIcon, NoStream_desc]).transpose()
                dfSchedule_team_nostream.columns = ["StartTime", "EndTime", "HomeChannel", "HomeTitle", "HomeIcon", "HomeAway", "AwayChannel", "AwayTitle", "AwayIcon", "ProgramDesc"]

                dfSchedule_team = dfSchedule_team.append(dfSchedule_team_nostream).reset_index(drop=True)

        dfSchedule = pd.concat([dfSchedule, dfSchedule_team]).reset_index(drop=True)

    dfSchedule = dfSchedule.sort_values(["HomeChannel", "StartTime"]).reset_index(drop=True)


    for i in range(len(dfSchedule)):
        StartTime = dfSchedule.iloc[i,0]
        EndTime = dfSchedule.iloc[i,1]
        HomeChannel = dfSchedule.iloc[i,2]
        HomeTitle = dfSchedule.iloc[i,3]
        HomeIcon = dfSchedule.iloc[i,4]
        ProgramDesc = dfSchedule.iloc[i,9]

        Program = TemplateProgramming.format(StartTime, EndTime, HomeChannel, HomeTitle, HomeIcon, ProgramDesc)

        XML_Text = XML_Text + Program



    XML_Text = XML_Text + XML_End

    remove("MLB.xml")
    NewFile = open("MLB.xml", "w+", encoding="latin1")
    NewFile.write(XML_Text)
    NewFile.close()

    dfSchedule.to_csv("Schedule_MLB.csv", index=False, sep=";")

    PushToGit = subprocess.run('git init')
    PushToGit = subprocess.run('git add *')
    PushToGit = subprocess.run('git commit -a -m "Update of the MLB schedule"')
    PushToGit = subprocess.run("git push")

    print("Schedule updated.")

    time.sleep(60*60)


