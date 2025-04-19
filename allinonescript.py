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

# Funzione per il quarto script (schedule_extractor.py)
def schedule_extractor():
    # Codice del quarto script qui
    # Aggiungi il codice del tuo script "schedule_extractor.py" in questa funzione.
    print("Eseguendo lo schedule_extractor.py...")
    # Il codice che avevi nello script "schedule_extractor.py" va qui, senza modifiche.

# Funzione per il quinto script (epg_eventi_generator.py)
def epg_eventi_generator():
    # Codice del quinto script qui
    # Aggiungi il codice del tuo script "epg_eventi_generator.py" in questa funzione.
    print("Eseguendo l'epg_eventi_generator.py...")
    # Il codice che avevi nello script "epg_eventi_generator.py" va qui, senza modifiche.

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