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
    "1": "uno", "2": "due", "3": "tre", "4": "quattro", "5": "cinque",
    "6": "sei", "7": "sette", "8": "otto", "9": "nove", "10": "dieci",
}

def convert_number_to_words(number):
    """Converte un numero in lettere fino a 99."""
    if number in NUMBER_WORDS:
        return NUMBER_WORDS[number]
    return str(number)

# Categorie IPTV
CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney"],
    "Documentari": ["discovery", "geo", "history", "nat geo"],
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

        return ET.fromstring(xml_content)

    except Exception as e:
        print(f"Errore download/parsing EPG {epg_url}: {e}")
        return None

def get_tvg_id_and_icon(channel_name, epg_data):
    """Trova il tvg-id e l'icona migliore per un canale."""
    best_match = None
    best_score = 0
    best_icon = None

    normalized_name, _ = normalize_for_matching(channel_name)

    for epg in epg_data:
        for channel in epg.findall("channel"):
            epg_name = channel.find("display-name").text
            if not epg_name:
                continue  

            normalized_epg_name, _ = normalize_for_matching(epg_name)
            similarity = fuzz.token_sort_ratio(normalized_name, normalized_epg_name)

            if similarity > best_score:
                best_score = similarity
                best_match = channel.get("id")
                best_icon = channel.find("icon").get("src") if channel.find("icon") is not None else None

            if best_score >= 90:
                return best_match, best_icon

    return best_match if best_score >= 85 else "", best_icon

def categorize_channel(channel_name):
    """Assegna una categoria IPTV in base al nome."""
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(word in channel_name.lower() for word in keywords):
            return category
    return "Altro"

def save_m3u8(channels, epg_data):
    """Salva i canali IPTV in un file M3U8 con categorie e metadati EPG."""
    temp_file = OUTPUT_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(EPG_URLS)}"\n\n')
        for name, url, _ in channels:
            tvg_id, tvg_icon = get_tvg_id_and_icon(name, epg_data)
            category = categorize_channel(name)
            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-icon="{tvg_icon}", {name}\n')
            f.write(f"{url}\n\n")

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
    epg_data = [download_epg(url) for url in EPG_URLS if download_epg(url)]
    all_links = fetch_all_channels()
    save_m3u8(all_links, epg_data)

if __name__ == "__main__":
    main()