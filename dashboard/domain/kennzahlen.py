"""Wertobjekt Kennzahlen."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Kennzahlen:
    """Momentaufnahme aller Kennzahlen zu einem Stichtag.

    Das Wertobjekt gehört zur Domain-Schicht, weil es fachliche Größen
    beschreibt und von den Zielen (:meth:`Ziel.bewerte`) verwendet wird. Die
    Werte werden von den Service-Klassen berechnet und hier nur gebündelt.
    Da es genau ein Fristziel gibt, existiert je Kennzahl genau ein Wert.

    Attributes:
        erreichte_ects: ECTS aus bestandenen und anerkannten Modulen.
        benoetigte_ects: für den Abschluss erforderliche ECTS.
        verbleibende_ects: noch fehlende ECTS.
        verbleibende_monate: Monate vom Stichtag bis zur Frist.
        reales_tempo: bisher erreichte ECTS pro Monat seit Studienbeginn.
        benoetigte_ects_pro_monat: nötiges Tempo bis zur Frist;
            ``None``, wenn die Frist bereits abgelaufen ist.
        prognose_abschluss: voraussichtliches Abschlussdatum bei
            gleichbleibendem Tempo; ``None`` ohne bisherigen Fortschritt.
        durchschnitt: ECTS-gewichteter Notendurchschnitt; ``None`` ohne Noten.
        benoetigter_restdurchschnitt: Durchschnitt, der in den verbleibenden
            ECTS nötig ist, um den Zielwert zu erreichen; ``None``, wenn nicht
            berechenbar (kein Notenziel oder keine verbleibenden ECTS).
    """

    erreichte_ects: int
    benoetigte_ects: int
    verbleibende_ects: int
    verbleibende_monate: float
    reales_tempo: float
    benoetigte_ects_pro_monat: float | None
    prognose_abschluss: date | None
    durchschnitt: float | None
    benoetigter_restdurchschnitt: float | None
