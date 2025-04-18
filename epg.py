import requests
import lzma
import io
import xml.etree.ElementTree as ET

# URL dei file
url_xz = 'https://www.epgitalia.tv/guidexz'
url_eventi = 'https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.xml'
url_it = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml'
output_xml = 'epg.xml'

def load_xml_from_response(response):
    """Tenta di decomprimere come .xz, altrimenti assume XML puro."""
    try:
        # Prova a leggere come .xz
        with lzma.open(io.BytesIO(response.content), 'rb') as f_in:
            content = f_in.read()
        print("Contenuto decompresso come .xz")
    except lzma.LZMAError:
        # Fallito, tratta come XML normale
        content = response.content
        print("Contenuto trattato come XML non compresso")
    return ET.ElementTree(ET.fromstring(content))

def download_and_parse_xml(url):
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return load_xml_from_response(response)
    except Exception as e:
        print(f"Errore durante il download o parsing da {url}: {e}")
        return None

# XML vuoto principale
root_finale = ET.Element('tv')
tree_finale = ET.ElementTree(root_finale)

# Carica il file principale (.xz o XML)
tree_main = download_and_parse_xml(url_xz)
if tree_main:
    for elem in tree_main.getroot():
        root_finale.append(elem)

# Aggiunge eventi.xml
try:
    r_eventi = requests.get(url_eventi, timeout=30)
    r_eventi.raise_for_status()
    root_eventi = ET.fromstring(r_eventi.content)
    for programme in root_eventi.findall(".//programme"):
        root_finale.append(programme)
except Exception as e:
    print(f"Errore eventi.xml: {e}")

# Aggiunge it.xml
try:
    r_it = requests.get(url_it, timeout=30)
    r_it.raise_for_status()
    root_it = ET.fromstring(r_it.content)
    for programme in root_it.findall(".//programme"):
        root_finale.append(programme)
except Exception as e:
    print(f"Errore it.xml: {e}")

# Pulizia attributi
def clean_attribute(element, attr_name):
    if attr_name in element.attrib:
        element.attrib[attr_name] = element.attrib[attr_name].replace(" ", "").lower()

for ch in root_finale.findall(".//channel"):
    clean_attribute(ch, 'id')

for prg in root_finale.findall(".//programme"):
    clean_attribute(prg, 'channel')

# Salva XML finale
with open(output_xml, 'wb') as f_out:
    tree_finale.write(f_out, encoding='utf-8', xml_declaration=True)
print(f"File XML salvato: {output_xml}")