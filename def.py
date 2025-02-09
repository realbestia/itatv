import requests
import json
import re
import os

# Lista tvg-id (senza i nomi dei canali, solo gli ID)
tvg_ids = [
    "20Mediaset.it",  
    "Twentyseven.it",  
    "7goldtelepadova.it",  
    "AlmaTV.it",  
    "Antenna3.it",  
    "AutoMotoTV.it",  
    "BIKE.it",  
    "Boing.it",  
    "BoingPlus1.it",  
    "Boomerang.it",  
    "BoomerangPlus1.it",  
    "Caccia.it",  
    "Canale5.it",  
    "Canale5Plus1.it",  
    "Canale10.it",  
    "CartoonPlus1.it",  
    "CartoonNetwork.it",  
    "Cartoonito.it",  
    "CrimeInvestigation.it",  
    "Cielo.it",  
    "Cine34.it",  
    "ClassCNBC.it",  
    "Classica.it",  
    "ClassTVModa.it",  
    "ComedyPlus1.it",  
    "ComedyCentral.it",  
    "DAZNZona.it",  
    "DEAjr.it",  
    "DEAkids.it",  
    "DEAkidsPlus1.it",  
    "myDeejay.it",  
    "DITV.it",  
    "DiscoveryPlus1.it",  
    "Discovery.it",  
    "DMAX.it",  
    "DMAXPlus1.it",  
    "DonnaTV.it",  
    "EQUTV.it",  
    "Eurosport2.it",  
    "Eurosport1.it",  
    "Focus.it",  
    "FoodNetwork.it",  
    "FoxBusiness.it",  
    "FoxNews.it",  
    "Frisbee.it",  
    "GamberoRosso.it",  
    "Giallo.it",  
    "HGTV.it",  
    "HistoryChannel.it",  
    "HistoryChannel+1.it",  
    "HorseTV.it",  
    "Iris.it",  
    "Italia1.it",  
    "Italia2.it",  
    "Italia7Gold.it",  
    "ItalianFishingTv.it",  
    "K2.it",  
    "LA5.it",  
    "La7.it",  
    "La7d.it",  
    "LaC-tv.it",  
    "LaQtv.it",  
    "LazioStyleChannel.it",  
    "MediasetExtra.it",  
    "Mezzo.en",  
    "MilanTV.it",  
    "MotorTrend.it",  
    "MTV.it",  
    "MTVMusic.it",  
    "NETTV.mt",  
    "NickJr.it",  
    "NickJrPlus1.it",  
    "Nickelodeon.it",  
    "NickelodeonPlus1.it",  
    "Nove.it",  
    "One.mt",  
    "Pesca.it",  
    "QVC.it",  
    "R101TV.it",  
    "Radio105TV.it",  
    "RadioBruno.it",  
    "RadioFreccia.it",  
    "RadioItalia.it",  
    "RadionorbaTV.it",  
    "radiozeta.it",  
    "Rai1.it",  
    "Rai1Plus1.it",  
    "Rai2.it",  
    "Rai2Plus1.it",  
    "Rai3.it",  
    "Rai3Plus1.it",  
    "Rai4.it",  
    "Rai5.it",  
    "RaiGulp.it",  
    "RaiMovie.it",  
    "RaiNews.it",  
    "RaiPremium.it",  
    "RaiRadio2.it",  
    "RaiScuola.it",  
    "RaiSport.it",  
    "RaiStoria.it",  
    "RaiYoyo.it",  
    "Rai4K.it",  
    "RDS.it",  
    "RDS-social.it",  
    "RealTime.it",  
    "RealTimePlus1.it",  
    "Rete4.it",  
    "Rete4Plus1.it",  
    "RTL102.5TV.it",  
    "SkyArte.it",  
    "SkyAtlantic.it",  
    "SkyAtlanticPlus1.it",  
    "SkyCinemaAction.it",  
    "SkyCinemaCollection.it",  
    "SkyCinemaComedy.it",  
    "SkyCinemaDrama.it",  
    "SkyCinemaDue.it",  
    "SkyCinemaDue+24.it",  
    "SkyCinemaFamily.it",  
    "SkyCinemaFamilyPlus1.it",  
    "SkyCinemaRomance.it",  
    "SkyCinemaSuspense.it",  
    "SkyCinemaUno.it",  
    "SkyCinemaUnoPlus1.it",  
    "SkyCinemaUnoPlus24.it",  
    "SkyCrime.it",  
    "SkyCrime+1.it",  
    "SkyDocumentaries.it",  
    "SkyDocumentaries+1.it",  
    "SkyInvestigation.it",  
    "SkyInvestigation+1.it",  
    "SkyNature.it",  
    "SkySerie.it",  
    "SkySerie+1.it",  
    "SkySport258.it",  
    "SkySport259.it",  
    "SkySport260.it",  
    "SkySport261.it",  
    "SkySport24.it",  
    "SkySport4K.it",  
    "SkySportArena.it",  
    "SkySportCalcio.it",  
    "SkySportF1.it",  
    "SkySportAction.it",  
    "SkySport251.it",  
    "SkySport252.it",  
    "SkySport253.it",  
    "SkySport254.it",  
    "SkySport255.it",  
    "SkySport256.it",  
    "SkySport257.it",  
    "SkySportMax.it",  
    "SkySportMotoGP.it",  
    "SkySportNBA.it",  
    "SkySportTennis.it",  
    "SkySportUno.it",  
    "SkyUno.it",  
    "SkyUnoPlus1.it",  
    "SmashTV.mt",  
    "SMtv.it",  
    "SMtvSport.it",  
    "Sportitalia.it",  
    "Super!.it",  
    "SuperTennis.it",  
    "TeleDue.it",  
    "TeleNorba.it",  
    "TeleOne.it",  
    "TeleRent.it",  
    "Telechiara.it",  
    "TeleCity.it",  
    "TeleLombardia.it",  
    "Telepace.it",  
    "Telereporter.it",  
    "TeleTicino.ch",  
    "Tgnorba24.it",  
    "SkyTG24.it",  
    "Tgcom24.it",  
    "TopCalcio24.it",  
    "TopCrime.it",  
    "TRCModena.it",  
    "TRMh24.it",  
    "TVCentroMarche.it",  
    "TVCapodistria.it",  
    "TV2000.it",  
    "Tv8.it",  
    "TVM.mt",  
    "TVM2.mt",  
    "UNINETTUNOUniversityTV.it",  
    "Videonovara.it",  
    "WarnerTV.it",  
    "WeDoTV.it",  
    "ZonaDAZN2.it"
]

# Siti da cui scaricare i dati
BASE_URLS = [
    "https://vavoo.to",
    # Aggiungi altri siti qui
]

OUTPUT_FILE = "channels_italy.m3u8"

# Mappatura servizi
SERVICE_KEYWORDS = {
    "Sky": ["sky", "fox", "hbo"],
    "DTT": ["rai", "mediaset", "focus", "boing"],
    "IPTV gratuite": ["radio", "local", "regional", "free"]
}

# Mappatura categorie tematiche
CATEGORY_KEYWORDS = {
    "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
    "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
    "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
    "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
    "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
    "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
    "Musica": ["mtv", "vh1", "radio", "music"]
}

def clean_channel_name(name):
    """Pulisce il nome del canale rimuovendo caratteri indesiderati."""
    return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

def fetch_channels(base_url):
    """Scarica i dati JSON da /channels di un sito."""
    try:
        response = requests.get(f"{base_url}/channels", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Errore durante il download da {base_url}: {e}")
        return []

def filter_italian_channels(channels, base_url):
    """Filtra i canali con country Italy e genera il link m3u8 con il nome del canale."""
    seen = {}
    results = []
    source_map = {
        "https://vavoo.to": "V",
        "https://huhu.to": "H",
        "https://kool.to": "K",
        "https://oha.to": "O"
    }
    
    for ch in channels:
        if ch.get("country") == "Italy":
            clean_name = clean_channel_name(ch["name"])
            source_tag = source_map.get(base_url, "")
            count = seen.get(clean_name, 0) + 1
            seen[clean_name] = count
            if count > 1:
                clean_name = f"{clean_name} ({source_tag}{count})"
            else:
                clean_name = f"{clean_name} ({source_tag})"
            results.append((clean_name, f"{base_url}/play/{ch['id']}/index.m3u8", base_url))
    
    return results

def classify_channel(name):
    """Classifica il canale per servizio e categoria tematica."""
    service = "IPTV gratuite"  # Default
    category = "Intrattenimento"  # Default

    for key, words in SERVICE_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            service = key
            break

    for key, words in CATEGORY_KEYWORDS.items():
        if any(word in name.lower() for word in words):
            category = key
            break

    return service, category

def extract_user_agent(base_url):
    """Estrae il nome del sito senza estensione e lo converte in maiuscolo per l'user agent."""
    match = re.search(r"https?://([^/.]+)", base_url)
    if match:
        return match.group(1).upper()
    return "DEFAULT"

def find_tvg_id(name, tvg_ids):
    """Associa un tvg-id al canale basato sul nome"""
    for tvg_id in tvg_ids:
        if re.search(r"\b" + re.escape(tvg_id.split('_')[0]) + r"\b", name.lower()):
            return tvg_id
    return ""  # Se non trova una corrispondenza

def organize_channels(channels):
    """Organizza i canali per servizio e categoria."""
    organized_data = {service: {category: [] for category in CATEGORY_KEYWORDS.keys()} for service in SERVICE_KEYWORDS.keys()}

    for name, url, base_url in channels:
        service, category = classify_channel(name)
        user_agent = extract_user_agent(base_url)
        organized_data[service][category].append((name, url, base_url, user_agent))

    return organized_data

def save_m3u8(organized_channels):
    """Salva i canali in un file M3U8."""
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for service, categories in organized_channels.items():
            for category, channels in categories.items():
                for name, url, base_url, user_agent in channels:
                    tvg_id = find_tvg_id(name, tvg_ids)  # Trova il tvg-id basato sul nome del canale
                    f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" http-user-agent="{user_agent}" http-referrer="{base_url}", {name}\n')
                    f.write(f"#EXTVLCOPT:http-user-agent={user_agent}/1.0\n")
                    f.write(f"#EXTVLCOPT:http-referrer={base_url}/\n")
                    f.write(f'#EXTHTTP:{{"User-Agent":"{user_agent}/1.0","Referer":"{base_url}/"}}\n')
                    f.write(f"{url}\n\n")

def main():
    all_links = []

    for url in BASE_URLS:
        channels = fetch_channels(url)
        italian_channels = filter_italian_channels(channels, url)
        all_links.extend(italian_channels)

    # Organizzazione dei canali
    organized_channels = organize_channels(all_links)

    # Salvataggio nel file M3U8
    save_m3u8(organized_channels)

    print(f"File {OUTPUT_FILE} creato con successo!")

if __name__ == "__main__":
    main()