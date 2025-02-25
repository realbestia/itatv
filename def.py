import requests
import re
import os
import json
import xml.etree.ElementTree as ET

# Configurazioni
EPG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"
LOGO_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logos.json"
OUTPUT_FILE = "channels_italy.m3u8"
DEFAULT_TVG_ICON = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logo.png"
SKY_SPORT_TVG_ICON = "https://play-lh.googleusercontent.com/-kP0io9_T-LULzdpmtb4E-nFYFwDIKW7cwBhOSRwjn6T2ri0hKhz112s-ksI26NFCKOg"
DAZN_TVG_ICON = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQbZuFm5FAHI9BU6grAccuylVDS_hu_m7N-Dw&s"

BASE_URLS = [
    "https://vavoo.to"
]

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

# Scarica il file EPG XML
def fetch_epg(epg_url):
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Errore durante il download dell'EPG: {e}")
        return None

# Scarica il file logos.json da un URL
def fetch_logos(logo_url):
    try:
        response = requests.get(logo_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download di {logo_url}: {e}")
        return {}

# Normalizza il nome del canale
def normalize_channel_name(name):
    name = re.sub(r"\s+", " ", name.strip().lower())  # Rimuove spazi extra e converte in minuscolo
    name = re.sub(r"\bhd\b", "", name)  # Rimuove la parola "HD"
    name = re.sub(r"\bfullhd\b", "", name)  # Rimuove "FULLHD"
    name = name.replace("&", "e")  # Sostituisce "&" con "e"
    return name.strip()

# Crea una mappatura tvg-id
def create_channel_id_map(epg_root):
    channel_id_map = {}
    for channel in epg_root.findall('channel'):
        tvg_id = channel.get('id')
        display_name = channel.find('display-name').text
        if tvg_id and display_name:
            normalized_name = normalize_channel_name(display_name)
            channel_id_map[normalized_name] = tvg_id
    return channel_id_map

# Scarica la lista dei canali
def fetch_channels(base_url):
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

# Pulisce il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)  
    return name.strip()

# Filtra i canali italiani
def filter_italian_channels(channels, base_url):
    seen = {}
    results = []
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            
            if "zona dazn" in clean_name.lower() or "dazn 1" in clean_name.lower():
                clean_name = "DAZN1"
            
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({count})"
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    return results

# Classifica il canale
def classify_channel(name):
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

# Salva il file M3U8
def save_m3u8(organized_channels, channel_id_map, logos):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)  
                    normalized_name = normalize_channel_name(tvg_name_cleaned)
                    tvg_id = channel_id_map.get(normalized_name, "")
                    
                    # Trova il logo nel JSON con il nome normalizzato
                    tvg_logo = logos.get(normalized_name, DEFAULT_TVG_ICON)

                    if "dazn" in normalized_name and not tvg_id:
                        tvg_logo = DAZN_TVG_ICON
                    elif "sky sport" in normalized_name and not tvg_id:
                        tvg_logo = SKY_SPORT_TVG_ICON

                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" tvg-logo="{tvg_logo}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"VAVOO/2.6","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")

# Funzione principale
def main():
    epg_root = fetch_epg(EPG_URL)
    if not epg_root:
        print("Impossibile recuperare il file EPG, procedura interrotta.")
        return

    channel_id_map = create_channel_id_map(epg_root)
    logos = fetch_logos(LOGO_URL)

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    organized_channels = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}
    for name, url, base_url in all_links:
        service, category = classify_channel(name)
        organized_channels[service][category].append((name, url, base_url))

    save_m3u8(organized_channels, channel_id_map, logos)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()