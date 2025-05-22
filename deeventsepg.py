import os
import re
import json
from datetime import datetime, timedelta, timezone

# Funzione di utilità per pulire il testo (rimuovere tag HTML span)
def clean_text(text):
    return re.sub(r'</?span.*?>', '', str(text))

# --- SCRIPT 5: epg_eventi_xml_generator (genera eventi.xml) ---
def load_json_for_epg(json_file_path):
    if not os.path.exists(json_file_path):
        print(f"[!] File JSON non trovato per EPG: {json_file_path}")
        return {}
    with open(json_file_path, "r", encoding="utf-8") as file:
        json_data = json.load(file)
    
    filtered_data = {}
    for date, categories in json_data.items():
        filtered_categories = {}
        for category, events in categories.items():
            filtered_events = []
            for event_info in events:
                filtered_channels = []
                # Utilizza .get("channels", []) per gestire casi in cui "channels" potrebbe mancare
                for channel in event_info.get("channels", []): 
                    channel_name = clean_text(channel.get("channel_name", "")) # Usa .get per sicurezza
                    # Filtra per canali italiani
                    if re.search(r'\b(de)\b', channel_name, re.IGNORECASE):
                        filtered_channels.append(channel)
                if filtered_channels:
                    # Assicura che event_info sia un dizionario prima dello unpacking
                    if isinstance(event_info, dict):
                        filtered_events.append({**event_info, "channels": filtered_channels})
                    else:
                        # Logga un avviso se il formato dell'evento non è quello atteso
                        print(f"[!] Formato evento non valido durante il filtraggio per EPG: {event_info}")
            if filtered_events:
                filtered_categories[category] = filtered_events
        if filtered_categories:
            filtered_data[date] = filtered_categories
    return filtered_data

def generate_epg_xml(json_data):
    epg_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
    
    italian_offset = timedelta(hours=2)
    italian_offset_str = "+0200" 
    italian_tz = timezone(italian_offset)

    current_datetime_utc = datetime.now(timezone.utc)
    current_datetime_local = current_datetime_utc + italian_offset

    # Tiene traccia degli ID dei canali per cui è già stato scritto il tag <channel>
    channel_ids_processed_for_channel_tag = set() 

    for date_key, categories in json_data.items():
        # Dizionario per memorizzare l'ora di fine dell'ultimo evento per ciascun canale IN QUESTA DATA SPECIFICA
        # Viene resettato per ogni nuova data.
        last_event_end_time_per_channel_on_date = {}

        try:
            date_str_from_key = date_key.split(' - ')[0]
            date_str_cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str_from_key)
            event_date_part = datetime.strptime(date_str_cleaned, "%A %d %B %Y").date()
        except ValueError as e:
            print(f"[!] Errore nel parsing della data EPG: '{date_str_from_key}'. Errore: {e}")
            continue

        if event_date_part < current_datetime_local.date():
            continue

        for category_name, events_list in categories.items():
            # Ordina gli eventi per orario di inizio (UTC) per garantire la corretta logica "evento precedente"
            try:
                sorted_events_list = sorted(
                    events_list,
                    key=lambda x: datetime.strptime(x.get("time", "00:00"), "%H:%M").time()
                )
            except Exception as e_sort:
                print(f"[!] Attenzione: Impossibile ordinare gli eventi per la categoria '{category_name}' nella data '{date_key}'. Si procede senza ordinamento. Errore: {e_sort}")
                sorted_events_list = events_list

            for event_info in sorted_events_list:
                time_str_utc = event_info.get("time", "00:00")
                event_name = clean_text(event_info.get("event", "Unbekanntes Ereignis"))
                event_desc = event_info.get("description", f"{event_name} live übertragen.")

                try:
                    event_time_utc_obj = datetime.strptime(time_str_utc, "%H:%M").time()
                    # Crea un datetime naive
                    event_datetime_utc_naive = datetime.combine(event_date_part, event_time_utc_obj)
                    # Aggiungi l'offset italiano
                    event_datetime_local_naive = event_datetime_utc_naive + italian_offset
                    # Rendi il datetime consapevole del fuso orario
                    event_datetime_local = event_datetime_local_naive.replace(tzinfo=italian_tz)
                except ValueError as e:
                    print(f"[!] Errore parsing orario UTC '{time_str_utc}' per EPG evento '{event_name}'. Errore: {e}")
                    continue
                
                # Ora entrambi i datetime sono offset-aware e possono essere confrontati
                if event_datetime_local < (current_datetime_local - timedelta(hours=2)):
                    continue

                for channel_data in event_info.get("channels", []):
                    channel_id = channel_data.get("channel_id", "")
                    channel_name_cleaned = clean_text(channel_data.get("channel_name", "Unbekannter Kanal"))

                    if not channel_id: 
                        continue

                    if channel_id not in channel_ids_processed_for_channel_tag:
                        epg_content += f'  <channel id="{channel_id}">\n'
                        epg_content += f'    <display-name>{channel_name_cleaned}</display-name>\n'
                        epg_content += f'  </channel>\n'
                        channel_ids_processed_for_channel_tag.add(channel_id)
                    
                    # --- LOGICA ANNUNCIO MODIFICATA ---
                    announcement_stop_local = event_datetime_local # L'annuncio termina quando inizia l'evento corrente

                    # Determina l'inizio dell'annuncio
                    if channel_id in last_event_end_time_per_channel_on_date:
                        # C'è stato un evento precedente su questo canale in questa data
                        previous_event_end_time_local = last_event_end_time_per_channel_on_date[channel_id]
                        
                        # Assicurati che l'evento precedente termini prima che inizi quello corrente
                        if previous_event_end_time_local < event_datetime_local:
                            announcement_start_local = previous_event_end_time_local
                        else:
                            # Sovrapposizione o stesso orario di inizio, problematico.
                            # Fallback a 00:00 del giorno, o potresti saltare l'annuncio.
                            print(f"[!] Attenzione: L'evento '{event_name}' sul canale '{channel_id}' inizia prima o contemporaneamente alla fine dell'evento precedente su questo canale. Fallback per l'inizio dell'annuncio.")
                            announcement_start_local = datetime.combine(event_datetime_local.date(), datetime.min.time()).replace(tzinfo=italian_tz)
                    else:
                        # Primo evento per questo canale in questa data
                        announcement_start_local = datetime.combine(event_datetime_local.date(), datetime.min.time()).replace(tzinfo=italian_tz)

                    # Assicura che l'inizio dell'annuncio sia prima della fine
                    if announcement_start_local < announcement_stop_local:
                        announcement_title = f'Es beginnt um {event_datetime_local.strftime("%H:%M")}.' # Orario italiano
                        
                        epg_content += f'  <programme start="{announcement_start_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" stop="{announcement_stop_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" channel="{channel_id}">\n'
                        epg_content += f'    <title lang="de">{announcement_title}</title>\n'
                        epg_content += f'    <desc lang="de">{event_name}.</desc>\n' 
                        epg_content += f'    <category lang="de">Bekanntmachung</category>\n'
                        epg_content += f'  </programme>\n'
                    elif announcement_start_local == announcement_stop_local:
                        print(f"[INFO] Annuncio di durata zero saltato per l'evento '{event_name}' sul canale '{channel_id}'.")
                    else: # announcement_start_local > announcement_stop_local
                        print(f"[!] Attenzione: L'orario di inizio calcolato per l'annuncio è successivo all'orario di fine per l'evento '{event_name}' sul canale '{channel_id}'. Annuncio saltato.")

                    # --- EVENTO PRINCIPALE ---
                    main_event_start_local = event_datetime_local
                    main_event_stop_local = event_datetime_local + timedelta(hours=2) # Durata fissa 2 ore
                    
                    epg_content += f'  <programme start="{main_event_start_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" stop="{main_event_stop_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" channel="{channel_id}">\n'
                    epg_content += f'    <title lang="de">{event_name}</title>\n'
                    epg_content += f'    <desc lang="de">{event_desc}</desc>\n'
                    epg_content += f'    <category lang="de">{clean_text(category_name)}</category>\n'
                    epg_content += f'  </programme>\n'

                    # Aggiorna l'orario di fine dell'ultimo evento per questo canale in questa data
                    last_event_end_time_per_channel_on_date[channel_id] = main_event_stop_local
    
    epg_content += "</tv>\n"
    return epg_content
    
def epg_eventi_xml_generator():
    print("Eseguendo la generazione di deevents.xml...")
    JSON_INPUT_FILE_EPG = "daddyliveSchedule.json" # File JSON di input
    XML_OUTPUT_FILE_EPG = "deevents.xml"          # File XML di output
    
    # Determina il percorso assoluto dei file basandosi sulla directory dello script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_input_full_path = os.path.join(script_dir, JSON_INPUT_FILE_EPG)
    xml_output_full_path = os.path.join(script_dir, XML_OUTPUT_FILE_EPG)

    # Carica i dati JSON filtrati per i canali italiani
    json_data_for_epg = load_json_for_epg(json_input_full_path)
    if not json_data_for_epg: # Se non ci sono dati (es. file non trovato o vuoto dopo il filtro)
        print(f"[!] Nessun dato JSON caricato o filtrato da {json_input_full_path}. Salto la generazione di {XML_OUTPUT_FILE_EPG}.")
        return # Esce dalla funzione se non ci sono dati

    # Genera il contenuto XML dell'EPG
    epg_content_xml = generate_epg_xml(json_data_for_epg)
    
    # Salva il contenuto XML nel file di output
    with open(xml_output_full_path, "w", encoding="utf-8") as file:
        file.write(epg_content_xml)
    print(f"File EPG eventi.xml salvato in: {xml_output_full_path}")

if __name__ == "__main__":
    epg_eventi_xml_generator()
