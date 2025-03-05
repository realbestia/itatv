import requests
import gzip
import os
import xml.etree.ElementTree as ET
import io

# URL del file gzip
url = 'https://www.epgitalia.tv/gzip'

# Nome del file dove salvare il file scaricato
output_filename = 'file_scaricato.gz'

# Scaricare il file
response = requests.get(url)
response.raise_for_status()
with open(output_filename, 'wb') as file:
    file.write(response.content)

# Decomprimere il file .gz e leggerlo come stringa
with gzip.open(output_filename, 'rb') as f_in:
    file_content = f_in.read()

# Creiamo un oggetto BytesIO per trattare il contenuto come un file
xml_content = io.BytesIO(file_content)

# Caricare il contenuto XML
tree = ET.parse(xml_content)
root = tree.getroot()

# Funzione per rimuovere spazi e scrivere in minuscolo
def clean_attribute(element, attr_name):
    if attr_name in element.attrib:
        old_value = element.attrib[attr_name]
        new_value = old_value.replace(" ", "").lower()
        element.attrib[attr_name] = new_value
        print(f"{attr_name}: '{old_value}' → '{new_value}'")  # Debug

# Pulire gli ID dei canali
for channel in root.findall(".//channel"):
    clean_attribute(channel, 'id')

# Pulire gli attributi 'channel' nei programmi
for programme in root.findall(".//programme"):
    clean_attribute(programme, 'channel')

# Salviamo il file XML modificato con codifica UTF-8
with open('epg.xml', 'wb') as f_out:
    tree.write(f_out, encoding='utf-8', xml_declaration=True)

# Eliminare il file .gz
os.remove(output_filename)

print('Download, modifica e salvataggio del file XML completati.')
