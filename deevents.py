import requests
import random
import time
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Headers per le richieste HTTP
headers = { 
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6,ru;q=0.5",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

client = requests
channel_cache = {}

# Funzione per pulire il testo rimuovendo tag HTML
def clean_text(text):
    return re.sub(r'</?span.*?>', '', text)

# Funzione per ottenere il link M3U8 per un canale
def get_stream_link(channel_id, max_retries=3):
    if channel_id in channel_cache:
        return channel_cache[channel_id]

    for attempt in range(max_retries):
        try:
            response = client.get(f"https://daddylive.mp/embed/stream-{channel_id}.php", headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.find('iframe', id='thatframe')

            if iframe and iframe.get('src'):
                real_link = iframe.get('src')
                parent_site_domain = real_link.split('/premiumtv')[0]
                server_key_link = f'{parent_site_domain}/server_lookup.php?channel_id=premium{channel_id}'

                response_key = client.get(server_key_link, headers=headers, timeout=10)
                time.sleep(random.uniform(1, 3))
                response_key.raise_for_status()

                server_key_data = response_key.json()
                if 'server_key' in server_key_data:
                    server_key = server_key_data['server_key']
                    stream_url = f"https://{server_key}new.newkso.ru/{server_key}/premium{channel_id}/mono.m3u8"

                    channel_cache[channel_id] = stream_url  # Salva nella cache
                    return stream_url

        except requests.exceptions.RequestException:
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    return None  # Se tutte le prove falliscono

# Funzione per generare il file M3U8
def generate_m3u8_from_json(json_data):
    m3u8_content = '#EXTM3U tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/deevents.xml"\n'
    current_datetime = datetime.now()

    for date, categories in json_data.items():
        try:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            event_date = date_obj.date()
        except ValueError:
            continue

        if event_date < current_datetime.date():
            continue  # Esclude eventi di giorni passati

        for category, events in categories.items():
            category_name = clean_text(category)

            # Filtra solo gli eventi con almeno un canale disponibile
            valid_events = []
            for event_info in events:
                time_str = event_info["time"]
                event_name = event_info["event"]

                try:
                    event_time = (datetime.strptime(time_str, "%H:%M") + timedelta(hours=2)).time()  # Aggiungi 2 ora
                    event_datetime = datetime.combine(event_date, event_time)
                except ValueError:
                    continue

                # Se l'evento è passato da più di 2 ore, lo esclude
                if event_datetime < current_datetime - timedelta(hours=2):
                    continue  

                valid_channels = []
                for channel in event_info["channels"]:
                    channel_name = clean_text(channel["channel_name"])
                    channel_id = channel["channel_id"]
                    stream_url = get_stream_link(channel_id)

                    if stream_url:
                        valid_channels.append({
                            "channel_id": channel_id,
                            "channel_name": channel_name,
                            "stream_url": stream_url
                        })

                if valid_channels:
                    valid_events.append({
                        "event_name": event_name,
                        "event_date": event_date,
                        "event_time": event_time,
                        "channels": valid_channels
                    })

            # Aggiunge la categoria solo se ha eventi con canali validi
            if valid_events:
                m3u8_content += f"#EXTINF:-1 tvg-name=\"----- {category_name} -----\" group-title=\"Eventi\", ----- {category_name} -----\n"
                m3u8_content += f"http://example.com/{category_name.replace(' ', '_')}.m3u8\n"

                for event in valid_events:
                    tvg_name = f"{event['event_name']} - {event['event_date'].strftime('%d/%m/%Y')} {event['event_time'].strftime('%H:%M')}"
                    tvg_name = clean_text(tvg_name)

                    for channel in event["channels"]:
                        m3u8_content += f"#EXTINF:-1 tvg-id=\"{channel['channel_id']}\" tvg-name=\"{tvg_name}\" group-title=\"Eventi\" tvg-logo=\"https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/livestreaming.png\", {tvg_name}\n"
                        m3u8_content += f"{channel['stream_url']}\n"

    return m3u8_content

# Funzione per caricare e filtrare il JSON (solo canali italiani)
def load_json(json_file):
    with open(json_file, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    filtered_data = {}
    for date, categories in json_data.items():
        filtered_categories = {}

        for category, events in categories.items():
            filtered_events = []

            for event_info in events:
                filtered_channels = []

                for channel in event_info["channels"]:
                    channel_name = clean_text(channel["channel_name"])

                    # Filtro per "DE"
                    if re.search(r'\b(DE)\b', channel_name, re.IGNORECASE):
                        filtered_channels.append(channel)

                if filtered_channels:
                    filtered_events.append({**event_info, "channels": filtered_channels})

            if filtered_events:
                filtered_categories[category] = filtered_events

        if filtered_categories:
            filtered_data[date] = filtered_categories

    return filtered_data

# Carica il JSON e filtra i canali italiani
json_data = load_json("daddyliveSchedule.json")

# Genera il file M3U8
m3u8_content = generate_m3u8_from_json(json_data)

# Salva il file M3U8
with open("deevents.m3u8", "w", encoding="utf-8") as file:
    file.write(m3u8_content)

print("✅ Generazione completata! Il file 'deevents.m3u8' è pronto.")
