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
    
    # ... [altri attributi di classe rimangono gli stessi]

    def load_config(self) -> List[Dict]:
        """Load EPG data from config.json file."""
        try:
            with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Loaded {len(data)} EPG entries from config.json")
                # Debug: print first few entries
                for entry in data[:3]:
                    print(f"Sample EPG entry: {entry}")
                return data
        except Exception as e:
            print(f"Error loading config file: {e}")
            return []

    def get_tvg_info(self, channel: Channel) -> Tuple[str, str]:
        """Find best matching TVG ID and icon from config.json data."""
        channel_name = channel.name.lower().replace(' ', '')
        print(f"\nMatching channel: {channel.name}")  # Debug log
        
        best_match = None
        best_score = 0

        for epg_entry in self.epg_data:
            epg_name = epg_entry.get("tvg-name", "").lower().replace(' ', '')
            
            # Calcola similarità
            score = self._calculate_similarity(channel_name, epg_name)
            
            if score > best_score:
                best_score = score
                best_match = epg_entry
                print(f"New best match: {epg_entry.get('tvg-name')} (score: {score})")  # Debug log

        if best_score >= 85:
            tvg_id = best_match.get("tvg-id", "")
            tvg_icon = best_match.get("tvg-icon", "")
            print(f"Final match for {channel.name}: ID={tvg_id}, Icon={tvg_icon}")  # Debug log
            return tvg_id, tvg_icon
        
        print(f"No match found for {channel.name}")  # Debug log
        return "", ""

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two channel names."""
        # Converte entrambi i nomi in minuscolo e rimuove spazi
        name1 = name1.lower().replace(" ", "").replace(".it", "")
        name2 = name2.lower().replace(" ", "").replace(".it", "")
        
        # Se uno dei nomi è vuoto, ritorna 0
        if not name1 or not name2:
            return 0
        
        # Se i nomi sono identici, ritorna 100
        if name1 == name2:
            return 100
        
        # Se uno è contenuto nell'altro completamente
        if name1 in name2 or name2 in name1:
            return 90
        
        # Calcola la lunghezza della più lunga sottostringa comune
        m = len(name1)
        n = len(name2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        longest = 0
        
        for i in range(m):
            for j in range(n):
                if name1[i] == name2[j]:
                    dp[i + 1][j + 1] = dp[i][j] + 1
                    longest = max(longest, dp[i + 1][j + 1])
        
        # Calcola il punteggio come percentuale della lunghezza media dei nomi
        return (longest * 200) / (len(name1) + len(name2))

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
                        # Debug: print channel info before writing
                        print(f"Writing channel: {channel.name}")
                        print(f"TVG ID: {channel.tvg_id}")
                        print(f"TVG Icon: {channel.tvg_icon}")
                        
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

        print(f"Processing {len(channels)} channels...")  # Debug log

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
