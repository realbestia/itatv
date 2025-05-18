import json
import re
from datetime import datetime, timedelta
from dateutil import parser
import urllib.parse # Per codificare i termini di ricerca nell'URL

# Librerie necessarie per la ricerca di loghi online
try:
    import requests
    from bs4 import BeautifulSoup
    LIBRARIES_AVAILABLE = True
except ImportError:
    LIBRARIES_AVAILABLE = False
    print("[!] ATTENZIONE: Librerie 'requests' e/o 'beautifulsoup4' non trovate.")
    print("    Per la funzionalità di ricerca loghi, installale con: pip install requests beautifulsoup4")
    print("    La ricerca dei loghi sarà disabilitata.")


JSON_FILE = "daddyliveSchedule.json"
OUTPUT_FILE = "eventi.m3u8"
MFP_IP = "https://mfp2.nzo66.com"  # Inserisci il tuo IP/porta MFP
MFP_PASSWORD = "mfp123"   # Inserisci la tua password API MFP

def clean_category_name(name):
    return re.sub(r'<[^>]+>', '', name).strip()

def get_event_logo_url(event_title, channel_name):
    """
    Cerca un URL di un logo per l'evento specificato usando Google Immagini.
    NOTA: Lo scraping di Google Immagini è instabile e potrebbe smettere di funzionare
    se Google cambia la struttura HTML delle sue pagine di risultati.
    """
    if not LIBRARIES_AVAILABLE:
        return "" # Restituisce stringa vuota se le librerie non sono disponibili

    search_term = f"{event_title} logo"
    print(f"[?] Cercando il logo per: '{search_term}'...")

    try:
        encoded_search_term = urllib.parse.quote_plus(search_term)
        # Nota: Google potrebbe bloccare richieste automatizzate o cambiare la struttura HTML.
        search_url = f"https://www.google.com/search?tbm=isch&q={encoded_search_term}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7" # Richiedi risultati in italiano/inglese
        }

        response = requests.get(search_url, headers=headers, timeout=15) # Timeout aumentato leggermente
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Tentativo di estrarre URL di immagini. Questo è il punto più fragile.
        # Google Images cambia spesso la sua struttura.
        # Questa strategia cerca tag <img> con una classe comune ('rg_i') usata per le anteprime.
        # Potrebbe restituire thumbnail o immagini di bassa qualità, o smettere di funzionare.
        
        image_tags = soup.find_all("img", {"class": "rg_i"}, limit=5) # Limita a 5 per velocizzare

        for img in image_tags:
            # Prova 'data-src' prima, poi 'src', perché 'data-src' è spesso usato per il lazy loading
            src = img.get("data-src") or img.get("src")
            if src and src.startswith("http") and not src.startswith("data:image"):
                # Semplice controllo per evitare URL eccessivamente lunghi che a volte non sono immagini dirette
                if len(src) < 2000: # Un URL molto lungo potrebbe essere un data URI codificato o script
                    print(f"[✓] Logo preliminare trovato per '{event_title}': {src}")
                    return src
        
        print(f"[!] Nessun logo trovato con la strategia corrente per '{event_title}'.")
        return ""

    except requests.exceptions.Timeout:
        print(f"[!] Timeout durante la ricerca del logo per '{search_term}'.")
        return ""
    except requests.exceptions.RequestException as e:
        print(f"[!] Errore di rete durante la ricerca del logo per '{search_term}': {e}")
        return ""
    except Exception as e:
        print(f"[!] Errore imprevisto durante la ricerca del logo per '{search_term}': {e}")
        return ""

def extract_channels_from_json(path):
    keywords = {"italy", "rai", "italia", "it"}
    now = datetime.now()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[!] ERRORE: File JSON '{path}' non trovato.")
        return {}
    except json.JSONDecodeError:
        print(f"[!] ERRORE: Impossibile decodificare il file JSON '{path}'. Controlla la formattazione.")
        return {}


    categorized_channels = {}

    for date_key, sections in data.items():
        date_part = date_key.split(" - ")[0]
        try:
            date_obj = parser.parse(date_part, fuzzy=True).date()
        except Exception as e:
            print(f"[!] Errore parsing data '{date_part}': {e}")
            continue

        if date_obj != now.date():
            continue

        for category_raw, event_items in sections.items():
            category = clean_category_name(category_raw)
            if category not in categorized_channels:
                categorized_channels[category] = []

            for item in event_items:
                time_str = item.get("time", "00:00")
                try:
                    time_obj = datetime.strptime(time_str, "%H:%M") + timedelta(hours=2) # Orario sorgente +2 ore
                    event_datetime = datetime.combine(date_obj, time_obj.time())

                    # Salta eventi già terminati da più di 2 ore (rispetto all'ora locale dello script)
                    if now - event_datetime > timedelta(hours=2):
                        continue
                    
                    time_formatted = time_obj.strftime("%H:%M")
                except ValueError: # Gestisce formati di tempo non validi
                     print(f"[!] Orario non valido '{time_str}' per l'evento '{item.get('event', 'N/A')}'. Uso orario originale.")
                     time_formatted = time_str # Usa l'orario originale se il parsing fallisce
                except Exception as e: # Gestione generica per altri errori di tempo
                    print(f"[!] Errore nel processare l'orario '{time_str}' per '{item.get('event', 'N/A')}': {e}. Uso orario originale.")
                    time_formatted = time_str


                event_title = item.get("event", "Evento Sconosciuto")

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
                            "event_title_for_logo": event_title
                        })
    return categorized_channels

def generate_m3u_from_schedule(json_file, output_file):
    categorized_channels = extract_channels_from_json(json_file)

    if not categorized_channels:
        print("[i] Nessun canale da processare trovato per la data odierna o il file JSON è vuoto/invalido.")
        # Crea comunque un file M3U vuoto con l'intestazione
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for category, channels_list in categorized_channels.items(): # Rinominato 'channels' in 'channels_list'
            if not channels_list:
                continue

            f.write(f'#EXTINF:-1 tvg-name="{category}" group-title="Eventi Live",--- {category} ---\nhttps://example.m3u8\n\n')

            for ch_info in channels_list:
                tvg_name = ch_info["tvg_name"]
                channel_id = ch_info["channel_id"]
                event_title_for_logo = ch_info["event_title_for_logo"]
                channel_name_for_logo = ch_info["channel_name"]

                logo_url = ""
                if LIBRARIES_AVAILABLE: # Tenta di cercare il logo solo se le librerie ci sono
                    logo_url = get_event_logo_url(event_title_for_logo, channel_name_for_logo)

                stream_url = (f"{MFP_IP}/extractor/video?host=DLHD&d=https://thedaddy.to/embed/stream-{channel_id}.php"
                              f"&redirect_stream=true&api_password={MFP_PASSWORD}")

                extinf_line_parts = [
                    f'#EXTINF:-1 tvg-id="{channel_id}"',
                    f'tvg-name="{tvg_name}"'
                ]
                if logo_url:
                    extinf_line_parts.append(f'tvg-logo="{logo_url}"')
                extinf_line_parts.append(f'group-title="Eventi Live",{tvg_name}')

                f.write(f'{" ".join(extinf_line_parts)}\n{stream_url}\n\n')
                print(f"[✓] Aggiunto: {tvg_name} (Logo: {'Trovato' if logo_url else 'Non trovato/Disabilitato'})")

if __name__ == "__main__":
    if LIBRARIES_AVAILABLE or input("Le librerie per la ricerca loghi non sono disponibili. Continuare senza ricerca loghi? (s/N): ").lower() == 's':
        generate_m3u_from_schedule(JSON_FILE, OUTPUT_FILE)
        print(f"\n[i] File M3U '{OUTPUT_FILE}' generato.")
        if LIBRARIES_AVAILABLE:
            print(f"[!] Nota: La ricerca dei loghi online è sperimentale e potrebbe non funzionare sempre o restituire loghi non corretti.")
        else:
            print(f"[i] La ricerca dei loghi è stata disabilitata per mancanza di librerie.")
    else:
        print("[i] Operazione annullata dall'utente.")
