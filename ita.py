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

def fetch_epg(epg_url):
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Errore durante il download dell'EPG: {e}")
        return None

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

def normalize_channel_name(name):
    name = re.sub(r"\s+", "", name.strip().lower())
    name = re.sub(r"hd|fullhd", "", name)
    return name

def create_channel_id_map(epg_root):
    channel_id_map = {}
    for channel in epg_root.findall('channel'):
        tvg_id = channel.get('id')
        display_name = channel.find('display-name').text
        if tvg_id and display_name:
            normalized_name = normalize_channel_name(display_name)
            channel_id_map[normalized_name] = tvg_id
    return channel_id_map

def fetch_channels(base_url):
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

def clean_channel_name(name):
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)
    
    if "zona dazn" in name.lower() or "dazn 1" in name.lower():
        return "DAZN2"

    return name.strip()

def filter_italian_channels(channels, base_url):
    seen = {}
    results = []
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            
            if clean_name.lower() in ["dazn", "dazn 2"]:
                continue
            
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({count})"
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    return results

def classify_channel(name):
    service = "IPTV gratuite"
    category = "Altro"

    SERVICE_KEYWORDS = {
        "Sky": ["sky", "fox", "hbo"],
        "DTT": ["rai", "mediaset", "focus", "boing"],
        "IPTV gratuite": ["radio", "local", "regional", "free"]
    }

    CATEGORY_KEYWORDS = {
        "Sport": ["inter", "milan", "lazio", "calcio", "tennis", "sport", "supertennis", "dazn", "eurosport", "sky sport", "rai sport"],
        "Film & Serie TV": ["crime", "primafila", "cinema", "movie", "film", "serie", "hbo", "fox", "rakuten", "atlantic"],
        "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
        "Altro": ["focus", "real time"],
        "Rai": ["rai"],
        "Mediaset": ["twenty seven", "twentyseven", "mediaset", "italia 1", "italia 2", "canale 5"],
        "Bambini": ["frisbee", "super!", "fresbee", "k2", "cartoon", "boing", "nick", "disney", "baby", "rai yoyo"],
        "Documentari": ["documentaries", "discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
        "Musica": ["deejay", "rds", "hits", "rtl", "mtv", "vh1", "radio", "music", "kiss", "kisskiss", "kiss kiss", "kiss kiss italia", "m2o", "fm"]
    }

    for key, words in SERVICE_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            service = key
            break

    for key, words in CATEGORY_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            category = key
            break

    return service, category

def save_m3u8(organized_channels, channel_id_map, logos_dict):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('#EXTM3U tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"\n\n')

        for service in sorted(organized_channels.keys()):  
            categories = organized_channels[service]

            for category in categories.keys():  # Mantiene l'ordine originale delle categorie
                channels = categories[category]

                sorted_channels = sorted(channels, key=lambda x: re.sub(r"[^a-zA-Z0-9]", "", x[0]).lower())

                for name, url, base_url in sorted_channels:
                    tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)
                    normalized_name = normalize_channel_name(tvg_name_cleaned)
                    tvg_id = channel_id_map.get(normalized_name, "")
                    tvg_logo = logos_dict.get(tvg_name_cleaned.lower(), DEFAULT_TVG_ICON)

                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" tvg-logo="{tvg_logo}" group-title="{category}", {name}\n')
                    f.write(f"{url}\n\n")

def main():
    epg_root = fetch_epg(EPG_URL)
    if not epg_root:
        print("Impossibile recuperare il file EPG, procedura interrotta.")
        return

    logos_dict = fetch_logos(LOGOS_URL)
    channel_id_map = create_channel_id_map(epg_root)

    all_links = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    organized_channels = {service: {category: [] for category in ["Sport", "Film & Serie TV", "News", "Altro", "Rai", "Mediaset", "Bambini", "Documentari", "Musica"]} for service in ["Sky", "DTT", "IPTV gratuite"]}
    
    for name, url, base_url in all_links:
        service, category = classify_channel(name)
        organized_channels[service][category].append((name, url, base_url))

    save_m3u8(organized_channels, channel_id_map, logos_dict)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()