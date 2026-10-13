"""Tests der Domain-Schicht: Validierung, Komposition, abgeleitete Attribute."""

import unittest
from dataclasses import FrozenInstanceError
from datetime import date

from dashboard.domain import (
    Fristziel, Kennzahlen, Modul, Modulstatus, Notenziel, Pruefungsart,
    Pruefungsleistung, Studiengang, Ziel, Zielstatus,
)
from tests.hilfen import beispiel_studiengang


class TestPruefungsleistung(unittest.TestCase):
    def test_validierung_der_note(self):
        for ungueltig in (0.7, 2.33, 2.5, 4.3, 6.0, -1.0):
            with self.subTest(note=ungueltig), self.assertRaises(ValueError):
                Pruefungsleistung(Pruefungsart.KLAUSUR, 1, note=ungueltig)
        with self.assertRaises(TypeError):
            Pruefungsleistung(Pruefungsart.KLAUSUR, 1, note="2,3")  # type: ignore[arg-type]
        self.assertEqual(Pruefungsleistung(Pruefungsart.KLAUSUR, 1, note=2).note, 2.0)

    def test_validierung_art_und_versuch(self):
        with self.assertRaises(TypeError):
            Pruefungsleistung("Klausur", 1)  # type: ignore[arg-type]
        for ungueltig in (0, -1, True, 1.5):
            with self.subTest(versuch=ungueltig), self.assertRaises(ValueError):
                Pruefungsleistung(Pruefungsart.KLAUSUR, ungueltig)  # type: ignore[arg-type]

    def test_abgeleitete_attribute(self):
        offen = Pruefungsleistung(Pruefungsart.KLAUSUR, 1)
        self.assertFalse(offen.bewertet)
        self.assertFalse(offen.bestanden)
        self.assertTrue(Pruefungsleistung(Pruefungsart.KLAUSUR, 1, note=4.0).bestanden)
        self.assertFalse(Pruefungsleistung(Pruefungsart.KLAUSUR, 1, note=5.0).bestanden)

    def test_unveraenderlich(self):
        p = Pruefungsleistung(Pruefungsart.KLAUSUR, 1)
        with self.assertRaises(FrozenInstanceError):
            p.note = 1.0  # type: ignore[misc]


class TestModulKomposition(unittest.TestCase):
    def test_versuche_werden_nur_vom_modul_erzeugt_und_nummeriert(self):
        m = Modul("IREN01", "Requirements Engineering", 5)
        m.ergebnis_eintragen(Pruefungsart.KLAUSUR, 5.0)
        zweiter = m.neuer_versuch(Pruefungsart.KLAUSUR)
        self.assertEqual(zweiter.versuch, 2)
        self.assertIs(m.offener_versuch, zweiter)
        self.assertEqual(m.status, Modulstatus.IN_BEARBEITUNG)

    def test_externe_referenzen_veraendern_das_modul_nicht(self):
        m = Modul("X01", "Test", 5)
        versuch = m.neuer_versuch(Pruefungsart.KLAUSUR)
        liste = m.pruefungsleistungen
        self.assertIsInstance(liste, tuple)
        with self.assertRaises(AttributeError):
            liste.append(Pruefungsleistung(Pruefungsart.KLAUSUR, 9))  # type: ignore[attr-defined]
        # Eine „bewertete Kopie“ außerhalb des Moduls ändert das Modul nicht.
        kopie = versuch.mit_bewertung(1.0)
        self.assertTrue(kopie.bestanden)
        self.assertFalse(m.bestanden)
        self.assertIsNone(m.pruefungsleistungen[0].note)

    def test_regeln_fuer_weitere_versuche(self):
        m = Modul("X01", "Test", 5)
        m.neuer_versuch(Pruefungsart.KLAUSUR)
        with self.assertRaises(ValueError):  # noch ein Versuch offen
            m.neuer_versuch(Pruefungsart.KLAUSUR)
        m.ergebnis_eintragen(Pruefungsart.KLAUSUR, 2.0)
        with self.assertRaises(ValueError):  # bereits bestanden
            m.neuer_versuch(Pruefungsart.KLAUSUR)
        with self.assertRaises(ValueError):  # anerkannt
            Modul("Y01", "Anerkannt", 5, anerkannt=True).neuer_versuch(Pruefungsart.KLAUSUR)

    def test_ergebnis_eintragen_ist_atomar(self):
        m = Modul("X01", "Test", 5)
        with self.assertRaises(ValueError):
            m.ergebnis_eintragen(Pruefungsart.KLAUSUR, 2.5)
        self.assertEqual(m.pruefungsleistungen, ())  # kein halb angelegter Versuch

    def test_status_und_note(self):
        sg = beispiel_studiengang()
        status = {m.kuerzel: m.status for m in sg.alle_module()}
        self.assertEqual(status["A01"], Modulstatus.BESTANDEN)
        self.assertEqual(status["C01"], Modulstatus.ANERKANNT)
        self.assertEqual(status["D01"], Modulstatus.NICHT_BESTANDEN)
        self.assertEqual(status["W01"], Modulstatus.GEPLANT)
        self.assertIsNone(sg.finde_modul("c01").note)  # anerkannt: keine Note

    def test_validierung_modul(self):
        for args in (("", "T", 5), ("K", " ", 5), ("K", "T", 0), ("K", "T", True)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                Modul(*args)


class TestStudiengangUndSemester(unittest.TestCase):
    def test_aggregation_ohne_duplikate(self):
        sg = beispiel_studiengang()
        self.assertEqual(len(sg.alle_module()), 5)
        self.assertIs(sg.semester[0].module[2], sg.semester[1].module[2])

    def test_semester_nur_einmal_und_modul_nur_einmal_je_semester(self):
        sg = beispiel_studiengang()
        with self.assertRaises(ValueError):
            sg.semester_hinzufuegen(1)
        with self.assertRaises(ValueError):
            sg.semester[0].modul_zuordnen(sg.finde_modul("A01"))

    def test_genau_ein_fristziel(self):
        with self.assertRaises(TypeError):
            Studiengang("X", 180, None)  # type: ignore[arg-type]
        sg = beispiel_studiengang()
        self.assertEqual(len(sg.ziele), 2)
        self.assertIsInstance(sg.ziele[0], Fristziel)


class TestZiele(unittest.TestCase):
    @staticmethod
    def kennzahlen(**werte) -> Kennzahlen:
        basis = dict(erreichte_ects=50, benoetigte_ects=180, verbleibende_ects=130,
                     verbleibende_monate=20.0, reales_tempo=2.0, benoetigte_ects_pro_monat=6.5,
                     prognose_abschluss=None, durchschnitt=2.4, benoetigter_restdurchschnitt=None)
        basis.update(werte)
        return Kennzahlen(**basis)

    def test_ziel_ist_abstrakt(self):
        with self.assertRaises(TypeError):
            Ziel("abstrakt")  # type: ignore[abstract]

    def test_fristziel(self):
        fz = Fristziel("F", date(2024, 3, 15), date(2028, 3, 15))
        self.assertEqual(fz.bewerte(self.kennzahlen()), Zielstatus.GEFAEHRDET)
        self.assertEqual(fz.bewerte(self.kennzahlen(reales_tempo=7.0)), Zielstatus.IM_PLAN)
        self.assertEqual(fz.bewerte(self.kennzahlen(verbleibende_ects=0)), Zielstatus.ERREICHT)
        self.assertEqual(fz.bewerte(self.kennzahlen(benoetigte_ects_pro_monat=None)), Zielstatus.GEFAEHRDET)
        with self.assertRaises(ValueError):
            Fristziel("F", date(2028, 1, 1), date(2024, 1, 1))

    def test_notenziel(self):
        nz = Notenziel("N", 2.5)
        self.assertEqual(nz.bewerte(self.kennzahlen()), Zielstatus.IM_PLAN)
        self.assertEqual(nz.bewerte(self.kennzahlen(durchschnitt=2.85)), Zielstatus.GEFAEHRDET)
        self.assertEqual(nz.bewerte(self.kennzahlen(durchschnitt=None)), Zielstatus.IM_PLAN)
        self.assertEqual(nz.bewerte(self.kennzahlen(verbleibende_ects=0)), Zielstatus.ERREICHT)
        with self.assertRaises(ValueError):
            Notenziel("N", 5.0)


if __name__ == "__main__":
    unittest.main()
