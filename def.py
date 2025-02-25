import requests
import re
import os
import xml.etree.ElementTree as ET

EPG_URL = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"
OUTPUT_FILE = "channels_italy.m3u8"
DEFAULT_TVG_ICON = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logo.png"

LOGO_URLS_FILE = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logos.txt"

# Scarica e analizza il file EPG XML
def fetch_epg(epg_url):
    try:
        response = requests.get(epg_url, timeout=10)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except requests.RequestException as e:
        print(f"Errore durante il download dell'EPG: {e}")
        return None

# Normalizza il nome del canale rimuovendo spazi e "HD"
def normalize_channel_name(name):
    name = re.sub(r"\s+", "", name.strip().lower())  # Rimuove spazi e converte in minuscolo
    name = re.sub(r"hd", "", name)  # Rimuove "HD"
    name = re.sub(r"fullhd", "", name)  # Rimuove "FULLHD"
    return name

# Scarica il file di loghi
def fetch_logos():
    try:
        response = requests.get(LOGO_URLS_FILE, timeout=10)
        response.raise_for_status()
        logos = response.text
        logo_dict = {}
        
        # Analizza il contenuto del file logos.txt
        for line in logos.splitlines():
            match = re.match(r'"(.*?)": "(.*?)"', line)
            if match:
                channel_name = match.group(1).strip().lower()  # Normalizza il nome del canale
                logo_url = match.group(2).strip()
                logo_dict[channel_name] = logo_url
        
        return logo_dict
    except requests.RequestException as e:
        print(f"Errore durante il download del file logos.txt: {e}")
        return {}

# Pulisce il nome del canale
def clean_channel_name(name):
    name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)", "", name)
    name = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove tutto tra parentesi
    return name.strip()

# Crea un dizionario che mappa nomi canali normalizzati ai loro tvg-id
def create_channel_id_map(epg_root):
    channel_id_map = {}
    for channel in epg_root.findall('channel'):
        tvg_id = channel.get('id')
        display_name = channel.find('display-name').text
        if tvg_id and display_name:
            normalized_name = normalize_channel_name(display_name)
            if normalized_name not in channel_id_map:
                channel_id_map[normalized_name] = tvg_id
    return channel_id_map

# Salva il file M3U8 con il tvg-id o tvg-icon
def save_m3u8(organized_channels, channel_id_map, logo_dict):
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url in channels:
                    tvg_name_cleaned = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove parentesi
                    normalized_name = normalize_channel_name(tvg_name_cleaned)
                    tvg_id = channel_id_map.get(normalized_name, "")
                    logo_url = logo_dict.get(normalized_name, DEFAULT_TVG_ICON)

                    # Scrive il canale con il logo associato
                    if tvg_id:
                        f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{tvg_name_cleaned}" group-title="{category}" tvg-logo="{logo_url}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')
                    else:
                        f.write(f'#EXTINF:-1 tvg-name="{tvg_name_cleaned}" tvg-logo="{logo_url}" group-title="{category}" http-user-agent="VAVOO/2.6" http-referrer="{base_url}",{name}\n')

                    f.write(f"#EXTVLCOPT:http-user-agent=VAVOO/2.6\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"VAVOO/2.6","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")


# Funzione principale
def main():
    epg_root = fetch_epg(EPG_URL)
    if not epg_root:
        print("Impossibile recuperare il file EPG, procedura interrotta.")
        return

    channel_id_map = create_channel_id_map(epg_root)

    logo_dict = fetch_logos()  # Scarica e crea il dizionario dei loghi

    # A questo punto puoi organizzare e filtrare i canali come necessario.
    all_channels = []  # Supponiamo che tu abbia una lista di canali da aggiungere

    # Salvataggio nel file M3U8
    save_m3u8(all_channels, channel_id_map, logo_dict)
    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()