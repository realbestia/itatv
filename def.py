import requests
import json
import re
import os
import time
from fuzzywuzzy import fuzz

# URL sorgenti IPTV
BASE_URLS = [
    "https://vavoo.to",
]

OUTPUT_FILE = "channels_italy.m3u8"
EXCLUDED_LOG = "excluded_channels.log"

# URL del config JSON
CONFIG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/config.json"

# Lista dei canali richiesti
ALLOWED_CHANNELS = [
    "sky", "fox", "rai", "cine34", "real time", "crime+ investigation", "top crime", "wwe", "tennis", "k2",
    "inter", "rsi", "la 7", "la7", "la 7d", "la7d", "27 twentyseven", "premium crime", "comedy central", "super!",
    "animal planet", "hgtv", "avengers grimm channel", "catfish", "rakuten", "nickelodeon", "cartoonito", "nick jr",
    "history", "nat geo", "tv8", "canale 5", "italia", "mediaset", "rete 4",
    "focus", "iris", "discovery"
]

CATEGORY_MAPPING = {
    "SKY": ["sky", "tv8", "fox", "comedy central", "animal planet", "nat geo"],
    "RAI": ["rai"],
    "MEDIASET": ["mediaset", "canale 5", "rete 4", "italia", "focus"],
    "DISCOVERY": ["discovery", "real time", "crime+ investigation", "top crime", "wwe", "hgtv"],
    "ALTRI": []
}

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name, flags=re.IGNORECASE)

def fetch_channels(base_url, retries=3):
    """Scarica i canali IPTV con gestione errori"""
    for attempt in range(retries):
        try:
            response = requests.get(f"{base_url}/channels", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Errore durante il download da {base_url} (tentativo {attempt + 1}): {e}")
            time.sleep(2 ** attempt)
    return []

def assign_category(channel_name):
    """Assegna una categoria al canale in base al nome."""
    for category, keywords in CATEGORY_MAPPING.items():
        if any(keyword in channel_name for keyword in keywords):
            return category
    return "ALTRI"

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani e seleziona solo quelli nella lista ALLOWED_CHANNELS"""
    results = {}
    excluded = []
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"]).lower()
            if any(keyword in clean_name for keyword in ALLOWED_CHANNELS):
                category = assign_category(clean_name)
                results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", category)
            else:
                excluded.append(clean_name)
    
    with open(EXCLUDED_LOG, "w", encoding="utf-8") as log_file:
        for channel in excluded:
            log_file.write(channel + "\n")
    
    print(f"File {EXCLUDED_LOG} creato con la lista dei canali esclusi.")
    return list(results.values())

def save_m3u8(channels):
    """Salva i canali IPTV filtrati in un file M3U8"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U\n\n')
        for name, url, category in channels:
            f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{category}", {name}\n')
            f.write(f"{url}\n\n")
    
    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))
    
    save_m3u8(all_links)

if __name__ == "__main__":
    main()
