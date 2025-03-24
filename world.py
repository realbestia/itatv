import requests
import re
import os
from collections import defaultdict

OUTPUT_FILE = "world.m3u8"
BASE_URLS = [
    "https://vavoo.to"
]

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
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name).strip()

# Salva il file M3U8 con i canali ordinati alfabeticamente per categoria
def save_m3u8(channels):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    # Raggruppa i canali per nazione (group-title)
    grouped_channels = defaultdict(list)
    for name, url, country in channels:
        grouped_channels[country].append((name, url))

    # Ordina le categorie alfabeticamente e i canali dentro ogni categoria
    sorted_categories = sorted(grouped_channels.keys())

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write('#EXTM3U\n\n')

        for country in sorted_categories:
            # Ordina i canali in ordine alfabetico dentro la categoria
            grouped_channels[country].sort(key=lambda x: x[0].lower())

            for name, url in grouped_channels[country]:
                f.write(f'#EXTINF:-1 tvg-name="{name}" group-title="{country}", {name}\n')
                f.write(f"{url}\n\n")

# Funzione principale
def main():
    all_channels = []
    for url in BASE_URLS:
        channels = fetch_channels(url)
        for ch in channels:
            clean_name = clean_channel_name(ch["name"])
            country = ch.get("country", "Unknown")  # Estrai la nazione del canale, default è "Unknown"
            all_channels.append((clean_name, f"{url}/play/{ch['id']}/index.m3u8", country))

    save_m3u8(all_channels)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()
