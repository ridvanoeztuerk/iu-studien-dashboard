"""Tests der Service-Schicht: ECTS, Lerntempo, Notendurchschnitt."""

import unittest
from datetime import date

from dashboard.service import FortschrittService, NotenService
from dashboard.service.fortschritt_service import monate_zwischen
from dashboard.service.noten_service import auf_zwei_stellen_abschneiden
from tests.hilfen import beispiel_studiengang


class TestFortschrittService(unittest.TestCase):
    def setUp(self):
        self.sg = beispiel_studiengang()
        self.fz = self.sg.fristziel
        self.service = FortschrittService()

    def test_ects(self):
        # A01 (5) + B01 (10) + C01 anerkannt (5); D01 nicht bestanden, W01 geplant
        self.assertEqual(self.service.erreichte_ects(self.sg), 20)
        self.assertEqual(self.service.verbleibende_ects(self.sg), 10)

    def test_monate_und_tempo(self):
        stichtag = date(2025, 1, 1)
        self.assertAlmostEqual(monate_zwischen(date(2024, 1, 1), stichtag), 12.0, delta=0.05)
        self.assertAlmostEqual(self.service.reales_tempo(self.sg, self.fz, stichtag), 20 / 12, places=1)
        self.assertAlmostEqual(self.service.benoetigte_ects_pro_monat(self.sg, self.fz, stichtag), 10 / 12, places=1)

    def test_frist_abgelaufen(self):
        nach_frist = date(2026, 6, 1)
        self.assertEqual(self.service.verbleibende_monate(self.fz, nach_frist), 0.0)
        self.assertIsNone(self.service.benoetigte_ects_pro_monat(self.sg, self.fz, nach_frist))

    def test_prognose(self):
        stichtag = date(2025, 1, 1)
        prognose = self.service.prognostiziertes_abschlussdatum(self.sg, self.fz, stichtag)
        # 10 offene ECTS bei ca. 1,67 ECTS/Monat -> ca. 6 Monate
        self.assertTrue(date(2025, 6, 25) <= prognose <= date(2025, 7, 5), prognose)
        self.assertIsNone(self.service.prognostiziertes_abschlussdatum(self.sg, self.fz, date(2024, 1, 1)))


class TestNotenService(unittest.TestCase):
    def setUp(self):
        self.sg = beispiel_studiengang()
        self.service = NotenService()

    def test_gewichteter_durchschnitt(self):
        # (5 * 1,3 + 10 * 3,0) / 15 = 2,4333 -> abgeschnitten 2,43
        # anerkannt (ohne Note) und nicht bestanden zählen nicht.
        self.assertEqual(self.service.gewichteter_durchschnitt(self.sg), 2.43)
        self.assertEqual(self.service.benotete_ects(self.sg), 15)

    def test_abschneiden_statt_runden(self):
        self.assertEqual(auf_zwei_stellen_abschneiden(2.8555), 2.85)
        self.assertEqual(auf_zwei_stellen_abschneiden(2.3), 2.3)  # Gleitkomma-Toleranz

    def test_benoetigter_restdurchschnitt(self):
        # Ziel 2,5 über 15 + 10 ECTS: (2,5 * 25 - 36,5) / 10 = 2,6
        self.assertAlmostEqual(self.service.benoetigter_restdurchschnitt(self.sg, 2.5, 10), 2.6)
        self.assertIsNone(self.service.benoetigter_restdurchschnitt(self.sg, 2.5, 0))


if __name__ == "__main__":
    unittest.main()
