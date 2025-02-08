import requests
import json
import re
import os
import xml.etree.ElementTree as ET

# Configurazione
BASE_URLS = ["https://vavoo.to"]
OUTPUT_FILE = "channels_italy.m3u8"
EPG_URL = "http://example.com/epg.xml"  # Sostituisci con l'URL del tuo file EPG

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
    seen = {}
    results = []
    source_map = {
        "https://vavoo.to": "V",
        "https://huhu.to": "H",
        "https://kool.to": "K",
        "https://oha.to": "O"
    }
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            source_tag = source_map.get(base_url, "")
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({source_tag}{count})"
            else:
                clean_name = f"{clean_name} ({source_tag})"
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    
    return results

def classify_channel(name):
    """Classifica il canale per servizio e categoria tematica."""
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

def extract_user_agent(base_url):
    """Estrae il nome del sito senza estensione e lo converte in maiuscolo per l'user agent."""
    match = re.search(r"https?://([^/.]+)", base_url)
    if match:
        return match.group(1).upper()
    return "DEFAULT"

def fetch_epg_logos(epg_url):
    """Scarica e analizza l'EPG per ottenere una mappatura canale -> logo."""
    logos = {}
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        root = ET.fromstring(response.content)

        for channel in root.findall("channel"):
            channel_id = channel.get("id")
            logo_element = channel.find("icon")
            if channel_id and logo_element is not None:
                logos[channel_id] = logo_element.get("src")

    except requests.RequestException as e:
        print(f"Errore durante il download dell'EPG: {e}")
    except ET.ParseError as e:
        print(f"Errore nell'analisi dell'EPG XML: {e}")

    return logos

def organize_channels(channels, epg_logos):
    """Organizza i canali per servizio e categoria e assegna i loghi dall'EPG."""
    organized_data = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        service, category = classify_channel(name)
        user_agent = extract_user_agent(base_url)

        # Cerca il logo dal dizionario EPG, se esiste
        logo = epg_logos.get(name, "")

        organized_data[service][category].append((name, url, base_url, user_agent, logo))

    return organized_data

def save_m3u8(organized_channels):
    """Salva i canali in un file M3U8 con supporto per EPG e loghi."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # Aggiunge il riferimento all'EPG
        f.write(f"#EXTM3U x-tvg-url=\"{EPG_URL}\"\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url, user_agent, logo in channels:
                    f.write(f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}" group-title="{category}" tvg-logo="{logo}" http-user-agent="{user_agent}" http-referrer="{base_url}",{name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent={user_agent}/1.0\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"{user_agent}/1.0","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")

def main():
    all_links = []

    # Scarica i loghi dall'EPG
    epg_logos = fetch_epg_logos(EPG_URL)

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Organizza i canali con i loghi dall'EPG
    organized_channels = organize_channels(all_links, epg_logos)

    # Salvataggio nel file M3U8 con supporto per EPG e loghi
    save_m3u8(organized_channels)

    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()