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
    """Filtra i canali italiani e mappa i nomi puliti agli URL."""
    results = {}
    for ch in channels:
        clean_name = clean_channel_name(ch['name'])
        if "italiano" in clean_name.lower():
            results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url)
    return results

def main():
    """Funzione principale per eseguire lo script."""
    all_channels = []
    for base_url in BASE_URLS:
        channels = fetch_channels(base_url)
        all_channels.extend(channels)

    italian_channels = filter_italian_channels(all_channels, BASE_URLS[0])
    
    with open(OUTPUT_FILE, 'w') as f:
        for channel in italian_channels.values():
            f.write(f"#EXTINF:-1,{channel[0]}\n{channel[1]}\n")

if __name__ == "__main__":
    main()