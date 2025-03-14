import requests
import re
from datetime import datetime
from xml.etree import ElementTree

# URL delle liste
m3u8_url = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.m3u8"
xml_url = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.xml"
output_file = "eventi.m3u8"
url_tvg = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.xml"  # Replace this with the actual TVG URL

def scarica_contenuto(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def estrai_tvg_id(xml_content):
    tree = ElementTree.fromstring(xml_content)
    id_mapping = {}

    for channel in tree.findall(".//channel"):
        channel_id = channel.get("id")
        display_name = channel.find("display-name").text.strip() if channel.find("display-name") is not None else ""
        id_mapping[display_name.lower()] = channel_id
    
    return id_mapping

def modifica_orario_tvg_name(riga, id_mapping):
    tvg_name_match = re.search(r'tvg-name="([^"]+)"', riga)
    if tvg_name_match:
        tvg_name = tvg_name_match.group(1).lower()
        tvg_id = id_mapping.get(tvg_name)
        if tvg_id:
            # Modifica solo il tvg-id esistente, senza aggiungerne uno nuovo
            riga = re.sub(r'tvg-id="[^"]+"', f'tvg-id="{tvg_id}"', riga)
        
        # Aggiungi tvg-url subito dopo group-title
        riga = re.sub(r'(group-title="[^"]+")', r'\1 tvg-url="' + url_tvg + '"', riga)
    
    return riga

def estrai_data_dal_nome(riga):
    match = re.search(r'tvg-name="[^"]* (\d{2}/\d{2}/\d{2}) ', riga)
    return match.group(1) if match else None

def filtra_canali_eventi_e_italiani(m3u8_content, id_mapping):
    righe = m3u8_content.splitlines()
    canali_eventi_italiani = []
    salva = False
    oggi = datetime.today().strftime('%d/%m/%y')

    for riga in righe:
        if riga.startswith("#EXTINF"):
            if 'group-title="Eventi"' in riga and ('IT' in riga or 'Italia' in riga or 'Rai' in riga or 'Italy' in riga):
                data_canale = estrai_data_dal_nome(riga)
                if data_canale and data_canale >= oggi:
                    salva = True
                else:
                    salva = False
                
                if salva:
                    riga = modifica_orario_tvg_name(riga, id_mapping)
                    canali_eventi_italiani.append(riga)
            else:
                salva = False
        elif salva:
            canali_eventi_italiani.append(riga)

    return "\n".join(canali_eventi_italiani)

def pulisci_tvg_name_finale(contenuto):
    righe = contenuto.splitlines()
    righe_pulite = []

    for riga in righe:
        match = re.search(r'tvg-name="([^"]+)"', riga)
        if match:
            tvg_name = match.group(1)
            # Mantieni la data e l'orario, rimuovi solo la parte successiva
            pulito = re.sub(r'(\d{2}/\d{2}/\d{2} - \d{2}:\d{2})\s.*$', r'\1', tvg_name).strip()
            riga = riga.replace(tvg_name, pulito)

        righe_pulite.append(riga)

    return "\n".join(righe_pulite)

def salva_lista(output_file, contenuto):
    contenuto_pulito = pulisci_tvg_name_finale(contenuto)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + contenuto_pulito)

def main():
    try:
        lista_m3u8 = scarica_contenuto(m3u8_url)
        xml_content = scarica_contenuto(xml_url)
        id_mapping = estrai_tvg_id(xml_content)

        canali_filtrati = filtra_canali_eventi_e_italiani(lista_m3u8, id_mapping)
        salva_lista(output_file, canali_filtrati)

        if canali_filtrati:
            print(f"Lista salvata in {output_file}")
        else:
            print(f"Nessun canale trovato. File {output_file} creato vuoto.")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
