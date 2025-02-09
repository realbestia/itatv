import requests
import os
import re

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
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

# Funzione per pulire il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*\(.*?\)\s*", "", name)  # Rimuove testo tra parentesi
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s|\(H\d*\)|\(V\d*\))\s*", "", name)  # Rimuove tag extra
    return name.strip()

# Funzione per generare il tvg-id
def generate_tvg_id(channel_name):
    clean_name = clean_channel_name(channel_name)

    # Se il nome è DMAX, lo lasciamo maiuscolo
    if clean_name.upper() == "DMAX":
        return "DMAX.it"

    # Converti in CamelCase corretto (prima lettera di ogni parola maiuscola)
    words = clean_name.split()
    camel_case_name = "".join(word.capitalize() for word in words)

    return camel_case_name + ".it"

# Funzione per classificare il canale per servizio e categoria
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

# Funzione per scaricare i canali dai siti
def fetch_channels(base_url):
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

# Funzione per filtrare i canali italiani
def filter_italian_channels(channels, base_url):
    results = []
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    
    return results

# Funzione per salvare il file M3U8
def save_m3u8(channels):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for name, url, base_url in channels:
            tvg_id = generate_tvg_id(name)
            service, category = classify_channel(name)
            f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-group="{service}",{name}\n')
            f.write(f"#EXTVLCOPT:http-user-agent=Mozilla/5.0\n")  # User-Agent generico
            f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
            f.write(f"{url}\n\n")

# Funzione principale
def main():
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    save_m3u8(all_links)
    print(f"File {OUTPUT_FILE} creato con successo!")

# Esegui lo script
if __name__ == "__main__":
    main()