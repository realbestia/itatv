from playwright.sync_api import sync_playwright
import os
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

def html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Inizializza il dizionario del risultato
    result = {}
    
    # Trova tutte le righe della data
    date_rows = soup.find_all('tr', class_='date-row')
    
    if not date_rows:
        print("AVVISO: Nessuna riga di data trovata nel contenuto HTML!")
        return {}
    
    current_date = None
    current_category = None
    
    # Processa ogni elemento nella tabella
    for row in soup.find_all('tr'):
        # Se è una riga di data, imposta la data corrente
        if 'date-row' in row.get('class', []):
            current_date = row.find('strong').text.strip()
            result[current_date] = {}
            current_category = None
        
        # Se è una riga di categoria, imposta la categoria corrente
        elif 'category-row' in row.get('class', []) and current_date:
            current_category = row.find('strong').text.strip() + "</span>"
            result[current_date][current_category] = []
        
        # Se è una riga di evento e abbiamo sia la data che la categoria
        elif 'event-row' in row.get('class', []) and current_date and current_category:
            event_time = row.find('div', class_='event-time').find('strong').text.strip()
            event_info = row.find('div', class_='event-info').text.strip()
            
            event_data = {
                "time": event_time,
                "event": event_info,
                "channels": []
            }
            
            # Trova la riga del canale che segue questa riga di evento
            event_index = len(result[current_date][current_category])
            channel_row_id = f"channels-{current_date}-{current_category}-{event_index}"
            channel_row = soup.find('tr', id=channel_row_id)
            
            if channel_row:
                channel_links = channel_row.find_all('a', class_='channel-button-small')
                for link in channel_links:
                    href = link['href']
                    channel_id_match = re.search(r'stream-(\d+)\.php', href)
                    if channel_id_match:
                        channel_id = channel_id_match.group(1)
                        channel_name = link.text.strip()
                        # Rimuovi l'ID del canale dal nome del canale se è tra parentesi
                        channel_name = re.sub(r'\s*\(CH-\d+\)$', '', channel_name)
                        
                        event_data["channels"].append({
                            "channel_name": channel_name,
                            "channel_id": channel_id
                        })
            
            result[current_date][current_category].append(event_data)
    
    return result

def modify_json_file(json_file_path):
    # Carica il file JSON
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Ottieni il mese corrente
    current_month = datetime.now().strftime("%B")
    
    # Modifica le date nel JSON per aggiungere il mese se mancante
    for date in list(data.keys()):
        # Cerca i suffissi "st", "nd", "rd", "th" e aggiungi il mese dopo
        match = re.match(r"(\w+\s\d+)(st|nd|rd|th)\s(\d{4})", date)
        if match:
            day_part = match.group(1)
            suffix = match.group(2)
            year_part = match.group(3)
            # Crea la data finale con il mese aggiunto dopo il suffisso
            new_date = f"{day_part}{suffix} {current_month} {year_part}"
            # Mantieni la chiave con il mese aggiunto
            data[new_date] = data.pop(date)
    
    # Risalva il file JSON con le modifiche
    with open(json_file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print(f"File JSON modificato e salvato in {json_file_path}")

def extract_schedule_container():
    url = "https://daddylive.mp/"

    # Ottieni la directory dello script per salvare il file JSON
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_output = os.path.join(script_dir, "daddyliveSchedule.json")

    print(f"Accesso alla pagina {url} per estrarre il main-schedule-container...")

    with sync_playwright() as p:
        # Lancia un browser Chromium in background
        browser = p.chromium.launch(headless=True)

        # Configura il contesto con un user agent realistico
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
        )

        # Crea una nuova pagina
        page = context.new_page()

        try:
            # Naviga alla URL
            print("Navigazione alla pagina...")
            page.goto(url)

            # Attendi per il caricamento dinamico del contenuto
            print("Attesa per il caricamento completo...")
            page.wait_for_timeout(10000)  # 10 secondi

            # Estrai il contenuto HTML
            schedule_content = page.evaluate("""() => {
                const container = document.getElementById('main-schedule-container');
                return container ? container.outerHTML : '';
            }""")

            if not schedule_content:
                print("AVVISO: main-schedule-container trovato ma è vuoto o non presente!")
                return False

            # Converti HTML in JSON
            print("Conversione HTML in formato JSON...")
            json_data = html_to_json(schedule_content)

            # Salva i dati JSON nella stessa cartella dello script
            with open(json_output, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4)

            print(f"Dati JSON salvati in {json_output}")

            # Modifica il file JSON per aggiungere il mese corrente se necessario
            modify_json_file(json_output)

            # Chiudi il browser
            browser.close()

            return True

        except Exception as e:
            print(f"ERRORE: {str(e)}")
            return False

if __name__ == "__main__":
    success = extract_schedule_container()
    if not success:
        exit(1)
