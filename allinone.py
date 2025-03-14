import requests
import os

# URL delle playlist M3U8
url1 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/channels_italy.m3u8"
url2 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.m3u8"
url3 = "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"

# Funzione per scaricare una playlist
def download_playlist(url, exclude_x_tvg_url=False, remove_extm3u=False, add_tvg_url=False, append_params=False):
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
    
    if exclude_x_tvg_url:
        # Filtra la linea contenente 'x-tvg-url='
        playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('x-tvg-url='))
    
    if remove_extm3u:
        # Rimuovi la riga che inizia con '#EXTM3U'
        playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('#EXTM3U'))
    
    if add_tvg_url:
        # Aggiungi 'tvg-url' subito dopo 'group-title="Pluto TV Italia"'
        lines = playlist.split('\n')
        for i in range(len(lines)):
            if 'group-title="Pluto TV Italia"' in lines[i]:
                # Trova l'indice del group-title e aggiungi l'tvg-url subito dopo
                index = lines[i].find('group-title="Pluto TV Italia"') + len('group-title="Pluto TV Italia"')
                lines[i] = lines[i][:index] + ' tvg-url="https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml"' + lines[i][index:]
        playlist = '\n'.join(lines)
    
    return playlist

# Ottieni la directory dove si trova lo script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Scarica le playlist, escludendo 'x-tvg-url=' dalla terza playlist, rimuovendo la riga '#EXTM3U' e aggiungendo 'tvg-url'
playlist1 = download_playlist(url1)
playlist2 = download_playlist(url2, append_params=True)  # Aggiungi i parametri alla playlist eventi.m3u8
playlist3 = download_playlist(url3, exclude_x_tvg_url=True, remove_extm3u=True, add_tvg_url=True)

# Unisci le tre playlist
combined_playlist = playlist1 + "\n" + playlist2 + "\n" + playlist3

# Percorso completo del file di output
output_filename = os.path.join(script_directory, "combined_playlist.m3u8")

# Salva la playlist combinata
with open(output_filename, 'w') as file:
    file.write(combined_playlist)

print(f"Playlist combinata salvata in: {output_filename}")
