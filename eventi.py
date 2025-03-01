import requests
import re

# URL della lista M3U8
url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/mergeita.m3u8"
output_file = "eventi.m3u8"

def scarica_lista_m3u8(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def filtra_canali_eventi_e_italiani(m3u8_content):
    righe = m3u8_content.splitlines()
    canali_eventi_italiani = []
    salva = False

    for riga in righe:
        # Verifica se la riga è una descrizione di un canale (#EXTINF)
        if riga.startswith("#EXTINF"):
            # Controlla se il gruppo è "Eventi" e il nome del canale contiene "IT" o "Italia"
            if 'group-title="Eventi"' in riga and ('IT' in riga or 'Italia' in riga):
                salva = True  # Se entrambe le condizioni sono soddisfatte, salva il canale
                canali_eventi_italiani.append(riga)
            else:
                salva = False  # Reset se non soddisfa i criteri
        elif salva:
            # Se il flag 'salva' è True, aggiungi la URL del canale
            canali_eventi_italiani.append(riga)

    return "\n".join(canali_eventi_italiani)

def salva_lista(output_file, contenuto):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n" + contenuto)

def main():
    try:
        lista_m3u8 = scarica_lista_m3u8(url)
        canali_filtrati = filtra_canali_eventi_e_italiani(lista_m3u8)
        if canali_filtrati:
            salva_lista(output_file, canali_filtrati)
            print(f"Lista salvata in {output_file}")
        else:
            print("Nessun canale trovato con group-title='Eventi' e tvg-name contenente 'IT' o 'Italia'")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
