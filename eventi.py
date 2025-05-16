import json
import re
import requests
from urllib.parse import quote
from datetime import datetime, timedelta
from dateutil import parser

JSON_FILE = "daddyliveSchedule.json"
OUTPUT_FILE = "eventi.m3u8"
BASE_URL = "https://thedaddy.to/embed/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
}

HTTP_TIMEOUT = 10
session = requests.Session()
session.headers.update(HEADERS)

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

        stream_url = (f"https://{server_key}new.newkso.ru/{server_key}/{channel_key}/mono.m3u8")
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
    keywords = {"italy", "rai", "italia", "it"}
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
                        tvg_name = f"{event_title} ({date_str} {time_formatted})"
                        categorized_channels[category].append({
                            "tvg_name": tvg_name,
                            "channel_name": channel_name,
                            "channel_id": channel_id
                        })

    return categorized_channels

def generate_m3u_from_schedule(json_file, output_file):
    categorized_channels = extract_channels_from_json(json_file)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for category, channels in categorized_channels.items():
            if not channels:
                continue

            # Spacer con nome categoria pulito e group-title "Eventi Live"
            f.write(f'#EXTINF:-1 group-title="Eventi Live" tvg-name="{category}",--- {category} ---\nhttps://exemple.m3u8\n\n')

            for ch in channels:
                tvg_name = ch["tvg_name"]
                channel_id = ch["channel_id"]

                try:
                    stream = get_stream_from_channel_id(channel_id)
                    if stream:
                        f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{tvg_name}" group-title="Eventi Live",{tvg_name}\n{stream}\n\n')
                        print(f"[✓] {tvg_name}")
                    else:
                        print(f"[✗] {tvg_name} - Nessuno stream trovato")
                except Exception as e:
                    print(f"[!] Errore su {tvg_name}: {e}")

if __name__ == "__main__":
    generate_m3u_from_schedule(JSON_FILE, OUTPUT_FILE)
