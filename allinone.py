import requests
import os

# URL delle playlist M3U8
url1 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/channels_italy.m3u8"
url2 = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.m3u8"

# Funzione per scaricare una playlist
def download_playlist(url):
    response = requests.get(url)
    response.raise_for_status()  # Se c'è un errore, solleva un'eccezione
    return response.text

# Ottieni la directory dove si trova lo script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Scarica entrambe le playlist
playlist1 = download_playlist(url1)
playlist2 = download_playlist(url2)

# Unisci le due playlist
combined_playlist = playlist1 + "\n" + playlist2

# Percorso completo del file di output
output_filename = os.path.join(script_directory, "combined_playlist.m3u8")

# Salva la playlist combinata
with open(output_filename, 'w') as file:
    file.write(combined_playlist)

print(f"Playlist combinata salvata in: {output_filename}")
