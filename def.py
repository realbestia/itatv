import requests
import json
import re
import os
import time
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz

BASE_URLS = ["https://vavoo.to"]
OUTPUT_FILE = "channels_italy.m3u8"
EPG_URLS = ["https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/merged_epg.xml"]
CONFIG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/config.json"

NUMBER_WORDS = {
    "1": "uno", "2": "due", "3": "tre", "4": "quattro",
    "5": "cinque", "6": "sei", "7": "sette", "8": "otto", "9": "nove",
    "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici", "14": "quattordici",
    "15": "quindici", "16": "sedici", "17": "diciassette", "18": "diciotto", "19": "diciannove",
    "20": "venti"
}

SERVICE_KEYWORDS = {"Sky": ["sky", "fox", "hbo"], "DTT": ["rai", "mediaset", "focus", "boing"], "IPTV gratuite": ["radio", "local", "regional", "free"]}
CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"], "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"], "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"], "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"], "Musica": ["mtv", "vh1", "radio", "music"]
}

def download_config():
    """Scarica il file config.json"""
    try:
        response = requests.get(CONFIG_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download del file config.json: {e}")
        return []

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def normalize_for_matching(name):
    """Normalizza il nome solo per il confronto (rimuove .it, (BACKUP) e converte numeri in lettere)"""
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

        if similarity > 90:  # Accetta solo un buon match
            best_match = channel.get("tvg-id")
            best_icon = channel.get("tvg-icon")
            break  # Esci dopo aver trovato il miglior match

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

def download_epg(epg_url):
    """Scarica e decomprime un file EPG XML (anche GZIP/XZ)"""
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()

        file_signature = response.content[:2]

        if file_signature.startswith(b'\x1f\x8b'):  
            with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz_file:
                xml_content = gz_file.read()
        elif file_signature.startswith(b'\xfd7z'):  
            with lzma.LZMAFile(fileobj=io.BytesIO(response.content)) as xz_file:
                xml_content = xz_file.read()
        else:  
            xml_content = response.content

        return ET.ElementTree(ET.fromstring(xml_content)).getroot()

    except (requests.RequestException, gzip.BadGzipFile, lzma.LZMAError, ET.ParseError) as e:
        print(f"Errore durante il download/parsing dell'EPG da {epg_url}: {e}")
        return None

def save_m3u8(organized_channels, epg_urls, epg_data, config_data):
    """Salva i canali IPTV in un file M3U8 con metadati EPG"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    # Trova il miglior tvg-id e tvg-icon dal config.json
                    tvg_id, tvg_icon = get_tvg_id_and_icon_from_config(name, config_data)
                    if not tvg_id:
                        tvg_id = name  # Se non troviamo un tvg-id, usiamo il nome del canale come tvg-id
                    if not tvg_icon:
                        tvg_icon = ""  # Se non troviamo un'icona, lasciala vuota

                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-icon="{tvg_icon}", {name}\n')
                    f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    # Scarica il file config.json
    config_data = download_config()
    if not config_data:
        print("Impossibile ottenere i dati dal file config.json.")
        return

    epg_data = [download_epg(url) for url in EPG_URLS if (data := download_epg(url))]

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))

    # Organizzazione dei canali in base a servizio e categoria
    organized_channels = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}
    for name, url, base_url in all_links:
        service = "IPTV gratuita"
        category = "Intrattenimento"
        for key, words in SERVICE_KEYWORDS.items():
            if any(word in name.lower() for word in words):
                service =
