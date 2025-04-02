import requests
import os

# URL delle playlist M3U8
url1 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/channels_italy.m3u8"
url2 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/eventi.m3u8"
url3 = "https://raw.githubusercontent.com/Brenders/Pluto-TV-Italia-M3U/main/PlutoItaly.m3u"
url4 = "https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/world.m3u8"

# Funzione per scaricare una playlist
def download_playlist(url, append_params=False, exclude_group_title=None):
    response = requests.get(url)
    response.raise_for_status()
    playlist = response.text
    
    # Rimuove l'intestazione #EXTM3U duplicata
    playlist = '\n'.join(line for line in playlist.split('\n') if not line.startswith('#EXTM3U'))
    
    if append_params:
        playlist_lines = playlist.splitlines()
        for i in range(len(playlist_lines)):
            if '.m3u8' in playlist_lines[i]:
                playlist_lines[i] += "&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz"
        playlist = '\n'.join(playlist_lines)
    
    if exclude_group_title:
        playlist = '\n'.join(line for line in playlist.split('\n') if exclude_group_title not in line)
    
    return playlist

# Scarica le playlist
playlist1 = download_playlist(url1)
playlist2 = download_playlist(url2, append_params=True)
playlist3 = download_playlist(url3)
playlist4 = download_playlist(url4, exclude_group_title="Italy")

# Definizione dei nuovi canali sportivi
tv_sport_channels = """
#EXTINF:-1 tvg-id="871" tvg-name="SKY SPORT CALCIO 251" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 251
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://zekonew.newkso.ru/zeko/premium871/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz

#EXTINF:-1 tvg-id="872" tvg-name="SKY SPORT CALCIO 252" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 252
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://windnew.newkso.ru/wind/premium872/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz

#EXTINF:-1 tvg-id="873" tvg-name="SKY SPORT CALCIO 253" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 253
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://windnew.newkso.ru/wind/premium873/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz

#EXTINF:-1 tvg-id="874" tvg-name="SKY SPORT CALCIO 254" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 254
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://windnew.newkso.ru/wind/premium874/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz

#EXTINF:-1 tvg-id="875" tvg-name="SKY SPORT CALCIO 255" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 255
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://windnew.newkso.ru/wind/premium875/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz

#EXTINF:-1 tvg-id="876" tvg-name="SKY SPORT CALCIO 256" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 256
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://windnew.newkso.ru/wind/premium876/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz

#EXTINF:-1 tvg-id="877" tvg-name="SKY SPORT CALCIO 257" tvg-logo="https://raw.githubusercontent.com/tv-logo/tv-logos/main/countries/italy/sky-sport-calcio-it.png" group-title="Sport",SKY SPORT CALCIO 257
https://mfp2.nzo66.com/proxy/hls/manifest.m3u8?api_password=mfp123&d=https://nfsnew.newkso.ru/nfs/premium877/mono.m3u8&h_user-agent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F133.0.0.0+Safari%2F537.36&h_referer=https%3A%2F%2Filovetoplay.xyz%2F&h_origin=https%3A%2F%2Filovetoplay.xyz
"""


# Inserisci i nuovi canali sotto "Sky Sport Calcio"
sky_sport_index = playlist1.find("SKY SPORT CALCIO")

if sky_sport_index != -1:
    # Trova la posizione successiva dopo il canale "Sky Sport Calcio"
    end_index = playlist1.find("\n\n", sky_sport_index)
    
    if end_index != -1:
        # Inserisce i nuovi canali subito dopo il canale originale
        playlist1 = playlist1[:end_index] + tv_sport_channels + playlist1[end_index:]
    else:
        # Se non trova un newline, semplicemente aggiunge alla fine
        playlist1 += tv_sport_channels
else:
    print("⚠️ Attenzione: 'Sky Sport Calcio' non trovato nella playlist, i nuovi canali non verranno aggiunti.")

# Unisci le quattro playlist
combined_playlist = playlist1 + "\n" + playlist2 + "\n" + playlist3 + "\n" + playlist4

# Aggiungi il nuovo #EXTM3U tvg-url all'inizio della playlist combinata
combined_playlist = '#EXTM3U tvg-url="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/epg.xml"\n' + combined_playlist

# Salva la playlist combinata con encoding UTF-8
script_directory = os.path.dirname(os.path.abspath(__file__))
output_filename = os.path.join(script_directory, "combined_playlist.m3u8")

with open(output_filename, 'w', encoding='utf-8') as file:
    file.write(combined_playlist)

print(f"✅ Playlist combinata salvata in: {output_filename}")
