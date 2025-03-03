import requests
import re
from datetime import datetime

# URL della lista M3U8
url = "https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/itaevents.m3u8"
output_file = "eventi.m3u8"

def scarica_lista_m3u8(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def modifica_orario_tvg_name(riga):
    # Rimuove "Italy -" e lo spazio dopo da tutta la riga
    riga = re.sub(r'Italy\s*-\s*', '', riga)
    
    # Rimuove completamente il tvg-id
    riga = re.sub(r'tvg-id="[^"]*"', '', riga)
    
    return riga

def estrai_data_dal_nome(riga):
    # Cerca una data nel formato dd/mm/yy nel tvg-name
    match = re.search(r'tvg-name="[^"]* (\d{2}/\d{2}/\d{2}) ', riga)
    if match:
        return match.group(1)
    return None

def filtra_canali_eventi_e_italiani(m3u8_content):
    righe = m3u8_content.splitlines()
    canali_eventi_italiani = []
    salva = False
    oggi = datetime.today().strftime('%d/%m/%y')  # Data odierna nel formato dd/mm/yy

    for riga in righe:
        # Verifica se la riga è una descrizione di un canale (#EXTINF)
        if riga.startswith("#EXTINF"):
            # Controlla se il gruppo è "Eventi" e se il tvg-id contiene "Italy"
            if 'group-title="Eventi"' in riga and 'tvg-id="' in riga:
                if 'Italy' in riga:  # Solo 'Italy' per tvg-id
                    # Check if tvg-name contains "IT" or "Italia"
                    if 'tvg-name="' in riga and ('IT' in riga or 'Italia' in riga or 'Rai' in riga):
                        # Estrai la data dal tvg-name
                        data_canale = estrai_data_dal_nome(riga)
                        if data_canale:
                            # Confronta la data del canale con la data odierna
                            if data_canale >= oggi:  # Se la data è uguale o successiva, salva il canale
                                salva = True
                            else:
                                salva = False  # Non salvare i canali con data precedente
                        else:
                            salva = False
                        if salva:
                            riga = modifica_orario_tvg_name(riga)  # Rimuove "Italy -" e il tvg-id
                            canali_eventi_italiani.append(riga)
                    else:
                        salva = False  # Se tvg-name non contiene IT o Italia, non salvarlo
                else:
                    salva = False  # Non salvare canali senza "Italy" nel tvg-id
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
            print("Nessun canale trovato con group-title='Eventi', tvg-id contenente 'Italy' e tvg-name contenente 'IT' o 'Italia'")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
