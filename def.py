import requests
import re
import os
import xml.etree.ElementTree as ET

EPG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"
LOGOS_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logos.txt"
OUTPUT_FILE = "channels_italy.m3u8"
DEFAULT_TVG_ICON = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logo.png"

BASE_URLS = [
    "https://vavoo.to"
]

# Scarica e analizza il file logos.txt
def fetch_logos(logos_url):
    try:
        response = requests.get(logos_url, timeout=10)
        response.raise_for_status()
        logos_data = response.text
        logos_dict = {}

        for line in logos_data.splitlines():
            match = re.match(r'\s*"(.+?)":\s*"(.+?)",?', line)
            if match:
                channel_name, logo_url = match.groups()
                logos_dict[channel_name.lower()] = logo_url

        return logos_dict
    except requests.RequestException as e:
        print(f"Errore durante il download dei loghi: {e}")
        return {}

# Normalizza il nome del canale
def normalize_channel_name(name):
    name = re.sub(r"\s+", "", name.strip().lower())
    name = re.sub(r"hd|fullhd", "", name)
    return name

# Pulisce e rinomina il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)

    # Rinomina "Zona DAZN" e "DAZN 1" in "DAZN1"
    if "zona dazn" in name.lower() or "dazn 1" in name.lower():
        return "DAZN1"

    return name.strip()

# Filtra i canali italiani ed esclude DAZN e DAZN 2
def filter_italian_channels(channels, base_url):
    seen = {}
    results = []
    for ch in channels:
        if ch.get("country") == "Italy":
            original_name = ch["name"]
            clean_name = clean_channel_name(original_name)
            
            # Escludi "DAZN" e "DAZN 2"
            if clean_name.lower() in ["dazn", "dazn 2"]:
                continue
            
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({count})"
            
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url, original_name))
    return results

# Salva il file M3U8 con il tvg-id o tvg-logo
def save_m3u8(organized_channels, channel_id_map, logos_dict):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url, original_name in channels:
                    tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)  # Nome pulito
                    normalized_name = normalize_channel_name(tvg_name_cleaned)  # Normalizzato per EPG
                    tvg_id = channel_id_map.get(normalized_name, "")

                    # Cerca prima con il nome rinominato, poi con il nome originale
                    tvg_logo = logos_dict.get(tvg_name_cleaned.lower(), logos_dict.get(original_name.lower(), DEFAULT_TVG_ICON))

                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" tvg-logo="{tvg_logo}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"VAVOO/2.6","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")

# Funzione principale
def main():
    channel_id_map = {}  # Evitiamo errore se il file EPG non è disponibile
    epg_root = fetch_epg(EPG_URL)
    if epg_root:
        channel_id_map = create_channel_id_map(epg_root)

    logos_dict = fetch_logos(LOGOS_URL)

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    organized_channels = {service: {category: [] for category in ["Sport", "Film & Serie TV", "News", "Intrattenimento", "Bambini", "Documentari", "Musica"]} for service in ["Sky", "DTT", "IPTV gratuite"]}
    
    for name, url, base_url, original_name in all_links:
        service, category = classify_channel(name)
        organized_channels[service][category].append((name, url, base_url, original_name))

    save_m3u8(organized_channels, channel_id_map, logos_dict)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()