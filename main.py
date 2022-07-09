import asyncio
import websocket
import json

with open("tokens.txt", "r") as f:
    tokens = f.read().splitlines()

import requests
import time
import random

def CheckAccount(token):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "authorization": token
        }

        res = requests.get('https://discord.com/api/v10/users/@me', headers=headers)

        if res.status_code == 200:

            return [token, f"{res.json()['username']}#{res.json()['discriminator']}"]

        return res.json()

def GetSession(Token: str):
    ws = websocket.WebSocket()
    ws.connect("wss://gateway.discord.gg/?v=10&encoding=json")
    heartbeat_interval = json.loads(ws.recv())["d"]["heartbeat_interval"] / 1000

    ws.send(
        json.dumps(
            {
                "op": 2,
                "d": {
                    "token": Token,
                    "properties": {
                        "os": "windows",
                        "browser": "chrome",
                        "device": "pc",
                    },
                },
            }
        )
    )

    event = json.loads(ws.recv())

    if event["op"] == 9:
        return GetSession(Token)

    return event["d"]["sessions"][0]["session_id"]

class UserClient:
    def __init__(self, userdata, config, settings):
        self.user = userdata
        self.config = config
        self.settings = settings
        self.session = GetSession(self.user['token'])
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
            "authorization": self.user['token']
        }
        self.cols = {
            "r": "\033[31m",
            "g": "\033[32m",
            "b": "\033[36m",
            "y": "\033[33m"
        }
    
    def Request(self, method, url, payload:dict=None):
        if not payload:
            return requests.request(method, url, headers=self.headers)
        return requests.request(method, url, json=payload, headers=self.headers)

    def DiscordRoute(self, path, version="v10"):
        return f"https://discord.com/api/{version}/{path}"

    def Sleep(self, delay, multiplier):
        START = time.time() * multiplier
        while (START + delay >= time.time() * multiplier):
            pass

    def SendMessage(self, message):
        self.Request('POST', self.DiscordRoute(f'channels/{self.user["channel"]}/typing'))

        if self.settings['suspicion']['enabled']:
            TYPING = self.settings['suspicion']['typing']
            self.Sleep(random.randint(TYPING[0], TYPING[1]), 1000)

        message = self.Request('POST', self.DiscordRoute(f'channels/{self.user["channel"]}/messages'), payload={'content': message})

        if message.status_code == 200:
            return message.json()
        return None

    def DeleteMessage(self, message):
       return self.Request('DELETE', self.DiscordRoute(f'channels/{self.user["channel"]}/messages/{message}')).status_code

    def GetMessages(self):
        return self.Request('GET', self.DiscordRoute(f'channels/{self.user["channel"]}/messages'))

    def Reconnect(self):
        self.session = GetSession(self.user['token'])

if __name__ == "__main__":
    c = []

    async def Run():
        for token in tokens:
            try:
                user = CheckAccount(token)
                print(user)
                c.append(UserClient({"token": token, "user": user[1], "channel": 995284829958574133}, {}, {"suspicion": {
                    "enabled": True,
                    "typing": [450, 550],
                    "button": [350, 430],
                    "run": 10800,
                    "pause": 5400
                }}))
            except:
                pass

        for cs in c:
            cs.SendMessage("Connected")

        while 1:
            for cs in c:
                cs.Reconnect()

            time.sleep(120)

    asyncio.run(Run())
