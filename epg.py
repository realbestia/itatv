import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO

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
    response = requests.get(url)
    if url.endswith(".gz"):
        with gzip.GzipFile(fileobj=BytesIO(response.content)) as f:
            return f.read()
    else:
        return response.content

# Funzione per parse degli XML
def parse_xml(data):
    try:
        tree = ET.ElementTree(ET.fromstring(data))
        return tree.getroot()
    except ET.ParseError as e:
        print(f"Errore nel parsing del file XML: {e}")
        return None

# Unire tutti gli XML in un unico file
def merge_xml(files):
    merged_root = None
    for file in files:
        print(f"Scaricando e unendo: {file}")
        data = download_and_decompress(file)
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
    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)

# Main
def main():
    merged_root = merge_xml(urls)
    if merged_root is not None:
        write_xml(merged_root, "merged_epg.xml")
        print("File XML unificato salvato come 'merged_epg.xml'.")

if __name__ == "__main__":
    main()
