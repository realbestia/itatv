import requests
import json
import re
import os
from fuzzywuzzy import fuzz

# URL del file config.json
CONFIG_URL = "https://raw.githubusercontent.com/realbestia/itatv/main/config.json"

# Soglia di somiglianza per considerare due nomi di canali come corrispondenti
SIMILARITY_THRESHOLD = 90
OUTPUT_FILE = "channels_italy.m3u8"
EXCLUDED_LOG_FILE = "excluded_channels.log"

BASE_URLS = [
    "https://vavoo.to"
]

# Nuovi filtri per i canali
CHANNEL_FILTERS = [
    "sky", "fox", "rai", "cine34", "real time", "crime+ investigation", "top crime", "wwe", "tennis", "k2",
    "inter", "rsi", "la 7", "la7", "la 7d", "la7d", "27 twentyseven", "premium crime", "comedy central", "super!",
    "animal planet", "hgtv", "avengers grimm channel", "catfish", "rakuten", "nickelodeon", "cartoonito", "nick jr",
    "history", "nat geo", "tv8", "canale 5", "italia", "mediaset", "rete 4",
    "focus", "iris", "discovery", "dazn", "cine 34", "la 5", "giallo", "dmax", "cielo", "eurosport", "disney+", "food", "tv 8"
]

# Nuova categorizzazione dei canali
CATEGORY_KEYWORDS = {
    "SKY": ["sky", "tv 8", "fox", "comedy central", "animal planet", "nat geo", "tv8"],
    "RAI": ["rai"],
    "MEDIASET": ["mediaset", "canale 5", "rete 4", "italia", "focus"],
    "DISCOVERY": ["discovery", "real time", "crime+ investigation", "top crime", "wwe", "hgtv"],
    "SPORT": ["sport", "dazn", "tennis", "moto", "f1", "golf"],
    "ALTRI": []
}

# Funzione per scaricare il file config.json
def load_config(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download del file di configurazione: {e}")
        return []

# Funzione per trovare il canale corrispondente nel config.json
def find_channel_info(channel_name, config_data):
    channel_name = re.sub(r"\s*\(.*?\)", "", channel_name)  # Rimuove tutto tra parentesi
    for entry in config_data:
        config_name = re.sub(r"\s*\(.*?\)", "", entry.get("tvg-name", ""))  # Rimuove tutto tra parentesi
        similarity = fuzz.token_set_ratio(channel_name.lower(), config_name.lower())
        if similarity >= SIMILARITY_THRESHOLD:
            return entry.get("tvg-id", ""), entry.get("tvg-icon", "")
    return "", ""

# Funzione per scaricare i canali
def fetch_channels(base_url):
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

# Funzione per pulire il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove tutto tra parentesi
    return name.strip()

# Funzione per filtrare i canali specifici
def filter_channels(channels, base_url):
    seen = {}
    results = []
    excluded = []
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            # Verifica se il nome del canale contiene uno dei filtri
            if any(filter_keyword.lower() in clean_name.lower() for filter_keyword in CHANNEL_FILTERS):
                count = seen.get(clean_name, 0) + 1
                seen[clean_name] = count
                if count > 1:
                    clean_name = f"{clean_name} ({count})"
                results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
            else:
                excluded.append(f"{clean_name} - ID: {ch['id']} - Country: {ch.get('country')}")
    
    return results, excluded

# Funzione per classificare il canale in base alla nuova categorizzazione
def classify_channel(name):
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword.lower() in name.lower() for keyword in keywords):
            return category
    return "ALTRI"  # Categoria predefinita se non corrisponde a nessuna altra

# Funzione per salvare il file M3U8
def save_m3u8(organized_channels, config_data):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for category, channels in organized_channels.items():
            for name, url, base_url in channels:
                tvg_id, tvg_icon = find_channel_info(name, config_data)
                tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove le parentesi anche nel nome
                f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" tvg-logo="{tvg_icon}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
                f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                f.write(f'#EXTHTTP:{{"User-Agent":"VAVOO/2.6","Referer":"{base_url}/"}}\n')
                f.write(f"{url}\n\n")

# Funzione per salvare i canali esclusi
def save_excluded_channels(excluded_channels):
    with open(EXCLUDED_LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Totale canali esclusi: {len(excluded_channels)}\n\n")
        for channel in excluded_channels:
            f.write(f"{channel}\n")

# Funzione principale
def main():
    config_data = load_config(CONFIG_URL)
    all_links = []
    all_excluded = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        filtered_channels, excluded_channels = filter_channels(channels, url)
        all_links.extend(filtered_channels)
        all_excluded.extend(excluded_channels)

    # Organizzazione dei canali
    organized_channels = {category: [] for category in CATEGORY_KEYWORDS.keys()}
    for name, url, base_url in all_links:
        category = classify_channel(name)
        organized_channels[category].append((name, url, base_url))

    # Salvataggio nel file M3U8
    save_m3u8(organized_channels, config_data)
    
    # Salvataggio dei canali esclusi
    save_excluded_channels(all_excluded)
    
    print(f"File {OUTPUT_FILE} creato con successo!")
    print(f"Log dei canali esclusi salvato in {EXCLUDED_LOG_FILE}")

if __name__ == "__main__":
    main()
