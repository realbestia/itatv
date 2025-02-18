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
    "Musica": ["mtv", "vh1", "radio", "music"]
}

def load_epg_from_config(file_path):
    """Carica i dati EPG dal file config.json"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Errore durante il caricamento del file EPG: {e}")
        return []

# ... (resto del codice rimane invariato)

def get_tvg_id_and_icon_from_epg(tvg_name, epg_data):
    """Trova il miglior tvg-id e tvg-icon senza modificare il nome originale nel file M3U8"""
    best_match = None
    best_score = 0
    best_icon = None

    normalized_tvg_name, tvg_number = normalize_for_matching(tvg_name)

    for epg_channel in epg_data:
        epg_channel_name = epg_channel["tvg-name"]
        normalized_epg_name, epg_number = normalize_for_matching(epg_channel_name)

        # Se uno ha un numero e l'altro no, scarta il match
        if (tvg_number and not epg_number) or (epg_number and not tvg_number):
            continue  
        
        # Se entrambi hanno un numero, devono essere uguali
        if tvg_number and epg_number and tvg_number != epg_number:
            continue  

        # Utilizza diverse metriche di corrispondenza fuzzy
        similarity = fuzz.token_sort_ratio(normalized_tvg_name, normalized_epg_name)

        if similarity > best_score:
            best_score = similarity
            best_match = epg_channel["tvg-id"]
            best_icon = epg_channel["tvg-icon"]

        # Restituisci il miglior match se la somiglianza è sopra la soglia
        if best_score >= 95:
            return best_match, best_icon

    # Restituisci il miglior match se la somiglianza è sopra una soglia inferiore
    return best_match if best_score >= 90 else "", best_icon

def main():
    epg_data = load_epg_from_config('config.json')

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))

    # Organizzazione dei canali in base a servizio e categoria
    organized_channels = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}
    for name, url, base_url in all_links:
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

    save_m3u8(organized_channels, [], epg_data)

if __name__ == "__main__":
    main()
