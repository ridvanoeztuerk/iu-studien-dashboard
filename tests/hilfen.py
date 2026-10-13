"""Gemeinsame Testdaten."""

from datetime import date

from dashboard.domain import Fristziel, Modul, Notenziel, Pruefungsart, Studiengang


def beispiel_studiengang() -> Studiengang:
    """Kleiner Studiengang mit 30 ECTS: zwei benotete, ein anerkanntes,
    ein nicht bestandenes und ein in mehreren Semestern zugeordnetes Modul."""
    sg = Studiengang(
        "Test-Studiengang", 30,
        Fristziel("Abschluss", date(2024, 1, 1), date(2026, 1, 1)),
        Notenziel("Schnitt", 2.5),
    )
    a = Modul("A01", "Modul A", 5)
    a.ergebnis_eintragen(Pruefungsart.KLAUSUR, 1.3)
    b = Modul("B01", "Modul B", 10)
    b.ergebnis_eintragen(Pruefungsart.FALLSTUDIE, 3.0)
    c = Modul("C01", "Modul C", 5, anerkannt=True)
    d = Modul("D01", "Modul D", 5)
    d.ergebnis_eintragen(Pruefungsart.KLAUSUR, 5.0)
    wahl = Modul("W01", "Wahlmodul", 5)

    s1 = sg.semester_hinzufuegen(1)
    for m in (a, b, wahl):
        s1.modul_zuordnen(m)
    s2 = sg.semester_hinzufuegen(2)
    for m in (c, d, wahl):  # Wahlmodul in zwei Semestern (Aggregation)
        s2.modul_zuordnen(m)
    return sg
