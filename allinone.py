import requests
import os

# URL delle playlist M3U8
url1 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/channels_italy.m3u8"
url2 = "https://ddylv-proxy.hf.space/proxy?url=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.m3u8"
url3 = "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"
url4 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/world.m3u8"

# Funzione per scaricare una playlist
def download_playlist(url, append_params=False, exclude_group_title=None):
    response = requests.get(url)
    response.raise_for_status()
    playlist = response.text

    # Rimuove l'intestazione #EXTM3U se presente
    playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('#EXTM3U'))

    if append_params:
        playlist_lines = playlist.splitlines()
        for i in range(len(playlist_lines)):
            if '.m3u8' in playlist_lines[i]:
                playlist_lines[i] += "&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz"
        playlist = '\n'.join(playlist_lines)

    if exclude_group_title:
        lines = playlist.split('\n')
        filtered_lines = []
        skip_next = False
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if exclude_group_title in line and line.startswith("#EXTINF"):
                skip_next = True
                continue
            filtered_lines.append(line)
        playlist = '\n'.join(filtered_lines)

    return playlist

# Directory dello script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Scarica le playlist
playlist1 = download_playlist(url1)
playlist2 = download_playlist(url2, append_params=True)
playlist3 = download_playlist(url3)
playlist4 = download_playlist(url4, exclude_group_title="Italy")

# Unisci tutte le playlist
combined_playlist = playlist1 + "\n" + playlist2 + "\n" + playlist3 + "\n" + playlist4

# Aggiungi intestazione EPG per .m3u8
combined_playlist = '#EXTM3U tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"\n' + combined_playlist

# Percorsi dei file di output
output_filename_m3u8 = os.path.join(script_directory, "combined_playlist.m3u8")
output_filename_m3u = os.path.join(script_directory, "combined_playlist.m3u")

# Salva file .m3u8
with open(output_filename_m3u8, 'w', encoding='utf-8') as file:
    file.write(combined_playlist)

# Modifica intestazione per .m3u
combined_playlist_m3u = combined_playlist.replace("#EXTM3U tvg-url=", "#EXTM3U x-tvg-url=")

# Salva file .m3u
with open(output_filename_m3u, 'w', encoding='utf-8') as file:
    file.write(combined_playlist_m3u)

print(f"Playlist .m3u8 salvata in: {output_filename_m3u8}")
print(f"Playlist .m3 salvata in: {output_filename_m3u}")