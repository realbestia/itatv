import requests
import random
import time
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

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
                    stream_url = f"https://{server_key}new.iosplayer.ru/{server_key}/premium{channel_id}/mono.m3u8"

                    channel_cache[channel_id] = stream_url  # Salva nella cache
                    return stream_url

        except requests.exceptions.RequestException:
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    return None  # Se tutte le prove falliscono

# Funzione per generare il file EPG in XML
def generate_epg_xml(json_data):
    root = ET.Element("tv")

    for date, categories in json_data.items():
        try:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            event_date = date_obj.date()
        except ValueError:
            continue

        if event_date < datetime.now().date():
            continue  # Esclude eventi di giorni passati

        # Aggiungi evento a mezzanotte per ogni giorno
        midnight_event_datetime = datetime.combine(event_date, datetime.min.time())
        midnight_event = ET.SubElement(
            root,
            "programme",
            start=midnight_event_datetime.strftime("%Y%m%d%H%M%S %z"),
            stop=(midnight_event_datetime + timedelta(hours=2)).strftime("%Y%m%d%H%M%S %z"),
            channel="midnight_event"
        )
        title = ET.SubElement(midnight_event, "title")
        title.text = f"Evento del {event_date.strftime('%d/%m/%Y')} - Inizio alle 00:00"
        desc = ET.SubElement(midnight_event, "desc")
        desc.text = f"L'evento inizia alle {midnight_event_datetime.strftime('%H:%M')}"

        # Aggiungi gli altri eventi
        for category, events in categories.items():
            for event_info in events:
                time_str = event_info["time"]
                event_name = event_info["event"]

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)
                except ValueError:
                    continue

                # Se l'evento è passato da più di 2 ore, lo esclude
                if event_datetime < datetime.now() - timedelta(hours=2):
                    continue  

                for channel in event_info["channels"]:
                    channel_name = clean_text(channel["channel_name"])
                    channel_id = channel["channel_id"]
                    stream_url = get_stream_link(channel_id)

                    if stream_url:
                        # Creazione dell'elemento EPG per ogni evento
                        programme = ET.SubElement(
                            root,
                            "programme",
                            start=event_datetime.strftime("%Y%m%d%H%M%S %z"),
                            stop=(event_datetime + timedelta(hours=2)).strftime("%Y%m%d%H%M%S %z"),
                            channel=channel_name
                        )
                        title = ET.SubElement(programme, "title")
                        title.text = event_name
                        desc = ET.SubElement(programme, "desc")
                        desc.text = f"{event_name} inizia alle {event_datetime.strftime('%H:%M')}"

    tree = ET.ElementTree(root)
    tree.write("eventi.xml", encoding="UTF-8", xml_declaration=True)

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

                    # Filtro per "Italy", "Rai", "Italia", "IT"
                    if re.search(r'\b(italy|rai|italia|it)\b', channel_name, re.IGNORECASE):
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

# Genera il file EPG XML
generate_epg_xml(json_data)

print("✔ Generazione completata! Il file 'eventi.xml' è pronto.")