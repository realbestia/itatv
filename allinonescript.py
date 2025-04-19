import requests
import os
import re
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta

# Funzione per il primo script (merger_playlist.py)
def merger_playlist():
    # Codice del primo script qui
    # Aggiungi il codice del tuo script "merger_playlist.py" in questa funzione.
    # Ad esempio:
    print("Eseguendo il merger_playlist.py...")
    # Il codice che avevi nello script "merger_playlist.py" va qui, senza modifiche.

# Funzione per il secondo script (epg_merger.py)
def epg_merger():
    # Codice del secondo script qui
    # Aggiungi il codice del tuo script "epg_merger.py" in questa funzione.
    # Ad esempio:
    print("Eseguendo l'epg_merger.py...")
    # Il codice che avevi nello script "epg_merger.py" va qui, senza modifiche.

# Funzione per il terzo script (eventi_m3u8_generator.py)
def eventi_m3u8_generator():
    # Codice del terzo script qui
    # Aggiungi il codice del tuo script "eventi_m3u8_generator.py" in questa funzione.
    print("Eseguendo l'eventi_m3u8_generator.py...")
    # Il codice che avevi nello script "eventi_m3u8_generator.py" va qui, senza modifiche.

# Funzione per il quarto script (schedule_extractor.py)
def schedule_extractor():
    # Codice del quarto script qui
    # Aggiungi il codice del tuo script "schedule_extractor.py" in questa funzione.
    print("Eseguendo lo schedule_extractor.py...")
    # Il codice che avevi nello script "schedule_extractor.py" va qui, senza modifiche.

# Funzione per il quinto script (epg_eventi_generator.py)
def epg_eventi_generator():
    # Codice del quinto script qui
    # Aggiungi il codice del tuo script "epg_eventi_generator.py" in questa funzione.
    print("Eseguendo l'epg_eventi_generator.py...")
    # Il codice che avevi nello script "epg_eventi_generator.py" va qui, senza modifiche.

# Funzione per il sesto script (vavoo_italy_channels.py)
def vavoo_italy_channels():
    # Codice del sesto script qui
    # Aggiungi il codice del tuo script "vavoo_italy_channels.py" in questa funzione.
    print("Eseguendo il vavoo_italy_channels.py...")
    # Il codice che avevi nello script "vavoo_italy_channels.py" va qui, senza modifiche.

# Funzione per il settimo script (world_channels_generator.py)
def world_channels_generator():
    # Codice del settimo script qui
    # Aggiungi il codice del tuo script "world_channels_generator.py" in questa funzione.
    print("Eseguendo il world_channels_generator.py...")
    # Il codice che avevi nello script "world_channels_generator.py" va qui, senza modifiche.

# Funzione principale che esegue tutti gli script
def run_all_scripts():
    # Eseguiamo ogni funzione nello stesso ordine che avevamo nel run_all.py
    merger_playlist()
    epg_merger()
    eventi_m3u8_generator()
    schedule_extractor()
    epg_eventi_generator()
    vavoo_italy_channels()
    world_channels_generator()

# Esecuzione del programma principale
if __name__ == "__main__":
    run_all_scripts()