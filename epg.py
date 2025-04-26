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
output_xml = 'epg.xml'    # Nome del file XML finale

# URL remoto di it.xml
url_it = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml'

# File eventi locale
path_eventi = 'eventi.xml'

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

# Aggiungere it.xml da URL remoto
tree_it = download_and_parse_xml(url_it)
if tree_it is not None:
    root_it = tree_it.getroot()
    for programme in root_it.findall(".//programme"):
        root_finale.append(programme)
else:
    print(f"Impossibile scaricare o analizzare il file it.xml da {url_it}")

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