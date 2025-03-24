import requests
import gzip
import os
import xml.etree.ElementTree as ET
import io

# URL del file gzip
url = 'https://www.epgitalia.tv/gzip'
output_gzip = 'epg.gzip'  # File compresso finale con estensione .gzip
output_xml = 'epg.xml'  # Nome del file XML da salvare e comprimere
temp_gz = 'file_scaricato.gz'  # File temporaneo scaricato

# URL dei file eventi.xml e it.xml da aggiungere
url_eventi = 'https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.xml'
url_it = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml'
temp_eventi = 'eventi.xml'  # File temporaneo per eventi.xml
temp_it = 'it.xml'  # File temporaneo per it.xml

try:
    # Scaricare il file GZIP
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(temp_gz, 'wb') as file:
        file.write(response.content)

    # Decomprimere il file .gz
    with gzip.open(temp_gz, 'rb') as f_in:
        file_content = f_in.read()

    # Creiamo un oggetto BytesIO per trattare il contenuto come un file
    xml_content = io.BytesIO(file_content)

    # Caricare il contenuto XML del GZIP
    try:
        tree = ET.parse(xml_content)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Errore nel parsing del file XML: {e}")
        print(f"Posizione dell'errore: {e.position}")
        print(f"Contenuto del file (prima parte): {file_content[:500]}")  # Stampa i primi 500 caratteri
        raise

    # Scaricare il file eventi.xml
    response_eventi = requests.get(url_eventi, timeout=30)
    response_eventi.raise_for_status()
    
    # Salva l'evento XML temporaneo
    with open(temp_eventi, 'wb') as file:
        file.write(response_eventi.content)

    # Carica l'XML eventi.xml
    try:
        tree_eventi = ET.parse(temp_eventi)
        root_eventi = tree_eventi.getroot()
    except ET.ParseError as e:
        print(f"Errore nel parsing del file eventi.xml: {e}")
        print(f"Posizione dell'errore: {e.position}")
        print(f"Contenuto del file eventi.xml (prima parte): {response_eventi.content[:500]}")
        raise

    # Scaricare il file it.xml
    response_it = requests.get(url_it, timeout=30)
    response_it.raise_for_status()
    
    # Salva it.xml temporaneo
    with open(temp_it, 'wb') as file:
        file.write(response_it.content)

    # Carica l'XML it.xml
    try:
        tree_it = ET.parse(temp_it)
        root_it = tree_it.getroot()
    except ET.ParseError as e:
        print(f"Errore nel parsing del file it.xml: {e}")
        print(f"Posizione dell'errore: {e.position}")
        print(f"Contenuto del file it.xml (prima parte): {response_it.content[:500]}")
        raise

    # Funzione per pulire attributi
    def clean_attribute(element, attr_name):
        if attr_name in element.attrib:
            old_value = element.attrib[attr_name]
            new_value = old_value.replace(" ", "").lower()
            if old_value != new_value:
                element.attrib[attr_name] = new_value
                print(f"{attr_name}: '{old_value}' → '{new_value}'")  # Debug

    # Pulire gli ID dei canali nel file principale
    for channel in root.findall(".//channel"):
        clean_attribute(channel, 'id')

    # Pulire gli attributi 'channel' nei programmi del file principale
    for programme in root.findall(".//programme"):
        clean_attribute(programme, 'channel')

    # Aggiungere gli eventi da eventi.xml
    for programme in root_eventi.findall(".//programme"):
        root.append(programme)  # Aggiunge ogni programma da eventi.xml al file principale

    # Aggiungere gli eventi da it.xml
    for programme in root_it.findall(".//programme"):
        root.append(programme)  # Aggiunge ogni programma da it.xml al file principale

    # Salvare il file XML modificato come epg.xml
    with open(output_xml, 'wb') as f_out:
        tree.write(f_out, encoding='utf-8', xml_declaration=True)

    print(f"File XML salvato: {output_xml}")

    # Creare il file GZIP compresso con il nuovo XML e salvarlo come epg.gzip
    with open(output_xml, 'rb') as f_in, gzip.open(output_gzip, 'wb') as f_out:
        f_out.writelines(f_in)

    print(f"File compresso creato: {output_gzip}")

    # Rimuovere i file temporanei scaricati
    os.remove(temp_gz)
    os.remove(temp_it)

    print(f"Operazione completata. File disponibili: {output_xml}, {output_gzip}")

except requests.exceptions.RequestException as e:
    print(f"Errore durante il download: {e}")
except gzip.BadGzipFile:
    print("Errore: il file scaricato non è un GZIP valido.")
except ET.ParseError as e:
    print(f"Errore nel parsing del file XML: {e}")
except Exception as e:
    print(f"Errore imprevisto: {e}")
