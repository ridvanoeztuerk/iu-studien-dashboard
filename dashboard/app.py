"""Startpunkt der Anwendung (Composition Root)."""

import argparse
import sys
from datetime import date
from pathlib import Path

from dashboard.controller import DashboardController
from dashboard.repository import DatenFehler, JsonStudiengangRepository
from dashboard.service import FortschrittService, NotenService
from dashboard.view import DashboardView

#: Standard-Datendatei im Projektverzeichnis.
STANDARD_DATEI = Path(__file__).resolve().parent.parent / "daten" / "studium.json"


class DashboardApp:
    """Erzeugt alle Objekte, verbindet sie und steuert die Menüschleife.

    Nur hier werden konkrete Klassen ausgewählt (z. B. das JSON-Repository).
    Alle anderen Klassen erhalten ihre Abhängigkeiten über den Konstruktor
    (Dependency Injection).

    Args:
        argumente: Kommandozeilenargumente; ``None`` verwendet ``sys.argv``.
    """

    def __init__(self, argumente: list[str] | None = None) -> None:
        self._argumente = self._parser().parse_args(argumente)

    @staticmethod
    def _parser() -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="python main.py",
            description="Studien-Dashboard: Fortschritt, Lerntempo und Notendurchschnitt im Überblick.",
        )
        parser.add_argument("--datei", type=Path, default=STANDARD_DATEI,
                            help="Pfad zur JSON-Datendatei (Standard: daten/studium.json)")
        parser.add_argument("--stichtag", type=date.fromisoformat, default=None,
                            help="Stichtag im Format JJJJ-MM-TT (Standard: heute)")
        parser.add_argument("--nur-anzeigen", action="store_true",
                            help="Dashboard ausgeben und ohne Menü beenden")
        parser.add_argument("--ohne-farbe", action="store_true",
                            help="Ausgabe ohne Farben (z. B. für ältere Konsolen)")
        return parser

    def start(self) -> int:
        """Führt das Programm aus.

        Returns:
            Exit-Code (0 = Erfolg, 1 = Fehler beim Laden der Daten).
        """
        # Nicht darstellbare Zeichen ersetzen statt abzustürzen, z. B. bei
        # Umleitung der Ausgabe in eine Datei mit Windows-Codepage.
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(errors="replace")

        args = self._argumente
        view = DashboardView(farbe=False if args.ohne_farbe else None)
        controller = DashboardController(
            JsonStudiengangRepository(args.datei), FortschrittService(), NotenService()
        )
        stichtag = args.stichtag or date.today()

        try:
            view.zeige(controller.lade_dashboard_daten(stichtag))
        except DatenFehler as fehler:
            view.zeige_fehler(str(fehler))
            return 1
        if args.nur_anzeigen:
            return 0

        try:
            while True:
                wahl = view.frage_menue()
                if wahl == "0":
                    return 0
                if wahl == "1":
                    view.zeige(controller.lade_dashboard_daten(stichtag))
                elif wahl == "2":
                    self._ergebnis_erfassen(view, controller, stichtag)
                else:
                    view.zeige_fehler("Bitte 1, 2 oder 0 eingeben.")
        except (KeyboardInterrupt, EOFError):
            # Strg+C bzw. Ende der Eingabe beendet das Programm ohne Fehlermeldung.
            return 0

    @staticmethod
    def _ergebnis_erfassen(view: DashboardView, controller: DashboardController, stichtag: date) -> None:
        eingabe = view.frage_pruefungsergebnis(controller.module_mit_offenem_ergebnis(), stichtag)
        if eingabe is None:
            return
        try:
            meldung = controller.pruefungsergebnis_erfassen(
                eingabe.kuerzel, eingabe.art, eingabe.note, eingabe.datum
            )
        except ValueError as fehler:
            view.zeige_fehler(str(fehler))
            return
        view.zeige_meldung(meldung)
        view.zeige(controller.lade_dashboard_daten(stichtag))
