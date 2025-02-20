import requests
import re
import os
import xml.etree.ElementTree as ET

EPG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"
OUTPUT_FILE = "channels_italy.m3u8"
DEFAULT_TVG_ICON = "https://t3.ftcdn.net/jpg/03/41/08/84/360_F_341088443_BvmtggNaLwKIt92zRG8PtJed8x6i5TN6.jpg"
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

# Scarica e analizza il file EPG XML
def fetch_epg(epg_url):
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Errore durante il download dell'EPG: {e}")
        return None

# Normalizza il nome del canale rimuovendo spazi e "HD"
def normalize_channel_name(name):
    name = re.sub(r"\s+", "", name.strip().lower())  # Rimuove spazi e converte in minuscolo
    name = re.sub(r"hd", "", name)  # Rimuove "HD"
    name = re.sub(r"fullhd", "", name)  # Rimuove "FULLHD"
    return name

# Crea un dizionario che mappa nomi canali normalizzati ai loro tvg-id
def create_channel_id_map(epg_root):
    channel_id_map = {}
    for channel in epg_root.findall('channel'):
        tvg_id = channel.get('id')
        display_name = channel.find('display-name').text
        if tvg_id and display_name:
            normalized_name = normalize_channel_name(display_name)
            if normalized_name not in channel_id_map:
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
    name = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove tutto tra parentesi
    return name.strip()

# Filtra i canali italiani e rinomina "SKY SPORTS F1" in "SKY SPORT F1"
def filter_italian_channels(channels, base_url):
    seen = {}
    results = []
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            
            # Rinomina "ZONA DAZN" in "DAZN ZONA" e "DAZN 1" in "DAZN ZONA"
            if "zona dazn" in clean_name.lower():
                clean_name = "DAZN1"
            elif "dazn 1" in clean_name.lower():
                clean_name = "DAZN1"
            
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({count})"
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    return results


# Classifica il canale per servizio e categoria
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

# Salva il file M3U8 con il tvg-id o tvg-icon
def save_m3u8(organized_channels, channel_id_map):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove parentesi
                    normalized_name = normalize_channel_name(tvg_name_cleaned)
                    tvg_id = channel_id_map.get(normalized_name, "")

                    # Rimuovi i canali con tvg-name "DAZN" e "DAZN 2"
                    if "dazn" in normalized_name and ("dazn" in tvg_name_cleaned.lower() and (tvg_name_cleaned.lower() == "dazn" or tvg_name_cleaned.lower() == "dazn 2")):
                        continue  # Salta questo canale
                    
                    # Aggiungi l'icona specifica per i canali "Sky Sport" se non trovano tvg-id
                    # Aggiungi l'icona specifica per "Dazn" se non trovano tvg-id
                    if "dazn" in normalized_name and not tvg_id:
                        f.write(f'#EXTINF:-1 tvg-logo="{DAZN_TVG_ICON}" tvg-name="{tvg_name_cleaned}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    elif "sky sport" in normalized_name and not tvg_id:
                        f.write(f'#EXTINF:-1 tvg-logo="{SKY_SPORT_TVG_ICON}" tvg-name="{tvg_name_cleaned}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    elif tvg_id:
                        f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    else:
                        f.write(f'#EXTINF:-1 tvg-name="{tvg_name_cleaned}" tvg-logo="{DEFAULT_TVG_ICON}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
    
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

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Organizzazione dei canali
    organized_channels = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}
    for name, url, base_url in all_links:
        service, category = classify_channel(name)
        organized_channels[service][category].append((name, url, base_url))

    # Salvataggio nel file M3U8
    save_m3u8(organized_channels, channel_id_map)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()
