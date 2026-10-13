"""Kommandozeilen-Darstellung des Dashboards."""

import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime

from dashboard.domain import Modulstatus, Pruefungsart, Zielstatus
from dashboard.dto import DashboardDatenDTO, ModulZeileDTO, ZielDTO

BREITE = 92
"""Breite der Ausgabe in Zeichen."""

# ANSI-Escape-Sequenzen für Farben und Schriftschnitt.
_RESET, _FETT, _GEDIMMT = "\033[0m", "\033[1m", "\033[2m"
_ROT, _GRUEN, _GELB, _BLAU = "\033[31m", "\033[32m", "\033[33m", "\033[34m"

_AMPEL_FARBE = {Zielstatus.ERREICHT: _GRUEN, Zielstatus.IM_PLAN: _GELB, Zielstatus.GEFAEHRDET: _ROT}
_MODUL_FARBE = {
    Modulstatus.BESTANDEN: _GRUEN,
    Modulstatus.ANERKANNT: _GRUEN,
    Modulstatus.NICHT_BESTANDEN: _ROT,
    Modulstatus.IN_BEARBEITUNG: _GELB,
    Modulstatus.GEPLANT: _GEDIMMT,
}


@dataclass(frozen=True)
class ErgebnisEingabe:
    """Vom Benutzer eingegebenes Prüfungsergebnis."""

    kuerzel: str
    art: Pruefungsart
    note: float
    datum: date


def zahl(wert: float, stellen: int = 1) -> str:
    """Formatiert eine Zahl mit deutschem Dezimalkomma."""
    return f"{wert:.{stellen}f}".replace(".", ",")


def datum_de(wert: date) -> str:
    """Formatiert ein Datum als TT.MM.JJJJ."""
    return wert.strftime("%d.%m.%Y")


def _aktiviere_ansi_unter_windows() -> bool:
    """Schaltet in der klassischen Windows-Konsole die Verarbeitung von
    ANSI-Farbcodes ein (unter Windows Terminal/VS Code ohnehin aktiv).

    Returns:
        ``True``, wenn Farben dargestellt werden können.
    """
    if os.name != "nt":
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        modus = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(modus)):
            return False
        return bool(kernel32.SetConsoleMode(handle, modus.value | 0x0004))  # VIRTUAL_TERMINAL_PROCESSING
    except (AttributeError, OSError):
        return False


class DashboardView:
    """Gibt das Dashboard als Text aus und nimmt Eingaben entgegen.

    Die View enthält keine Fachlogik. Sie formatiert nur die Daten aus dem
    :class:`DashboardDatenDTO`. Ein- und Ausgabefunktion sind austauschbar,
    damit sich die View automatisiert testen lässt.

    Args:
        farbe: ``True`` für farbige Ausgabe, ``False`` für reinen Text,
            ``None`` für automatische Erkennung (Terminal, ``NO_COLOR``).
        ausgabe: Funktion zur Ausgabe einer Zeile (Standard: ``print``).
        eingabe: Funktion zum Einlesen einer Zeile (Standard: ``input``).
    """

    def __init__(
        self,
        farbe: bool | None = None,
        ausgabe: Callable[[str], None] | None = None,
        eingabe: Callable[[str], str] | None = None,
    ) -> None:
        if farbe is None:
            farbe = sys.stdout.isatty() and "NO_COLOR" not in os.environ and _aktiviere_ansi_unter_windows()
        self._farbe = farbe
        # Standardfunktionen erst beim Aufruf auflösen (lambda), damit sie sich
        # z. B. in Tests per unittest.mock ersetzen lassen.
        self._ausgabe = ausgabe or (lambda text: print(text))
        self._eingabe = eingabe or (lambda prompt: input(prompt))

    # --- Hilfsfunktionen ---------------------------------------------------------

    def _f(self, text: str, *codes: str) -> str:
        """Färbt Text ein, sofern Farben aktiv sind."""
        return f"{''.join(codes)}{text}{_RESET}" if self._farbe and codes else text

    def _ampel(self, status: Zielstatus) -> str:
        """Ampel-Symbol mit Text, damit die Bedeutung auch ohne Farbe erkennbar ist."""
        return self._f(f"● {status.value.upper()}", _FETT, _AMPEL_FARBE[status])

    def _zeile(self, text: str = "") -> None:
        self._ausgabe(text)

    def _ueberschrift(self, links: str, rechts: str = "") -> None:
        """Abschnittsüberschrift; ``rechts`` wird rechtsbündig ergänzt."""
        kopf = " " + self._f(links, _FETT, _BLAU)
        if rechts:
            luecke = BREITE - 1 - len(links) - len(_ohne_ansi(rechts))
            kopf += " " * max(1, luecke) + rechts
        self._zeile(kopf)

    # --- Dashboard ---------------------------------------------------------------

    def zeige(self, daten: DashboardDatenDTO) -> None:
        """Gibt das vollständige Dashboard aus."""
        k = daten.kennzahlen
        self._zeile("═" * BREITE)
        titel = f"STUDIEN-DASHBOARD · {daten.studiengang}"
        stichtag = f"Stichtag {datum_de(daten.stichtag)}"
        self._zeile(" " + self._f(titel, _FETT) + " " * max(1, BREITE - 2 - len(titel) - len(stichtag)) + stichtag)
        self._zeile("═" * BREITE)
        self._zeige_fristziel(daten)
        self._zeige_ects(daten)
        if daten.notenziel is not None and daten.zielwert_note is not None:
            self._zeige_notenziel(daten.notenziel, daten.zielwert_note, k.durchschnitt, k.benoetigter_restdurchschnitt)
        self._zeige_module(daten.module)
        self._zeige_schritte(daten.naechste_schritte)
        self._zeile("─" * BREITE)
        legende = " · ".join(self._f("●", _AMPEL_FARBE[st]) + f" {st.value}" for st in Zielstatus)
        self._zeile(" Legende: " + legende)

    def _zeige_fristziel(self, daten: DashboardDatenDTO) -> None:
        k = daten.kennzahlen
        self._zeile()
        self._ueberschrift(f"ZIEL 1 · {daten.fristziel.bezeichnung}", self._ampel(daten.fristziel.status))
        self._zeile(f"   Start {datum_de(daten.startdatum)} · Frist {datum_de(daten.zieldatum)} · "
                    f"noch {zahl(k.verbleibende_monate)} Monate")
        benoetigt = "Frist abgelaufen" if k.benoetigte_ects_pro_monat is None \
            else f"{zahl(k.benoetigte_ects_pro_monat)} ECTS/Monat"
        self._zeile(f"   Tempo bisher {zahl(k.reales_tempo)} ECTS/Monat · benötigt {benoetigt}")
        if k.prognose_abschluss is not None and k.verbleibende_ects > 0:
            spaet = k.prognose_abschluss > daten.zieldatum
            text = f"   Prognose bei gleichem Tempo: Abschluss {k.prognose_abschluss.strftime('%m/%Y')}"
            self._zeile(self._f(text, _ROT) if spaet else text)

    def _zeige_ects(self, daten: DashboardDatenDTO) -> None:
        k = daten.kennzahlen
        self._zeile()
        self._ueberschrift("ECTS-FORTSCHRITT")
        balken_breite = 40
        anteil = min(1.0, k.erreichte_ects / k.benoetigte_ects) if k.benoetigte_ects else 0.0
        voll = round(anteil * balken_breite)
        balken = self._f("█" * voll, _GRUEN) + self._f("░" * (balken_breite - voll), _GEDIMMT)
        self._zeile(f"   {balken}  {k.erreichte_ects} / {k.benoetigte_ects} ECTS ({round(anteil * 100)} %)"
                    f" · {k.verbleibende_ects} offen")

    def _zeige_notenziel(
        self, ziel: ZielDTO, zielwert: float, schnitt: float | None, rest: float | None
    ) -> None:
        self._zeile()
        self._ueberschrift(f"ZIEL 2 · {ziel.bezeichnung}", self._ampel(ziel.status))
        if schnitt is None:
            self._zeile("   Noch keine Note vorhanden.")
            return
        abweichung = schnitt - zielwert
        vorzeichen = "+" if abweichung > 0 else ("±" if abweichung == 0 else "−")
        self._zeile(f"   aktuell Ø {zahl(schnitt, 2)} · Ziel ≤ {zahl(zielwert, 2)} · "
                    f"Abweichung {vorzeichen}{zahl(abs(abweichung), 2)}")
        if rest is not None:
            if rest < 1.0:
                self._zeile(self._f("   Zielwert rechnerisch nicht mehr erreichbar.", _ROT))
            elif rest > 4.0:
                self._zeile("   Jede bestandene Note hält den Zielwert ein.")
            else:
                self._zeile(f"   Nötig in den verbleibenden ECTS: Ø {zahl(rest, 2)} oder besser")

    def _zeige_module(self, zeilen: tuple[ModulZeileDTO, ...]) -> None:
        self._zeile()
        self._ueberschrift("MEINE MODULE")
        kopf = f"   {'Sem':<4}{'Kürzel':<15}{'Modul':<37}{'ECTS':>4}  {'Status':<16}{'Vers.':>5}{'Note':>6}"
        self._zeile(self._f(kopf, _FETT))
        letztes_semester = None
        for z in zeilen:
            if letztes_semester is not None and z.semester != letztes_semester:
                self._zeile(self._f("   " + "·" * (BREITE - 3), _GEDIMMT))
            letztes_semester = z.semester
            titel = z.titel if len(z.titel) <= 35 else z.titel[:34] + "…"
            note = zahl(z.note) if z.note is not None else "–"
            versuche = str(z.versuche) if z.versuche else "–"
            text = (f"   {z.semester:<4}{z.kuerzel:<15}{titel:<37}{z.ects:>4}  "
                    f"{z.status.value:<16}{versuche:>5}{note:>6}")
            self._zeile(self._f(text, _MODUL_FARBE[z.status]))

    def _zeige_schritte(self, schritte: tuple[str, ...]) -> None:
        self._zeile()
        self._ueberschrift("NÄCHSTE SCHRITTE")
        if not schritte:
            self._zeile("   Keine offenen Punkte.")
        for s in schritte:
            self._zeile(f"   › {s}")

    # --- Interaktion -------------------------------------------------------------

    def frage_menue(self) -> str:
        """Zeigt das Hauptmenü und liefert die Auswahl."""
        self._zeile()
        self._zeile(self._f(" [1] Dashboard anzeigen   [2] Prüfungsergebnis erfassen   [0] Beenden", _FETT))
        return self._eingabe(" Auswahl: ").strip()

    def frage_pruefungsergebnis(
        self, module: tuple[ModulZeileDTO, ...], stichtag: date
    ) -> ErgebnisEingabe | None:
        """Fragt Modul, Prüfungsart, Note und Datum ab.

        Returns:
            die Eingabe oder ``None``, wenn der Benutzer abbricht (leere Eingabe).
        """
        if not module:
            self.zeige_meldung("Es gibt keine Module mit offenem Ergebnis.")
            return None
        self._zeile()
        self._zeile(" Module mit offenem Ergebnis:")
        for z in module:
            self._zeile(f"   {z.kuerzel:<15}{z.titel[:50]:<52}{z.status.value}")
        kuerzel = self._eingabe(" Kürzel (leer = Abbruch): ").strip()
        if not kuerzel:
            return None
        auswahl = next((z for z in module if z.kuerzel.casefold() == kuerzel.casefold()), None)
        if auswahl is None:
            self.zeige_fehler(f"{kuerzel} ist kein Modul mit offenem Ergebnis.")
            return None

        arten = list(Pruefungsart)
        vorschlag = next((a for a in arten if a.value == auswahl.pruefungsart), Pruefungsart.KLAUSUR)
        for i, art in enumerate(arten, start=1):
            self._zeile(f"   [{i:>2}] {art.value}")
        roh = self._eingabe(f" Prüfungsart (leer = {vorschlag.value}): ").strip()
        if not roh:
            art = vorschlag
        elif roh.isdigit() and 1 <= int(roh) <= len(arten):
            art = arten[int(roh) - 1]
        else:
            self.zeige_fehler("Ungültige Prüfungsart.")
            return None

        try:
            note = float(self._eingabe(" Note (z. B. 2,3): ").strip().replace(",", "."))
        except ValueError:
            self.zeige_fehler("Die Note muss eine Zahl sein.")
            return None

        roh = self._eingabe(f" Datum TT.MM.JJJJ (leer = {datum_de(stichtag)}): ").strip()
        try:
            datum = stichtag if not roh else datetime.strptime(roh, "%d.%m.%Y").date()
        except ValueError:
            self.zeige_fehler("Ungültiges Datum.")
            return None
        return ErgebnisEingabe(auswahl.kuerzel, art, note, datum)

    def zeige_meldung(self, text: str) -> None:
        self._zeile(self._f(f" ✓ {text}", _GRUEN))

    def zeige_fehler(self, text: str) -> None:
        self._zeile(self._f(f" ✗ {text}", _ROT))


def _ohne_ansi(text: str) -> str:
    """Entfernt ANSI-Sequenzen, um die sichtbare Textlänge zu bestimmen."""
    return re.sub(r"\033\[[0-9;]*m", "", text)
