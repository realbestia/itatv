import requests
import json
import re
import os
import gzip
import lzma
import io
import time
import xml.etree.ElementTree as ET
from fuzzywuzzy import fuzz
import logging
from functools import lru_cache

# Configurazione
CONFIG = {
    "base_urls": ["https://vavoo.to"],
    "epg_urls": ["https://raw.githubusercontent.com/realbestia/itatv/main/merged_epg.xml"],
    "output_file": "channels_italy.m3u8",
    "request_timeout": 15,
    "max_retries": 3,
    "matching_threshold": 88,
    "number_words": {
        "1": "uno", "2": "due", "3": "tre", "4": "quattro",
        "5": "cinque", "6": "sei", "7": "sette", "8": "otto", "9": "nove",
        "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici", 
        "14": "quattordici", "15": "quindici", "16": "sedici", 
        "17": "diciassette", "18": "diciotto", "19": "diciannove",
        "20": "venti"
    },
    "categories": {
        "service": {
            "Sky": ["sky", "fox", "hbo"],
            "DTT": ["rai", "mediaset", "focus", "boing"],
            "IPTV Gratuite": ["radio", "local", "regional", "free"]
        },
        "content": {
            "Sport": ["sport", "dazn", "eurosport"],
            "Film & Serie TV": ["cinema", "movie", "film", "serie"],
            "News": ["news", "tg", "meteo"],
            "Intrattenimento": ["rai", "mediaset", "italia"],
            "Bambini": ["cartoon", "boing", "disney"],
            "Documentari": ["discovery", "history", "nat geo"],
            "Musica": ["mtv", "radio", "music"]
        }
    }
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class EPGProcessor:
    def __init__(self):
        self.epg_map = {}
        self.logger = logging.getLogger("EPGProcessor")
    
    def preprocess_epg(self, epg_data):
        """Crea una mappa EPG normalizzata per ricerche veloci"""
        self.epg_map.clear()
        for epg_root in epg_data:
            if epg_root is None:
                continue
            for channel in epg_root.findall("channel"):
                self._process_channel(channel)

    def _process_channel(self, channel):
        """Elabora un singolo canale EPG"""
        display_name = channel.findtext("display-name")
        if not display_name:
            return

        channel_id = channel.get("id")
        icon = self._extract_icon(channel)
        
        normalized, numbers = self.normalize_name(display_name)
        
        self.epg_map.setdefault(normalized, []).append({
            "id": channel_id,
            "icon": icon,
            "numbers": numbers,
            "original": display_name
        })

    def _extract_icon(self, channel):
        """Gestisce diversi formati per le icone"""
        # Caso 1: <icon src="URL"/>
        icon_element = channel.find("icon")
        if icon_element is not None:
            return icon_element.get("src", "")
        
        # Caso 2: <icon>URL</icon>
        icon_text = channel.findtext("icon")
        return icon_text.strip() if icon_text else ""

    @lru_cache(maxsize=2000)
    def normalize_name(self, name):
        """Normalizza i nomi per il matching con cache"""
        name = re.sub(r"\(.*?\)|[^\w\s]", "", name).lower().strip()
        numbers = tuple(re.findall(r"\b\d{1,2}\b", name))
        
        # Sostituisci numeri con parole
        for num in sorted(numbers, key=lambda x: -len(x)):
            if num in CONFIG["number_words"]:
                name = re.sub(rf"\b{num}\b", CONFIG["number_words"][num], name)
        
        return re.sub(r"\s+", " ", name), numbers

    def find_best_match(self, channel_name):
        """Trova il miglior match EPG utilizzando la mappa preprocessata"""
        normalized, numbers = self.normalize_name(channel_name)
        best = {"score": 0, "id": "", "icon": ""}

        for epg_norm, entries in self.epg_map.items():
            for entry in entries:
                if self._numbers_match(numbers, entry["numbers"]):
                    score = fuzz.token_sort_ratio(normalized, epg_norm)
                    if score > best["score"] and score >= CONFIG["matching_threshold"]:
                        best.update(score=score, id=entry["id"], icon=entry["icon"])
                        if score == 100:  # Match perfetto
                            return best["id"], best["icon"]
        
        return (best["id"], best["icon"]) if best["score"] > 0 else ("", "")

    def _numbers_match(self, ch_numbers, epg_numbers):
        """Verifica la compatibilità tra numeri nei nomi"""
        if not ch_numbers and not epg_numbers:
            return True
        return any(n in epg_numbers for n in ch_numbers)

class IPTVManager:
    def __init__(self):
        self.logger = logging.getLogger("IPTVManager")
        self.epg_processor = EPGProcessor()

    def fetch_data(self, url):
        """Scarica dati con ritentativi"""
        for attempt in range(CONFIG["max_retries"]):
            try:
                response = requests.get(url, timeout=CONFIG["request_timeout"])
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                self.logger.error(f"Errore durante il download da {url} (tentativo {attempt + 1}): {e}")
                time.sleep(2 ** attempt)
        return []

    def filter_italian_channels(self, channels):
        """Filtra i canali italiani e rimuove duplicati"""
        results = {}
        for ch in channels:
            if ch.get("country", "").lower() in ["italy", "it", "italia"]:
                clean_name = re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", ch["name"])
                if clean_name not in results:
                    results[clean_name] = (clean_name, f"{ch['url']}", ch['base_url'])
        return list(results.values())

    def download_epg(self, epg_url):
        """Scarica e decomprime un file EPG XML (anche GZIP/XZ)"""
        try:
            response = requests.get(epg_url, timeout=CONFIG["request_timeout"])
            response.raise_for_status()
            file_signature = response.content[:2]

            if file_signature.startswith(b'\x1f\x8b'):
                with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as gz_file:
                    return ET.ElementTree(ET.fromstring(gz_file.read())).getroot()
            elif file_signature.startswith(b'\xFD7z'):
                with lzma.LZMAFile(fileobj=io.BytesIO(response.content)) as xz_file:
                    return ET.ElementTree(ET.fromstring(xz_file.read())).getroot()
            else:
                return ET.ElementTree(ET.fromstring(response.content)).getroot()
        except (requests.RequestException, gzip.BadGzipFile, lzma.LZMAError, ET.ParseError) as e:
            self.logger.error(f"Errore durante il download/parsing dell'EPG da {epg_url}: {e}")
            return None

    def save_m3u8(self, organized_channels, epg_urls):
        """Salva i canali IPTV in un file M3U8 con metadati EPG"""
        if os.path.exists(CONFIG["output_file"]):
            os.remove(CONFIG["output_file"])

        with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
            f.write(f'#EXTM3U x-tvg-url="{", ".join(epg_urls)}"\n\n')

            for service, categories in organized_channels.items():
                for category, channels in categories.items():
                    for name, url, base_url in channels:
                        tvg_id, tvg_icon = self.epg_processor.find_best_match(name)
                        f.write(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}" group-title="{category}" tvg-icon="{tvg_icon}", {name}\n')
                        f.write(f"{url}\n\n")

        self.logger.info(f"File {CONFIG['output_file']} creato con successo!")

    def main(self):
        epg_data = [self.download_epg(url) for url in CONFIG["epg_urls"]]
        self.epg_processor.preprocess_epg(epg_data)

        all_links = []
        for url in CONFIG["base_urls"]:
            channels = self.fetch_data(url)
            all_links.extend(self.filter_italian_channels(channels))

        # Organizzazione dei canali in base a servizio e categoria
        organized_channels = {service: {category: [] for category in CONFIG["categories"]["content"].keys()} for service in CONFIG["categories"]["service"].keys()}
        for name, url, base_url in all_links:
            service = "IPTV Gratuite"
            category = "Intrattenimento"
            for key, words in CONFIG["categories"]["service"].items():
                if any(word in name.lower() for word in words):
                    service = key
                    break
            for key, words in CONFIG["categories"]["content"].items():
                if any(word in name.lower() for word in words):
                    category = key
                    break
            organized_channels[service][category].append((name, url, base_url))

        self.save_m3u8(organized_channels, CONFIG["epg_urls"])

if __name__ == "__main__":
    IPTVManager().main()