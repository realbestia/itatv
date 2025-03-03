import requests

# URL del file M3U8
url = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.m3u8"

# Scarica il contenuto del file M3U8
response = requests.get(url)

# Verifica che la richiesta sia andata a buon fine
if response.status_code == 200:
    # Salva il contenuto in una lista
    m3u8_content = response.text.splitlines()
    
    # Lista per salvare i canali filtrati
    filtered_channels = []
    
    # Variabile per tenere traccia se la riga successiva è l'URL di un canale
    current_channel_info = None
    
    # Analizza il contenuto riga per riga
    for line in m3u8_content:
        if line.startswith("#EXTINF"):
            # Se la riga contiene un canale, verifica se contiene "IT", "Italia" o "Rai"
            if any(keyword in line for keyword in ["IT", "Italia", "Rai"]):
                # Aggiungi la riga corrente (che contiene info sul canale) e la successiva (URL)
                if current_channel_info:
                    filtered_channels.append(current_channel_info)
                current_channel_info = line
        elif line.startswith("http") and current_channel_info:
            # Se è l'URL di un canale, aggiungilo al risultato finale
            filtered_channels.append(line)
            current_channel_info = None  # Reset per il prossimo canale

    # Salva il contenuto filtrato in un nuovo file
    with open("eventi.m3u8", "w") as file:
        file.write("\n".join(filtered_channels))
    
    print("File M3U8 filtrato salvato come 'eventi.m3u8'")
else:
    print(f"Errore nel scaricare il file: {response.status_code}")
