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

# Funzione per caricare il file config.json locale
def load_local_config():
    """Carica il file config.json locale"""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Errore durante il caricamento di config.json: {e}")
        return []

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def normalize_for_matching(name):
    """Normalizza il nome per il confronto (rimuove .it, (BACKUP) e converte numeri in lettere)"""
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    temp_name = re.sub(r"\(.*?\)", "", temp_name)
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()
    
    number_match = re.search(r"\b\d+\b", temp_name)
    number = number_match.group() if number_match else None

    if number and number in NUMBER_WORDS:
        temp_name = temp_name.replace(number, NUMBER_WORDS[number])

    return temp_name, number

def get_tvg_id_and_icon_from_config(tvg_name, config_data):
    """Trova il miglior tvg-id e tvg-icon basato sul tvg-name dal file config.json"""
    best_match = None
    best_icon = None

    normalized_tvg_name, tvg_number = normalize_for_matching(tvg_name)

    for channel in config_data:
        config_tvg_name = channel.get("tvg-name", "")
        normalized_config_name, config_number = normalize_for_matching(config_tvg_name)

        if (tvg_number and not config_number) or (config_number and not tvg_number):
            continue  
        
        if tvg_number and config_number and tvg_number != config_number:
            continue  

        similarity = fuzz.token_sort_ratio(normalized_tvg_name, normalized_config_name)
        if similarity > 90:
            best_match = channel.get("tvg-id")
            best_icon = channel.get("tvg-icon")
            break

    return best_match, best_icon

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

def save_m3u8(channels, epg_urls, config_data):
    """Salva i canali IPTV in un file M3U8 con metadati EPG"""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')
        for name, url, base_url in channels:
            tvg_id, tvg_icon = get_tvg_id_and_icon_from_config(name, config_data)
            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-icon="{tvg_icon}", {name}\n')
            f.write(f"{url}\n\n")
    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    config_data = load_local_config()
    if not config_data:
        print("Impossibile ottenere i dati dal file config.json.")
        return
    
    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))
    
    save_m3u8(all_links, EPG_URLS, config_data)

if __name__ == "__main__":
    main()
