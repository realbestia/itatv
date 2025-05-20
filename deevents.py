import json
import re
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
from dateutil import parser
import urllib.parse

PROXY = "https://nzo66-tvproxy.hf.space"  # Proxy HLS
JSON_FILE = "daddyliveSchedule.json"
OUTPUT_FILE = "deevents.m3u"
BASE_URL = "https://thedaddy.to/embed/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

HTTP_TIMEOUT = 10
session = requests.Session()
session.headers.update(HEADERS)

def search_logo_for_event(event_name): 
    """ 
    Cerca un logo per l'evento specificato utilizzando Selenium per simulare esattamente un browser reale.
    Restituisce l'URL dell'immagine trovata o None se non trovata.
    """ 
    try:
        # Importa le librerie necessarie per Selenium
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        import re
        import urllib.parse
        import json

        # Rimuovi eventuali riferimenti all'orario dal nome dell'evento
        clean_event_name = re.sub(r'\s*\(\d{1,2}:\d{2}\)\s*$', '', event_name)
        
        # Estrai i nomi delle squadre (se presenti)
        teams_match = re.search(r'(.+?)\s+(?:vs\.?|contro|[-–—])\s+(.+)', clean_event_name, re.IGNORECASE)
        
        # Prepara query di ricerca diverse a seconda del tipo di evento
        if teams_match:
            team1, team2 = teams_match.groups()
            search_queries = [
                f"{team1} {team2} logo partita",
                f"{clean_event_name} logo dazn"
            ]
        else:
            search_queries = [
                f"{clean_event_name} logo dazn"
            ]
        
        # Configura le opzioni di Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36")
        
        # Inizializza il driver di Chrome
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            # Prova diverse query di ricerca
            for query in search_queries:
                search_query = urllib.parse.quote(query)
                search_url = f"https://www.bing.com/images/search?q={search_query}"
                driver.get(search_url)
                time.sleep(3)

                try:
                    image_elements = driver.find_elements(By.CSS_SELECTOR, ".mimg")
                    if not image_elements:
                        image_elements = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
                    
                    if image_elements:
                        first_image = image_elements[0]
                        
                        if first_image.tag_name == "img":
                            image_url = first_image.get_attribute("src")
                        else:
                            m_attr = first_image.get_attribute("m")
                            if m_attr:
                                try:
                                    m_data = json.loads(m_attr)
                                    image_url = m_data.get("murl")
                                except:
                                    first_image.click()
                                    time.sleep(2)
                                    full_image = driver.find_element(By.CSS_SELECTOR, "#mainImageWindow img")
                                    image_url = full_image.get_attribute("src")
                            else:
                                img_inside = first_image.find_element(By.TAG_NAME, "img")
                                image_url = img_inside.get_attribute("src")
                        
                        if image_url and image_url.startswith("http"):
                            return image_url

                except Exception as e:
                    print(f"[!] Errore nell'estrazione dell'immagine per '{query}': {e}")
                    continue
        
        finally:
            driver.quit()
        
        print(f"[!] Nessun logo trovato per '{clean_event_name}' dopo aver provato tutte le query")
                            
    except Exception as e: 
        print(f"[!] Errore nella ricerca del logo per '{event_name}': {e}") 
    
    return None

def get_iframe_url(url):
    try:
        resp = session.post(url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        match = re.search(r'iframe src="([^"]+)"', resp.text)
        return match.group(1) if match else None
    except requests.RequestException as e:
        print(f"[!] Errore richiesta iframe URL {url}: {e}")
        return None

def get_final_m3u8(iframe_url):
    try:
        parsed = re.search(r"https?://([^/]+)", iframe_url)
        if not parsed:
            print(f"[!] URL iframe non valido: {iframe_url}")
            return None
        referer_base = f"https://{parsed.group(1)}"

        page_resp = session.post(iframe_url, timeout=HTTP_TIMEOUT)
        page_resp.raise_for_status()
        page = page_resp.text

        key = re.search(r'var channelKey = "(.*?)"', page)
        ts  = re.search(r'var authTs     = "(.*?)"', page)
        rnd = re.search(r'var authRnd    = "(.*?)"', page)
        sig = re.search(r'var authSig    = "(.*?)"', page)

        if not all([key, ts, rnd, sig]):
            print(f"[!] Mancano variabili auth in pagina {iframe_url}")
            return None

        channel_key = key.group(1)
        auth_ts     = ts.group(1)
        auth_rnd    = rnd.group(1)
        auth_sig    = quote(sig.group(1), safe='')

        auth_url = f"https://top2new.newkso.ru/auth.php?channel_id={channel_key}&ts={auth_ts}&rnd={auth_rnd}&sig={auth_sig}"
        session.get(auth_url, headers={"Referer": referer_base}, timeout=HTTP_TIMEOUT)

        lookup_url = f"{referer_base}/server_lookup.php?channel_id={quote(channel_key)}"
        lookup = session.get(lookup_url, headers={"Referer": referer_base}, timeout=HTTP_TIMEOUT)
        lookup.raise_for_status()
        data = lookup.json()

        server_key = data.get("server_key")
        if not server_key:
            print(f"[!] server_key non trovato per channel {channel_key}")
            return None

        if server_key == "top1/cdn":
            return f"https://top1.newkso.ru/top1/cdn/{channel_key}/mono.m3u8"

        stream_url = (f"{PROXY}/proxy/m3u?url=https://{server_key}new.newkso.ru/{server_key}/{channel_key}/mono.m3u8")
        return stream_url

    except requests.RequestException as e:
        print(f"[!] Errore richiesta get_final_m3u8: {e}")
        return None
    except json.JSONDecodeError:
        print(f"[!] Errore parsing JSON da server_lookup per {iframe_url}")
        return None

def get_stream_from_channel_id(channel_id):
    embed_url = f"{BASE_URL}stream-{channel_id}.php"
    iframe = get_iframe_url(embed_url)
    if iframe:
        return get_final_m3u8(iframe)
    return None

def clean_category_name(name):
    # Rimuove tag html come </span> o simili
    return re.sub(r'<[^>]+>', '', name).strip()

def extract_channels_from_json(path):
    keywords = {"de"}
    now = datetime.now()  # ora attuale completa (data+ora)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    categorized_channels = {}

    for date_key, sections in data.items():
        date_part = date_key.split(" - ")[0]
        try:
            date_obj = parser.parse(date_part, fuzzy=True).date()
        except Exception as e:
            print(f"[!] Errore parsing data '{date_part}': {e}")
            continue

        # filtro solo per eventi del giorno corrente
        if date_obj != now.date():
            continue

        date_str = date_obj.strftime("%Y-%m-%d")

        for category_raw, event_items in sections.items():
            category = clean_category_name(category_raw)
            if category not in categorized_channels:
                categorized_channels[category] = []

            for item in event_items:
                time_str = item.get("time", "00:00")
                try:
                    # Parse orario evento
                    time_obj = datetime.strptime(time_str, "%H:%M") + timedelta(hours=2)  # correzione timezone?

                    # crea datetime completo con data evento e orario evento
                    event_datetime = datetime.combine(date_obj, time_obj.time())

                    # Controllo: includi solo se l'evento è iniziato da meno di 2 ore
                    if now - event_datetime > timedelta(hours=2):
                        # Evento iniziato da più di 2 ore -> salto
                        continue

                    time_formatted = time_obj.strftime("%H:%M")
                except Exception:
                    time_formatted = time_str

                event_title = item.get("event", "Evento")

                for ch in item.get("channels", []):
                    channel_name = ch.get("channel_name", "")
                    channel_id = ch.get("channel_id", "")

                    words = set(re.findall(r'\b\w+\b', channel_name.lower()))
                    if keywords.intersection(words):
                        tvg_name = f"{event_title} ({time_formatted})"
                        categorized_channels[category].append({
                            "tvg_name": tvg_name,
                            "channel_name": channel_name,
                            "channel_id": channel_id,
                            "event_title": event_title  # Aggiungiamo il titolo dell'evento per la ricerca del logo
                        })

    return categorized_channels

def generate_m3u_from_schedule(json_file, output_file):
    categorized_channels = extract_channels_from_json(json_file)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/deevents.xml"\n')

        for category, channels in categorized_channels.items():
            if not channels:
                continue

            # Spacer con nome categoria pulito e group-title "Eventi Live"
            f.write(f'#EXTINF:-1 tvg-name="{category}" group-title="Live Events",--- {category} ---\nhttps://exemple.m3u8\n\n')

            for ch in channels:
                tvg_name = ch["tvg_name"]
                channel_id = ch["channel_id"]
                event_title = ch["event_title"]  # Otteniamo il titolo dell'evento

                # Cerca un logo per questo evento
                # Rimuovi l'orario dal titolo dell'evento prima di cercare il logo
                clean_event_title = re.sub(r'\s*\(\d{1,2}:\d{2}\)\s*$', '', event_title)
                print(f"[🔍] Ricerca logo per: {clean_event_title}")
                logo_url = search_logo_for_event(clean_event_title)
                logo_attribute = f' tvg-logo="{logo_url}"' if logo_url else ''

                try:
                    stream = get_stream_from_channel_id(channel_id)
                    if stream:
                        f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{tvg_name}"{logo_attribute} group-title="Live Events",{tvg_name}\n{stream}\n\n')
                        print(f"[✓] {tvg_name}" + (f" (logo trovato)" if logo_url else " (nessun logo trovato)"))
                    else:
                        print(f"[✗] {tvg_name} - Nessuno stream trovato")
                except Exception as e:
                    print(f"[!] Errore su {tvg_name}: {e}")

if __name__ == "__main__":
    generate_m3u_from_schedule(JSON_FILE, OUTPUT_FILE)
