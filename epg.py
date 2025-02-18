import requests
import gzip
import shutil
import os

# URL del file .gzip e del file XML
url_gzip = 'https://www.epgitalia.tv/gzip'
url_xml = 'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/master/PlutoTV/it.xml'

# Nome del file dove salvare il file scaricato .gzip
output_gzip_filename = 'file_scaricato.gz'

# Scaricare il file .gzip
response_gzip = requests.get(url_gzip)
with open(output_gzip_filename, 'wb') as file:
    file.write(response_gzip.content)

# Decomprimere il file .gz e salvarlo come epg.xml
with gzip.open(output_gzip_filename, 'rb') as f_in:
    with open('epg.xml', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

# Eliminare il file .gz
os.remove(output_gzip_filename)

# Scaricare il file XML aggiuntivo
response_xml = requests.get(url_xml)
with open('plutoTV.xml', 'wb') as file:
    file.write(response_xml.content)

# Unire i contenuti dei due file XML
with open('epg.xml', 'rb') as file1, open('plutoTV.xml', 'rb') as file2:
    with open('epg_unito.xml', 'wb') as output_file:
        shutil.copyfileobj(file1, output_file)
        shutil.copyfileobj(file2, output_file)

# Eliminare i file XML separati dopo aver unito i contenuti
os.remove('epg.xml')
os.remove('plutoTV.xml')

print('Download, decompressione, unione dei file e pulizia completati.')
