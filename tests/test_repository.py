"""Tests der Repository-Schicht: vollständiger JSON-Roundtrip und Fehlerfälle."""

import json
import tempfile
import unittest
from pathlib import Path

from dashboard.app import STANDARD_DATEI
from dashboard.repository import DatenFehler, JsonStudiengangRepository
from tests.hilfen import beispiel_studiengang


class TestJsonRepository(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.pfad = Path(self._tmp.name) / "studium.json"
        self.repo = JsonStudiengangRepository(self.pfad)

    def tearDown(self):
        self._tmp.cleanup()

    def test_roundtrip_erhaelt_objektstruktur_und_beziehungen(self):
        original = beispiel_studiengang()
        self.repo.speichere(original)
        geladen = self.repo.lade()

        self.assertEqual(len(geladen.semester), 2)
        self.assertEqual(len(geladen.alle_module()), 5)
        # Das Wahlmodul ist nach dem Laden weiterhin EIN Objekt in zwei Semestern.
        self.assertIs(geladen.semester[0].module[2], geladen.semester[1].module[2])
        # Werte, Versuche und Ziele bleiben erhalten.
        self.assertEqual(JsonStudiengangRepository._als_dict(geladen),
                         JsonStudiengangRepository._als_dict(original))
        self.assertEqual(geladen.notenziel.zielwert, 2.5)
        self.assertTrue(geladen.finde_modul("C01").anerkannt)

    def test_kein_tmp_rest_nach_speichern(self):
        self.repo.speichere(beispiel_studiengang())
        self.assertEqual([p.name for p in self.pfad.parent.iterdir()], ["studium.json"])

    def _schreibe(self, daten):
        self.pfad.write_text(json.dumps(daten), encoding="utf-8")

    def test_fehlerhafte_daten_werden_erkannt(self):
        self.repo.speichere(beispiel_studiengang())
        gut = json.loads(self.pfad.read_text(encoding="utf-8"))
        faelle = {
            "ungueltige Note": lambda d: d["module"][0]["pruefungsleistungen"][0].update(note=2.5),
            "unbekannte Pruefungsart": lambda d: d["module"][0]["pruefungsleistungen"][0].update(art="TEST"),
            "unbekanntes Modul im Semester": lambda d: d["semester"][0]["module"].append("XYZ"),
            "Versuch nach Bestehen": lambda d: d["module"][0]["pruefungsleistungen"].append(
                {"art": "KLAUSUR", "versuch": 2, "datum": None, "note": 1.0}),
            "falsche Versionsnummer": lambda d: d.update(format_version=99),
        }
        for name, aendern in faelle.items():
            with self.subTest(name):
                daten = json.loads(json.dumps(gut))
                aendern(daten)
                self._schreibe(daten)
                with self.assertRaises(DatenFehler):
                    self.repo.lade()

    def test_fehlende_datei_und_kaputtes_json(self):
        with self.assertRaises(DatenFehler):
            self.repo.lade()
        self.pfad.write_text("{kein json", encoding="utf-8")
        with self.assertRaises(DatenFehler):
            self.repo.lade()

    def test_mitgelieferte_daten_sind_gueltig(self):
        sg = JsonStudiengangRepository(STANDARD_DATEI).lade()
        self.assertEqual(sum(m.ects for m in sg.alle_module()), sg.benoetigte_ects)


if __name__ == "__main__":
    unittest.main()
