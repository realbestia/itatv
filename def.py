import requests
import json
import re
import os
import gzip
import lzma
import io
import time
import urllib.parse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
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

DEFAULT_LOGO = "https://static.vecteezy.com/ti/gratis-vektor/p2/7688855-tv-logo-kostenlos-vektor.jpg"  # Logo predefinito se non trovato

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

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
    """Scarica e decomprime un file EPG XML"""
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.ElementTree(ET.fromstring(response.content)).getroot()
    except (requests.RequestException, ET.ParseError) as e:
        print(f"Errore EPG: {e}")
        return None

def get_tvg_info_from_epg(tvg_name, epg_data):
    """Trova il tvg-id e il logo nel file EPG"""
    best_match = None
    best_score = 0
    best_logo = None

    for epg_root in epg_data:
        for channel in epg_root.findall("channel"):
            epg_channel_name = channel.find("display-name").text
            logo_elem = channel.find("icon")
            tvg_id = channel.get("id", "")

            if epg_channel_name:
                similarity = fuzz.token_sort_ratio(tvg_name, epg_channel_name)
                if similarity > best_score:
                    best_score = similarity
                    best_match = tvg_id
                    best_logo = logo_elem.get("src", "") if logo_elem is not None else None

                if best_score >= 95:
                    return best_match, best_logo

    return best_match if best_score >= 90 else "", best_logo

def search_logo_google(query):
    """Cerca un logo su Google Immagini e restituisce il link dell'immagine."""
    search_url = f"https://www.google.com/search?hl=en&tbm=isch&q={urllib.parse.quote(query)}+logo"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    img_tags = soup.find_all("img")
    if len(img_tags) > 1:  
        return img_tags[1]["src"]  
    return None

def search_logo_pixabay(query):
    """Cerca un logo su Pixabay."""
    search_url = f"https://pixabay.com/images/search/{urllib.parse.quote(query)}%20logo/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    img_tags = soup.find_all("img")
    if len(img_tags) > 1:
        return img_tags[1]["src"]
    return None

def find_best_logo(channel_name, epg_data):
    """Trova il logo del canale attraverso più fonti."""
    _, logo_url = get_tvg_info_from_epg(channel_name, epg_data)
    if logo_url:
        print(f"Logo trovato da EPG: {logo_url}")
        return logo_url

    logo_url = search_logo_google(channel_name)
    if logo_url:
        print(f"Logo trovato su Google: {logo_url}")
        return logo_url

    logo_url = search_logo_pixabay(channel_name)
    if logo_url:
        print(f"Logo trovato su Pixabay: {logo_url}")
        return logo_url

    print(f"Nessun logo trovato per {channel_name}, uso il predefinito.")
    return DEFAULT_LOGO

def save_m3u8(channels, epg_urls, epg_data):
    """Salva i canali IPTV in un file M3U8 con metadati EPG e logo"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for name, url, base_url in channels:
            tvg_id, logo_url = get_tvg_info_from_epg(name, epg_data)
            if not logo_url:  # Se non c'è un logo nell'EPG, cerca online
                logo_url = find_best_logo(name, epg_data)

            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo_url}" group-title="TV", {name}\n')
            f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    epg_data = [download_epg(url) for url in EPG_URLS if download_epg(url)]

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))

    save_m3u8(all_links, EPG_URLS, epg_data)

if __name__ == "__main__":
    main()