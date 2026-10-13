"""Tests von Controller, View und App (Zusammenspiel der Schichten)."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest.mock import patch

from dashboard.app import STANDARD_DATEI, DashboardApp
from dashboard.controller import DashboardController
from dashboard.domain import Pruefungsart, Zielstatus
from dashboard.repository import JsonStudiengangRepository
from dashboard.service import FortschrittService, NotenService
from dashboard.view import DashboardView
from tests.hilfen import beispiel_studiengang

STICHTAG = date(2025, 1, 1)


class TestController(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = JsonStudiengangRepository(Path(self._tmp.name) / "s.json")
        self.repo.speichere(beispiel_studiengang())
        self.controller = DashboardController(self.repo, FortschrittService(), NotenService())

    def tearDown(self):
        self._tmp.cleanup()

    def test_dashboard_daten(self):
        daten = self.controller.lade_dashboard_daten(STICHTAG)
        self.assertEqual(daten.kennzahlen.erreichte_ects, 20)
        self.assertEqual(daten.fristziel.status, Zielstatus.IM_PLAN)
        self.assertEqual(daten.notenziel.status, Zielstatus.IM_PLAN)
        self.assertEqual(len(daten.module), 5)  # Wahlmodul nur einmal
        self.assertTrue(any("D01" in h for h in daten.naechste_schritte))

    def test_ergebnis_erfassen_speichert(self):
        meldung = self.controller.pruefungsergebnis_erfassen("D01", Pruefungsart.KLAUSUR, 2.0, STICHTAG)
        self.assertIn("Versuch 2", meldung)
        neu_geladen = self.repo.lade()
        self.assertTrue(neu_geladen.finde_modul("D01").bestanden)

    def test_ungueltige_erfassung_speichert_nichts(self):
        vorher = self.repo.dateipfad.read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            self.controller.pruefungsergebnis_erfassen("A01", Pruefungsart.KLAUSUR, 1.0, STICHTAG)
        with self.assertRaises(ValueError):
            self.controller.pruefungsergebnis_erfassen("GIBTSNICHT", Pruefungsart.KLAUSUR, 1.0, STICHTAG)
        self.assertEqual(self.repo.dateipfad.read_text(encoding="utf-8"), vorher)


class TestViewUndApp(unittest.TestCase):
    def test_view_ausgabe_ohne_farbe(self):
        controller = DashboardController(
            JsonStudiengangRepository(STANDARD_DATEI), FortschrittService(), NotenService())
        zeilen: list[str] = []
        DashboardView(farbe=False, ausgabe=zeilen.append).zeige(controller.lade_dashboard_daten(STICHTAG))
        text = "\n".join(zeilen)
        for erwartet in ("ZIEL 1", "ZIEL 2", "MEINE MODULE", "NÄCHSTE SCHRITTE", "IREN01"):
            self.assertIn(erwartet, text)
        self.assertNotIn("\033[", text)

    def test_interaktive_erfassung_ueber_menue(self):
        with tempfile.TemporaryDirectory() as tmp:
            kopie = Path(tmp) / "studium.json"
            shutil.copy(STANDARD_DATEI, kopie)
            eingaben = iter(["2", "IREN01", "", "2,3", "20.11.2026", "0"])
            app = DashboardApp(["--datei", str(kopie), "--ohne-farbe", "--stichtag", "2026-12-01"])
            ausgabe = io.StringIO()
            with patch("builtins.input", lambda _prompt="": next(eingaben)), redirect_stdout(ausgabe):
                self.assertEqual(app.start(), 0)
            self.assertIn("IREN01, Versuch 2: Note 2,3 (bestanden) gespeichert", ausgabe.getvalue())
            iren = JsonStudiengangRepository(kopie).lade().finde_modul("IREN01")
            self.assertEqual(iren.note, 2.3)
            self.assertEqual(iren.pruefungsleistungen[1].datum, date(2026, 11, 20))

    def test_fehlende_datei_liefert_exitcode_1(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(DashboardApp(["--datei", "gibt/es/nicht.json", "--nur-anzeigen"]).start(), 1)


if __name__ == "__main__":
    unittest.main()
