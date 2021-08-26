#!/bin/python
import argparse
import ujson as json
#import json

from pathlib import Path

argparser = argparse.ArgumentParser()
argparser.add_argument("data", help="data file or folder:->folders->data.json")
argparser.add_argument("-o", "--output_dir", help="output folder")
argparser.add_argument("-p", "--per-sequence", action="store_true", help="Separates discord messages per user sequence")
argparser.add_argument('-ps','--prefix-sufix', action="store", help='Prefix:sufix of the parsed messages, default = "<|START|>\n:<|END|>\n" ')
args = argparser.parse_args()

class Data_parser():

    def __init__(self, data_path:str, prefix="<|START|>\n", sufix="<|END|>\n") -> None:
        self.data = Path(data_path)
        self.output = Path(f"{data_path}_parsed")
        self.output.mkdir(exist_ok=True)

        self.prefix = prefix
        self.suffix = sufix

    def per_sequence(self):
        "Separate messages per user sequence and data"

        def parse(messages, file:Path):
            def write(content):
                with file.open("a") as f:
                    f.write(content)

            current_author = None
            last_author    = None
            count = 1

            for m in messages:
                try:
                    # Ignore bots
                    if (m['author']['bot']):
                        continue
                except:
                    pass

                try:
                    # With messages
                    if not (m['content']) or (m['content'] == ""):
                        continue
                except:
                    return

                current_author = m['author']['username']
                text = ""

                if (count/100).is_integer():
                    print("Parsed:", count)

                if (current_author != last_author and last_author != None):
                    text += self.suffix

                if (current_author != last_author) or (last_author == None):
                    text += self.prefix

                text += (f"{m['content']}\n")

                write(text)
                last_author = current_author
                count += 1

            if (count > 1):
                write(self.suffix)

        def load(file:Path):
            try:
                with file.open("r") as f:
                    for x in reversed(json.load(f)):
                        yield x
            except:
                return []
        
        if (self.data.is_dir()): 
            for folder in self.data.iterdir():  # {Data} -> [Guilds] -> [channels.json]

                if ( not folder.is_dir()):
                    return
                
                files = [ x for x in folder.iterdir()] 
                guild_name = folder.name
                guild_parsed = (self.output/guild_name)

                try:
                    guild_parsed.mkdir()
                except:
                    print(f"Skipping {guild_name}")
                    continue
                
                print(f"Parsing Guild: {guild_name}")

                for channel in files:
                    channel_name = channel.name.split(".")[0]
                    channel_outp = (guild_parsed/f"{channel_name}.txt")
                    channel_outp.unlink(missing_ok=True)

                    print(f"Parsing {channel_name}")
                    try:
                        messages = load(channel)
                    except:
                        print(f"Can't load {channel}")
                        continue
                    parse(messages, channel_outp)
                    print("") 

        if ( self.data.is_file()):
            messages = load(self.data)
            parse(messages)

def main():

    if args.prefix_sufix:
        p = args.prefix_sufix.split(":")[0]
        s = args.prefix_sufix.split(":")[1]
        data_parser = Data_parser(args.data, prefix=p, sufix=s)

    else:
        data_parser = Data_parser(args.data)

    if args.per_sequence:
        data_parser.per_sequence()


main()