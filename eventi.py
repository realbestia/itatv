import xml.etree.ElementTree as ET
import random
import uuid
import json
import os
import datetime
import pytz
import requests
from bs4 import BeautifulSoup
import time

# Costanti
NUM_CHANNELS = 10000
DADDY_JSON_FILE = "daddyliveSchedule.json"
M3U8_OUTPUT_FILE = "events.m3u8"
EPG_OUTPUT_FILE = "events.xml"
LOGO = "https://raw.githubusercontent.com/cribbiox/eventi/refs/heads/main/ddsport.png"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}

# Scarica il file JSON con la programmazione
url = "https://thedaddy.to/schedule/schedule-generated.json"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    with open(DADDY_JSON_FILE, "w", encoding="utf-8") as file:
        file.write(response.text)
else:
    print(f"Errore nel download del JSON: {response.status_code}")
    exit(1)

# Funzioni utili
def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_stream_link(dlhd_id, max_retries=3):
    print(f"Recupero stream per il canale ID: {dlhd_id}...")

    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"https://thedaddy.to/embed/stream-{dlhd_id}.php",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            iframe = soup.find('iframe', id='thatframe')

            if not iframe or not iframe.get('src'):
                print(f"Errore: iframe non trovato per ID {dlhd_id} (tentativo {attempt+1}/{max_retries})")
                time.sleep((2 ** attempt) + random.uniform(0, 1))
                continue

            real_link = iframe.get('src')
            parent_site_domain = real_link.split('/premiumtv')[0]
            server_key_link = f'{parent_site_domain}/server_lookup.php?channel_id=premium{dlhd_id}'
            
            response_key = requests.get(server_key_link, headers=headers, timeout=10)
            response_key.raise_for_status()
            server_key_data = response_key.json()

            if 'server_key' in server_key_data:
                server_key = server_key_data['server_key']
                return f"https://{server_key}new.iosplayer.ru/{server_key}/premium{dlhd_id}/mono.m3u8"

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Errore nel recupero stream per ID {dlhd_id}: {e}")
        
        time.sleep((2 ** attempt) + random.uniform(0, 1))

    return None

def generate_unique_ids(count):
    return [str(uuid.uuid4()) for _ in range(count)]

def createSingleChannelEPGData(UniqueID, tvgName):
    xmlChannel = ET.Element('channel', id=UniqueID)
    ET.SubElement(xmlChannel, 'display-name').text = tvgName
    ET.SubElement(xmlChannel, 'icon', src=LOGO)
    return xmlChannel

def createSingleEPGData(startTime, stopTime, UniqueID, channelName):
    programme = ET.Element('programme', start=f"{startTime} +0000", stop=f"{stopTime} +0000", channel=UniqueID)
    ET.SubElement(programme, 'title').text = channelName
    ET.SubElement(programme, 'desc').text = "No Description"
    return programme

def addChannelsByLeagueSport():
    global channelCount
    processed_schedule_channels = 0

    for day, value in dadjson.items():
        try:
            for sport in dadjson[day].values():
                for game in sport:
                    for channel in game["channels"]:
                        date_time = day.replace("th ", " ").replace("rd ", " ").replace("st ", " ").replace("nd ", " ").replace("Dec Dec", "Dec")
                        date_time = date_time.replace("-", game["time"] + " -")
                        date_format = "%A %d %b %Y %H:%M - Schedule Time UK GMT"

                        try:
                            start_date_utc = datetime.datetime.strptime(date_time, date_format)
                        except ValueError:
                            continue

                        amsterdam_timezone = pytz.timezone("Europe/Amsterdam")
                        start_date_amsterdam = start_date_utc.replace(tzinfo=pytz.utc).astimezone(amsterdam_timezone)

                        mStartTime = start_date_amsterdam.strftime("%Y%m%d%H%M%S")
                        mStopTime = (start_date_amsterdam + datetime.timedelta(days=2)).strftime("%Y%m%d%H%M%S")

                        formatted_date_time_cet = start_date_amsterdam.strftime("%m/%d/%y") + " - " + start_date_amsterdam.strftime("%H:%M") + " (CET)"

                        UniqueID = unique_ids.pop(0)
                        channelName = f"{game['event']} {formatted_date_time_cet} {channel['channel_name']}"
                        channelID = f"{channel['channel_id']}"
                        tvgName = channelName
                        tvLabel = tvgName

                        channelCount += 1
                        print(f"Processing schedule channel: {channelName} - Channel Count: {channelCount}")

                        stream_url_dynamic = get_stream_link(channelID)

                        if stream_url_dynamic:
                            with open(M3U8_OUTPUT_FILE, 'a', encoding='utf-8') as file:
                                if channelCount == 1:
                                    file.write('#EXTM3U\n')

                                file.write(f'#EXTINF:-1 tvg-id="{UniqueID}" tvg-name="{tvgName}" tvg-logo="{LOGO}" group-title="Eventi", {tvLabel}\n')
                                file.write(f'{stream_url_dynamic}\n\n')
                            processed_schedule_channels += 1
                        else:
                            print(f"Failed to get stream URL for channel ID: {channelID}. Skipping M3U8 entry.")

                        xmlChannel = createSingleChannelEPGData(UniqueID, tvgName)
                        root.append(xmlChannel)

                        programme = createSingleEPGData(mStartTime, mStopTime, UniqueID, channelName)
                        root.append(programme)
        except KeyError:
            pass
    return processed_schedule_channels

# Rimuove i file esistenti per garantirne la rigenerazione
for file in [M3U8_OUTPUT_FILE, EPG_OUTPUT_FILE, DADDY_JSON_FILE]:
    if os.path.exists(file):
        os.remove(file)

# Inizio del codice principale
channelCount = 0
unique_ids = generate_unique_ids(NUM_CHANNELS)

# Carica i dati JSON
dadjson = loadJSON(DADDY_JSON_FILE)

# Crea il nodo radice dell'EPG
root = ET.Element('tv')

# Aggiunge i canali reali
total_schedule_channels = addChannelsByLeagueSport()

if channelCount == 0:
    print("Nessun canale valido trovato dalla programmazione.")
else:
    tree = ET.ElementTree(root)
    tree.write(EPG_OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
    print(f"EPG generato con {channelCount} canali validi.")

print(f"Script completato. Canali programmazione aggiunti: {total_schedule_channels}")