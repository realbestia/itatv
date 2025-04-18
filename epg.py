import requests
import lzma
import os
import xml.etree.ElementTree as ET
import io

# URL del file .xz da elaborare
url_xz = 'https://www.epgitalia.tv/guidexz'

# File di output
output_xml = 'epg.xml'  # Nome del file XML finale

# URL dei file eventi.xml e it.xml da aggiungere
url_eventi = 'https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.xml'
url_it = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml'

def download_and_parse_xz(url):
    """Scarica e decomprime un file XZ contenente XML."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with lzma.open(io.BytesIO(response.content), 'rb') as f_in:
            xml_content = f_in.read()
        
        return ET.ElementTree(ET.fromstring(xml_content))
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download: {e}")
    except lzma.LZMAError:
        print("Errore: il file scaricato non è un XZ valido.")
    except ET.ParseError as e:
        print(f"Errore nel parsing del file XML: {e}")
    return None

# Creare un unico XML vuoto
root_finale = ET.Element('tv')
tree_finale = ET.ElementTree(root_finale)

# Scaricare e processare il file .xz
tree = download_and_parse_xz(url_xz)
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