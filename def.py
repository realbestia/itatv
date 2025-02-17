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
    "https://www.epgitalia.tv/gzip",
    "https://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
    "https://www.open-epg.com/files/italy1.xml",
    "https://www.open-epg.com/files/italy2.xml",
    "https://epgshare01.online/epgshare01/epg_ripper_RAKUTEN_IT1.xml.gz"
]

# Liste M3U8 esterne
EXTRA_M3U8_URLS = [
    "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"
]

# Categorie canali
CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

def fetch_channels(base_url):
    """Scarica i canali IPTV e restituisce una lista di tuple (nome, URL)."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore nel download da {base_url}: {e}")
        return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani e restituisce una lista di tuple (nome, URL)."""
    results = {}
    for ch in channels:
        if ch.get("country") == "Italy":
            name = ch["name"]
            url = f"{base_url}/play/{ch['id']}/index.m3u8"
            results[name] = (name, url)
    return list(results.values())

def download_epg(epg_url):
    """Scarica e decomprime un file EPG XML (anche GZIP/XZ)."""
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

def fetch_m3u8_list(url):
    """Scarica una lista M3U8 e restituisce il contenuto come stringa."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Errore nel download della lista M3U8 {url}: {e}")
        return None

def save_m3u8(channels, epg_urls, epg_data, extra_m3u8_urls):
    """Salva i canali in un file M3U8 con metadati EPG e liste extra."""
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for name, url in channels:
            tvg_id = get_tvg_id_from_epg(name, epg_data)
            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}", {name}\n')
            f.write(f"{url}\n\n")

        for extra_url in extra_m3u8_urls:
            m3u8_content = fetch_m3u8_list(extra_url)
            if m3u8_content:
                f.write(m3u8_content + "\n\n")

    print(f"File {OUTPUT_FILE} generato con successo!")

def main():
    """Esegue il processo di raccolta e salvataggio delle liste IPTV."""
    print("Scaricamento EPG...")
    epg_data = [download_epg(url) for url in EPG_URLS if download_epg(url)]
    
    print("Scaricamento canali IPTV...")
    all_channels = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_channels.extend(filter_italian_channels(channels, url))

    print("Generazione file M3U8...")
    save_m3u8(all_channels, EPG_URLS, epg_data, EXTRA_M3U8_URLS)

if __name__ == "__main__":
    main()