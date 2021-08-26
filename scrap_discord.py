#!/bin/python
import time
import sys

from requests_html import HTMLSession
import discord_unapi as discord_api
import argparse
import json

from pathlib import Path

# Argparse
parse = argparse.ArgumentParser(description="scrap discord")
parse.add_argument('-c','--channel-id',type=int,help='gather a specified channel', action='store')
parse.add_argument('-g','--guild-id',type=int,help='gather all guilds channel', action='store')
parse.add_argument('-d', '--disboard', help='scrap disboard channels', action='store_true')
parse.add_argument('-o','--output', help='output file', action='store')
parse.add_argument('-A','--authentication', help='discord authentication')

# Set discord_unapi auth
discord_api.setAuth('AUTHENTICATION KEY')

# Terminal colors
class C:
    pur = '\033[95m'
    blu = '\033[94m'
    cya = '\033[96m'
    gre = '\033[92m'
    ora = '\033[93m'
    red = '\033[91m'
    ec = '\033[0m'
    bold = '\033[1m'
    underline = '\033[4m'

# Util functions
def printc(string, color:C):
    sys.stderr.write(color + string + C.ec + '\n')

def inputc(string, color:C):
    return input(color+string+C.ec)

def setc(color:C):
    print(color, end="")

def endc():
    print(C.ec)

def printJson(dict):
    data = json.dumps(dict, indent=3)
    print(data)

def dictTojstr(dict):
    return json.dumps(dict)

def printd(str:str, opt=""):
    debug_str = f"{C.red} [ DEBUG {opt}] {C.ec} "; setc(C.ora)
    print(f"{debug_str} {str}\n")
    endc()

class AppendJson():
    """Append to a json file faster, without reading the entire file."""

    def __init__(self, file):
        self.file   = Path(file)
        self.ended  = False
    
    def append(self, object:dict):
        """Append object to a file"""
        object = dictTojstr(object)

        if (not self.file.is_file()):
            data = "[\n"
            data += f"\t{object},\n"

            with self.file.open("w", encoding="utf8") as f:
                f.write(data)
            return
        
        with self.file.open("a") as f:
            data = f"\t{object},\n"
            f.write(data)
    
    def end(self):
        """Remove json appending last newlines and close ] list """

        if (self.ended):
            return

        with self.file.open("r+b") as f: 
            try:
                count = -4
                while True:
                    f.seek(count, 2)
                    loaded = f.read()
                    f.seek(count, 2)

                    if (b",\n" in loaded):
                        loaded = loaded.replace(b",", b"")
                        f.write(loaded+b"]")
                        break

                    count -= 4

            except:
                pass

# Filter messages function
def filter(messages:list, min_len=5, max_len=500):
    # Filter some messages
    ban_prefixes = tuple("! @ # $ % & * _ - + = ; . / http https".split(" "))
    filtered = []

    try:
        for x in messages:
            if x['content'].startswith(ban_prefixes):
                continue
            try:
                if x['content']['athor']['bot'] == True:
                    continue
            except:
                pass

            filtered.append(x)
    
        return filtered
    except:
        return []

# Scrap a single channel
def scrap_channel(channel_id, output, name=None):
    split = 50000 # split files every x messages
    splitted = 0
    increment=100 # max messages get per request is 100
    count = 0
    last = False # last message id
    completed=False

    printc(f"Scrapping {name}", C.ora)
    jsonAp = AppendJson(output)

    while not completed:
        messages = discord_api.read_messages(channel_id, increment, before=last)
        count += increment

        # Filter messages
        if (not messages):
            try:
                jsonAp.end()
            except:
                pass
            printc("Error, none messages.", C.red)
            completed = True
            continue

        messages = filter(messages)
        printc(f"messages: {count}", C.blu)

        # Split in small files
        if (count%split == 0):
            print("Spliting channel in multiple files")
            splitted += 1
            count = 0

            jsonAp.end()
            jsonAp = AppendJson(f"{output}-{splitted}")

        # Append every message
        for m in messages:
            jsonAp.append(m)

        # get last message
        try:
            last = messages[-1]["id"]
        except:
            #completed!
            try: jsonAp.end()
            except: pass

            print("Completed!")
            completed = True

# Scrap all guild channels
def scrap_guild(guild, output_f="./scrapped"):
    "Scrap a guild with a given guild object or guild id<int>"

    if (type(guild) == dict):
        guild_id = guild['id']
        guild_name = guild['name']
    elif (type(guild) == int):
        guild_id = guild
        guild_name = discord_api.get_guild_info(guild_id)['name']
    else:
        print("Error, passed guild is not a int id or a dict.")
        raise TypeError()

    channels = discord_api.get_guild_channels(guild_id, 0)    

    if (not channels):
        print("Error, some how the guild do not return any channel.")
        return

    if not Path(output_f).is_dir():
        Path(output_f).mkdir()
    
    output_f+=f"/{guild_name}"

    if not Path(output_f).is_dir():
        Path(output_f).mkdir()

    with (Path(output_f)/"guild.json").open("w") as f:
        guild_info = discord_api.get_guild_info(guild_id)
        json.dump(guild_info, f, indent=4)

    for ch in channels:
        scrap_channel(ch['id'], output_f+f"/{ch['name']}.json", name=ch['name'])
        #discord_api.post_science(guild_id, ch['id'])

# Scrap x pages of disboard guilds
class Disboard_scrapper():
    """
    Scrap all disboard servers with a given tag and pages number
    this is possible by entering on each guild and scrapping each channel.
    the output folder hierarchy is
    
    ./disboard
        server0
            channel.txt
            channel.txt
        server1
            channel.txt
            channel.txt
    """

    def __init__(self, tag, pages=10, output="./disboard") -> None:
        self.tag = tag
        self.pages = pages
        self.output = output

        self.s = HTMLSession()
        self.error_count = 0
        self.db = Path(output) 
        self.gdata = (self.db/"guilds.json")  # Disboard guilds data

        if (not self.db.is_dir() ):
            self.db.mkdir()
        
        self.scrap()

    def get_disboard_guilds(self) -> list[object]:
        # Load saved
        if (self.gdata.is_file()):
            print("Loading saved disboard guilds") 
            with self.gdata.open("r", encoding="utf8") as j:
                return json.load(j)

        data = []
        for x in range(1, self.pages+1):
            url = f"https://disboard.org/servers/tag/{self.tag}/{x}"
            html = self.s.get(url).html
            servers = html.find(".server-name")

            for sv in servers:
                name = sv.find('a')[0].text
                href = sv.find('a')[0].attrs['href']
                id = href.split('/')[2]
                
                data.append({
                    "name": name,
                    "href": href,
                    "id": id
                })

        # Save
        with self.gdata.open("w", encoding="utf8") as j:
            json.dump(data, j, indent=4)
        return data

    def get_disboard_invite(self, id) -> str:
        url = f"https://disboard.org/site/get-invite/{id}"
        invite = None
        count = 0

        while (invite == None) and count < 3:
            try:
                invite = self.s.get(url).json().split('/')[-1]
                count += 1
            except:
                return None

        return invite

    def scrap(self, time_bt_guilds=4):
        guilds = self.get_disboard_guilds()
        scrapped_guilds = [x.name for x in self.db.iterdir()]
        error_count = 0

        for sv in guilds:
            if (sv['name'] in scrapped_guilds):
                print(f"Skipping {sv['name']}")
                continue # donot execute bellow
                
            invite = self.get_disboard_invite(sv['id'])

            printc(f"Scrapping Guild: {sv['name']}", C.blu)
            printc(f"Invite: {invite}\n", C.blu)

            if (error_count >= 3):
                print(f"Maybe your account {C.red} have been blocked. {C.ec}")
                exit()

            # Get guild object
            guild = discord_api.enter_guild(invite)

            if (guild == None):
                printc(f"Error, could not enter guild with invite", C.ora)
                error_count +=1
                continue
            
            guild = guild['guild']
            printd(guild, 'guild')

            # Scrap guild and leave
            scrap_guild(guild, f"disboard/{guild['name']}") 
            r = discord_api.leave_guild(guild['id'])
            printd(r, "Leaving guild.")
            time.sleep(time_bt_guilds) # delay
            error_count =0

        # Completed!
        print("Scrapping completed!")
        self.gdata.unlink(missing_ok=True)

def main():
    args = parse.parse_args()

    if args.authentication:
        discord_api.setAuth(args.authentication)

    if args.channel_id:
        scrap_channel(args.channel_id, str(args.channel_id)+'.txt')

    if args.guild_id:
        scrap_guild(args.guild_id)

    if args.disboard:
        Disboard_scrapper("brasil", pages=1)
    

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exiting...")
        pass