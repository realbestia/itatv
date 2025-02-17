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
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurazione delle URL e delle mappature
BASE_URLS = [
    "https://vavoo.to"
]
OUTPUT_FILE = "channels_italy.m3u8"
EPG_URLS = [
    "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/merged_epg.xml"
]
NUMBER_WORDS = {
    "1": "uno", "2": "due", "3": "tre", "4": "quattro",
    "5": "cinque", "6": "sei", "7": "sette", "8": "otto", "9": "nove",
    "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici", "14": "quattordici",
    "15": "quindici", "16": "sedici", "17": "diciassette", "18": "diciotto", "19": "diciannove",
    "20": "venti"
}
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

def normalize_for_matching(name):
    """Normalizza il nome solo per il confronto (rimuove .it, (BACKUP) e converte numeri in lettere)."""
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    temp_name = re.sub(r"\(.*?\)", "", temp_name)
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()

    number_match = re.search(r"\b\d+\b", temp_name)
    number = number_match.group() if number_match else None

    if number and number in NUMBER_WORDS:
        temp_name = temp_name.replace(number, NUMBER_WORDS[number])

    return temp_name, number

def fetch_channels(base_url, retries=3):
    """Scarica i canali IPTV con gestione errori."""
    for attempt in range(retries):
        try:
            response = requests.get(f"{base_url}/channels", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logging.error(f"Errore durante il download da {base_url} (tentativo {attempt+1}): {e}")
            time.sleep(2 ** attempt)  
    return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani e rimuove duplicati."""
    results = {}
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            if clean_name not in results:
                results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url)
 results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url)

    return results

def fetch_epg_data(epg_urls):
    """Scarica i dati EPG da URL forniti."""
    epg_data = []
    for url in epg_urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            epg_data.append(response.content)
        except requests.RequestException as e:
            logging.error(f"Errore durante il download EPG da {url}: {e}")
    return epg_data

def parse_epg_data(epg_data):
    """Parsa i dati EPG e restituisce un dizionario di eventi."""
    events = {}
    for data in epg_data:
        root = ET.fromstring(data)
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            for programme in channel.findall('programme'):
                start = programme.get('start')
                end = programme.get('end')
                title = programme.find('title').text
                events[channel_id] = {
                    'start': start,
                    'end': end,
                    'title': title
                }
    return events

def save_channels_to_file(channels, output_file):
    """Salva i canali IPTV in un file M3U8."""
    with open(output_file, 'w') as f:
        f.write("#EXTM3U\n")
        for channel in channels.values():
            f.write(f"#EXTINF:-1,{channel[0]}\n")
            f.write(f"{channel[1]}\n")

def main():
    all_channels = {}
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_channels, url) for url in BASE_URLS]
        for future in futures:
            channels = future.result()
            filtered_channels = filter_italian_channels(channels, BASE_URLS[0])
            all_channels.update(filtered_channels)

    epg_data = fetch_epg_data(EPG_URLS)
    parsed_epg = parse_epg_data(epg_data)

    save_channels_to_file(all_channels, OUTPUT_FILE)
    logging.info(f"Canali salvati in {OUTPUT_FILE}")

if __name__ == "__main__":
    main()