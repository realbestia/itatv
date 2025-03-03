import requests

# URL del file m3u8
url = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.m3u8"

# Scarica il file m3u8
response = requests.get(url)

# Controlla se la risposta è valida
if response.status_code == 200:
    # Ottieni il contenuto del file m3u8
    m3u8_content = response.text

    # Filtra le linee che contengono "IT", "Italia" o "Rai"
    filtered_lines = []
    for line in m3u8_content.splitlines():
        if "IT" in line or "Italia" in line or "Rai" in line:
            # Rimuovi la parola "Italy" dalla linea
            line = line.replace("Italy", "")
            filtered_lines.append(line)

    # Crea il nuovo contenuto m3u8 con solo i canali filtrati
    filtered_m3u8_content = "\n".join(filtered_lines)

    # Salva il file filtrato
    with open("filtered_itaevents.m3u8", "w") as f:
        f.write(filtered_m3u8_content)

    print("File filtrato salvato come 'filtered_itaevents.m3u8'")

else:
    print("Errore nel download del file m3u8.")
