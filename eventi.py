import requests

# URL del file M3U8
url = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.m3u8"

# Scarica il contenuto del file M3U8
response = requests.get(url)

# Verifica che la richiesta sia andata a buon fine
if response.status_code == 200:
    # Salva il contenuto in una lista
    m3u8_content = response.text.splitlines()
    
    # Filtra i canali contenenti "IT", "Italia" o "Rai"
    filtered_lines = [line for line in m3u8_content if any(keyword in line for keyword in ["IT", "Italia", "Rai"])]
    
    # Salva il contenuto filtrato in un nuovo file
    with open("eventi.m3u8", "w") as file:
        file.write("\n".join(filtered_lines))
    
    print("File M3U8 filtrato salvato come 'eventi.m3u8'")
else:
    print(f"Errore nel scaricare il file: {response.status_code}")
