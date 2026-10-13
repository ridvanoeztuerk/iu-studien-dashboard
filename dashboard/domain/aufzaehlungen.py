"""Aufzählungstypen (Enumerations) der Domain-Schicht.

Feste Wertebereiche werden als ``Enum`` statt als frei belegbarer ``str``
modelliert. Ein Tippfehler wie ``"Klausr"`` fällt dadurch sofort beim
Erzeugen bzw. Einlesen auf und nicht erst bei der Auswertung.
"""

from enum import Enum


class Pruefungsart(Enum):
    """Prüfungsformen laut Studienablaufplan B.Sc. Cyber Security (FS-BACSD-01).

    Der Wert ist die Bezeichnung, wie sie im Dashboard angezeigt wird.
    """

    KLAUSUR = "Klausur"
    ADVANCED_WORKBOOK = "Advanced Workbook"
    PORTFOLIO = "Portfolio"
    PROJEKTBERICHT = "Projektbericht"
    PROJEKTPRAESENTATION = "Projektpräsentation"
    FALLSTUDIE = "Fallstudie"
    HAUSARBEIT = "Hausarbeit"
    SEMINARARBEIT = "Seminararbeit"
    PRAXISREFLEXION = "Praxisreflexion"
    BACHELORARBEIT = "Bachelorarbeit"
    KOLLOQUIUM = "Kolloquium"


class Zielstatus(Enum):
    """Ergebnis der Bewertung eines Ziels (Darstellung als Ampel)."""

    ERREICHT = "erreicht"
    IM_PLAN = "im Plan"
    GEFAEHRDET = "gefährdet"


class Modulstatus(Enum):
    """Aus den Prüfungsleistungen abgeleiteter Bearbeitungsstand eines Moduls."""

    ANERKANNT = "anerkannt"
    BESTANDEN = "bestanden"
    NICHT_BESTANDEN = "nicht bestanden"
    IN_BEARBEITUNG = "in Bearbeitung"
    GEPLANT = "geplant"
