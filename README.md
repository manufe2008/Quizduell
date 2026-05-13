# Quizduell
Quizduell als Highscore mode oder als multiplayer spiel mit maximal 4 Spielern 

import json              # Zum Lesen und Schreiben von JSON-Dateien
import os                # Für Datei- und Pfadoperationen
import string            # Enthält u.a. Satzzeichen
import random            # Für Zufallsauswahl bei Antworten
from difflib import SequenceMatcher  # Zum Vergleichen der Ähnlichkeit von Texten

# Initialisiert den Zufallsgenerator mit aktueller Zeit
random.seed()

Frage+ant = "loesung.json" #fragen und antwortsmöglichkeiten
Highscore = "highscore.json"  # Highscore inklusive name der bisher gespielten Leute

def singleplayer():
    
