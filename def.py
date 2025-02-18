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
    "Sport": ["sport", "dazn", "eurosport"],
    "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["canale", "dmax", "rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music", "kisskiss"]
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

def assign_category(channel_name):
    """Assegna la miglior categoria per un canale utilizzando fuzzy matching"""
    best_category = "Intrattenimento"  # Categoria predefinita
    best_score = 0  

    normalized_name = channel_name.lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            similarity = fuzz.partial_ratio(normalized_name, keyword)

            if similarity > best_score:  # Trova il miglior match
                best_score = similarity
                best_category = category

            if best_score >= 90:  # Se trova un match quasi perfetto, assegna subito
                return best_category

    return best_category  # Restituisce la miglior categoria trovata

def get_tvg_id_and_icon_from_epg(tvg_name, epg_data):
    """Trova il miglior tvg-id e tvg-icon senza modificare il nome originale nel file M3U8"""
    best_match = None
    best_score = 0
    best_icon = None

    normalized_tvg_name, tvg_number = normalize_for_matching(tvg_name)

    for epg_root in epg_data:
        for channel in epg_root.findall("channel"):
            epg_channel_name = channel.find("display-name").text
            if not epg_channel_name:
                continue  

            normalized_epg_name, epg_number = normalize_for_matching(epg_channel_name)

            # Se uno ha un numero e l'altro no, scarta il match
            if (tvg_number and not epg_number) or (epg_number and not tvg_number):
                continue  
            
            # Se entrambi hanno un numero, devono essere uguali
            if tvg_number and epg_number and tvg_number != epg_number:
                continue  

            # Utilizza diverse metriche di corrispondenza fuzzy
            similarity = fuzz.token_sort_ratio(normalized_tvg_name, normalized_epg_name)

            if similarity > best_score:
                best_score = similarity
                best_match = channel.get("id")
                best_icon = channel.find("icon").get("src") if channel.find("icon") is not None else None

            # Restituisci il miglior match se la somiglianza è sopra la soglia
            if best_score >= 90:
                return best_match, best_icon

    # Restituisci il miglior match se la somiglianza è sopra una soglia inferiore
    return best_match if best_score >= 85 else "", best_icon

def save_m3u8(organized_channels, epg_urls, epg_data):
    """Salva i canali IPTV in un file M3U8 con metadati EPG"""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_id, tvg_icon = get_tvg_id_and_icon_from_epg(name, epg_data)
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-icon="{tvg_icon}", {name}\n')
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
        category = assign_category(name)  # Assegna la categoria usando fuzzy matching
        for key, words in SERVICE_KEYWORDS.items():
            if any(word in name.lower() for word in words):
                service = key
                break

        organized_channels[service][category].append((name, url, base_url))

    save_m3u8(organized_channels, EPG_URLS, epg_data)

if __name__ == "__main__":
    main()