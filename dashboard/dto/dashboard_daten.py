"""Datentransferobjekte für die Dashboard-Anzeige.

Die View erhält ausschließlich diese unveränderlichen, bereits aufbereiteten
Daten und keine Entity-Objekte (Studiengang, Modul ...). Sie kann deshalb
weder Fachlogik ausführen noch den Zustand der Domain verändern. Einzige
Ausnahme ist das ebenfalls unveränderliche Wertobjekt ``Kennzahlen``.
"""

from dataclasses import dataclass
from datetime import date

from dashboard.domain import Kennzahlen, Modulstatus, Zielstatus


@dataclass(frozen=True)
class ZielDTO:
    """Ein Ziel mit seinem abgeleiteten Status."""

    bezeichnung: str
    status: Zielstatus


@dataclass(frozen=True)
class ModulZeileDTO:
    """Eine Zeile der Modultabelle."""

    semester: int
    kuerzel: str
    titel: str
    ects: int
    status: Modulstatus
    note: float | None
    versuche: int
    pruefungsart: str | None


@dataclass(frozen=True)
class DashboardDatenDTO:
    """Alle Daten, die die View für eine vollständige Anzeige benötigt."""

    studiengang: str
    stichtag: date
    startdatum: date
    zieldatum: date
    zielwert_note: float | None
    kennzahlen: Kennzahlen
    fristziel: ZielDTO
    notenziel: ZielDTO | None
    module: tuple[ModulZeileDTO, ...]
    naechste_schritte: tuple[str, ...]
