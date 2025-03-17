import requests
import gzip
import os
import xml.etree.ElementTree as ET
import io

# URL del file gzip
url = 'https://www.epgitalia.tv/gzip'
output_gz = 'epg.gz'  # File compresso finale
output_xml = 'epg.xml'  # Nome del file XML dentro il GZIP
temp_gz = 'file_scaricato.gz'  # File temporaneo scaricato

try:
    # Scaricare il file
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    with open(temp_gz, 'wb') as file:
        file.write(response.content)

    # Decomprimere il file .gz
    with gzip.open(temp_gz, 'rb') as f_in:
        file_content = f_in.read()

    # Creiamo un oggetto BytesIO per trattare il contenuto come un file
    xml_content = io.BytesIO(file_content)

    # Caricare il contenuto XML
    tree = ET.parse(xml_content)
    root = tree.getroot()

    # Funzione per pulire attributi
    def clean_attribute(element, attr_name):
        if attr_name in element.attrib:
            old_value = element.attrib[attr_name]
            new_value = old_value.replace(" ", "").lower()
            if old_value != new_value:
                element.attrib[attr_name] = new_value
                print(f"{attr_name}: '{old_value}' → '{new_value}'")  # Debug

    # Pulire gli ID dei canali
    for channel in root.findall(".//channel"):
        clean_attribute(channel, 'id')

    # Pulire gli attributi 'channel' nei programmi
    for programme in root.findall(".//programme"):
        clean_attribute(programme, 'channel')

    # Salvare il file XML modificato temporaneamente
    with open(output_xml, 'wb') as f_out:
        tree.write(f_out, encoding='utf-8', xml_declaration=True)

    # Creare il file GZIP compresso con il nuovo XML
    with open(output_xml, 'rb') as f_in, gzip.open(output_gz, 'wb') as f_out:
        f_out.writelines(f_in)

    # Rimuovere i file temporanei
    os.remove(temp_gz)
    os.remove(output_xml)

    print(f"File modificato e salvato come {output_gz} (contenente {output_xml}).")

except requests.exceptions.RequestException as e:
    print(f"Errore durante il download: {e}")
except gzip.BadGzipFile:
    print("Errore: il file scaricato non è un GZIP valido.")
except ET.ParseError:
    print("Errore: il file XML non è ben formato.")
except Exception as e:
    print(f"Errore imprevisto: {e}")