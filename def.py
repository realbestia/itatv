import requests
import json
import re
import os

# Siti da cui scaricare i dati
BASE_URLS = [
    "https://huhu.to",
    # "https://vavoo.to",
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
    "Bambini": ["baby", "boing", "cartoon", "disney", "nick"],
    "Documentari": ["arte", "discovery", "documentary", "geo", "history", "nat geo", "nature"],
    "Film & Serie TV": ["cinema", "film", "fox", "hbo", "movie", "primafila", "serie"],
    "Intrattenimento": ["focus", "italia", "mediaset", "rai", "real time"],
    "Musica": ["mtv", "music", "radio", "vh1"],
    "News": ["news", "rai news", "sky tg", "tg", "tgcom"],
    "Sport": ["dazn", "eurosport", "rai sport", "sky sport", "sport"]
}

# Funzione per pulire il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*\(.*?\)\s*", "", name)  # Rimuove testo tra parentesi
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s|\(H\d*\)|\(V\d*\))\s*", "", name)  # Rimuove tag extra
    return name.strip()

# Funzione per generare il tvg-id in CamelCase
def generate_tvg_id(channel_name):
    clean_name = clean_channel_name(channel_name)
    
    # Se il nome è DMAX, lo lasciamo maiuscolo
    if clean_name.upper() == "DMAX":
        return "DMAX.it"

    words = clean_name.split()
    camel_case_name = "".join(word.capitalize() for word in words)
    return camel_case_name + ".it"

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
        print(f"Errore durante il download da {base_url}: {e}")
        return []

# Funzione per filtrare i canali italiani e generare nomi unici
def filter_italian_channels(channels, base_url):
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
            
            # Se esiste già, aggiungiamo un numero progressivo
            if count > 1:
                clean_name = f"{clean_name} ({source_tag}{count})"
            else:
                clean_name = f"{clean_name} ({source_tag})"
                
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    
    return results

# Funzione per organizzare i canali per servizio e categoria, con ordinamento A-Z
def organize_channels(channels):
    organized_data = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        service, category = classify_channel(name)
        tvg_id = generate_tvg_id(name)
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
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}",{name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent={user_agent}/1.0\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'{url}\n\n')

# Funzione principale
def main():
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    organized_channels = organize_channels(all_links)
    save_m3u8(organized_channels)

    print(f"File {OUTPUT_FILE} creato con successo!")

# Esegui lo script
if __name__ == "__main__":
    main()