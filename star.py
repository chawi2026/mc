import os
import asyncio
import aiohttp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import uuid
import json
import sys

# ===== Colors =====
w = "\033[1;00m"
g = "\033[1;32m"
y = "\033[1;33m"
r = "\033[1;31m"
b = "\033[1;34m"
reset = "\033[0m"

# ===== Configuration =====
LOCAL_DATA_FILE = ".data.json"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def Line():
    try:
        cols = os.get_terminal_size().columns
    except:
        cols = 40
    print(f"{y}-\033[1;00m" * cols)

def Logo():
    clear()
    logo = f"""{b}
  ______   ________  ______   _______  
 /      \\ /        |/      \\ /       \\ 
/$$$$$$  |$$$$$$$$//$$$$$$  |$$$$$$$  |
$$ \\__$$/    $$ |  $$ |__$$ |$$ |__$$ |
$$      \\    $$ |  $$    $$ |$$    $$< 
 $$$$$$  |   $$ |  $$$$$$$$ |$$$$$$$  |
/  \\__$$ |   $$ |  $$ |  $$ |$$ |  $$ |
$$    $$/    $$ |  $$ |  $$ |$$ |  $$ |
 $$$$$$/     $$/   $$/   $$/ $$/   $$/ {w}
"""
    print(logo)
    Line()
    print(f"{w}[*] This tool is only for Ruijie Network Router")
    Line()

async def auto_detect_network():
    print(f"{b}[*] Detecting network parameters (MAC & Gateway IP)...{reset}")
    test_url = "http://connectivitycheck.gstatic.com/generate_204"
    headers = {"User-Agent": "Mozilla/5.0 (Android 14) AppleWebKit/537.36"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                test_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False
            ) as resp:
                if resp.status in (301, 302):
                    location = resp.headers.get("Location", "")
                    params = parse_qs(urlparse(location).query)
                    gw = params.get("gw_address") or params.get("nasip")
                    mac = params.get("mac") or params.get("umac")
                    return (gw[0] if gw else None, mac[0] if mac else None)
        except:
            pass
    return None, None

def get_session_url():
    """Ask user to paste the captive portal session URL."""
    Line()
    print(f"{y}[*] Paste the SESSION URL from your captive portal / router redirect.{reset}")
    print(f"{w}    (e.g. https://portal-as.ruijienetworks.com/api/auth/wifidog?...){reset}")
    while True:
        url = input(f"{g}[?] Session URL: {reset}").strip()
        if not url:
            print(f"{y}[!] URL cannot be empty. Please paste the session URL.{reset}")
            continue
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            print(f"{r}[!] That doesn't look like a valid URL. Try again.{reset}")
            continue
        return url

def inject_network_params(session_url, gw_ip, mac_addr):
    """Inject auto-detected (or manually entered) MAC and Gateway IP into the session URL."""
    parsed = urlparse(session_url)
    params = parse_qs(parsed.query, keep_blank_values=True)

    if mac_addr:
        params["mac"] = [mac_addr]
        print(f"{g}[+] MAC injected   : {mac_addr}{reset}")

    if gw_ip:
        params["gw_address"] = [gw_ip]
        params["nasip"] = [gw_ip]
        print(f"{g}[+] Gateway injected: {gw_ip}{reset}")

    new_query = urlencode({k: v[0] for k, v in params.items()})
    final_url = urlunparse(parsed._replace(query=new_query))
    return final_url

def open_in_browser(url):
    """Open the final URL in the default browser."""
    print(f"\n{b}[*] Final URL:{reset}")
    print(f"{w}    {url}{reset}\n")
    try:
        # For Termux, use termux-open-url if available
        os.system(f'termux-open-url "{url}" 2>/dev/null || xdg-open "{url}" 2>/dev/null || open "{url}" 2>/dev/null || start "" "{url}"')
        print(f"{g}[+] Browser opened successfully!{reset}")
    except Exception as e:
        print(f"{r}[!] Failed to open browser: {e}{reset}")
        print(f"{y}[*] Please open the URL above manually.{reset}")

async def main():
    Logo()

    # ── Step 1: Ask user for the session URL ─────────────────────────────────
    session_url = get_session_url()

    # ── Step 2: Auto-detect MAC & Gateway IP ─────────────────────────────────
    gw_ip, mac_addr = await auto_detect_network()

    if gw_ip and mac_addr:
        print(f"{g}[+] Auto-detected — MAC: {mac_addr}  |  Gateway: {gw_ip}{reset}")
    else:
        print(f"{y}[!] Auto-detection failed. Manual entry required.{reset}")
        mac_input = input(f"{g}[?] Enter MAC address (leave blank to skip): {reset}").strip()
        gw_input  = input(f"{g}[?] Enter Gateway IP  (leave blank to skip): {reset}").strip()
        if mac_input:
            mac_addr = mac_input
        if gw_input:
            gw_ip = gw_input

    # ── Step 3: Inject params into session URL & open browser ────────────────
    final_url = inject_network_params(session_url, gw_ip, mac_addr)
    open_in_browser(final_url)

    input(f"\n{reset}Press Enter to exit...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Stopped.")
