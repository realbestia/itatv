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

        category_has_channels = False  # Flag per verificare se ci sono eventi nelle categorie

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
                m3u8_content += f"#EXTINF:-1 tvg-name=\"----- {category_name} -----\" group-title=\"Eventi\", ----- {category_name} -----\n"
                m3u8_content += f"http://example.com/{category_name.replace(' ', '_')}.m3u8\n"
                m3u8_content += event_blocks

        # Se non ci sono eventi per nessuna categoria
        if not category_has_channels:
            m3u8_content += "#EXTINF:-1 tvg-name=\"----- Nessun Evento Disponibile -----\" group-title=\"Eventi\", Nessun evento disponibile\n"
            m3u8_content += "http://example.com/nessun_evento.m3u8\n"  # Link fittizio

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

        category_has_events = False  # Flag per verificare se ci sono eventi in tutte le categorie

        for category, events in categories.items():
            category_has_events_in_category = False  # Flag per una singola categoria

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
                    midnight_time = datetime.combine(event_date, datetime.min.time())
                    start_time_for_description = midnight_time.strftime("%Y%m%d%H%M%S") + " +0000"
                    epg_content += f'<programme start="{start_time_for_description}" stop="{start_time_for_description}" channel="{channel_id}">\n'
                    epg_content += f'  <title>{event_name} inizia alle {event_datetime.strftime("%H:%M")}</title>\n'
                    epg_content += f'  <desc>Preparati per l\'evento: {event_name}. L\'evento inizierà alle {event_datetime.strftime("%H:%M")} su {channel_name} o su questo Canale.</desc>\n'
                    epg_content += '</programme>\n'

                    # Programma dell'evento
                    start_time = event_datetime.strftime("%Y%m%d%H%M%S") + " +0000"
                    end_time = (event_datetime + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0000"
                    description = f"Evento live: {event_name}. Segui l'azione in diretta su {channel_name} o su questo Canale."

                    epg_content += f'<programme start="{start_time}" stop="{end_time}" channel="{channel_id}">\n'
                    epg_content += f'  <title>{event_name}</title>\n'
                    epg_content += f'  <desc>{description}</desc>\n'
                    epg_content += '</programme>\n'

                category_has_events_in_category = True

            category_has_events |= category_has_events_in_category  # Flag globale per la data

        # Se non ci sono eventi per nessuna categoria
        if not category_has_events:
            epg_content += '<channel id="nessun_evento">\n'
            epg_content += '  <display-name>Nessun Evento Disponibile</display-name>\n'
            epg_content += '</channel>\n'

            # Aggiungi un programma che segnala l'assenza di eventi
            midnight_time = datetime.combine(event_date, datetime.min.time())
            start_time_for_description = midnight_time.strftime("%Y%m%d%H%M%S") + " +0000"
            epg_content += f'<programme start="{start_time_for_description}" stop="{start_time_for_description}" channel="nessun_evento">\n'
            epg_content += f'  <title>Nessun Evento Disponibile</title>\n'
            epg_content += f'  <desc>Non ci sono eventi disponibili per la data {event_date.strftime("%d/%m/%Y")}.</desc>\n'
            epg_content += '</programme>\n'

    for channel_id, channel_name in channel_set:
        epg_content += f'<channel id="{channel_id}">\n'
        epg_content += f'  <display-name>{channel_name}</display-name>\n'
        epg_content += '</channel>\n'

    epg_content += "</tv>"
    return epg_content