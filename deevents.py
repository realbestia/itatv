import json
import re
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
from dateutil import parser
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
import io
import time
import os

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
    Cerca un logo per l'evento specificato utilizzando un motore di ricerca
    Restituisce l'URL dell'immagine trovata o None se non trovata
    """
    try:
        # Rimuovi eventuali riferimenti all'orario dal nome dell'evento
        # Cerca pattern come "Team A vs Team B (20:00)" e rimuovi la parte dell'orario
        clean_event_name = re.sub(r'\s*\(\d{1,2}:\d{2}\)\s*$', '', event_name)
        # Se c'è un ':', prendi solo la parte dopo
        if ':' in clean_event_name:
            clean_event_name = clean_event_name.split(':', 1)[1].strip()

        # Verifica se l'evento contiene "vs" o "-" per identificare le due squadre
        teams = None
        if " vs " in clean_event_name:
            teams = clean_event_name.split(" vs ")
        elif " - " in clean_event_name:
            teams = clean_event_name.split(" - ")

        # Se abbiamo identificato due squadre, cerchiamo i loghi separatamente
        if teams and len(teams) == 2:
            team1 = teams[0].strip()
            team2 = teams[1].strip()

            print(f"[🔍] Ricerca logo per Team 1: {team1}")
            logo1_url = search_team_logo(team1)

            print(f"[🔍] Ricerca logo per Team 2: {team2}")
            logo2_url = search_team_logo(team2)

            # Se abbiamo trovato entrambi i loghi, creiamo un'immagine combinata
            if logo1_url and logo2_url:
                # Scarica i loghi e l'immagine VS
                try:
                    from os.path import exists, getmtime

                    # Crea la cartella logos se non esiste
                    logos_dir = "logos"
                    os.makedirs(logos_dir, exist_ok=True)

                    # Controlla e rimuovi i loghi più vecchi di 3 ore
                    current_time = time.time()
                    three_hours_in_seconds = 3 * 60 * 60

                    for logo_file in os.listdir(logos_dir):
                        logo_path = os.path.join(logos_dir, logo_file)
                        if os.path.isfile(logo_path):
                            file_age = current_time - os.path.getmtime(logo_path)
                            if file_age > three_hours_in_seconds:
                                try:
                                    os.remove(logo_path)
                                    print(f"[🗑️] Rimosso logo obsoleto: {logo_path}")
                                except Exception as e:
                                    print(f"[!] Errore nella rimozione del logo {logo_path}: {e}")

                    # Verifica se l'immagine combinata esiste già e non è obsoleta
                    output_filename = f"logos/{team1}_vs_{team2}.png"
                    if exists(output_filename):
                        file_age = current_time - os.path.getmtime(output_filename)
                        if file_age <= three_hours_in_seconds:
                            print(f"[✓] Utilizzo immagine combinata esistente: {output_filename}")

                            # Carica le variabili d'ambiente per GitHub
                            NOMEREPO = os.getenv("NOMEREPO", "").strip()
                            NOMEGITHUB = os.getenv("NOMEGITHUB", "").strip()

                            # Se le variabili GitHub sono disponibili, restituisci l'URL raw di GitHub
                            if NOMEGITHUB and NOMEREPO:
                                github_raw_url = f"https://raw.githubusercontent.com/{NOMEGITHUB}/{NOMEREPO}/main/{output_filename}"
                                print(f"[✓] URL GitHub generato per logo esistente: {github_raw_url}")
                                return github_raw_url
                            else:
                                # Altrimenti restituisci il percorso locale
                                return output_filename

                    # Scarica i loghi
                    response1 = requests.get(logo1_url, timeout=10)
                    img1 = Image.open(io.BytesIO(response1.content))

                    response2 = requests.get(logo2_url, timeout=10)
                    img2 = Image.open(io.BytesIO(response2.content))

                    # Carica l'immagine VS (assicurati che esista nella directory corrente)
                    vs_path = "vs.png"
                    if exists(vs_path):
                        img_vs = Image.open(vs_path)
                        # Converti l'immagine VS in modalità RGBA se non lo è già
                        if img_vs.mode != 'RGBA':
                            img_vs = img_vs.convert('RGBA')
                    else:
                        # Crea un'immagine di testo "VS" se il file non esiste
                        img_vs = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
                        from PIL import ImageDraw, ImageFont
                        draw = ImageDraw.Draw(img_vs)
                        try:
                            font = ImageFont.truetype("arial.ttf", 40)
                        except:
                            font = ImageFont.load_default()
                        draw.text((30, 30), "VS", fill=(255, 0, 0), font=font)

                    # Ridimensiona le immagini a dimensioni uniformi
                    size = (150, 150)
                    img1 = img1.resize(size)
                    img2 = img2.resize(size)
                    img_vs = img_vs.resize((100, 100))

                    # Assicurati che tutte le immagini siano in modalità RGBA per supportare la trasparenza
                    if img1.mode != 'RGBA':
                        img1 = img1.convert('RGBA')
                    if img2.mode != 'RGBA':
                        img2 = img2.convert('RGBA')

                    # Crea una nuova immagine con spazio per entrambi i loghi e il VS
                    combined_width = 300
                    combined = Image.new('RGBA', (combined_width, 150), (255, 255, 255, 0))

                    # Posiziona le immagini con il VS sovrapposto al centro
                    # Posiziona il primo logo a sinistra
                    combined.paste(img1, (0, 0), img1)
                    # Posiziona il secondo logo a destra
                    combined.paste(img2, (combined_width - 150, 0), img2)

                    # Posiziona il VS al centro, sovrapposto ai due loghi
                    vs_x = (combined_width - 100) // 2

                    # Crea una copia dell'immagine combinata prima di sovrapporre il VS
                    # Questo passaggio è importante per preservare i dettagli dei loghi sottostanti
                    combined_with_vs = combined.copy()
                    combined_with_vs.paste(img_vs, (vs_x, 25), img_vs)

                    # Usa l'immagine con VS sovrapposto
                    combined = combined_with_vs

                    # Salva l'immagine combinata
                    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                    combined.save(output_filename)

                    print(f"[✓] Immagine combinata creata: {output_filename}")

                    # Carica le variabili d'ambiente per GitHub
                    NOMEREPO = os.getenv("NOMEREPO", "").strip()
                    NOMEGITHUB = os.getenv("NOMEGITHUB", "").strip()

                    # Se le variabili GitHub sono disponibili, restituisci l'URL raw di GitHub
                    if NOMEGITHUB and NOMEREPO:
                        github_raw_url = f"https://raw.githubusercontent.com/{NOMEGITHUB}/{NOMEREPO}/main/{output_filename}"
                        print(f"[✓] URL GitHub generato: {github_raw_url}")
                        return github_raw_url
                    else:
                        # Altrimenti restituisci il percorso locale
                        return output_filename

                except Exception as e:
                    print(f"[!] Errore nella creazione dell'immagine combinata: {e}")
                    # Se fallisce, restituisci solo il primo logo trovato
                    return logo1_url

            # Se non abbiamo trovato entrambi i loghi, restituisci quello che abbiamo
            return logo1_url or logo2_url

        # Se non riusciamo a identificare le squadre, procedi con la ricerca normale
        # Prepara la query di ricerca più specifica
        search_query = urllib.parse.quote(f"{clean_event_name} logo epg")

        # Utilizziamo l'API di Bing Image Search con parametri migliorati
        search_url = f"https://www.bing.com/images/search?q={search_query}&qft=+filterui:photo-transparent+filterui:aspect-square&form=IRFLTR"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Metodo 1: Cerca pattern per murl (URL dell'immagine media)
            patterns = [
                r'murl&quot;:&quot;(https?://[^&]+)&quot;',
                r'"murl":"(https?://[^"]+)"',
                r'"contentUrl":"(https?://[^"]+\.(?:png|jpg|jpeg|svg))"',
                r'<img[^>]+src="(https?://[^"]+\.(?:png|jpg|jpeg|svg))[^>]+class="mimg"',
                r'<a[^>]+class="iusc"[^>]+m=\'{"[^"]*":"[^"]*","[^"]*":"(https?://[^"]+)"'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches and len(matches) > 0:
                    # Prendi il primo risultato che sembra un logo (preferibilmente PNG o SVG)
                    for match in matches:
                        if '.png' in match.lower() or '.svg' in match.lower():
                            return match
                    # Se non troviamo PNG o SVG, prendi il primo risultato
                    return matches[0]

            # Metodo alternativo: cerca JSON incorporato nella pagina
            json_match = re.search(r'var\s+IG\s*=\s*(\{.+?\});\s*', response.text)
            if json_match:
                try:
                    # Estrai e analizza il JSON
                    json_str = json_match.group(1)
                    # Pulisci il JSON se necessario
                    json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+):', r'\1"\2":', json_str)
                    data = json.loads(json_str)

                    # Cerca URL di immagini nel JSON
                    if 'images' in data and len(data['images']) > 0:
                        for img_data in data['images']: # Rinominato 'img' in 'img_data' per evitare conflitto
                            if 'murl' in img_data:
                                return img_data['murl']
                except Exception as e:
                    print(f"[!] Errore nell'analisi JSON: {e}")

            print(f"[!] Nessun logo trovato per '{clean_event_name}' con i pattern standard")

            # Ultimo tentativo: cerca qualsiasi URL di immagine nella pagina
            any_img = re.search(r'(https?://[^"\']+\.(?:png|jpg|jpeg|svg|webp))', response.text)
            if any_img:
                return any_img.group(1)

    except Exception as e:
        print(f"[!] Errore nella ricerca del logo per '{event_name}': {e}")

    # Se non troviamo nulla, restituiamo None
    return None

def search_team_logo(team_name):
    """
    Funzione dedicata alla ricerca del logo di una singola squadra
    """
    try:
        # Prepara la query di ricerca specifica per la squadra
        search_query = urllib.parse.quote(f"{team_name} logo squadra calcio")

        # Utilizziamo l'API di Bing Image Search con parametri migliorati
        search_url = f"https://www.bing.com/images/search?q={search_query}&qft=+filterui:photo-transparent+filterui:aspect-square&form=IRFLTR"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive"
        }

        response = requests.get(search_url, headers=headers, timeout=10)

        if response.status_code == 200:
            # Metodo 1: Cerca pattern per murl (URL dell'immagine media)
            patterns = [
                r'murl&quot;:&quot;(https?://[^&]+)&quot;',
                r'"murl":"(https?://[^"]+)"',
                r'"contentUrl":"(https?://[^"]+\.(?:png|jpg|jpeg|svg))"',
                r'<img[^>]+src="(https?://[^"]+\.(?:png|jpg|jpeg|svg))[^>]+class="mimg"',
                r'<a[^>]+class="iusc"[^>]+m=\'{"[^"]*":"[^"]*","[^"]*":"(https?://[^"]+)"'
            ]

            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                if matches and len(matches) > 0:
                    # Prendi il primo risultato che sembra un logo (preferibilmente PNG o SVG)
                    for match in matches:
                        if '.png' in match.lower() or '.svg' in match.lower():
                            return match
                    # Se non troviamo PNG o SVG, prendi il primo risultato
                    return matches[0]

            # Metodo alternativo: cerca JSON incorporato nella pagina
            json_match = re.search(r'var\s+IG\s*=\s*(\{.+?\});\s*', response.text)
            if json_match:
                try:
                    # Estrai e analizza il JSON
                    json_str = json_match.group(1)
                    # Pulisci il JSON se necessario
                    json_str = re.sub(r'([{,])\s*([a-zA-Z0-9_]+):', r'\1"\2":', json_str)
                    data = json.loads(json_str)

                    # Cerca URL di immagini nel JSON
                    if 'images' in data and len(data['images']) > 0:
                        for img_data in data['images']: # Rinominato 'img' in 'img_data' per evitare conflitto
                            if 'murl' in img_data:
                                return img_data['murl']
                except Exception as e:
                    print(f"[!] Errore nell'analisi JSON: {e}")

            print(f"[!] Nessun logo trovato per '{team_name}' con i pattern standard")

            # Ultimo tentativo: cerca qualsiasi URL di immagine nella pagina
            any_img = re.search(r'(https?://[^"\']+\.(?:png|jpg|jpeg|svg|webp))', response.text)
            if any_img:
                return any_img.group(1)

    except Exception as e:
        print(f"[!] Errore nella ricerca del logo per '{team_name}': {e}")

    # Se non troviamo nulla, restituiamo None
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
