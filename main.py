

import json
import os
import sys
import time
from pathlib import Path


ANZAHL_FRAGEN = 10
ZEIT_PRO_FRAGE = 15          # Sekunden
SCHNELL_BONUS_FAKTOR = 1.5   # Bonus bei Antwort in der ersten Hälfte der Zeit
MAX_HIGHSCORES = 10

BASIS_DIR = Path(__file__).resolve().parent
FRAGEN_DATEI = BASIS_DIR / "questions.json"
HIGHSCORE_DATEI = BASIS_DIR / "highscores.json"

class Farbe:
    RESET = "\033[0m"
    FETT = "\033[1m"
    GRAU = "\033[90m"
    ROT = "\033[91m"
    GRUEN = "\033[92m"
    GELB = "\033[93m"
    BLAU = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

if os.name == "nt":
    os.system("")  
    
if os.name == "nt":
    import msvcrt

    def _lese_zeichen_nonblocking():
        if msvcrt.kbhit():
            try:
                return msvcrt.getch().decode("utf-8", errors="ignore")
            except UnicodeDecodeError:
                return ""
        return None

    def _terminal_vorbereiten():
        return None

    def _terminal_wiederherstellen(zustand):
        pass

else:
    import select
    import termios
    import tty

    def _lese_zeichen_nonblocking():
        rlist, _, _ = select.select([sys.stdin], [], [], 0)
        if rlist:
            return sys.stdin.read(1)
        return None

    def _terminal_vorbereiten():
        fd = sys.stdin.fileno()
        alt = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        return alt

    def _terminal_wiederherstellen(zustand):
        if zustand is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, zustand)


def warte_auf_antwort(zeitlimit):
    """
    Wartet bis zu `zeitlimit` Sekunden auf eine gültige Taste (1-4).
    'q' beendet das Spiel sofort. Gibt (index_0_basiert | None, dauer) zurück.
    None bedeutet: Zeit abgelaufen, keine gültige Antwort.
    """
    start = time.time()
    terminal_zustand = _terminal_vorbereiten()
    try:
        while True:
            verstrichen = time.time() - start
            verbleibend = zeitlimit - verstrichen
            if verbleibend <= 0:
                return None, zeitlimit

            zeige_countdown(verbleibend)

            zeichen = _lese_zeichen_nonblocking()
            if zeichen:
                if zeichen.lower() == "q":
                    _terminal_wiederherstellen(terminal_zustand)
                    print("\n\nSpiel beendet. Bis zum nächsten Duell!")
                    sys.exit(0)
                if zeichen in ("1", "2", "3", "4"):
                    return int(zeichen) - 1, time.time() - start
                # ungültige Taste -> weiter warten, Zeit läuft weiter
            time.sleep(0.05)
    finally:
        _terminal_wiederherstellen(terminal_zustand)


def zeige_countdown(verbleibend):
    sekunden = max(0, int(verbleibend) + 1)
    farbe = Farbe.GRUEN
    if sekunden <= 5:
        farbe = Farbe.ROT
    elif sekunden <= 8:
        farbe = Farbe.GELB
    text = f"\r⏱  Verbleibende Zeit: {farbe}{sekunden:>2} Sek.{Farbe.RESET}  (Taste 1-4, 'q' = beenden)  "
    print(text, end="", flush=True)



def lade_fragen():
    if not FRAGEN_DATEI.exists():
        print(f"{Farbe.ROT}Fehler: '{FRAGEN_DATEI.name}' wurde nicht gefunden.{Farbe.RESET}")
        sys.exit(1)
    with open(FRAGEN_DATEI, encoding="utf-8") as f:
        daten = json.load(f)
    pool = daten.get("fragen", [])
    if len(pool) < ANZAHL_FRAGEN:
        print(f"{Farbe.ROT}Zu wenige Fragen in '{FRAGEN_DATEI.name}' "
              f"(mindestens {ANZAHL_FRAGEN} nötig).{Farbe.RESET}")
        sys.exit(1)
    return pool


def baue_runde(pool):
    import random
    ausgewaehlt = random.sample(pool, ANZAHL_FRAGEN)
    runde = []
    for f in ausgewaehlt:
        reihenfolge = list(range(4))
        random.shuffle(reihenfolge)
        neue_antworten = [f["antworten"][i] for i in reihenfolge]
        neuer_richtig_index = reihenfolge.index(f["richtig"])
        runde.append({
            "kategorie": f["kategorie"],
            "schwierigkeit": f["schwierigkeit"],
            "punkte": f["punkte"],
            "frage": f["frage"],
            "antworten": neue_antworten,
            "richtig": neuer_richtig_index,
        })
    return runde


def lade_highscores():
    if not HIGHSCORE_DATEI.exists():
        return []
    try:
        with open(HIGHSCORE_DATEI, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def speichere_highscore(name, score):
    liste = lade_highscores()
    liste.append({
        "name": name,
        "score": score,
        "datum": time.strftime("%d.%m.%Y"),
    })
    liste.sort(key=lambda e: e["score"], reverse=True)
    liste = liste[:MAX_HIGHSCORES]
    with open(HIGHSCORE_DATEI, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)
    return liste


def zeige_highscore_liste(liste, hervorheben_name=None, hervorheben_score=None):
    print(f"\n{Farbe.FETT}{Farbe.CYAN}🏆 Highscore-Liste{Farbe.RESET}")
    if not liste:
        print(f"  {Farbe.GRAU}Noch keine Einträge. Du bist der Erste!{Farbe.RESET}")
        return
    for i, eintrag in enumerate(liste, start=1):
        ist_meiner = (eintrag["name"] == hervorheben_name and eintrag["score"] == hervorheben_score)
        zeile = f"  {i:>2}. {eintrag['name']:<18} {eintrag['score']:>5} Punkte   ({eintrag['datum']})"
        if ist_meiner:
            print(f"{Farbe.GELB}{zeile}  ← Du{Farbe.RESET}")
        else:
            print(zeile)

def berechne_punkte(basis_punkte, dauer):
    schnell_genug = dauer <= ZEIT_PRO_FRAGE / 2
    if schnell_genug:
        return round(basis_punkte * SCHNELL_BONUS_FAKTOR)
    return basis_punkte



def bildschirm_leeren():
    os.system("cls" if os.name == "nt" else "clear")


def zeige_frage(frage, index, gesamt, punktestand):
    bildschirm_leeren()
    print(f"{Farbe.MAGENTA}{Farbe.FETT}QUIZDUELL{Farbe.RESET}  "
          f"{Farbe.GRAU}|  Frage {index}/{gesamt}  |  "
          f"Kategorie: {frage['kategorie']}  |  "
          f"Wert: +{frage['punkte']} Punkte  |  "
          f"Punktestand: {punktestand}{Farbe.RESET}\n")
    print(f"{Farbe.FETT}{frage['frage']}{Farbe.RESET}\n")
    for i, antwort in enumerate(frage["antworten"], start=1):
        print(f"  {Farbe.CYAN}[{i}]{Farbe.RESET} {antwort}")
    print()


def zeige_feedback(richtig, verdient, zeit_abgelaufen, frage):
    if richtig:
        bonus = f" {Farbe.GELB}(Tempo-Bonus!){Farbe.RESET}" if verdient > frage["punkte"] else ""
        print(f"\n\n{Farbe.GRUEN}✔ Richtig! +{verdient} Punkte{bonus}{Farbe.RESET}")
    else:
        grund = "Zeit abgelaufen" if zeit_abgelaufen else "Leider falsch"
        richtige_antwort = frage["antworten"][frage["richtig"]]
        print(f"\n\n{Farbe.ROT}✘ {grund} – keine Punkte.{Farbe.RESET}")
        print(f"  Richtige Antwort war: {Farbe.GRUEN}{richtige_antwort}{Farbe.RESET}")
    time.sleep(1.8)


def spiele_runde(pool, spielername):
    runde = baue_runde(pool)
    punktestand = 0

    for index, frage in enumerate(runde, start=1):
        zeige_frage(frage, index, len(runde), punktestand)
        gewaehlter_index, dauer = warte_auf_antwort(ZEIT_PRO_FRAGE)

        if gewaehlter_index == frage["richtig"]:
            verdient = berechne_punkte(frage["punkte"], dauer)
            punktestand += verdient
            zeige_feedback(True, verdient, False, frage)
        else:
            zeit_abgelaufen = gewaehlter_index is None
            zeige_feedback(False, 0, zeit_abgelaufen, frage)

    return punktestand


def begruessung():
    bildschirm_leeren()
    print(f"{Farbe.MAGENTA}{Farbe.FETT}")
    print("  ___       _      ___        _ _ ")
    print(" |   \\ _  _(_)____|   \\ _  _ (_) |")
    print(" | |) | || | |_ /| |) | || || | | ")
    print(" |___/ \\_,_|_/__|___/ \\_,_||_|_| ")
    print(f"{Farbe.RESET}")
    print(f"{Farbe.GRAU}Singleplayer  ·  {ANZAHL_FRAGEN} Fragen  ·  {ZEIT_PRO_FRAGE} Sek. pro Frage  ·  "
          f"{SCHNELL_BONUS_FAKTOR}× Tempo-Bonus{Farbe.RESET}\n")

    bisherige = lade_highscores()
    if bisherige:
        print(f"Bisheriger Rekord: {Farbe.GELB}{bisherige[0]['score']} Punkte{Farbe.RESET} "
              f"({bisherige[0]['name']})\n")


def main():
    pool = lade_fragen()
    begruessung()

    while True:
        spielername = input("Dein Name: ").strip() or "Spieler"
        print(f"\n{Farbe.GRAU}Los geht's, {spielername}! Drücke Enter, um zu starten …{Farbe.RESET}")
        input()

        punktestand = spiele_runde(pool, spielername)

        bildschirm_leeren()
        print(f"{Farbe.FETT}{Farbe.CYAN}Duell beendet!{Farbe.RESET}\n")
        print(f"{Farbe.FETT}Gesamtpunkte: {Farbe.GELB}{punktestand}{Farbe.RESET}\n")

        liste = speichere_highscore(spielername, punktestand)
        zeige_highscore_liste(liste, hervorheben_name=spielername, hervorheben_score=punktestand)

        print()
        nochmal = input("\nNochmal spielen? (j/n): ").strip().lower()
        if nochmal != "j":
            print("\nBis zum nächsten Duell!")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSpiel abgebrochen.")
        sys.exit(0)