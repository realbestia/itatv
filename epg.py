import requests
import gzip
import os
import xml.etree.ElementTree as ET
import io

# URL dei file GZIP da elaborare
urls_gzip = [
    'https://www.epgitalia.tv/gzip',
    'https://www.epgitalia.tv/epggermania',
    'https://www.epgitalia.tv/epgfrancia'
]

# File di output
output_gzip = 'epg.gzip'  # File compresso finale
output_xml = 'epg.xml'  # Nome del file XML finale

temp_files = []  # Per gestire i file temporanei

# URL dei file eventi.xml e it.xml da aggiungere
url_eventi = 'https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.xml'
url_it = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml'

def download_and_parse_xml(url):
    """Scarica e decomprime un file GZIP contenente XML."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with gzip.open(io.BytesIO(response.content), 'rb') as f_in:
            xml_content = f_in.read()
            
        return ET.ElementTree(ET.fromstring(xml_content))
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download: {e}")
    except gzip.BadGzipFile:
        print("Errore: il file scaricato non è un GZIP valido.")
    except ET.ParseError as e:
        print(f"Errore nel parsing del file XML: {e}")
    return None

# Creare un unico XML vuoto
root_finale = ET.Element('tv')

tree_finale = ET.ElementTree(root_finale)

# Processare ogni URL GZIP
for url in urls_gzip:
    tree = download_and_parse_xml(url)
    if tree is not None:
        root = tree.getroot()
        for element in root:
            root_finale.append(element)

# Scaricare e aggiungere eventi.xml
response_eventi = requests.get(url_eventi, timeout=30)
if response_eventi.ok:
    try:
        root_eventi = ET.ElementTree(ET.fromstring(response_eventi.content)).getroot()
        for programme in root_eventi.findall(".//programme"):
            root_finale.append(programme)
    except ET.ParseError as e:
        print(f"Errore nel parsing del file eventi.xml: {e}")

# Scaricare e aggiungere it.xml
response_it = requests.get(url_it, timeout=30)
if response_it.ok:
    try:
        root_it = ET.ElementTree(ET.fromstring(response_it.content)).getroot()
        for programme in root_it.findall(".//programme"):
            root_finale.append(programme)
    except ET.ParseError as e:
        print(f"Errore nel parsing del file it.xml: {e}")

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
