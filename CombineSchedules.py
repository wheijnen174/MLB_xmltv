

from os import remove
import subprocess


MLB_m3u = open("MLB.m3u", "r+", encoding="latin1").read()
MLB_xml = open("MLB.xml", "r+", encoding="latin1").read()

Overig_m3u = open("Overig.m3u", "r+", encoding="latin1").read()
Overig_xml = open("Overig.xml", "r+", encoding="latin1").read()

Combined_m3u = [MLB_m3u.split("\n")[0]]
Combined_m3u_temp = [MLB_m3u.split("\n")[0]] + MLB_m3u.split("\n")[1:-1] + Overig_m3u.split("\n")[1:-1]
Combined_xml = [MLB_xml.split("\n")[0], MLB_xml.split("\n")[1]]


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










PushToGit = subprocess.run('git init')
PushToGit = subprocess.run('git add *')
PushToGit = subprocess.run('''git commit -a -m "Update of the 'Overig' schedule"''')
PushToGit = subprocess.run("git push")

