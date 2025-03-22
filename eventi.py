import requests
import random
import time
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re

# Headers e variabili globali
Referer = "https://ilovetoplay.xyz/"
Origin = "https://ilovetoplay.xyz"
headers = { 
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,ru;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

client = requests

# Cache per memorizzare gli URL dei canali
channel_cache = {}

# Funzione per rimuovere i tag HTML
def clean_text(text):
    return re.sub(r'</?span.*?>', '', text)  # Rimuove i tag <span> e </span>

# Funzione per ottenere il link M3U8 per un canale con cache
def get_stream_link(channel_id, max_retries=3):
    # Controlla se il link è già in cache
    if channel_id in channel_cache:
        print(f"Canale {channel_id} trovato in cache.")
        return channel_cache[channel_id]

    print(f"Getting stream link for channel ID: {channel_id}...")
    base_timeout = 10  # Timeout in secondi

    for attempt in range(max_retries):
        try:
            response = client.get(
                f"https://daddylive.mp/embed/stream-{channel_id}.php",
                headers=headers,
                timeout=base_timeout
            )
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.find('iframe', id='thatframe')

            if iframe and iframe.get('src'):
                real_link = iframe.get('src')
                parent_site_domain = real_link.split('/premiumtv')[0]
                server_key_link = f'{parent_site_domain}/server_lookup.php?channel_id=premium{channel_id}'

                response_key = client.get(server_key_link, headers=headers, timeout=base_timeout)
                time.sleep(random.uniform(1, 3))
                response_key.raise_for_status()

                server_key_data = response_key.json()
                if 'server_key' in server_key_data:
                    server_key = server_key_data['server_key']
                    stream_url = f"https://{server_key}new.iosplayer.ru/{server_key}/premium{channel_id}/mono.m3u8"

                    # Salva l'URL nella cache
                    channel_cache[channel_id] = stream_url
                    return stream_url

        except requests.exceptions.RequestException as e:
            print(f"Error fetching stream for {channel_id}: {e}")
        time.sleep((2 ** attempt) + random.uniform(0, 1))

    return None  # Se tutte le prove falliscono

# Funzione per creare un file M3U8 dal JSON con categorie come canali
def generate_m3u8_from_json(json_data):
    m3u8_content = "#EXTM3U\n"
    current_date = datetime.now().strftime("%d/%m/%Y")
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

    for date, categories in json_data.items():
        try:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            formatted_date = date_obj.strftime("%d/%m/%Y")
        except ValueError:
            formatted_date = "Unknown Date"
        
        if formatted_date < current_date:
            continue

        for category, events in categories.items():
            category_name = clean_text(category)
            m3u8_content += f"#EXTINF:-1 tvg-name=\"-----{category_name}-----\" group-title=\"Eventi\", -----{category_name}-----\n"
            m3u8_content += f"http://example.com/{category_name.replace(' ', '_')}.m3u8\n"

            for event_info in events:
                time = event_info["time"]
                event = event_info["event"]

                try:
                    event_time = datetime.strptime(time, "%H:%M") + timedelta(hours=1)
                    new_time = event_time.strftime("%H:%M")
                except ValueError:
                    new_time = time

                for channel in event_info["channels"]:
                    channel_name = clean_text(channel["channel_name"])
                    channel_id = channel["channel_id"]
                    stream_url = get_stream_link(channel_id)

                    if stream_url:
                        if formatted_date == current_date:
                            tvg_name = f"{event} ALLE {new_time}"
                        elif formatted_date == tomorrow_date:
                            tvg_name = f"DOMANI ALLE {new_time}"
                        else:
                            tvg_name = f"{event} - {formatted_date} {new_time}"

                        tvg_name = clean_text(tvg_name)
                        m3u8_content += f"#EXTINF:-1 tvg-id=\"{channel_id}\" tvg-name=\"{tvg_name}\" group-title=\"Eventi\", {tvg_name}\n"
                        m3u8_content += f"{stream_url}\n"
                    else:
                        print(f"Errore: Link M3U8 non trovato per il canale {channel_id}.")

    return m3u8_content

# Funzione per caricare e filtrare il JSON
def load_json(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    print("Categorie trovate nel JSON (Filtrate per 'Italy', 'IT', 'Italia', 'Rai'):")

    filtered_data = {}
    for date, categories in json_data.items():
        filtered_categories = {}

        for category, events in categories.items():
            filtered_events = []

            for event_info in events:
                filtered_channels = [channel for channel in event_info["channels"] if any(
                    term.lower() in channel["channel_name"].lower() for term in ["italy", "it", "italia", "rai"]
                )]

                if filtered_channels:
                    filtered_events.append({**event_info, "channels": filtered_channels})

            if filtered_events:
                filtered_categories[category] = filtered_events

        if filtered_categories:
            filtered_data[date] = filtered_categories

    for date, categories in filtered_data.items():
        print(f"Data: {date}")
        for category, events in categories.items():
            num_channels = sum(len(event_info["channels"]) for event_info in events)
            num_events = len(events)
            print(f" - {category} (Eventi trovati: {num_events}, Canali trovati: {num_channels})")

    return filtered_data

# Carica il file JSON, filtra i canali e visualizza le categorie
json_data = load_json("daddyliveSchedule.json")

# Genera il file M3U8
m3u8_content = generate_m3u8_from_json(json_data)

# Scrivi il contenuto M3U8 su un file
with open("output.m3u8", "w", encoding="utf-8") as file:
    file.write(m3u8_content)

print("Generazione completata!")
