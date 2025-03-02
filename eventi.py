import requests
import re
from datetime import datetime, timedelta

# URL della lista M3U8
url = "https://raw.githubusercontent.com/ciccioxm3/omg/refs/heads/main/mergeita.m3u8"
output_file = "eventi.m3u8"

def scarica_lista_m3u8(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def aggiungi_un_ora(orario):
    try:
        # Converte l'orario in un oggetto datetime e aggiunge un'ora
        nuovo_orario = (datetime.strptime(orario, "%H:%M") + timedelta(hours=1)).strftime("%H:%M")
        return nuovo_orario
    except ValueError:
        return orario  # Se non è un orario valido, lo lascia invariato

def modifica_orario_tvg_name(riga):
    # Cerca un orario nel formato HH:MM dentro il tvg-name
    match = re.search(r'tvg-name="([^"]*\b\d{1,2}:\d{2}\b[^"]*)"', riga)
    if match:
        orario_originale = re.search(r'\b\d{1,2}:\d{2}\b', match.group(1))
        if orario_originale:
            nuovo_orario = aggiungi_un_ora(orario_originale.group(0))
            riga = riga.replace(orario_originale.group(0), nuovo_orario)

        # Rimuove "Italy -" dal tvg-name, indipendentemente dalla posizione
        riga = re.sub(r'tvg-name="([^"]*Italy - [^"]*)"', lambda m: m.group(0).replace("Italy - ", ""), riga)

        # Sostituisce il tvg-logo esistente con il nuovo logo
        riga = re.sub(r'tvg-logo="[^"]*"', 'tvg-logo="https://raw.githubusercontent.com/realbestia/itatv/refs/heads/main/logo.png"', riga)

    return riga

def filtra_canali_eventi_e_italiani(m3u8_content):
    righe = m3u8_content.splitlines()
    canali_eventi_italiani = []
    salva = False

    for riga in righe:
        # Verifica se la riga è una descrizione di un canale (#EXTINF)
        if riga.startswith("#EXTINF"):
            # Controlla se il gruppo è "Eventi" e se il tvg-id contiene "Italy"
            if 'group-title="Eventi"' in riga and 'tvg-id="' in riga:
                if 'Italy' in riga:  # Solo 'Italy' per tvg-id
                    # Check if tvg-name contains "IT" or "Italia"
                    if 'tvg-name="' in riga and ('IT' in riga or 'Italia' in riga):
                        salva = True
                        riga = modifica_orario_tvg_name(riga)  # Modifica l'orario nel tvg-name e sostituisce il logo
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
