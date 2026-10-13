"""Domain-Schicht: fachliche Klassen ohne Abhängigkeiten zu anderen Schichten."""

from dashboard.domain.aufzaehlungen import Modulstatus, Pruefungsart, Zielstatus
from dashboard.domain.kennzahlen import Kennzahlen
from dashboard.domain.modul import Modul
from dashboard.domain.pruefungsleistung import BESTEHENSGRENZE, ZULAESSIGE_NOTEN, Pruefungsleistung
from dashboard.domain.semester import Semester
from dashboard.domain.studiengang import Studiengang
from dashboard.domain.ziele import Fristziel, Notenziel, Ziel

__all__ = [
    "BESTEHENSGRENZE",
    "ZULAESSIGE_NOTEN",
    "Fristziel",
    "Kennzahlen",
    "Modul",
    "Modulstatus",
    "Notenziel",
    "Pruefungsart",
    "Pruefungsleistung",
    "Semester",
    "Studiengang",
    "Ziel",
    "Zielstatus",
]
