import requests
import gzip
import shutil
import os
import xml.etree.ElementTree as ET
import io
# URL del file gzip
url = 'https://www.epgitalia.tv/gzip'
# Nome del file dove salvare il file scaricato
output_filename = 'file_scaricato.gz'
# Scaricare il file
response = requests.get(url)
with open(output_filename, 'wb') as file:
    file.write(response.content)
# Decomprimere il file .gz e leggerlo come stringa
with gzip.open(output_filename, 'rb') as f_in:
    file_content = f_in.read()
# Modificare il contenuto prima di decomprimerlo
# Creiamo un oggetto StringIO per trattare il contenuto come un file
xml_content = io.BytesIO(file_content)
# Caricare il contenuto XML
tree = ET.parse(xml_content)
root = tree.getroot()
# Funzione per rimuovere spazi e scrivere in minuscolo
def clean_channel_id(element):
    if 'id' in element.attrib:
        element.attrib['id'] = element.attrib['id'].replace(" ", "").lower()
for programme in root.findall(".//programme"):
    if 'channel' in programme.attrib:
        programme.attrib['channel'] = programme.attrib['channel'].replace(" ", "").lower()
# Salviamo il file XML modificato
with open('epg.xml', 'wb') as f_out:
    tree.write(f_out)
# Eliminare il file .gz
os.remove(output_filename)
print('Download, modifica e salvataggio del file XML completati.')
