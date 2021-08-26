#!/usr/bin/python3 

import requests
import time
import json
from random import randrange

from requests.api import request

headers = {
    "Authorization" : "",
    "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.309 Chrome/83.0.4103.122 Electron/9.3.5 Safari/537.36",
}

def setAuth(x:str):
    global headers
    headers["Authorization"] = x

def printJson(str):
    data = json.dumps(str, indent=3)
    print(data)

def vrfy_error(response, json=True):
    """Return response, if has error print and return none."""

    if (json): # Verify json response errors, and return dict
        try:
            response = response.json()
        except:
            print(f"[ DISCORD API ERROR] : {response.text}")
            r = None

        try:
            print(f"[ DISCORD API ERROR ]  {response['message']}") # if has Error message
            response = None
        except:
            pass
    
    return response

def get_guild_info(guild_id):
    r = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}", headers=headers)
    return r.json()

def enter_guild(invite:str):
    headers2 = {
        "Host": "discord.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Accept": "*/*",
        "Accept-Language": "en-US",
        "Authorization": headers['Authorization'],
    }

    r = requests.post(f'https://discord.com/api/v9/invites/{invite}', headers=headers2)
    r = vrfy_error(r)
    return r

def leave_guild(guild_id):
    url = f"https://discord.com/api/v9/users/@me/guilds/{guild_id}"
    return requests.delete(url, headers=headers, data={"lurking":False}).status_code

def get_guild_channels(guild_id:int, type:int):
    r = requests.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=headers)
    r = vrfy_error(r); 

    if (r != None):
        r  = [ x for x in r if x['type'] == 0]

    return r

def get_user_guilds():
    r = requests.get(f"https://discord.com/api/v9/users/@me/guilds", headers=headers)
    r = vrfy_error(r)
    return r

def change_status(status:int):
    if status == 0:
        string = '{"status":"invisible"}'
    if status == 1:
        string = '{"status":"dnd"}'
    if status == 2:
        string = '{"status":"idle"}'
    if status == 3:
        string = '{"status":"online"}'

    headers["Content-Type"] = "application/json"
    
    url = f"https://discord.com/api/v9/users/@me/settings"
    res = requests.patch(url, string, headers=headers)
    return res.json()

def loop_status(min=0, cooldown=0.5, list_:list=False):
    if list_:
        status = list_[0]
        count = 0

        while True:
            if status == list_[-1]:
                count =0
            
            status = list_[count]
            change_status(status)
            time.sleep(cooldown)
            count+=1
    else:
        status = min
        while True:
            if status > 3:
                status = min

            change_status(status)
            time.sleep(cooldown)
            status+=1

def read_messages(channel_id, count, before=False) -> list:
    url = f"https://discord.com/api/v8/channels/{str(channel_id)}/messages?limit={count}"
    if before:
        url += f"&before={str(before)}"

    res = requests.get(url, headers=headers)
    res = vrfy_error(res)
    return res

def read_message(channel_id, message_id):
    url = f"https://discord.com/api/v8/channels/{str(channel_id)}/messages/{str(message_id)}"
    res = requests.get(url, headers=headers)
    return res.json()

def send_message(channel_id,message:str):
    message ={"content": message}

    url= f"https://discord.com/api/v6/channels/{str(channel_id)}/messages"
    res = requests.post(url, headers=headers, data=message)
    return res

def react_message(channel, message_id, reaction):
    url = f"https://discord.com/api/v9/channels/{channel}/messages/{message_id}/reactions/{reaction}/%40me"

def send_friend_request(name, number):
    url = f"https://discord.com/api/v9/users/@me/relationships"
    body = {"username":name,"discriminator":int(number)}
    res = requests.post(url, data=body, headers=headers)
    return res.json()

def relationships():
    url='https://discord.com/api/v9/users/@me/relationships'
    res = requests.post(url,headers=headers)

def get_server_info(id:int):
    url=f'https://discord.com/api/v9/guilds/{id}/members/@me?lurker=true&session_id=fb72548ff73619eb3fdee1cbe1c012a9'
    res = requests.put(url,headers=headers)
    return res.json()