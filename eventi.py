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
    "User-Agent": "Mozilla/5.0"
}

client = requests
channel_cache = {}

# Funzione per pulire il testo rimuovendo tag HTML
def clean_text(text):
    return re.sub(r'</?span.*?>', '', text)

# Funzione per ottenere il link M3U8 di un canale
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

    return None

# Funzione per filtrare solo i canali italiani (aggiunta attenzione sui nomi dei canali)
def is_italian_channel(channel_name):
    italian_keywords = ['italy', 'rai', 'italia', 'it']  # Keywords per il filtro
    channel_name = channel_name.lower()
    
    # Verifica se uno dei termini italiani è nel nome del canale
    return any(keyword in channel_name for keyword in italian_keywords)

# Funzione per generare il file M3U8
def generate_m3u8(json_data):
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
            continue  

        category_has_channels = False  

        for category, events in categories.items():
            category_name = clean_text(category)
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
                    continue  

                for channel in event_info["channels"]:
                    channel_name = clean_text(channel["channel_name"])
                    channel_id = channel["channel_id"]

                    # Verifica se il canale è italiano
                    if is_italian_channel(channel_name):
                        stream_url = get_stream_link(channel_id)

                        if stream_url:
                            tvg_name = f"{event_name} - {event_date.strftime('%d/%m/%Y')} {event_time.strftime('%H:%M')}"
                            tvg_name = clean_text(tvg_name)

                            event_blocks += f"#EXTINF:-1 tvg-id=\"{channel_id}\" tvg-name=\"{tvg_name}\" group-title=\"Eventi\" tvg-logo=\"https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/livestreaming.png\", {tvg_name}\n"
                            event_blocks += f"{stream_url}\n"
                            category_has_channels = True

            if category_has_channels:
                m3u8_content += f"#EXTINF:-1 tvg-name=\"----- {category_name} -----\" group-title=\"Eventi\", ----- {category_name} -----\n"
                m3u8_content += f"http://example.com/{category_name.replace(' ', '_')}.m3u8\n"
                m3u8_content += event_blocks

        if not category_has_channels:
            m3u8_content += "#EXTINF:-1 tvg-name=\"----- Nessun Evento Disponibile -----\" group-title=\"Eventi\", Nessun evento disponibile\n"
            m3u8_content += "http://example.com/nessun_evento.m3u8\n"

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

        category_has_events = False  

        for category, events in categories.items():
            for event in events:
                time_str = event["time"]
                event_name = event["event"]

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)
                except ValueError:
                    continue

                if event_datetime < current_datetime - timedelta(hours=2):
                    continue  

                for channel in event["channels"]:
                    channel_id = channel["channel_id"]
                    channel_name = clean_text(channel["channel_name"])

                    # Verifica se il canale è italiano
                    if is_italian_channel(channel_name):
                        channel_set.add((channel_id, channel_name))

                        midnight_time = datetime.combine(event_date, datetime.min.time())
                        start_time_for_description = midnight_time.strftime("%Y%m%d%H%M%S") + " +0000"

                        epg_content += f'<programme start="{start_time_for_description}" stop="{start_time_for_description}" channel="{channel_id}">\n'
                        epg_content += f'  <title>{event_name} inizia alle {event_datetime.strftime("%H:%M")}</title>\n'
                        epg_content += f'  <desc>Preparati per l\'evento: {event_name}. L\'evento inizierà alle {event_datetime.strftime("%H:%M")} su {channel_name}.</desc>\n'
                        epg_content += '</programme>\n'

                        start_time = event_datetime.strftime("%Y%m%d%H%M%S") + " +0000"
                        end_time = (event_datetime + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0000"

                        epg_content += f'<programme start="{start_time}" stop="{end_time}" channel="{channel_id}">\n'
                        epg_content += f'  <title>{event_name}</title>\n'
                        epg_content += f'  <desc>Evento live: {event_name}. Segui l\'azione in diretta su {channel_name}.</desc>\n'
                        epg_content += '</programme>\n'

    epg_content += '</tv>\n'
    return epg_content