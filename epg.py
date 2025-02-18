import requests
import gzip
import shutil
import os

# URL del file gzip
url = 'https://www.epgitalia.tv/gzip'

# Nome del file dove salvare il file scaricato
output_filename = 'file_scaricato.gz'

# Scaricare il file
response = requests.get(url)
with open(output_filename, 'wb') as file:
    file.write(response.content)

# Decomprimere il file .gz e salvarlo come epg.xml
with gzip.open(output_filename, 'rb') as f_in:
    with open('epg.xml', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

# Eliminare il file .gz
os.remove(output_filename)

print('Download, decompressione e eliminazione del file .gz completati.')
