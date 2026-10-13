"""Abstrakte Klasse Ziel und ihre Spezialisierungen Fristziel und Notenziel."""

from abc import ABC, abstractmethod
from datetime import date

from dashboard.domain.aufzaehlungen import Zielstatus
from dashboard.domain.kennzahlen import Kennzahlen


class Ziel(ABC):
    """Gemeinsame Oberklasse aller Studienziele.

    Python kennt kein Schlüsselwort für abstrakte Klassen. Die Abstraktion
    entsteht über ``abc.ABC`` und ``@abstractmethod``: Ein ``Ziel`` selbst kann
    nicht instanziiert werden, jede Unterklasse muss :meth:`bewerte`
    implementieren (Polymorphie).

    Args:
        bezeichnung: Anzeigename des Ziels.
    """

    def __init__(self, bezeichnung: str) -> None:
        if not isinstance(bezeichnung, str) or not bezeichnung.strip():
            raise ValueError("bezeichnung darf nicht leer sein")
        self._bezeichnung = bezeichnung.strip()

    @property
    def bezeichnung(self) -> str:
        return self._bezeichnung

    @abstractmethod
    def bewerte(self, kennzahlen: Kennzahlen) -> Zielstatus:
        """Leitet den Zielstatus aus Ist- und Zielwerten ab."""


class Fristziel(Ziel):
    """Ziel 1: Abschluss aller benötigten ECTS bis zu einem Zieldatum.

    Args:
        bezeichnung: Anzeigename.
        startdatum: Studienbeginn.
        zieldatum: späteste Frist für den Abschluss (nach dem Startdatum).
    """

    def __init__(self, bezeichnung: str, startdatum: date, zieldatum: date) -> None:
        super().__init__(bezeichnung)
        if not isinstance(startdatum, date) or not isinstance(zieldatum, date):
            raise TypeError("startdatum und zieldatum müssen vom Typ datetime.date sein")
        if zieldatum <= startdatum:
            raise ValueError("zieldatum muss nach dem startdatum liegen")
        self._startdatum = startdatum
        self._zieldatum = zieldatum

    @property
    def startdatum(self) -> date:
        return self._startdatum

    @property
    def zieldatum(self) -> date:
        return self._zieldatum

    def bewerte(self, kennzahlen: Kennzahlen) -> Zielstatus:
        """ERREICHT ohne verbleibende ECTS; IM_PLAN, wenn das bisherige Tempo
        mindestens dem benötigten entspricht; sonst GEFAEHRDET.
        """
        if kennzahlen.verbleibende_ects == 0:
            return Zielstatus.ERREICHT
        benoetigt = kennzahlen.benoetigte_ects_pro_monat
        if benoetigt is not None and kennzahlen.reales_tempo >= benoetigt:
            return Zielstatus.IM_PLAN
        return Zielstatus.GEFAEHRDET


class Notenziel(Ziel):
    """Ziel 2: gewichteter Notendurchschnitt höchstens ``zielwert``.

    Args:
        bezeichnung: Anzeigename.
        zielwert: angestrebter Höchstwert des Durchschnitts (1,0 bis 4,0).
    """

    def __init__(self, bezeichnung: str, zielwert: float) -> None:
        super().__init__(bezeichnung)
        if isinstance(zielwert, bool) or not isinstance(zielwert, (int, float)):
            raise TypeError("zielwert muss eine Zahl sein")
        if not 1.0 <= zielwert <= 4.0:
            raise ValueError("zielwert muss zwischen 1,0 und 4,0 liegen")
        self._zielwert = float(zielwert)

    @property
    def zielwert(self) -> float:
        return self._zielwert

    def bewerte(self, kennzahlen: Kennzahlen) -> Zielstatus:
        """IM_PLAN, solange der Durchschnitt den Zielwert einhält (oder noch
        keine Note vorliegt); ERREICHT erst mit Studienabschluss, weil sich der
        Durchschnitt bis dahin noch ändern kann; sonst GEFAEHRDET.
        """
        schnitt = kennzahlen.durchschnitt
        if schnitt is None:
            return Zielstatus.IM_PLAN
        if schnitt <= self._zielwert:
            return Zielstatus.ERREICHT if kennzahlen.verbleibende_ects == 0 else Zielstatus.IM_PLAN
        return Zielstatus.GEFAEHRDET
