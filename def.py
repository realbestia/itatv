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

BASE_URLS = [
    "https://vavoo.to"
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

# Funzione per filtrare i canali italiani
def filter_italian_channels(channels, base_url):
    seen = {}
    results = []
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({count})"
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    return results

# Funzione per classificare il canale per servizio e categoria
def classify_channel(name):
    service = "IPTV gratuite"  # Default
    category = "Intrattenimento"  # Default

    for key, words in SERVICE_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            service = key
            break

    for key, words in CATEGORY_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            category = key
            break

    return service, category

# Funzione per salvare il file M3U8
def save_m3u8(organized_channels, config_data):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_id, tvg_icon = find_channel_info(name, config_data)
                    tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove le parentesi anche nel nome
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" tvg-logo="{tvg_icon}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"VAVOO/2.6","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")

# Funzione principale
def main():
    config_data = load_config(CONFIG_URL)
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Organizzazione dei canali
    organized_channels = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}
    for name, url, base_url in all_links:
        service, category = classify_channel(name)
        organized_channels[service][category].append((name, url, base_url))

    # Salvataggio nel file M3U8
    save_m3u8(organized_channels, config_data)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()
