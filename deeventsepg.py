import json
import re
from datetime import datetime, timedelta

# Funzione per pulire il testo rimuovendo tag HTML
def clean_text(text):
    return re.sub(r'</?span.*?>', '', text)  # Rimuove tag HTML, incluso <span>

# Funzione per generare il file EPG XML
def generate_epg_xml(json_data):
    epg_content = '<?xml version="1.0" encoding="utf-8"?>\n<tv>\n'
    current_datetime = datetime.now()

    channel_ids = set()  # Per evitare duplicati nei canali

    for date, categories in json_data.items():
        try:
            # Converte la data in formato corretto
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date.split(' - ')[0])
            date_obj = datetime.strptime(date_str, "%A %d %B %Y")
            event_date = date_obj.date()
        except ValueError:
            continue  # Se la data non è valida, passa all'elemento successivo

        if event_date < current_datetime.date():
            continue  # Esclude eventi passati

        for category, events in categories.items():
            for event_info in events:
                time_str = event_info["time"]
                event_name = clean_text(event_info["event"])  # Pulisce il nome evento
                event_desc = event_info.get("description", f"{event_name} LIVE.")

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)

                    # Aggiunta 2 ore per convertire da UTC a +0200 (ora locale)
                    event_datetime_local = event_datetime + timedelta(hours=2)
                except ValueError:
                    continue

                if event_datetime_local < current_datetime - timedelta(hours=2):
                    continue  # Esclude eventi già terminati

                for channel in event_info["channels"]:
                    channel_id = channel["channel_id"]
                    channel_name = clean_text(channel["channel_name"])  # Pulisce il nome del canale

                    # Se il canale non è stato ancora aggiunto, lo aggiunge
                    if channel_id not in channel_ids:
                        epg_content += f'<channel id="{channel_id}">\n'
                        epg_content += f'<display-name>{channel_name}</display-name>\n'  # Nome canale qui
                        epg_content += f'</channel>\n'
                        channel_ids.add(channel_id)

                    # Format start e stop con orario locale +0200
                    start_time = event_datetime_local.strftime("%Y%m%d%H%M%S") + " +0200"
                    stop_time = (event_datetime_local + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0200"

                    # Aggiunge l'evento principale nel file EPG
                    epg_content += f'<programme start="{start_time}" stop="{stop_time}" channel="{channel_id}">\n'
                    epg_content += f'<title lang="it">{event_name}</title>\n'
                    epg_content += f'<desc lang="it">{event_desc}</desc>\n'
                    epg_content += f'<category lang="it">{clean_text(category)}</category>\n'
                    epg_content += f'</programme>\n'

    epg_content += "</tv>\n"
    return epg_content

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

# Carica il JSON e filtra i canali tedeschi
json_data = load_json("daddyliveSchedule.json")

# Genera il file EPG XML
epg_content = generate_epg_xml(json_data)

# Salva il file EPG
with open("deevents.xml", "w", encoding="utf-8") as file:
    file.write(epg_content)

print("✅ Generazione completata! Il file 'deevents.xml' è pronto.")