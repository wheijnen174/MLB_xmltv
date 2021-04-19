

from os import remove
import subprocess


MLB_m3u = open("MLB.m3u", "r+", encoding="latin1").read()
MLB_xml = open("MLB.xml", "r+", encoding="latin1").read()

Overig_m3u = open("Overig.m3u", "r+", encoding="latin1").read()
Overig_xml = open("Overig.xml", "r+", encoding="latin1").read()

Combined_m3u = [MLB_m3u.split("\n")[0]]
Combined_m3u_temp = [MLB_m3u.split("\n")[0]] + MLB_m3u.split("\n")[1:-1] + Overig_m3u.split("\n")[1:-1]
Combined_xml_temp = [MLB_xml.split("\n")[0], MLB_xml.split("\n")[1]]


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



Overig_xml_programs = Overig_xml.split("    <programme")[1:]
MLB_xml_programs = MLB_xml.split("    <programme")[1:]


for i in range(len(Overig_xml_programs)):
    Overig_xml_programs[i] = "    <programme" + Overig_xml_programs[i]

for i in range(len(MLB_xml_programs)):
    MLB_xml_programs[i] = "    <programme" + MLB_xml_programs[i]


XML_Channels = []

for i in range(1, len(Combined_m3u.split("\n")), 2):
    Channel = "\n".join(Combined_m3u.split("\n")[i: i+1+1])
    ChannelID = Channel[Channel.find("tvg-id")+8:]
    ChannelID = str(ChannelID[:ChannelID.find('"')])
    ChannelName = Channel[Channel.find("tvg-name")+10:]
    ChannelName = str(ChannelName[:ChannelName.find('"')])
    ChannelIcon = Channel[Channel.find("tvg-logo")+10:]
    ChannelIcon = str(ChannelIcon[:ChannelIcon.find('"')])

    XML_Channels.append("""    <channel id="{}">\n        <display-name lang="en">{}</display-name>\n        <icon src="{}"/>\n    </channel>""".format(ChannelID, ChannelName, ChannelIcon))

XML_Programs = MLB_xml_programs + Overig_xml_programs

Combined_xml = "\n".join(Combined_xml_temp + XML_Channels + XML_Programs)


remove("Combined.xml")
NewFile = open("Combined.xml", "w+", encoding="UTF-8") # , encoding="latin1"
NewFile.write(Combined_xml)
NewFile.close()



PushToGit = subprocess.run('git init')
PushToGit = subprocess.run('git add *')
PushToGit = subprocess.run('''git commit -a -m "Update of the 'Overig' schedule"''')
PushToGit = subprocess.run("git push")

