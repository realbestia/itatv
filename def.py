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
CONFIG_FILE = "config.json"

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


def load_config():
    """Carica la lista EPG da config.json"""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Errore nel caricamento del file config.json: {e}")
        return []


def clean_channel_name(name):
    """Pulisce il nome del canale rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)


def normalize_for_matching(name):
    """Normalizza il nome per il confronto."""
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    temp_name = re.sub(r"\(.*?\)", "", temp_name)
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()
    return temp_name


def fetch_channels(base_url, retries=3):
    """Scarica i canali IPTV con gestione errori."""
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
    """Filtra i canali italiani e rimuove duplicati."""
    results = {}
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            if clean_name not in results:
                results[clean_name] = (clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url)
    return list(results.values())


def get_tvg_id_and_icon_from_config(tvg_name, epg_list):
    """Trova il miglior tvg-id e tvg-icon dal config.json"""
    best_match = None
    best_score = 0
    best_icon = None

    normalized_tvg_name = normalize_for_matching(tvg_name)

    for epg_entry in epg_list:
        epg_name = epg_entry["tvg-name"]
        epg_id = epg_entry["tvg-id"]
        epg_icon = epg_entry.get("tvg-icon", "")
        
        normalized_epg_name = normalize_for_matching(epg_name)
        similarity = fuzz.token_sort_ratio(normalized_tvg_name, normalized_epg_name)

        if similarity > best_score:
            best_score = similarity
            best_match = epg_id
            best_icon = epg_icon

        if best_score >= 99:
            return best_match, best_icon

    return best_match if best_score >= 90 else "", best_icon


def save_m3u8(organized_channels, epg_list):
    """Salva i canali IPTV in un file M3U8 con metadati EPG."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('#EXTM3U\n\n')
        
        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_id, tvg_icon = get_tvg_id_and_icon_from_config(name, epg_list)
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-icon="{tvg_icon}", {name}\n')
                    f.write(f"{url}\n\n")
    
    print(f"File {OUTPUT_FILE} creato con successo!")


def main():
    epg_list = load_config()  # Carica la lista EPG dal config.json

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

    save_m3u8(organized_channels, epg_list)


if __name__ == "__main__":
    main()
