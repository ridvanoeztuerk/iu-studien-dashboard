"""Berechnungen zum Notendurchschnitt (Ziel 2)."""

import math

from dashboard.domain import Modul, Studiengang


def auf_zwei_stellen_abschneiden(wert: float) -> float:
    """Schneidet nach der zweiten Nachkommastelle ab (2,856 -> 2,85).

    Abschneiden statt Runden, damit der angezeigte Durchschnitt nie besser
    erscheint als der tatsächliche Wert. Die kleine Toleranz gleicht
    Gleitkomma-Darstellungsfehler aus (z. B. 2,3 als 2,2999999...).
    """
    return math.floor(wert * 100 + 1e-9) / 100


class NotenService:
    """Zustandslose Berechnungen zum ECTS-gewichteten Notendurchschnitt."""

    @staticmethod
    def _benotete_module(studiengang: Studiengang) -> list[Modul]:
        """Bestandene Module mit Note. Anerkannte Module haben keine Note und
        zählen nicht zum Durchschnitt; nicht bestandene Versuche ebenfalls nicht.
        """
        return [m for m in studiengang.alle_module() if m.bestanden and m.note is not None]

    def benotete_ects(self, studiengang: Studiengang) -> int:
        """Summe der ECTS, die in den Durchschnitt eingehen."""
        return sum(m.ects for m in self._benotete_module(studiengang))

    def gewichteter_durchschnitt(self, studiengang: Studiengang) -> float | None:
        """ECTS-gewichteter Durchschnitt über alle bestandenen, benoteten Module.

        Returns:
            Durchschnitt auf zwei Nachkommastellen abgeschnitten; ``None``,
            solange noch keine Note vorliegt.
        """
        module = self._benotete_module(studiengang)
        gewichte = sum(m.ects for m in module)
        if gewichte == 0:
            return None
        summe = sum(m.ects * m.note for m in module)  # type: ignore[operator]
        return auf_zwei_stellen_abschneiden(summe / gewichte)

    def benoetigter_restdurchschnitt(
        self, studiengang: Studiengang, zielwert: float, verbleibende_ects: int
    ) -> float | None:
        """Durchschnitt, der in den verbleibenden ECTS nötig ist, um den Zielwert zu erreichen.

        Annahme: Alle verbleibenden ECTS werden benotet. Ein Ergebnis unter 1,0
        bedeutet, dass das Ziel rechnerisch nicht mehr erreichbar ist; ein
        Ergebnis über 4,0, dass jede bestandene Note genügt.

        Returns:
            benötigter Durchschnitt (ungerundet); ``None`` ohne verbleibende ECTS.
        """
        if verbleibende_ects <= 0:
            return None
        module = self._benotete_module(studiengang)
        bisher_ects = sum(m.ects for m in module)
        bisher_summe = sum(m.ects * m.note for m in module)  # type: ignore[operator]
        return (zielwert * (bisher_ects + verbleibende_ects) - bisher_summe) / verbleibende_ects
