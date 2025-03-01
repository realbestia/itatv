import requests
import re

# URL della lista M3U8
url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/mergeita.m3u8"
output_file = "eventi_italy.m3u8"

def scarica_lista_m3u8(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def filtra_canali_eventi(m3u8_content):
    righe = m3u8_content.splitlines()
    canali_eventi = []
    salva = False

    for riga in righe:
        if riga.startswith("#EXTINF"):
            if 'group-title="Eventi"' in riga:
                salva = True
                canali_eventi.append(riga)
            else:
                salva = False
        elif salva:
            canali_eventi.append(riga)

    return canali_eventi

def filtra_italia(canali_eventi):
    canali_eventi_italia = []
    for riga in canali_eventi:
        if riga.startswith("#EXTINF"):
            # Check if 'Italy' is present in the tvg-name
            if re.search(r'tvg-name="[^"]*Italy[^"]*"', riga):
                canali_eventi_italia.append(riga)
        else:
            canali_eventi_italia.append(riga)
    
    return canali_eventi_italia

def salva_lista(output_file, contenuto):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + contenuto)

def main():
    try:
        lista_m3u8 = scarica_lista_m3u8(url)
        canali_eventi = filtra_canali_eventi(lista_m3u8)  # First filter: group-title="Eventi"
        canali_filtrati = filtra_italia(canali_eventi)  # Second filter: tvg-name contains "Italy"
        
        if canali_filtrati:
            salva_lista(output_file, "\n".join(canali_filtrati))
            print(f"Lista salvata in {output_file}")
        else:
            print("Nessun canale trovato con group-title='Eventi' e 'Italy' nel tvg-name")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
