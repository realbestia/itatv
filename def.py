import requests
import json
import re
import os
import xml.etree.ElementTree as ET

# URL dei siti da cui scaricare i canali IPTV
BASE_URLS = [
    "https://vavoo.to",
    # "https://huhu.to",
    # "https://kool.to",
    # "https://oha.to"
]

# File di output
OUTPUT_FILE = "channels_italy.m3u8"

# Lista dei link EPG
EPG_URLS = [
    "https://www.open-epg.com/files/italy1.xml",
    "https://www.open-epg.com/files/italy2.xml"
]

# Mappatura servizi
SERVICE_KEYWORDS = {
    "Sky": ["sky", "fox", "hbo"],
    "DTT": ["rai", "mediaset", "focus", "boing"],
    "IPTV gratuite": ["radio", "local", "regional", "free"]
}

# Mappatura categorie tematiche
CATEGORY_KEYWORDS = {
    "Bambini": ["baby", "boing", "cartoon", "disney", "nick"],
    "Documentari": ["arte", "discovery", "documentary", "geo", "history", "nat geo", "nature"],
    "Film & Serie TV": ["cinema", "film", "fox", "hbo", "movie", "primafila", "serie"],
    "Intrattenimento": ["focus", "italia", "mediaset", "rai", "real time"],
    "Musica": ["mtv", "music", "radio", "vh1"],
    "News": ["news", "rai news", "sky tg", "tg", "tgcom"],
    "Sport": ["dazn", "eurosport", "rai sport", "sky sport", "sport"]
}

# Funzione per scaricare le liste EPG e caricarle in un dizionario
def load_epg_channels(epg_urls):
    epg_channels = {}
    for epg_url in epg_urls:
        try:
            print(f"🔄 Scaricamento EPG: {epg_url}")
            response = requests.get(epg_url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)

            for channel in root.findall("channel"):
                channel_id = channel.get("id")
                display_name = channel.find("display-name").text if channel.find("display-name") is not None else channel_id
                epg_channels[display_name.lower()] = channel_id  # Match case-insensitive
        except requests.RequestException as e:
            print(f"❌ Errore nel download dell'EPG {epg_url}: {e}")
        except ET.ParseError as e:
            print(f"❌ Errore nel parsing dell'EPG {epg_url}: {e}")
    
    return epg_channels

# Carica i dati delle EPG
EPG_CHANNELS = load_epg_channels(EPG_URLS)

# Funzione per pulire il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*\(.*?\)\s*", "", name)  # Rimuove testo tra parentesi
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s|\(H\d*\)|\(V\d*\))\s*", "", name)  # Rimuove tag extra
    return name.strip()

# Funzione per ottenere il tvg-id solo se presente nell'EPG
def get_tvg_id(channel_name):
    clean_name = clean_channel_name(channel_name)
    return EPG_CHANNELS.get(clean_name.lower(), "")  # Restituisce il channel ID dell'EPG o stringa vuota

# Funzione per classificare un canale in servizio e categoria
def classify_channel(name):
    service = "IPTV gratuite"  # Default
    category = "Intrattenimento"  # Default

    for key, words in SERVICE_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            service = key
            break

    for key, words in CATEGORY_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            category = key
            break

    return service, category

# Funzione per estrarre user-agent dal dominio
def extract_user_agent(base_url):
    match = re.search(r"https?://([^/.]+)", base_url)
    if match:
        return match.group(1).upper()
    return "DEFAULT"

# Funzione per scaricare i canali dai siti
def fetch_channels(base_url):
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"❌ Errore durante il download da {base_url}: {e}")
        return []

# Funzione per filtrare i canali italiani
def filter_italian_channels(channels):
    seen = set()
    results = []

    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            url = ch.get("url", "")  # Se 'url' non esiste, usa una stringa vuota
            source = ch.get("source", "Unknown")  # Se 'source' non esiste, metti "Unknown"

            if url:  # Aggiungi solo se l'URL è valido
                if clean_name not in seen:  # Evita duplicati
                    seen.add(clean_name)
                    results.append((clean_name, url, source))

    return results

# Funzione per organizzare i canali per servizio e categoria
def organize_channels(channels):
    organized_data = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        tvg_id = get_tvg_id(name)  # Ottieni il tvg-id se esiste, altrimenti ""
        service, category = classify_channel(name)
        user_agent = extract_user_agent(base_url)
        organized_data[service][category].append((name, url, base_url, tvg_id, user_agent))

    # Ordina i canali dentro ogni categoria dalla A alla Z
    for service in organized_data:
        for category in organized_data[service]:
            organized_data[service][category].sort(key=lambda x: x[0].lower())

    return organized_data

# Funzione per salvare il file M3U8
def save_m3u8(organized_channels):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url, tvg_id, user_agent in channels:
                    tvg_id_str = f'tvg-id="{tvg_id}" ' if tvg_id else ""  # Se il tvg-id è vuoto, lo omettiamo
                    f.write(f'#EXTINF:-1 {tvg_id_str}tvg-name="{name}" group-title="{category}",{name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent={user_agent}/1.0\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'{url}\n\n')

# Funzione principale
def main():
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels)
        all_links.extend(italian_channels)

    organized_channels = organize_channels(all_links)
    save_m3u8(organized_channels)

    print(f"✅ File {OUTPUT_FILE} creato con successo!")

# Esegui lo script
if __name__ == "__main__":
    main()