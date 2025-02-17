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

# URL delle sorgenti IPTV
BASE_URLS = [
    "https://vavoo.to",
]

# Liste M3U8 extra
EXTRA_M3U8_URLS = [
    "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"
]

OUTPUT_FILE = "channels_italy.m3u8"

# URL degli EPG
EPG_URLS = [
    "https://www.epgitalia.tv/gzip",
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
    "https://www.open-epg.com/files/italy1.xml",
    "https://www.open-epg.com/files/italy2.xml",
    "https://epgshare01.online/epgshare01/epg_ripper_RAKUTEN_IT1.xml.gz"
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

def normalize_name(name):
    """Normalizza il nome del canale per il confronto."""
    name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"[^\w\s]", "", name).strip().lower()

    number_match = re.search(r"\b\d+\b", name)
    number = number_match.group() if number_match else None

    if number and number in NUMBER_WORDS:
        name = name.replace(number, NUMBER_WORDS[number])

    return name, number

def fetch_channels(base_url):
    """Scarica i canali IPTV e restituisce una lista."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore nel download da {base_url}: {e}")
        return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani e rimuove duplicati."""
    results = {}
    for ch in channels:
        if ch.get("country") == "Italy":
            name = ch["name"]
            url = f"{base_url}/play/{ch['id']}/index.m3u8"
            results[name] = (name, url, base_url)
    return list(results.values())

def download_epg(epg_url):
    """Scarica e decomprime un file EPG XML (GZIP/XZ supportati)."""
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        content = response.content

        if content.startswith(b'\x1f\x8b'):
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz_file:
                content = gz_file.read()
        elif content.startswith(b'\xfd7z'):
            with lzma.LZMAFile(fileobj=io.BytesIO(content)) as xz_file:
                content = xz_file.read()
        
        return ET.ElementTree(ET.fromstring(content)).getroot()
    except Exception as e:
        print(f"Errore nel download/parsing dell'EPG {epg_url}: {e}")
        return None

def get_tvg_id_from_epg(tvg_name, epg_data):
    """Trova il miglior tvg-id confrontando i nomi con l'EPG."""
    best_match = None
    best_score = 0

    for epg_root in epg_data:
        for channel in epg_root.findall("channel"):
            epg_channel_name = channel.find("display-name").text
            if epg_channel_name:
                score = fuzz.token_sort_ratio(tvg_name.lower(), epg_channel_name.lower())
                if score > best_score:
                    best_score = score
                    best_match = channel.get("id")

                if best_score >= 95:
                    return best_match

    return best_match if best_score >= 90 else ""

def classify_channel(name):
    """Assegna un servizio e una categoria a un canale."""
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

    return service, category

def save_m3u8(channels, epg_urls, epg_data, extra_m3u8_urls):
    """Salva i canali IPTV in un file M3U8 con metadati EPG e liste extra."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for name, url, base_url in channels:
            service, category = classify_channel(name)
            tvg_id = get_tvg_id_from_epg(name, epg_data)
            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}", {name}\n')
            f.write(f"{url}\n\n")

        for extra_url in extra_m3u8_urls:
            m3u8_content = fetch_channels(extra_url)
            if m3u8_content:
                f.write(m3u8_content + "\n\n")

    print(f"File {OUTPUT_FILE} generato con successo!")

def main():
    """Esegue il processo di raccolta e salvataggio delle liste IPTV."""
    epg_data = [download_epg(url) for url in EPG_URLS if download_epg(url)]
    
    all_channels = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_channels.extend(filter_italian_channels(channels, url))

    save_m3u8(all_channels, EPG_URLS, epg_data, EXTRA_M3U8_URLS)

if __name__ == "__main__":
    main()