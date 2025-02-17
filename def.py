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

DEFAULT_LOGO = "https://static.vecteezy.com/ti/gratis-vektor/p2/7688855-tv-logo-kostenlos-vektor.jpg"

def clean_channel_name(name):
    """Pulisce il nome rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def normalize_for_matching(name):
    """Normalizza il nome per migliorare il matching"""
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    temp_name = re.sub(r"\(.*?\)", "", temp_name)
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()
    return temp_name

def fetch_channels(base_url):
    """Scarica i canali IPTV"""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore nel download da {base_url}: {e}")
        return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali italiani"""
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
    except (requests.RequestException, ET.ParseError) as e:
        print(f"Errore nel download/parsing dell'EPG da {epg_url}: {e}")
        return None

def get_tvg_id_and_icon_from_epg(tvg_name, epg_data):
    """Trova il miglior tvg-id e il link dell'icona dal file EPG"""
    best_match = None
    best_score = 0
    icon_url = None

    normalized_tvg_name = normalize_for_matching(tvg_name)

    for epg_root in epg_data:
        for channel in epg_root.findall("channel"):
            epg_channel_name = channel.find("display-name").text
            if not epg_channel_name:
                continue  

            normalized_epg_name = normalize_for_matching(epg_channel_name)
            similarity = fuzz.token_sort_ratio(normalized_tvg_name, normalized_epg_name)

            if similarity > best_score:
                best_score = similarity
                best_match = channel.get("id")

                icon_element = channel.find("icon")
                if icon_element is not None:
                    icon_url = icon_element.get("src")  

            if best_score >= 95:
                return best_match, icon_url

    return best_match if best_score >= 90 else "", icon_url

def search_logo_google(query):
    """Cerca un logo su Google Immagini"""
    search_url = f"https://www.google.com/search?hl=en&tbm=isch&q={urllib.parse.quote(query)}+logo"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        img_tags = soup.find_all("img")
        if len(img_tags) > 1:
            return img_tags[1]["src"]  
    except requests.RequestException:
        pass
    return None

def find_best_logo(channel_name, epg_data):
    """Trova il logo migliore tra EPG e Google"""
    _, logo_url = get_tvg_id_and_icon_from_epg(channel_name, epg_data)
    if logo_url:
        return logo_url

    logo_url = search_logo_google(channel_name)
    if logo_url:
        return logo_url

    return DEFAULT_LOGO

def save_m3u8(channels, epg_urls, epg_data):
    """Salva i canali IPTV in un file M3U8"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for name, url, base_url in channels:
            tvg_id, logo_url = get_tvg_id_and_icon_from_epg(name, epg_data)
            if not logo_url:  
                logo_url = find_best_logo(name, epg_data)

            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" tvg-logo="{logo_url}" group-title="TV", {name}\n')
            f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    epg_data = [download_epg(url) for url in EPG_URLS if download_epg(url)]
    if not epg_data:
        print("❌ Nessun file EPG caricato. Controlla gli URL.")
        return

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        all_links.extend(filter_italian_channels(channels, url))

    save_m3u8(all_links, EPG_URLS, epg_data)

if __name__ == "__main__":
    main()