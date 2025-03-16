import requests
import re
import os
import xml.etree.ElementTree as ET

EPG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"
LOGOS_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logos.txt"
OUTPUT_FILE_WORLD = "world.m3u8"
DEFAULT_TVG_ICON = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logo.png"

BASE_URLS = [
    "https://vavoo.to"
]

# Scarica e analizza il file logos.txt
def fetch_logos(logos_url):
    try:
        response = requests.get(logos_url, timeout=10)
        response.raise_for_status()
        logos_data = response.text
        logos_dict = {}

        for line in logos_data.splitlines():
            match = re.match(r'\s*"(.+?)":\s*"(.+?)",?', line)
            if match:
                channel_name, logo_url = match.groups()
                logos_dict[channel_name.lower()] = logo_url

        return logos_dict
    except requests.RequestException as e:
        print(f"Errore durante il download dei loghi: {e}")
        return {}

# Scarica la lista dei canali
def fetch_channels(base_url):
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

# Pulisce il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)
    return name.strip()

# Salva il file world.m3u8 con tutti i canali dopo pulizia del nome
def save_world_m3u8(all_channels, logos_dict):
    if os.path.exists(OUTPUT_FILE_WORLD):
        os.remove(OUTPUT_FILE_WORLD)
    
    with open(OUTPUT_FILE_WORLD, "w", encoding="utf-8") as f:
        f.write('#EXTM3U\n\n')

        for name, url, base_url in all_channels:
            tvg_logo = logos_dict.get(name.lower(), DEFAULT_TVG_ICON)

            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{tvg_logo}" group-title="World" tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
            f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
            f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
            f.write(f'#EXTHTTP:{{"User-Agent":"VAVOO/2.6","Referer":"{base_url}/"}}\n')
            f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE_WORLD} creato con successo!")

# Funzione principale
def main():
    logos_dict = fetch_logos(LOGOS_URL)

    all_links = []
    
    for url in BASE_URLS:
        channels = fetch_channels(url)
        
        # Lista completa con nomi puliti per world.m3u8
        all_links.extend([(clean_channel_name(ch["name"]), f"{url}/play/{ch['id']}/index.m3u8", url) for ch in channels])

    # Salva il file world.m3u8 con tutti i canali
    save_world_m3u8(all_links, logos_dict)

if __name__ == "__main__":
    main()