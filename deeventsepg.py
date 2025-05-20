import json
import re
import html
from datetime import datetime, timedelta

# Funzione per pulire il testo rimuovendo tag HTML
def clean_text(text):
    return re.sub(r'<[^>]+>', '', text)  # Rimuove tutti i tag HTML

# Funzione per generare il file EPG XML
def generate_epg_xml(json_data):
    epg_lines = ['<?xml version="1.0" encoding="utf-8"?>', '<tv>']
    current_datetime = datetime.now()
    channel_ids = set()

    for date, categories in json_data.items():
        try:
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            event_date = date_obj.date()
        except ValueError:
            continue

        if event_date < current_datetime.date():
            continue

        for category, events in categories.items():
            for event_info in events:
                time_str = event_info["time"]
                event_name = html.escape(clean_text(event_info["event"]))
                event_desc = html.escape(event_info.get("description", f"{event_name} LIVE."))
                category_name = html.escape(clean_text(category))

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)
                    event_datetime_local = event_datetime + timedelta(hours=2)  # UTC+2
                except ValueError:
                    continue

                if event_datetime_local < current_datetime - timedelta(hours=2):
                    continue

                for channel in event_info["channels"]:
                    channel_id = channel["channel_id"]
                    channel_name = html.escape(clean_text(channel["channel_name"]))

                    if channel_id not in channel_ids:
                        epg_lines.append(f'  <channel id="{channel_id}">')
                        epg_lines.append(f'    <display-name lang="de">{channel_name}</display-name>')
                        epg_lines.append(f'  </channel>')
                        channel_ids.add(channel_id)

                    start_time = event_datetime_local.strftime("%Y%m%d%H%M%S") + " +0200"
                    stop_time = (event_datetime_local + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0200"

                    epg_lines.append(f'  <programme start="{start_time}" stop="{stop_time}" channel="{channel_id}">')
                    epg_lines.append(f'    <title lang="it">{event_name}</title>')
                    epg_lines.append(f'    <desc lang="it">{event_desc}</desc>')
                    epg_lines.append(f'    <category lang="it">{category_name}</category>')
                    epg_lines.append(f'  </programme>')

    epg_lines.append('</tv>')
    return '\n'.join(epg_lines)

# Funzione per caricare e filtrare il JSON (solo canali DE)
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

                    if re.search(r'\bde\b|german|germany|dazn de|sky de', channel_name, re.IGNORECASE):
                        filtered_channels.append(channel)

                if filtered_channels:
                    filtered_events.append({**event_info, "channels": filtered_channels})

            if filtered_events:
                filtered_categories[category] = filtered_events

        if filtered_categories:
            filtered_data[date] = filtered_categories

    return filtered_data

# Carica il JSON e filtra i canali tedeschi
json_data = load_json("daddyliveSchedule.json")

# Genera il file EPG XML
epg_content = generate_epg_xml(json_data)

# Salva il file EPG
with open("deevents.xml", "w", encoding="utf-8") as file:
    file.write(epg_content)

print("✅ Generazione completata! Il file 'deevents.xml' è pronto.")