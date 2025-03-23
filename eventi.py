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
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

client = requests
channel_cache = {}

# Funzione per pulire il testo dai tag HTML
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
                    stream_url = f"https://{server_key}new.iosplayer.ru/{server_key}/premium{channel_id}/mono.m3u8"

                    channel_cache[channel_id] = stream_url
                    return stream_url

        except requests.exceptions.RequestException:
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    return None  # Se tutte le prove falliscono

# Funzione per generare il file M3U8
def generate_m3u8_from_json(json_data):
    m3u8_content = "#EXTM3U\n"
    current_datetime = datetime.now()

    for date, categories in json_data.items():
        try:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            event_date = date_obj.date()
        except ValueError:
            continue

        if event_date < current_datetime.date():
            continue  # Esclude eventi passati

        for category, events in categories.items():
            category_name = clean_text(category)
            category_has_channels = False  # Flag per verificare se ci sono canali validi

            category_block = f"#EXTINF:-1 tvg-name=\"----- {category_name} -----\" group-title=\"Eventi\", ----- {category_name} -----\n"
            category_block += f"http://example.com/{category_name.replace(' ', '_')}.m3u8\n"

            event_blocks = ""

            for event_info in events:
                time_str = event_info["time"]
                event_name = event_info["event"]

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)
                except ValueError:
                    continue

                if event_datetime < current_datetime - timedelta(hours=2):
                    continue  # Esclude eventi passati di oltre 2 ore

                for channel in event_info["channels"]:
                    channel_name = clean_text(channel["channel_name"])
                    channel_id = channel["channel_id"]

                    stream_url = get_stream_link(channel_id)

                    if stream_url:
                        tvg_name = f"{event_name} - {event_date.strftime('%d/%m/%Y')} {event_time.strftime('%H:%M')}"
                        tvg_name = clean_text(tvg_name)

                        event_blocks += f"#EXTINF:-1 tvg-id=\"{channel_id}\" tvg-name=\"{tvg_name}\" group-title=\"Eventi\" tvg-logo=\"https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/livestreaming.png\", {tvg_name}\n"
                        event_blocks += f"{stream_url}\n"
                        category_has_channels = True

            if category_has_channels:
                m3u8_content += category_block + event_blocks

    return m3u8_content

# Funzione per generare l'EPG XML
def generate_epg(json_data):
    epg_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
    current_datetime = datetime.now()
    channel_set = set()

    for date, categories in json_data.items():
        try:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            event_date = date_obj.date()
        except ValueError:
            continue

        if event_date < current_datetime.date():
            continue

        for events in categories.values():
            for event in events:
                time_str = event["time"]
                event_name = event["event"]

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)
                except ValueError:
                    continue

                if event_datetime < current_datetime - timedelta(hours=2):
                    continue  # Esclude eventi passati di oltre 2 ore

                for channel in event["channels"]:
                    channel_id = channel["channel_id"]
                    channel_name = clean_text(channel["channel_name"])
                    channel_set.add((channel_id, channel_name))

                    # Descrizione prima dell'inizio dell'evento
                    # Inizia a mezzanotte del giorno dell'evento
                    midnight_time = datetime.combine(event_date, datetime.min.time())
                    start_time_for_description = midnight_time.strftime("%Y%m%d%H%M%S") + " +0000"
                    epg_content += f'<programme start="{start_time_for_description}" stop="{start_time_for_description}" channel="{channel_id}">\n'
                    epg_content += f'  <title>{event_name} inizia alle {event_datetime.strftime("%H:%M")}</title>\n'
                    epg_content += f'  <desc>Preparati per l\'evento: {event_name}. L\'evento inizierà alle {event_datetime.strftime("%H:%M")} su {channel_name}.</desc>\n'
                    epg_content += '</programme>\n'

                    # Ora aggiungi l'evento vero e proprio
                    start_time = event_datetime.strftime("%Y%m%d%H%M%S") + " +0000"
                    end_time = (event_datetime + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0000"
                    description = f"Evento live: {event_name}. Segui l'azione in diretta su {channel_name}."

                    epg_content += f'<programme start="{start_time}" stop="{end_time}" channel="{channel_id}">\n'
                    epg_content += f'  <title>{event_name}</title>\n'
                    epg_content += f'  <desc>{description}</desc>\n'
                    epg_content += '</programme>\n'

    for channel_id, channel_name in channel_set:
        epg_content += f'<channel id="{channel_id}">\n'
        epg_content += f'  <display-name>{channel_name}</display-name>\n'
        epg_content += '</channel>\n'

    epg_content += "</tv>"
    return epg_content

# Carica e filtra il JSON
with open("daddyliveSchedule.json", "r", encoding="utf-8") as file:
    json_data = json.load(file)

# Genera e salva i file
with open("eventi.m3u8", "w", encoding="utf-8") as file:
    file.write(generate_m3u8_from_json(json_data))

with open("eventi.xml", "w", encoding="utf-8") as file:
    file.write(generate_epg(json_data))

print("Generazione completata!")