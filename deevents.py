import requests
import os
import re
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta

def eventi_m3u8_generator():
    # Codice del terzo script qui
    # Aggiungi il codice del tuo script "eventi_m3u8_generator.py" in questa funzione.
    print("Eseguendo l'eventi_m3u8_generator.py...")
    # Il codice che avevi nello script "eventi_m3u8_generator.py" va qui, senza modifiche.
    import json 
    import re 
    import requests 
    from datetime import datetime, timedelta 
    from dateutil import parser 
    import urllib.parse 
    import os
    from dotenv import load_dotenv
    from PIL import Image, ImageDraw, ImageFont
    import io
    import time

    # Carica le variabili d'ambiente dal file .env
    load_dotenv()

    PROXY = os.getenv("PROXYIP", "").strip()  
    JSON_FILE = "daddyliveSchedule.json" 
    OUTPUT_FILE = "deevents.m3u" 
    LINK_DADDY = os.getenv("LINK_DADDY", "https://daddylive.dad").strip()

    # Funzione per pulire il nome della categoria
    def clean_category_name(name): 
        # Rimuove tag html come </span> o simili 
        return re.sub(r'<[^>]+>', '', name).strip()
     
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
                            for img in data['images']:
                                if 'murl' in img:
                                    return img['murl']
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
                            for img in data['images']:
                                if 'murl' in img:
                                    return img['murl']
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
     
    def extract_channels_from_json(path): 
        keywords = {"de"} 
        now = datetime.now() 
      
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
                        time_obj = datetime.strptime(time_str, "%H:%M") + timedelta(hours=2) 
                        event_datetime = datetime.combine(date_obj, time_obj.time()) 
      
                        if now - event_datetime > timedelta(hours=2): 
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
            f.write("#EXTM3U\n") 
      
            for category, channels in categorized_channels.items(): 
                if not channels: 
                    continue 
      
                f.write(f'#EXTINF:-1 tvg-name="{category}" group-title="Eventi Live",--- {category} ---\nhttps://example.m3u8\n\n') 
      
                for ch in channels: 
                    tvg_name = ch["tvg_name"] 
                    channel_id = ch["channel_id"] 
                    event_title = ch["event_title"] 
                    
                    # Cerca un logo per questo evento
                    # Rimuovi l'orario dal titolo dell'evento prima di cercare il logo
                    clean_event_title = re.sub(r'\s*\(\d{1,2}:\d{2}\)\s*$', '', event_title)
                    print(f"[🔍] Ricerca logo per: {clean_event_title}") 
                    logo_url = search_logo_for_event(clean_event_title) 
                    logo_attribute = f' tvg-logo="{logo_url}"' if logo_url else '' 
      
                    stream_url = (f"{PROXY}/proxy/m3u?url={LINK_DADDY}/embed/stream-{channel_id}.php")                    
                    f.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{tvg_name}"{logo_attribute} group-title="Eventi Live",{tvg_name}\n{stream_url}\n\n') 
                    print(f"[✓] {tvg_name}" + (f" (logo trovato)" if logo_url else " (nessun logo trovato)")) 
      
    if __name__ == "__main__": 
        # Assicurati che il modulo requests sia installato 
        try: 
            import requests 
        except ImportError: 
            print("[!] Il modulo 'requests' non è installato. Installalo con 'pip install requests'") 
            exit(1) 
             
        generate_m3u_from_schedule(JSON_FILE, OUTPUT_FILE) 
    
# Funzione per il quarto script (schedule_extractor.py)
def schedule_extractor():
    # Codice del quarto script qui
    # Aggiungi il codice del tuo script "schedule_extractor.py" in questa funzione.
    print("Eseguendo lo schedule_extractor.py...")
    # Il codice che avevi nello script "schedule_extractor.py" va qui, senza modifiche.
    from playwright.sync_api import sync_playwright
    import os
    import json
    from datetime import datetime
    import re
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv

    # Carica le variabili d'ambiente dal file .env
    load_dotenv()

    LINK_DADDY = os.getenv("LINK_DADDY", "https://daddylive.dad").strip()
    
    def html_to_json(html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        result = {}
        
        date_rows = soup.find_all('tr', class_='date-row')
        if not date_rows:
            print("AVVISO: Nessuna riga di data trovata nel contenuto HTML!")
            return {}
    
        current_date = None
        current_category = None
    
        for row in soup.find_all('tr'):
            if 'date-row' in row.get('class', []):
                current_date = row.find('strong').text.strip()
                result[current_date] = {}
                current_category = None
    
            elif 'category-row' in row.get('class', []) and current_date:
                current_category = row.find('strong').text.strip() + "</span>"
                result[current_date][current_category] = []
    
            elif 'event-row' in row.get('class', []) and current_date and current_category:
                time_div = row.find('div', class_='event-time')
                info_div = row.find('div', class_='event-info')
    
                if not time_div or not info_div:
                    continue
    
                time_strong = time_div.find('strong')
                event_time = time_strong.text.strip() if time_strong else ""
                event_info = info_div.text.strip()
    
                event_data = {
                    "time": event_time,
                    "event": event_info,
                    "channels": []
                }
    
                # Cerca la riga dei canali successiva
                next_row = row.find_next_sibling('tr')
                if next_row and 'channel-row' in next_row.get('class', []):
                    channel_links = next_row.find_all('a', class_='channel-button-small')
                    for link in channel_links:
                        href = link.get('href', '')
                        channel_id_match = re.search(r'stream-(\d+)\.php', href)
                        if channel_id_match:
                            channel_id = channel_id_match.group(1)
                            channel_name = link.text.strip()
                            channel_name = re.sub(r'\s*\(CH-\d+\)$', '', channel_name)
    
                            event_data["channels"].append({
                                "channel_name": channel_name,
                                "channel_id": channel_id
                            })
    
                result[current_date][current_category].append(event_data)
    
        return result
    
    def modify_json_file(json_file_path):
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        current_month = datetime.now().strftime("%B")
    
        for date in list(data.keys()):
            match = re.match(r"(\w+\s\d+)(st|nd|rd|th)\s(\d{4})", date)
            if match:
                day_part = match.group(1)
                suffix = match.group(2)
                year_part = match.group(3)
                new_date = f"{day_part}{suffix} {current_month} {year_part}"
                data[new_date] = data.pop(date)
    
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        
        print(f"File JSON modificato e salvato in {json_file_path}")
    
    def extract_schedule_container():
        url = f"{LINK_DADDY}/"
    
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_output = os.path.join(script_dir, "daddyliveSchedule.json")
    
        print(f"Accesso alla pagina {url} per estrarre il main-schedule-container...")
    
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
    
            try:
                print("Navigazione alla pagina...")
                page.goto(url)
                print("Attesa per il caricamento completo...")
                page.wait_for_timeout(10000)  # 10 secondi
    
                schedule_content = page.evaluate("""() => {
                    const container = document.getElementById('main-schedule-container');
                    return container ? container.outerHTML : '';
                }""")
    
                if not schedule_content:
                    print("AVVISO: main-schedule-container non trovato o vuoto!")
                    return False
    
                print("Conversione HTML in formato JSON...")
                json_data = html_to_json(schedule_content)
    
                with open(json_output, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4)
    
                print(f"Dati JSON salvati in {json_output}")
    
                modify_json_file(json_output)
                browser.close()
                return True
    
            except Exception as e:
                print(f"ERRORE: {str(e)}")
                return False
    
    if __name__ == "__main__":
        success = extract_schedule_container()
        if not success:
            exit(1)

def epg_eventi_generator():
    # Codice del quinto script qui
    # Aggiungi il codice del tuo script "epg_eventi_generator.py" in questa funzione.
    print("Eseguendo l'epg_eventi_generator.py...")
    # Il codice che avevi nello script "epg_eventi_generator.py" va qui, senza modifiche.
    import os
    import re
    import json
    from datetime import datetime, timedelta

    # Funzione di utilità per pulire il testo (rimuovere tag HTML span)
    def clean_text(text):
        return re.sub(r'</?span.*?>', '', str(text))

    # --- SCRIPT 5: epg_eventi_xml_generator (genera eventi.xml) ---
    def load_json_for_epg(json_file_path):
        if not os.path.exists(json_file_path):
            print(f"[!] File JSON non trovato per EPG: {json_file_path}")
            return {}
        with open(json_file_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
        
        filtered_data = {}
        for date, categories in json_data.items():
            filtered_categories = {}
            for category, events in categories.items():
                filtered_events = []
                for event_info in events:
                    filtered_channels = []
                    # Utilizza .get("channels", []) per gestire casi in cui "channels" potrebbe mancare
                    for channel in event_info.get("channels", []): 
                        channel_name = clean_text(channel.get("channel_name", "")) # Usa .get per sicurezza
                        # Filtra per canali italiani
                        if re.search(r'\b(de)\b', channel_name, re.IGNORECASE):
                            filtered_channels.append(channel)
                    if filtered_channels:
                        # Assicura che event_info sia un dizionario prima dello unpacking
                        if isinstance(event_info, dict):
                            filtered_events.append({**event_info, "channels": filtered_channels})
                        else:
                            # Logga un avviso se il formato dell'evento non è quello atteso
                            print(f"[!] Formato evento non valido durante il filtraggio per EPG: {event_info}")
                if filtered_events:
                    filtered_categories[category] = filtered_events
            if filtered_categories:
                filtered_data[date] = filtered_categories
        return filtered_data

    def generate_epg_xml(json_data):
        epg_content = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
        
        italian_offset = timedelta(hours=2)
        italian_offset_str = "+0200" 

        current_datetime_utc = datetime.utcnow()
        current_datetime_local = current_datetime_utc + italian_offset

        # Tiene traccia degli ID dei canali per cui è già stato scritto il tag <channel>
        channel_ids_processed_for_channel_tag = set() 

        for date_key, categories in json_data.items():
            # Dizionario per memorizzare l'ora di fine dell'ultimo evento per ciascun canale IN QUESTA DATA SPECIFICA
            # Viene resettato per ogni nuova data.
            last_event_end_time_per_channel_on_date = {}

            try:
                date_str_from_key = date_key.split(' - ')[0]
                date_str_cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str_from_key)
                event_date_part = datetime.strptime(date_str_cleaned, "%A %d %B %Y").date()
            except ValueError as e:
                print(f"[!] Errore nel parsing della data EPG: '{date_str_from_key}'. Errore: {e}")
                continue

            if event_date_part < current_datetime_local.date():
                continue

            for category_name, events_list in categories.items():
                # Ordina gli eventi per orario di inizio (UTC) per garantire la corretta logica "evento precedente"
                try:
                    sorted_events_list = sorted(
                        events_list,
                        key=lambda x: datetime.strptime(x.get("time", "00:00"), "%H:%M").time()
                    )
                except Exception as e_sort:
                    print(f"[!] Attenzione: Impossibile ordinare gli eventi per la categoria '{category_name}' nella data '{date_key}'. Si procede senza ordinamento. Errore: {e_sort}")
                    sorted_events_list = events_list

                for event_info in sorted_events_list:
                    time_str_utc = event_info.get("time", "00:00")
                    event_name = clean_text(event_info.get("event", "Evento Sconosciuto"))
                    event_desc = event_info.get("description", f"{event_name} trasmesso in diretta.")

                    try:
                        event_time_utc_obj = datetime.strptime(time_str_utc, "%H:%M").time()
                        event_datetime_utc = datetime.combine(event_date_part, event_time_utc_obj)
                        event_datetime_local = event_datetime_utc + italian_offset
                    except ValueError as e:
                        print(f"[!] Errore parsing orario UTC '{time_str_utc}' per EPG evento '{event_name}'. Errore: {e}")
                        continue
                    
                    if event_datetime_local < (current_datetime_local - timedelta(hours=2)):
                        continue

                    for channel_data in event_info.get("channels", []):
                        channel_id = channel_data.get("channel_id", "")
                        channel_name_cleaned = clean_text(channel_data.get("channel_name", "Canale Sconosciuto"))

                        if not channel_id: 
                            continue

                        if channel_id not in channel_ids_processed_for_channel_tag:
                            epg_content += f'  <channel id="{channel_id}">\n'
                            epg_content += f'    <display-name>{channel_name_cleaned}</display-name>\n'
                            epg_content += f'  </channel>\n'
                            channel_ids_processed_for_channel_tag.add(channel_id)
                        
                        # --- LOGICA ANNUNCIO MODIFICATA ---
                        announcement_stop_local = event_datetime_local # L'annuncio termina quando inizia l'evento corrente

                        # Determina l'inizio dell'annuncio
                        if channel_id in last_event_end_time_per_channel_on_date:
                            # C'è stato un evento precedente su questo canale in questa data
                            previous_event_end_time_local = last_event_end_time_per_channel_on_date[channel_id]
                            
                            # Assicurati che l'evento precedente termini prima che inizi quello corrente
                            if previous_event_end_time_local < event_datetime_local:
                                announcement_start_local = previous_event_end_time_local
                            else:
                                # Sovrapposizione o stesso orario di inizio, problematico.
                                # Fallback a 00:00 del giorno, o potresti saltare l'annuncio.
                                print(f"[!] Attenzione: L'evento '{event_name}' sul canale '{channel_id}' inizia prima o contemporaneamente alla fine dell'evento precedente su questo canale. Fallback per l'inizio dell'annuncio.")
                                announcement_start_local = datetime.combine(event_datetime_local.date(), datetime.min.time())
                        else:
                            # Primo evento per questo canale in questa data
                            announcement_start_local = datetime.combine(event_datetime_local.date(), datetime.min.time()) # 00:00 ora italiana

                        # Assicura che l'inizio dell'annuncio sia prima della fine
                        if announcement_start_local < announcement_stop_local:
                            announcement_title = f'Inizierà alle {event_datetime_local.strftime("%H:%M")}.' # Orario italiano
                            
                            epg_content += f'  <programme start="{announcement_start_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" stop="{announcement_stop_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" channel="{channel_id}">\n'
                            epg_content += f'    <title lang="it">{announcement_title}</title>\n'
                            epg_content += f'    <desc lang="it">{event_name}.</desc>\n' 
                            epg_content += f'    <category lang="it">Annuncio</category>\n'
                            epg_content += f'  </programme>\n'
                        elif announcement_start_local == announcement_stop_local:
                            print(f"[INFO] Annuncio di durata zero saltato per l'evento '{event_name}' sul canale '{channel_id}'.")
                        else: # announcement_start_local > announcement_stop_local
                            print(f"[!] Attenzione: L'orario di inizio calcolato per l'annuncio è successivo all'orario di fine per l'evento '{event_name}' sul canale '{channel_id}'. Annuncio saltato.")

                        # --- EVENTO PRINCIPALE ---
                        main_event_start_local = event_datetime_local
                        main_event_stop_local = event_datetime_local + timedelta(hours=2) # Durata fissa 2 ore
                        
                        epg_content += f'  <programme start="{main_event_start_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" stop="{main_event_stop_local.strftime("%Y%m%d%H%M%S")} {italian_offset_str}" channel="{channel_id}">\n'
                        epg_content += f'    <title lang="it">{event_name}</title>\n'
                        epg_content += f'    <desc lang="it">{event_desc}</desc>\n'
                        epg_content += f'    <category lang="it">{clean_text(category_name)}</category>\n'
                        epg_content += f'  </programme>\n'

                        # Aggiorna l'orario di fine dell'ultimo evento per questo canale in questa data
                        last_event_end_time_per_channel_on_date[channel_id] = main_event_stop_local
        
        epg_content += "</tv>\n"
        return epg_content

    def epg_eventi_xml_generator():
        print("Eseguendo la generazione di eventi.xml...")
        JSON_INPUT_FILE_EPG = "daddyliveSchedule.json" # File JSON di input
        XML_OUTPUT_FILE_EPG = "deevents.xml"          # File XML di output
        
        # Determina il percorso assoluto dei file basandosi sulla directory dello script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_input_full_path = os.path.join(script_dir, JSON_INPUT_FILE_EPG)
        xml_output_full_path = os.path.join(script_dir, XML_OUTPUT_FILE_EPG)

        # Carica i dati JSON filtrati per i canali italiani
        json_data_for_epg = load_json_for_epg(json_input_full_path)
        if not json_data_for_epg: # Se non ci sono dati (es. file non trovato o vuoto dopo il filtro)
            print(f"[!] Nessun dato JSON caricato o filtrato da {json_input_full_path}. Salto la generazione di {XML_OUTPUT_FILE_EPG}.")
            return # Esce dalla funzione se non ci sono dati

        # Genera il contenuto XML dell'EPG
        epg_content_xml = generate_epg_xml(json_data_for_epg)
        
        # Salva il contenuto XML nel file di output
        with open(xml_output_full_path, "w", encoding="utf-8") as file:
            file.write(epg_content_xml)
        print(f"File EPG deevents.xml salvato in: {xml_output_full_path}")

    if __name__ == "__main__":
        epg_eventi_xml_generator()

def run_all_scripts():
    
    try:
        eventi_m3u8_generator()
    except Exception as e:
        print(f"Errore durante l'esecuzione di schedule_extractor: {e}")
		
    try:
        epg_eventi_generator()
    except Exception as e:
        print(f"Errore durante l'esecuzione di schedule_extractor: {e}")

# Esecuzione principale
if __name__ == "__main__":
    run_all_scripts()
