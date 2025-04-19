import requests
import os
import re
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta

# Funzione per il primo script (merger_playlist.py)
def merger_playlist():
    # Codice del primo script qui
    # Aggiungi il codice del tuo script "merger_playlist.py" in questa funzione.
    # Ad esempio:
    print("Eseguendo il merger_playlist.py...")
    # Il codice che avevi nello script "merger_playlist.py" va qui, senza modifiche.
import requests
import os

# Percorsi ai file locali
file1 = "channels_italy.m3u8"
file2 = "eventi.m3u8"
file4 = "world.m3u8"

# URL remoto della playlist Pluto TV
url3 = "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"

# Funzione per leggere una playlist da file locale
def read_playlist(file_path, append_params=False, exclude_group_title=None):
    with open(file_path, 'r', encoding='utf-8') as f:
        playlist = f.read()

    # Rimuovi qualsiasi riga che inizia con '#EXTM3U'
    playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('#EXTM3U'))

    if append_params:
        playlist_lines = playlist.splitlines()
        for i in range(len(playlist_lines)):
            if '.m3u8' in playlist_lines[i]:
                playlist_lines[i] += "&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz"
        playlist = '\n'.join(playlist_lines)

    if exclude_group_title:
        playlist = '\n'.join(line for line in playlist.split('\n') if exclude_group_title not in line)

    return playlist

# Funzione per scaricare playlist da URL
def download_playlist(url):
    response = requests.get(url)
    response.raise_for_status()
    playlist = response.text
    playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('#EXTM3U'))
    return playlist

# Ottieni la directory dello script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Percorsi completi ai file locali
path1 = os.path.join(script_directory, file1)
path2 = os.path.join(script_directory, file2)
path4 = os.path.join(script_directory, file4)

# Leggi le playlist locali
playlist1 = read_playlist(path1)
playlist2 = read_playlist(path2, append_params=True)
playlist4 = read_playlist(path4, exclude_group_title="Italy")

# Scarica la playlist Pluto TV dal link
playlist3 = download_playlist(url3)

# Unisci tutte le playlist
combined_playlist = playlist1 + "\n" + playlist2 + "\n" + playlist3 + "\n" + playlist4

# Aggiungi intestazione #EXTM3U con EPG
combined_playlist = '#EXTM3U\n' + combined_playlist

# Salva la playlist finale
output_filename = os.path.join(script_directory, "combined_playlist.m3u8")
with open(output_filename, 'w', encoding='utf-8') as file:
    file.write(combined_playlist)

print(f"Playlist combinata salvata in: {output_filename}")

# Funzione per il secondo script (epg_merger.py)
def epg_merger():
    # Codice del secondo script qui
    # Aggiungi il codice del tuo script "epg_merger.py" in questa funzione.
    # Ad esempio:
    print("Eseguendo l'epg_merger.py...")
    # Il codice che avevi nello script "epg_merger.py" va qui, senza modifiche.
import requests
import gzip
import os
import xml.etree.ElementTree as ET
import io

# URL dei file GZIP o XML da elaborare
urls_gzip = [
    'https://www.open-epg.com/files/italy1.xml',
    'https://www.open-epg.com/files/italy2.xml',
    'https://www.open-epg.com/files/italy3.xml',
    'https://www.open-epg.com/files/italy4.xml'
]

# File di output
output_gzip = 'epg.gzip'  # File compresso finale
output_xml = 'epg.xml'    # Nome del file XML finale

# Percorsi dei file locali da aggiungere
path_eventi = 'eventi.xml'
path_it = 'it.xml'

def download_and_parse_xml(url):
    """Scarica un file .xml o .gzip e restituisce l'ElementTree."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Prova a decomprimere come GZIP
        try:
            with gzip.open(io.BytesIO(response.content), 'rb') as f_in:
                xml_content = f_in.read()
        except (gzip.BadGzipFile, OSError):
            # Non è un file gzip, usa direttamente il contenuto
            xml_content = response.content

        return ET.ElementTree(ET.fromstring(xml_content))
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download da {url}: {e}")
    except ET.ParseError as e:
        print(f"Errore nel parsing del file XML da {url}: {e}")
    return None

# Creare un unico XML vuoto
root_finale = ET.Element('tv')
tree_finale = ET.ElementTree(root_finale)

# Processare ogni URL
for url in urls_gzip:
    tree = download_and_parse_xml(url)
    if tree is not None:
        root = tree.getroot()
        for element in root:
            root_finale.append(element)

# Aggiungere eventi.xml da file locale
if os.path.exists(path_eventi):
    try:
        tree_eventi = ET.parse(path_eventi)
        root_eventi = tree_eventi.getroot()
        for programme in root_eventi.findall(".//programme"):
            root_finale.append(programme)
    except ET.ParseError as e:
        print(f"Errore nel parsing del file eventi.xml: {e}")
else:
    print(f"File non trovato: {path_eventi}")

# Aggiungere it.xml da file locale
if os.path.exists(path_it):
    try:
        tree_it = ET.parse(path_it)
        root_it = tree_it.getroot()
        for programme in root_it.findall(".//programme"):
            root_finale.append(programme)
    except ET.ParseError as e:
        print(f"Errore nel parsing del file it.xml: {e}")
else:
    print(f"File non trovato: {path_it}")

# Funzione per pulire attributi
def clean_attribute(element, attr_name):
    if attr_name in element.attrib:
        old_value = element.attrib[attr_name]
        new_value = old_value.replace(" ", "").lower()
        element.attrib[attr_name] = new_value

# Pulire gli ID dei canali
for channel in root_finale.findall(".//channel"):
    clean_attribute(channel, 'id')

# Pulire gli attributi 'channel' nei programmi
for programme in root_finale.findall(".//programme"):
    clean_attribute(programme, 'channel')

# Salvare il file XML finale
with open(output_xml, 'wb') as f_out:
    tree_finale.write(f_out, encoding='utf-8', xml_declaration=True)
print(f"File XML salvato: {output_xml}")

# Creare il file GZIP compresso con il nuovo XML
with open(output_xml, 'rb') as f_in, gzip.open(output_gzip, 'wb') as f_out:
    f_out.writelines(f_in)
print(f"File compresso creato: {output_gzip}")
# Funzione per il terzo script (eventi_m3u8_generator.py)
def eventi_m3u8_generator():
    # Codice del terzo script qui
    # Aggiungi il codice del tuo script "eventi_m3u8_generator.py" in questa funzione.
    print("Eseguendo l'eventi_m3u8_generator.py...")
    # Il codice che avevi nello script "eventi_m3u8_generator.py" va qui, senza modifiche.
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
    m3u8_content = '#EXTM3U\n'
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
                        m3u8_content += f"#EXTINF:-1 tvg-id=\"{channel['channel_id']}\" tvg-name=\"{tvg_name}\" group-title=\"Eventi\" tvg-logo=\"\", {tvg_name}\n"
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

# Genera il file M3U8
m3u8_content = generate_m3u8_from_json(json_data)

# Salva il file M3U8
with open("eventi.m3u8", "w", encoding="utf-8") as file:
    file.write(m3u8_content)

print("✅ Generazione completata! Il file 'eventi.m3u8' è pronto.")
# Funzione per il quarto script (schedule_extractor.py)
def schedule_extractor():
    # Codice del quarto script qui
    # Aggiungi il codice del tuo script "schedule_extractor.py" in questa funzione.
    print("Eseguendo lo schedule_extractor.py...")
    # Il codice che avevi nello script "schedule_extractor.py" va qui, senza modifiche.
from playwright.sync_api import sync_playwright
import os
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

def html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {}
    
    date_rows = soup.find_all('tr', class_='date-row')
    if not date_rows:
        print("AVVISO: Nessuna riga di data trovata nel contenuto HTML!")
        return {}

    current_date = None
    current_category = None

    for row in soup.find_all('tr'):
        if 'date-row' in row.get('class', []):
            current_date = row.find('strong').text.strip()
            result[current_date] = {}
            current_category = None

        elif 'category-row' in row.get('class', []) and current_date:
            current_category = row.find('strong').text.strip() + "</span>"
            result[current_date][current_category] = []

        elif 'event-row' in row.get('class', []) and current_date and current_category:
            time_div = row.find('div', class_='event-time')
            info_div = row.find('div', class_='event-info')

            if not time_div or not info_div:
                continue

            time_strong = time_div.find('strong')
            event_time = time_strong.text.strip() if time_strong else ""
            event_info = info_div.text.strip()

            event_data = {
                "time": event_time,
                "event": event_info,
                "channels": []
            }

            # Cerca la riga dei canali successiva
            next_row = row.find_next_sibling('tr')
            if next_row and 'channel-row' in next_row.get('class', []):
                channel_links = next_row.find_all('a', class_='channel-button-small')
                for link in channel_links:
                    href = link.get('href', '')
                    channel_id_match = re.search(r'stream-(\d+)\.php', href)
                    if channel_id_match:
                        channel_id = channel_id_match.group(1)
                        channel_name = link.text.strip()
                        channel_name = re.sub(r'\s*\(CH-\d+\)$', '', channel_name)

                        event_data["channels"].append({
                            "channel_name": channel_name,
                            "channel_id": channel_id
                        })

            result[current_date][current_category].append(event_data)

    return result

def modify_json_file(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    current_month = datetime.now().strftime("%B")

    for date in list(data.keys()):
        match = re.match(r"(\w+\s\d+)(st|nd|rd|th)\s(\d{4})", date)
        if match:
            day_part = match.group(1)
            suffix = match.group(2)
            year_part = match.group(3)
            new_date = f"{day_part}{suffix} {current_month} {year_part}"
            data[new_date] = data.pop(date)

    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"File JSON modificato e salvato in {json_file_path}")

def extract_schedule_container():
    url = "https://daddylive.mp/"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_output = os.path.join(script_dir, "daddyliveSchedule.json")

    print(f"Accesso alla pagina {url} per estrarre il main-schedule-container...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("Navigazione alla pagina...")
            page.goto(url)
            print("Attesa per il caricamento completo...")
            page.wait_for_timeout(10000)  # 10 secondi

            schedule_content = page.evaluate("""() => {
                const container = document.getElementById('main-schedule-container');
                return container ? container.outerHTML : '';
            }""")

            if not schedule_content:
                print("AVVISO: main-schedule-container non trovato o vuoto!")
                return False

            print("Conversione HTML in formato JSON...")
            json_data = html_to_json(schedule_content)

            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4)

            print(f"Dati JSON salvati in {json_output}")

            modify_json_file(json_output)
            browser.close()
            return True

        except Exception as e:
            print(f"ERRORE: {str(e)}")
            return False

if __name__ == "__main__":
    success = extract_schedule_container()
    if not success:
        exit(1)
# Funzione per il quinto script (epg_eventi_generator.py)
def epg_eventi_generator():
    # Codice del quinto script qui
    # Aggiungi il codice del tuo script "epg_eventi_generator.py" in questa funzione.
    print("Eseguendo l'epg_eventi_generator.py...")
    # Il codice che avevi nello script "epg_eventi_generator.py" va qui, senza modifiche.
import json
import re
from datetime import datetime, timedelta

# Funzione per pulire il testo rimuovendo tag HTML
def clean_text(text):
    return re.sub(r'</?span.*?>', '', text)  # Rimuove tag HTML, incluso <span>

# Funzione per generare il file EPG XML
def generate_epg_xml(json_data):
    epg_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
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
                event_desc = event_info.get("description", f"{event_name} trasmesso in diretta.")

                try:
                    event_time = datetime.strptime(time_str, "%H:%M").time()
                    event_datetime = datetime.combine(event_date, event_time)
                except ValueError:
                    continue

                if event_datetime < current_datetime - timedelta(hours=2):
                    continue  # Esclude eventi già terminati

                for channel in event_info["channels"]:
                    channel_id = channel["channel_id"]
                    channel_name = clean_text(channel["channel_name"])  # Pulisce il nome del canale

                    # Se il canale non è stato ancora aggiunto, lo aggiunge
                    if channel_id not in channel_ids:
                        epg_content += f'  <channel id="{channel_id}">\n'
                        epg_content += f'    <display-name>{event_name}</display-name>\n'  # Usa event_name per <display-name>
                        epg_content += f'  </channel>\n'
                        channel_ids.add(channel_id)

                    # Aggiungi un annuncio che parte da mezzanotte del giorno dell'evento
                    announcement_start_time = datetime.combine(event_date, datetime.min.time())  # 00:00 dello stesso giorno
                    announcement_stop_time = event_datetime

                    epg_content += f'  <programme start="{announcement_start_time.strftime("%Y%m%d%H%M%S") + " +0000"}" stop="{announcement_stop_time.strftime("%Y%m%d%H%M%S") + " +0000"}" channel="{channel_id}">\n'
                    epg_content += f'    <title lang="it">inizierà alle {(event_datetime + timedelta(hours=2)).strftime("%H:%M")}.</title>\n'
                    epg_content += f'    <desc lang="it">{event_name}.</desc>\n'
                    epg_content += f'    <category lang="it">Annuncio</category>\n'
                    epg_content += f'  </programme>\n'

                    # Formatta start e stop per l'evento principale
                    start_time = event_datetime.strftime("%Y%m%d%H%M%S") + " +0000"
                    stop_time = (event_datetime + timedelta(hours=2)).strftime("%Y%m%d%H%M%S") + " +0000"

                    # Aggiunge l'evento principale nel file EPG
                    epg_content += f'  <programme start="{start_time}" stop="{stop_time}" channel="{channel_id}">\n'
                    epg_content += f'    <title lang="it">{event_name}</title>\n'
                    epg_content += f'    <desc lang="it">{event_desc}</desc>\n'
                    epg_content += f'    <category lang="it">{clean_text(category)}</category>\n'  # Pulisce la categoria
                    epg_content += f'  </programme>\n'

    epg_content += "</tv>\n"
    return epg_content

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
epg_content = generate_epg_xml(json_data)

# Salva il file EPG
with open("eventi.xml", "w", encoding="utf-8") as file:
    file.write(epg_content)

print("✅ Generazione completata! Il file 'eventi.xml' è pronto.")
# Funzione per il sesto script (vavoo_italy_channels.py)
def vavoo_italy_channels():
    # Codice del sesto script qui
    # Aggiungi il codice del tuo script "vavoo_italy_channels.py" in questa funzione.
    print("Eseguendo il vavoo_italy_channels.py...")
    # Il codice che avevi nello script "vavoo_italy_channels.py" va qui, senza modifiche.

# Funzione per il settimo script (world_channels_generator.py)
def world_channels_generator():
    # Codice del settimo script qui
    # Aggiungi il codice del tuo script "world_channels_generator.py" in questa funzione.
    print("Eseguendo il world_channels_generator.py...")
    # Il codice che avevi nello script "world_channels_generator.py" va qui, senza modifiche.

# Funzione principale che esegue tutti gli script
def run_all_scripts():
    # Eseguiamo ogni funzione nello stesso ordine che avevamo nel run_all.py
    merger_playlist()
    epg_merger()
    eventi_m3u8_generator()
    schedule_extractor()
    epg_eventi_generator()
    vavoo_italy_channels()
    world_channels_generator()

# Esecuzione del programma principale
if __name__ == "__main__":
    run_all_scripts()