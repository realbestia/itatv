import requests
import json
import re
import os
import time

# URL sorgenti IPTV
BASE_URLS = [
    "https://vavoo.to",
]

OUTPUT_FILE = "channels_italy.m3u8"

# URL del config JSON
EPG_CONFIG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/config.json"

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

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def normalize_for_matching(name):
    """Normalizza il nome solo per il confronto"""
    # Rimuove .it per il matching
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    # Rimuove testo tra parentesi
    temp_name = re.sub(r"\[.*?\]|\(.*?\)", "", temp_name)
    # Rimuove caratteri speciali
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()

    # Rimuove i numeri e li converte in parole se necessario
    number_match = re.search(r"\b\d+\b", temp_name)
    number = number_match.group() if number_match else None

    if number and number in NUMBER_WORDS:
        temp_name = temp_name.replace(number, NUMBER_WORDS[number])

    return temp_name, number

def fetch_channels(base_url, retries=3):
    """Scarica i canali IPTV con gestione errori"""
    for attempt in range(retries):
        try:
            response = requests.get(f"{base_url}/channels", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Errore durante il download da {base_url} (tentativo {attempt+1}): {e}")
            if attempt < retries - 1:  # Se non è l'ultimo tentativo
                time.sleep(2 ** attempt)
                continue
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

def download_epg_config():
    """Scarica e carica il file di configurazione JSON EPG"""
    try:
        response = requests.get(EPG_CONFIG_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download del config EPG: {e}")
        return []

def get_tvg_id_and_icon_from_config(tvg_name, epg_config):
    """
    Trova tvg-id e tvg-icon cercando un match esatto del tvg-name nel config JSON.
    
    Args:
        tvg_name (str): Nome del canale da cercare
        epg_config (list): Lista di configurazioni dei canali
    
    Returns:
        tuple: (tvg-id, tvg-icon) del canale se trovato, altrimenti ("", "")
    """
    # Normalizza il nome del canale da cercare
    normalized_search_name = clean_channel_name(tvg_name).upper()
    
    # Cerca un match esatto nel config
    for channel in epg_config:
        config_name = channel.get("tvg-name", "").upper()
        if config_name == normalized_search_name:
            return channel.get("tvg-id", ""), channel.get("tvg-icon", "")
            
    # Se non trova un match esatto, prova a cercare se il nome è contenuto
    for channel in epg_config:
        config_name = channel.get("tvg-name", "").upper()
        if config_name in normalized_search_name or normalized_search_name in config_name:
            return channel.get("tvg-id", ""), channel.get("tvg-icon", "")
    
    # Se non trova nessun match, ritorna valori vuoti
    return "", ""

def save_m3u8(organized_channels, epg_config):
    """Salva i canali IPTV in un file M3U8 con metadati EPG"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{EPG_CONFIG_URL}"\n\n')

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_id, tvg_icon = get_tvg_id_and_icon_from_config(name, epg_config)
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-icon="{tvg_icon}", {name}\n')
                    f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    # Scarica la configurazione EPG
    epg_config = download_epg_config()
    if not epg_config:
        print("Errore: Impossibile scaricare la configurazione EPG")
        return

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

    save_m3u8(organized_channels, epg_config)

if __name__ == "__main__":
    main()
