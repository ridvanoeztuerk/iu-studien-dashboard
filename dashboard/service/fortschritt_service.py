"""Berechnungen zu ECTS-Fortschritt und Lerntempo (Ziel 1)."""

from datetime import date, timedelta

from dashboard.domain import Fristziel, Studiengang

#: Durchschnittliche Tage pro Monat (365,25 / 12), damit Monate taggenau
#: und unabhängig von unterschiedlichen Monatslängen berechnet werden.
TAGE_PRO_MONAT = 30.4375


def monate_zwischen(von: date, bis: date) -> float:
    """Anzahl Monate zwischen zwei Daten (negativ, wenn ``bis`` vor ``von`` liegt)."""
    return (bis - von).days / TAGE_PRO_MONAT


class FortschrittService:
    """Zustandslose Berechnungen über alle Module eines Studiengangs.

    Die Berechnungen betreffen mehrere Objekte und liegen daher nicht in
    einer einzelnen Domain-Klasse.
    """

    def erreichte_ects(self, studiengang: Studiengang) -> int:
        """Summe der ECTS aller bestandenen oder anerkannten Module."""
        return sum(m.ects for m in studiengang.alle_module() if m.bestanden)

    def verbleibende_ects(self, studiengang: Studiengang) -> int:
        """Noch fehlende ECTS bis zum Abschluss (nie negativ)."""
        return max(0, studiengang.benoetigte_ects - self.erreichte_ects(studiengang))

    def verbleibende_monate(self, fristziel: Fristziel, stichtag: date) -> float:
        """Monate vom Stichtag bis zur Frist (0, wenn die Frist abgelaufen ist)."""
        return max(0.0, monate_zwischen(stichtag, fristziel.zieldatum))

    def reales_tempo(self, studiengang: Studiengang, fristziel: Fristziel, stichtag: date) -> float:
        """Bisher erreichte ECTS pro Monat seit Studienbeginn."""
        vergangen = monate_zwischen(fristziel.startdatum, stichtag)
        if vergangen <= 0:
            return 0.0
        return self.erreichte_ects(studiengang) / vergangen

    def benoetigte_ects_pro_monat(
        self, studiengang: Studiengang, fristziel: Fristziel, stichtag: date
    ) -> float | None:
        """Nötiges Tempo, um die Frist einzuhalten.

        Returns:
            0.0, wenn keine ECTS mehr fehlen; ``None``, wenn noch ECTS fehlen,
            die Frist aber bereits abgelaufen ist.
        """
        rest = self.verbleibende_ects(studiengang)
        if rest == 0:
            return 0.0
        monate = self.verbleibende_monate(fristziel, stichtag)
        if monate <= 0:
            return None
        return rest / monate

    def prognostiziertes_abschlussdatum(
        self, studiengang: Studiengang, fristziel: Fristziel, stichtag: date
    ) -> date | None:
        """Voraussichtlicher Abschluss, wenn das bisherige Tempo beibehalten wird.

        Returns:
            Stichtag, wenn keine ECTS mehr fehlen; ``None`` ohne bisherigen
            Fortschritt (Tempo 0).
        """
        rest = self.verbleibende_ects(studiengang)
        if rest == 0:
            return stichtag
        tempo = self.reales_tempo(studiengang, fristziel, stichtag)
        if tempo <= 0:
            return None
        return stichtag + timedelta(days=round(rest / tempo * TAGE_PRO_MONAT))
