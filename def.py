import requests
import json
import re
import os
import gzip
import lzma
import io
import time
import shutil
import xml.etree.ElementTree as ET
import concurrent.futures
from rapidfuzz import fuzz

# URL sorgenti IPTV
BASE_URLS = [
    "https://vavoo.to",
]

OUTPUT_FILE = "channels_italy.m3u8"

# URL degli EPG
EPG_URLS = [
    "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/merged_epg.xml"
]

# Numeri in lettere fino a 99
NUMBER_WORDS = {
    "0": "zero", "1": "uno", "2": "due", "3": "tre", "4": "quattro",
    "5": "cinque", "6": "sei", "7": "sette", "8": "otto", "9": "nove",
    "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici", "14": "quattordici",
    "15": "quindici", "16": "sedici", "17": "diciassette", "18": "diciotto", "19": "diciannove",
    "20": "venti", "30": "trenta", "40": "quaranta", "50": "cinquanta",
    "60": "sessanta", "70": "settanta", "80": "ottanta", "90": "novanta",
}

def convert_number_to_words(number):
    """Converte un numero in lettere fino a 99."""
    if number in NUMBER_WORDS:
        return NUMBER_WORDS[number]
    
    if 21 <= number <= 99:
        tens = (number // 10) * 10  
        units = number % 10  

        if units in [1, 8]:
            return NUMBER_WORDS[tens][:-1] + NUMBER_WORDS[str(units)]
        else:
            return NUMBER_WORDS[tens] + NUMBER_WORDS[str(units)]
    
    return str(number)

# Mappatura servizi e categorie
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

session = requests.Session()

def clean_channel_name(name):
    """Pulisce il nome del canale IPTV."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def normalize_for_matching(name):
    """Normalizza il nome per il confronto."""
    temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
    temp_name = re.sub(r"\(.*?\)", "", temp_name)
    temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()

    number_match = re.search(r"\b\d+\b", temp_name)
    number = number_match.group() if number_match else None

    if number and number in NUMBER_WORDS:
        temp_name = temp_name.replace(number, convert_number_to_words(int(number)))

    return temp_name, number

def fetch_channels(base_url, retries=3):
    """Scarica i canali IPTV con gestione errori."""
    for attempt in range(retries):
        try:
            response = session.get(f"{base_url}/channels", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Errore download {base_url} (tentativo {attempt+1}): {e}")
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

def download_epg(epg_url):
    """Scarica e decomprime un file EPG XML in modo efficiente."""
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

        return ET.iterparse(io.BytesIO(xml_content), events=("start", "end"))

    except Exception as e:
        print(f"Errore download/parsing EPG {epg_url}: {e}")
        return None

def save_m3u8(channels):
    """Salva i canali IPTV in un file M3U8."""
    temp_file = OUTPUT_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(EPG_URLS)}"\n\n')
        for name, url, base_url in channels:
            f.write(f'#EXTINF:-1 tvg-name="{name}", {name}\n{url}\n\n')

    shutil.move(temp_file, OUTPUT_FILE)
    print(f"File {OUTPUT_FILE} creato con successo!")

def fetch_all_channels():
    """Scarica i canali IPTV in parallelo."""
    all_links = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(fetch_channels, url): url for url in BASE_URLS}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            try:
                channels = future.result()
                all_links.extend(filter_italian_channels(channels, url))
            except Exception as e:
                print(f"Errore nel download da {url}: {e}")
    return all_links

def main():
    all_links = fetch_all_channels()
    save_m3u8(all_links)

if __name__ == "__main__":
    main()