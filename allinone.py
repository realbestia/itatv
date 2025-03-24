import requests
import os

# URL delle playlist M3U8
url1 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/channels_italy.m3u8"
url2 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.m3u8"
url3 = "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"
url4 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/world.m3u8"

# Funzione per scaricare una playlist
def download_playlist(url, remove_extm3u=False, append_params=False, exclude_group_title=None):
    response = requests.get(url)
    response.raise_for_status()  # Se c'è un errore, solleva un'eccezione
    playlist = response.text
    
    if append_params:
        # Aggiungi i parametri agli URL di streaming nella playlist
        playlist_lines = playlist.splitlines()
        for i in range(len(playlist_lines)):
            if '.m3u8' in playlist_lines[i]:  # Cerca i link .m3u8
                # Aggiungi i parametri alla fine del link
                playlist_lines[i] += "&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz"
        playlist = '\n'.join(playlist_lines)
    
    if remove_extm3u:
        # Rimuovi la riga che inizia con '#EXTM3U'
        playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('#EXTM3U'))
    
    # Escludi canali con un determinato group-title
    if exclude_group_title:
        playlist = '\n'.join(line for line in playlist.split('\n') if exclude_group_title not in line)
    
    return playlist

# Ottieni la directory dove si trova lo script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Scarica le playlist
playlist1 = download_playlist(url1)
playlist2 = download_playlist(url2, append_params=True)  # Aggiungi i parametri alla playlist eventi.m3u8
playlist3 = download_playlist(url3, remove_extm3u=True)
playlist4 = download_playlist(url4, exclude_group_title="Italy")  # Escludi i canali con group-title="Italy"

# Unisci le quattro playlist
combined_playlist = playlist1 + "\n" + playlist2 + "\n" + playlist3 + "\n" + playlist4

# Aggiungi il nuovo #EXTM3U tvg-url all'inizio della playlist combinata
combined_playlist = '#EXTM3U tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"\n' + combined_playlist

# Percorso completo del file di output
output_filename = os.path.join(script_directory, "combined_playlist.m3u8")

# Salva la playlist combinata
with open(output_filename, 'w') as file:
    file.write(combined_playlist)

print(f"Playlist combinata salvata in: {output_filename}")
