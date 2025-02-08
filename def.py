import requests
import re
import os
import xml.etree.ElementTree as ET

# Siti da cui scaricare i dati IPTV
BASE_URLS = [
    "https://vavoo.to",
]

# File di output
OUTPUT_FILE = "channels_italy.m3u8"

# Link agli EPG
EPG_URLS = [
    "https://xmltv.tvkaista.net/guides/raiplay.it.xml",
    "https://xmltv.tvkaista.net/guides/guida.tv.xml",
    "https://xmltv.tvkaista.net/guides/mediasetinfinity.mediaset.it.xml",
    "https://xmltv.tvkaista.net/guides/superguidatv.it.xml",
    "https://xmltv.tvkaista.net/guides/tivu.tv.xml",
    "https://xmltv.tvkaista.net/guides/guidatv.sky.it.xml",
    "https://xmltv.tvkaista.net/guides/tv.blue.ch.xml",
    "https://xmltv.tvkaista.net/guides/melita.com.xml"
]

# Mappatura servizi e categorie
SERVICE_KEYWORDS = {
    "Sky": ["sky", "fox", "hbo"],
    "DTT": ["rai", "mediaset", "focus", "boing"],
    "IPTV gratuite": ["radio", "local", "regional", "free"]
}

CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

def clean_channel_name(name):
    """Rimuove caratteri indesiderati e suffissi tra parentesi."""
    name = re.sub(r"\s*\(.*?\)\s*", "", name)  # Rimuove qualsiasi cosa tra parentesi
    return name.strip()

def fetch_channels(base_url):
    """Scarica i dati JSON da /channels di un sito."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        print(f"Data from {base_url}: {response.json()}")  # Debug log
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali con country Italy e genera i link M3U8."""
    results = []
    for ch in channels:
        print(f"Processing channel: {ch.get('name')}")  # Debug log
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    return results

def classify_channel(name):
    """Determina il servizio e la categoria del canale."""
    service = "IPTV gratuite"
    category = "Intrattenimento"

    for key, words in SERVICE_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            service = key
            break

    for key, words in CATEGORY_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            category = key
            break

    return service, category

def extract_user_agent(base_url):
    """Crea un User-Agent personalizzato basato sul nome del sito."""
    match = re.search(r"https?://([^/.]+)", base_url)
    return match.group(1).upper() if match else "DEFAULT"

def clean_tvg_id(name):
    """Genera un tvg-id pulito."""
    name = re.sub(r"\s*\(.*?\)", "", name)  # Rimuove i suffissi tra parentesi
    name = re.sub(r"[^\w]", "", name)  # Rimuove caratteri non alfanumerici
    return name.lower() + ".it"

def fetch_epg_logos(epg_urls):
    """Scarica gli EPG e crea una mappatura tvg-id -> logo."""
    logo_map = {}

    for url in epg_urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            print(f"EPG data fetched from {url}: {ET.tostring(root, encoding='unicode')}")  # Aggiungi log del contenuto XML

            for programme in root.findall('programme'):
                channel_id = programme.get('channel')  # L'ID del canale si trova nell'attributo 'channel'
                image_url = programme.find('image')  # Cerca il tag 'image' per il logo
                if image_url is not None:
                    logo_map[channel_id] = image_url.text  # Aggiungi il link dell'immagine al logo_map
            print(f"Fetched EPG logos from {url}")  # Debug log
        except requests.RequestException as e:
            print(f"Errore nel download dell'EPG {url}: {e}")
        except Exception as e:
            print(f"Errore nel parsing dell'EPG {url}: {e}")
    
    return logo_map

def organize_channels(channels, epg_logos):
    """Organizza i canali per servizio e categoria, aggiungendo i loghi."""
    organized_data = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        service, category = classify_channel(name)
        user_agent = extract_user_agent(base_url)
        tvg_id = clean_tvg_id(name)
        logo = epg_logos.get(tvg_id, "")  # Cerca il logo nel dizionario

        # Debug log
        print(f"Channel {name} ({tvg_id}) - Logo: {logo if logo else 'Not found'}")

        organized_data[service][category].append((name, url, base_url, user_agent, logo))

    # Ordina alfabeticamente i canali dentro ogni categoria
    for service in organized_data:
        for category in organized_data[service]:
            organized_data[service][category].sort(key=lambda x: x[0].lower())

    return organized_data

def save_m3u8(organized_channels):
    """Salva i canali in un file M3U8 con supporto per più EPG e loghi."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # Scrive i link agli EPG
        f.write("#EXTM3U url-tvg=\"" + " ".join(EPG_URLS) + "\"\n\n")
        print(f"Writing to {OUTPUT_FILE}...")  # Debug log

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url, user_agent, logo in channels:
                    clean_name = clean_channel_name(name)
                    tvg_id = clean_tvg_id(name)

                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{clean_name}" group-title="{category}" logo="{logo}" http-user-agent="{user_agent}" http-referrer="{base_url}", {clean_name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent={user_agent}/1.0\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"{user_agent}/1.0","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")

    print(f"File {OUTPUT_FILE} creato con successo!")

def main():
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Scarica i loghi dai file EPG
    epg_logos = fetch_epg_logos(EPG_URLS)

    # Organizza i canali e include i loghi
    organized_channels = organize_channels(all_links, epg_logos)

    # Salva nel file M3U8
    save_m3u8(organized_channels)

if __name__ == "__main__":
    main()
