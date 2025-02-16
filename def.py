import requests
import xml.etree.ElementTree as ET
import gzip
from io import BytesIO
import re
import os
from fuzzywuzzy import fuzz

# Siti da cui scaricare i dati
BASE_URLS = [
    "https://vavoo.to",
    # "https://huhu.to",
    # "https://kool.to",
    # "https://oha.to"
]

OUTPUT_FILE = "channels_italy.m3u8"

# Mappatura servizi
SERVICE_KEYWORDS = {
    "Sky": ["sky", "fox", "hbo"],
    "DTT": ["rai", "mediaset", "focus", "boing"],
    "IPTV gratuite": ["radio", "local", "regional", "free"]
}

# Mappatura categorie tematiche
CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

def clean_channel_name(name):
    """Pulisce il nome del canale rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def fetch_channels(base_url):
    """Scarica i dati JSON da /channels di un sito."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali con country Italy e genera il link m3u8 con il nome del canale."""
    results = []
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])  # Rimuove caratteri indesiderati
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    
    return results

def classify_channel(name):
    """Classifica il canale per servizio e categoria tematica."""
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

def extract_user_agent(base_url):
    """Estrae il nome del sito senza estensione e lo converte in maiuscolo per l'user agent."""
    match = re.search(r"https?://([^/.]+)", base_url)
    if match:
        return match.group(1).upper()
    return "DEFAULT"

def organize_channels(channels):
    """Organizza i canali per servizio e categoria."""
    organized_data = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        service, category = classify_channel(name)
        user_agent = extract_user_agent(base_url)
        organized_data[service][category].append((name, url, base_url, user_agent))

    return organized_data

def save_m3u8(organized_channels, epg_data):
    """Salva i canali in un file M3U8 senza divisori di servizio e categoria, con tvg-id da EPG."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url, user_agent in channels:
                    tvg_id = get_tvg_id_from_epg(name, epg_data)
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" http-user-agent="{user_agent}/2.6" http-referrer="{base_url}", {name}\n')
                    f.write(f"{url}\n\n")

def get_tvg_id_from_epg(tvg_name, epg_data):
    """Cerca il tvg-id nel file EPG usando una corrispondenza fuzzy con tvg-name."""
    tvg_id = ""
    
    # Itera su tutti gli EPG (che sono in epg_data, una lista di ElementTree)
    for epg_root in epg_data:
        for channel in epg_root.findall("channel"):
            epg_channel_name = channel.find("display-name").text
            similarity = fuzz.partial_ratio(tvg_name.lower(), epg_channel_name.lower())
            
            if similarity > 90:  # Soglia di somiglianza
                tvg_id = channel.get("id")
                break  # Se c'è una corrispondenza abbastanza forte, fermati

        if tvg_id:  # Se è stato trovato un tvg-id, esci dal loop
            break

    return tvg_id

def download_epg(epg_url):
    """Scarica e decomprime il file EPG in formato GZIP."""
    try:
        response = requests.get(epg_url, stream=True, timeout=10)
        response.raise_for_status()

        # Verifica se il file è GZIP
        if 'gzip' in response.headers.get('Content-Encoding', ''):
            # Gestisce GZIP
            buf = BytesIO(response.content)
            with gzip.GzipFile(fileobj=buf) as f:
                try:
                    # Decodifica il contenuto
                    content = f.read().decode('utf-8')
                    # Verifica se il contenuto è in formato XML
                    return ET.ElementTree(ET.fromstring(content))
                except Exception as e:
                    print(f"Errore nel parsing del GZIP: {e}")
                    return None
        else:
            # Se il file non è GZIP, tenta di leggere direttamente
            try:
                return ET.ElementTree(ET.fromstring(response.content))
            except Exception as e:
                print(f"Errore nel parsing del file XML: {e}")
                return None

    except requests.RequestException as e:
        print(f"Errore durante il download dell'EPG da {epg_url}: {e}")
        return None

def main():
    all_links = []

    # URL dei file EPG (in formato XML o GZIP)
    epg_urls = [
        "https://www.epgitalia.tv/gzip"
    ]

    epg_data = []

    # Carica i dati EPG
    for epg_url in epg_urls:
        epg_tree = download_epg(epg_url)
        if epg_tree:
            epg_data.append(epg_tree.getroot())

    # Recupera i canali dai siti
    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Organizza i canali
    organized_channels = organize_channels(all_links)

    # Salva il file M3U8
    save_m3u8(organized_channels, epg_data)

    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()