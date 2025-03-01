import requests

# URL della lista M3U8
url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/mergeita.m3u8"
output_file = "eventi_italy.m3u8"

def scarica_lista_m3u8(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def filtra_canali_eventi_italy(m3u8_content):
    righe = m3u8_content.splitlines()
    canali_eventi_italy = []
    salva = False

    for riga in righe:
        if riga.startswith("#EXTINF"):
            if 'group-title="Eventi"' in riga and 'tvg-name="' in riga and 'Italy' in riga:
                salva = True
                canali_eventi_italy.append(riga)
            else:
                salva = False
        elif salva:
            canali_eventi_italy.append(riga)

    return "\n".join(canali_eventi_italy)

def salva_lista(output_file, contenuto):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + contenuto)

def main():
    try:
        lista_m3u8 = scarica_lista_m3u8(url)
        canali_filtrati = filtra_canali_eventi_italy(lista_m3u8)
        if canali_filtrati:
            salva_lista(output_file, canali_filtrati)
            print(f"Lista salvata in {output_file}")
        else:
            print("Nessun canale trovato con group-title='Eventi' e 'Italy' nel tvg-name")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
