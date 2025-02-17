import requests
import json
import re
import os
import gzip
import lzma
import io
import time
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz

# URL sorgenti IPTV
BASE_URLS = [
    "https://vavoo.to",
]

OUTPUT_FILE = "channels_italy.m3u8"

# URL degli EPG
EPG_URLS = [
    "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/merged_epg.xml"
]

SERVICE_KEYWORDS = {
    "Sky": ["sky", "fox", "hbo"],
    "DTT": ["rai", "mediaset", "focus", "boing"],
    "IPTV gratuite": ["radio", "local", "regional", "free"]
}

CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def fetch_channels(base_url):
    """Scarica i canali IPTV con gestione errori."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
    return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani e rimuove duplicati."""
    results = {}
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            if clean_name not in results:
                results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url)
    return list(results.values())

def download_epg(epg_url):
    """Scarica e decomprime un file EPG XML."""
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.ElementTree(ET.fromstring(response.content)).getroot()
    except requests.RequestException as e:
        print(f"Errore durante il download/parsing dell'EPG da {epg_url}: {e}")
        return None

def get_tvg_logo(channel_name):
    """Genera un URL per il logo del canale."""
    formatted_name = channel_name.lower().replace(" ", "_")
    return f"https://logo.clearbit.com/{formatted_name}.com"

def organize_channels(channels):
    """Organizza i canali in base a servizio e categoria."""
    organized_channels = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        service = "IPTV gratuite"
        category = "Intrattenimento"

        for key, words in SERVICE_KEYWORDS.items():
            if any(word in name.lower() for word in words):
                service = key
                break

        for key, words in CATEGORY_KEYWORDS.items():
            if any(word in name.lower() for word in words):
                category = key
                break

        organized_channels[service][category].append((name, url, base_url))

    return organized_channels

def save_m3u8(organized_channels, epg_urls):
    """Salva i canali IPTV in un file M3U8."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_logo = get_tvg_logo(name)
                    f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{tvg_logo}" group-title="{category}", {name}\n')
                    f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    epg_data = [download_epg(url) for url in EPG_URLS if (download_epg(url) is not None)]

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))

    organized_channels = organize_channels(all_links)
    save_m3u8(organized_channels, EPG_URLS)

if __name__ == "__main__":
    main()