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

# Elenco predefinito dei loghi per i canali più conosciuti
LOGO_DATABASE = {
    "Sky Sport": "https://upload.wikimedia.org/wikipedia/commons/a/a7/Sky_Sport_Logo_2020.svg",
    "RAI": "https://upload.wikimedia.org/wikipedia/commons/0/06/Logo_RAI_2020.svg",
    "Mediaset": "https://upload.wikimedia.org/wikipedia/commons/f/f9/Logo_Mediaset_2020.svg",
    "Eurosport": "https://upload.wikimedia.org/wikipedia/commons/7/7d/Eurosport_logo_2019.svg",
    "MTV": "https://upload.wikimedia.org/wikipedia/commons/4/42/MTV_logo.svg",
    "Fox": "https://upload.wikimedia.org/wikipedia/commons/1/12/Fox_Networks_Group_logo.svg"
}

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def normalize_for_matching(name):
    """Normalizza il nome solo per il confronto (rimuove .it, (BACKUP) e converte numeri in lettere)"""
    # Rimuove .it per il matching
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    # Rimuove testo tra parentesi (es. (BACKUP), (HD), ecc.)
    temp_name = re.sub(r"\(.*?\)", "", temp_name)
    # Rimuove caratteri speciali
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()

    # Rimuove i numeri e li converte in parole se necessario
    number_match = re.search(r"\b\d+\b", temp_name)
    number = number_match.group() if number_match else None

    if number and number in NUMBER_WORDS:
        temp_name = temp_name.replace(number, NUMBER_WORDS[number])

    return temp_name, number  # Restituisce il nome normalizzato e il numero trovato

def get_channel_logo(tvg_name):
    """Restituisce il logo del canale dalla lista predefinita"""
    return LOGO_DATABASE.get(tvg_name, None)

def save_m3u8(organized_channels, epg_urls, epg_data):
    """Salva i canali IPTV in un file M3U8 con metadati EPG e TVG Logo"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_id = get_tvg_id_from_epg(name, epg_data)
                    logo_url = get_channel_logo(name)  # Ottiene il logo predefinito

                    if logo_url:
                        f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-logo="{logo_url}", {name}\n')
                    else:
                        f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}", {name}\n')

                    f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    epg_data = [download_epg(url) for url in EPG_URLS if (data := download_epg(url))]

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

    save_m3u8(organized_channels, EPG_URLS, epg_data)

if __name__ == "__main__":
    main()