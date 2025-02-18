import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
import logging

# Configurazione del logging
logging.basicConfig(level=logging.INFO)

# URL dei file EPG
urls = [
    "https://www.open-epg.com/files/italy1.xml",
    "https://www.open-epg.com/files/italy2.xml",
    "https://epgshare01.online/epgshare01/epg_ripper_IT1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_RAKUTEN_IT1.xml.gz",
    "https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml"
]

# Funzione per scaricare e decomprimere file .gz
def download_and_decompress(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Solleva un'eccezione per risposte errate
        if url.endswith(".gz"):
            with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
                return f.read()
        else:
            return response.content
    except requests.RequestException as e:
        logging.error(f"Errore durante il download da {url}: {e}")
        return None

# Funzione per il parsing degli XML
def parse_xml(data):
    try:
        tree = ET.ElementTree(ET.fromstring(data))
        return tree.getroot()
    except ET.ParseError as e:
        logging.error(f"Errore nel parsing del file XML: {e}")
        return None

# Unire tutti gli XML in un unico file
def merge_xml(files):
    merged_root = None
    for file in files:
        logging.info(f"Scaricando e unendo: {file}")
        data = download_and_decompress(file)
        if data is None:
            continue  # Salta al file successivo se il download fallisce
        root = parse_xml(data)
        
        if root is not None:
            if merged_root is None:
                merged_root = root
            else:
                # Unire gli elementi del nuovo XML al root dell'XML unito
                for child in root:
                    merged_root.append(child)

    return merged_root

# Funzione per scrivere il file XML finale
def write_xml(root, filename):
    with open(filename, 'wb') as f:
        tree = ET.ElementTree(root)
        tree.write(f, encoding="utf-8", xml_declaration=True)

# Main
def main():
    merged_root = merge_xml(urls)
    if merged_root is not None:
        write_xml(merged_root, "merged_epg.xml")
        logging.info("File XML unificato salvato come 'merged_epg.xml'.")

if __name__ == "__main__":
    main()