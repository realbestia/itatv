import requests
import json
import re
import os
import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

@dataclass
class Channel:
    name: str
    url: str
    base_url: str
    service: str = "IPTV gratuite"
    category: str = "Intrattenimento"
    tvg_id: str = ""
    tvg_icon: str = ""

class IPTVProcessor:
    BASE_URLS = ["https://vavoo.to"]
    OUTPUT_FILE = "channels_italy.m3u8"
    CONFIG_FILE = "config.json"
    
    NUMBER_WORDS = {
        "1": "uno", "2": "due", "3": "tre", "4": "quattro",
        "5": "cinque", "6": "sei", "7": "sette", "8": "otto", "9": "nove",
        "10": "dieci", "11": "undici", "12": "dodici", "13": "tredici", "14": "quattordici",
        "15": "quindici", "16": "sedici", "17": "diciassette", "18": "diciotto", "19": "diciannove",
        "20": "venti"
    }

    SERVICE_KEYWORDS = {
        "Sky": ["sky", "fox", "hbo"],
        "DTT": ["rai", "mediaset", "focus", "boing"],
        "IPTV gratuite": ["radio", "local", "regional", "free"]
    }

    CATEGORY_KEYWORDS = {
        "Sport": ["sport", "dazn", "eurosport", "sky sport", "rai sport"],
        "Film & Serie TV": ["primafila", "cinema", "movie", "film", "serie", "hbo", "fox"],
        "News": ["news", "tg", "rai news", "sky tg", "tgcom"],
        "Intrattenimento": ["rai", "mediaset", "italia", "focus", "real time"],
        "Bambini": ["cartoon", "boing", "nick", "disney", "baby"],
        "Documentari": ["discovery", "geo", "history", "nat geo", "nature", "arte", "documentary"],
        "Musica": ["mtv", "vh1", "radio", "music"]
    }

    def __init__(self):
        self.epg_data = self.load_config()

    def load_config(self) -> List[Dict]:
        """Load EPG data from config.json file."""
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
            return []

    @staticmethod
    def clean_channel_name(name: str) -> str:
        """Remove unwanted characters from channel name."""
        return re.sub(r"\s*(\|E|\|H|\(6\)|\(7\)|\.c|\.s)\s*", "", name)

    @classmethod
    def normalize_for_matching(cls, name: str) -> Tuple[str, Optional[str]]:
        """Normalize channel name for comparison."""
        temp_name = re.sub(r"\.it\b", "", name, flags=re.IGNORECASE)
        temp_name = re.sub(r"\(.*?\)", "", temp_name)
        temp_name = re.sub(r"[^\w\s]", "", temp_name).strip().lower()

        number_match = re.search(r"\b\d+\b", temp_name)
        number = number_match.group() if number_match else None

        if number and number in cls.NUMBER_WORDS:
            temp_name = temp_name.replace(number, cls.NUMBER_WORDS[number])

        return temp_name, number

    def fetch_channels(self, base_url: str, retries: int = 3) -> List[Dict]:
        """Fetch channels with retry logic."""
        for attempt in range(retries):
            try:
                response = requests.get(f"{base_url}/channels", timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Error downloading from {base_url} (attempt {attempt+1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
        return []

    def filter_italian_channels(self, channels: List[Dict], base_url: str) -> List[Channel]:
        """Filter Italian channels and remove duplicates."""
        results = {}
        for ch in channels:
            if ch.get("country") == "Italy":
                clean_name = self.clean_channel_name(ch["name"])
                if clean_name not in results:
                    results[clean_name] = Channel(
                        name=clean_name,
                        url=f"{base_url}/play/{ch['id']}/index.m3u8",
                        base_url=base_url
                    )
        return list(results.values())

    def get_tvg_info(self, channel: Channel) -> Tuple[str, str]:
        """Find best matching TVG ID and icon from config.json data."""
        normalized_name, _ = self.normalize_for_matching(channel.name)
        
        best_match = None
        best_score = 0

        for epg_channel in self.epg_data:
            epg_name = epg_channel.get("tvg-name", "")
            normalized_epg_name, _ = self.normalize_for_matching(epg_name)
            
            # Calcola la similarità usando fuzzy matching
            similarity = self._calculate_similarity(normalized_name, normalized_epg_name)
            
            if similarity > best_score:
                best_score = similarity
                best_match = epg_channel

        if best_score >= 85:  # Soglia di corrispondenza abbassata per maggiore flessibilità
            return best_match["tvg-id"], best_match["tvg-icon"]
        return "", ""

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two channel names."""
        # Rimuovi spazi e converti in minuscolo per un confronto più accurato
        name1 = name1.lower().replace(" ", "")
        name2 = name2.lower().replace(" ", "")
        
        # Implementazione semplice di similarità basata su sottostringe comuni
        shorter = name1 if len(name1) < len(name2) else name2
        longer = name2 if len(name1) < len(name2) else name1
        
        if not shorter:
            return 0
            
        # Trova la più lunga sottostringa comune
        longest_common = 0
        for i in range(len(shorter)):
            for j in range(i + 1, len(shorter) + 1):
                if shorter[i:j] in longer:
                    longest_common = max(longest_common, j - i)
                    
        return (longest_common * 2 * 100) / (len(name1) + len(name2))

    def categorize_channel(self, channel: Channel) -> None:
        """Categorize channel by service and content type."""
        name_lower = channel.name.lower()
        
        for service, keywords in self.SERVICE_KEYWORDS.items():
            if any(keyword in name_lower for keyword in keywords):
                channel.service = service
                break

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in name_lower for keyword in keywords):
                channel.category = category
                break

    def save_m3u8(self, channels: List[Channel]) -> None:
        """Save channels to M3U8 file with EPG metadata."""
        organized: Dict[str, Dict[str, List[Channel]]] = {
            service: {category: [] for category in self.CATEGORY_KEYWORDS.keys()}
            for service in self.SERVICE_KEYWORDS.keys()
        }

        for channel in channels:
            organized[channel.service][channel.category].append(channel)

        with open(self.OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            
            for service_channels in organized.values():
                for category_channels in service_channels.values():
                    for channel in category_channels:
                        f.write(
                            f'#EXTINF:-1 tvg-id="{channel.tvg_id}" '
                            f'tvg-name="{channel.name}" '
                            f'group-title="{channel.category}" '
                            f'tvg-icon="{channel.tvg_icon}", {channel.name}\n'
                            f"{channel.url}\n\n"
                        )

    def process(self) -> None:
        """Main processing function."""
        if not self.epg_data:
            print("No EPG data found in config file!")
            return

        # Fetch and process channels
        channels = []
        for url in self.BASE_URLS:
            raw_channels = self.fetch_channels(url)
            channels.extend(self.filter_italian_channels(raw_channels, url))

        # Categorize and add EPG information
        for channel in channels:
            self.categorize_channel(channel)
            channel.tvg_id, channel.tvg_icon = self.get_tvg_info(channel)

        # Save to file
        self.save_m3u8(channels)
        print(f"File {self.OUTPUT_FILE} created successfully!")

if __name__ == "__main__":
    processor = IPTVProcessor()
    processor.process()
