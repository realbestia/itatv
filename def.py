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

# Mappa numeri → parole
NUMBER_WORDS = {
    "1": "uno", "2": "due", "3": "tre", "4": "quattro",
    "5": "cinque", "6": "sei", "7": "sette", "8": "otto", "9": "nove",
    "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici", "14": "quattordici",
    "15": "quindici", "16": "sedici", "17": "diciassette", "18": "diciotto", "19": "diciannove",
    "20": "venti"
}

# Mappatura dei servizi e delle categorie
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
    "Musica": ["mtv", "vh1", "radio", "music"],
    "Altro": []  # Categoria di default
}

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def fetch_channels(base_url, retries=3):
    """Scarica i canali IPTV con gestione errori"""
    for attempt in range(retries):
        try:
            response = requests.get(f"{base_url}/channels", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Errore durante il download da {base_url} (tentativo {attempt+1}): {e}")
            time.sleep(2 ** attempt)  
    return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani e rimuove duplicati"""
    results = {}
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            if clean_name not in results:
                results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url)
    
    return list(results.values())

def download_epg(epg_url):
    """Scarica e decomprime un file EPG XML"""
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.ElementTree(ET.fromstring(response.content)).getroot()
    except (requests.RequestException, ET.ParseError) as e:
        print(f"Errore durante il download/parsing dell'EPG da {epg_url}: {e}")
        return None

def get_tvg_id_and_icon_from_epg(tvg_name, epg_data):
    """Trova il miglior tvg-id e il link dell'icona dal file EPG"""
    best_match = None
    best_score = 0
    icon_url = None

    for epg_root in epg_data:
        for channel in epg_root.findall("channel"):
            epg_channel_name = channel.find("display-name").text
            if not epg_channel_name:
                continue  

            similarity = fuzz.token_sort_ratio(tvg_name.lower(), epg_channel_name.lower())

            if similarity > best_score:
                best_score = similarity
                best_match = channel.get("id")
                icon_element = channel.find("icon")
                if icon_element is not None:
                    icon_url = icon_element.get("src")

            if best_score >= 95:
                return best_match, icon_url

    return best_match if best_score >= 90 else "", icon_url

def assign_category(channel_name):
    """Assegna la categoria in base al nome del canale"""
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in channel_name.lower() for keyword in keywords):
            return category
    return "Altro"  # Se non corrisponde a nessuna categoria

def save_m3u8(channels, epg_urls, epg_data):
    """Salva i canali IPTV in un file M3U8"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for name, url, base_url in channels:
            tvg_id, icon_url = get_tvg_id_and_icon_from_epg(name, epg_data)
            category = assign_category(name)

            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-logo="{icon_url}", {name}\n')
            f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    epg_data = [download_epg(url) for url in EPG_URLS if download_epg(url)]
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))

    save_m3u8(all_links, EPG_URLS, epg_data)

if __name__ == "__main__":
    main()