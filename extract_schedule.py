from playwright.sync_api import sync_playwright
import os
import json
from datetime import datetime
import re
from bs4 import BeautifulSoup

def html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ottieni il mese corrente
    current_month = datetime.now().strftime('%B')  # Nome completo del mese (es. 'April')
    
    # Initialize the result dictionary
    result = {}
    
    # Find all date rows to handle multiple days
    date_rows = soup.find_all('tr', class_='date-row')
    
    if not date_rows:
        print("AVVISO: Nessuna riga di data trovata nel contenuto HTML!")
        return {}
    
    current_date = None
    current_category = None
    
    # Process each element in the table
    for row in soup.find_all('tr'):
        # If it's a date row, set the current date
        if 'date-row' in row.get('class', []):
            current_date = row.find('strong').text.strip()

            # Controlla se la data contiene uno dei suffissi (st, nd, rd, th) e il mese
            match = re.search(r'(\d+)(st|nd|rd|th)', current_date)
            if match:
                # Aggiungi il mese corrente dopo il suffisso, solo se il mese non è già presente
                if current_month not in current_date:
                    current_date = re.sub(r'(\d+)(st|nd|rd|th)', r'\1\2 ' + current_month, current_date)

            result[current_date] = {}
            current_category = None
        
        # If it's a category row, set the current category
        elif 'category-row' in row.get('class', []) and current_date:
            current_category = row.find('strong').text.strip() + "</span>"
            result[current_date][current_category] = []
        
        # If it's an event row and we have both date and category
        elif 'event-row' in row.get('class', []) and current_date and current_category:
            event_time = row.find('div', class_='event-time').find('strong').text.strip()
            event_info = row.find('div', class_='event-info').text.strip()
            
            event_data = {
                "time": event_time,
                "event": event_info,
                "channels": []
            }
            
            # Find the channel row that follows this event row
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
                        # Remove the channel ID from the channel name if it's in parentheses
                        channel_name = re.sub(r'\s*\(CH-\d+\)$', '', channel_name)
                        
                        event_data["channels"].append({
                            "channel_name": channel_name,
                            "channel_id": channel_id
                        })
            
            result[current_date][current_category].append(event_data)
    
    return result

def extract_schedule_container():
    url = "https://daddylive.mp/"

    # Get the script's directory to save the JSON file there
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

            # Chiudi il browser
            browser.close()

            return True

        except Exception as e:
            print(f"ERRORE: {str(e)}")
            return False

if __name__ == "__main__":
    success = extract_schedule_container()
    # Imposta il codice di uscita in base al successo dell'operazione
    # Utile per i sistemi CI che controllano i codici di uscita
    if not success:
        exit(1)
