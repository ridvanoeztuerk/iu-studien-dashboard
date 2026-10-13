"""Entity-Klasse Prüfungsleistung."""

from dataclasses import dataclass, replace
from datetime import date

from dashboard.domain.aufzaehlungen import Pruefungsart

#: Zulässige Noten nach deutscher Notenskala; 5,0 = nicht bestanden.
ZULAESSIGE_NOTEN: tuple[float, ...] = (1.0, 1.3, 1.7, 2.0, 2.3, 2.7, 3.0, 3.3, 3.7, 4.0, 5.0)

#: Schlechteste Note, mit der eine Prüfung noch bestanden ist.
BESTEHENSGRENZE: float = 4.0


@dataclass(frozen=True)
class Pruefungsleistung:
    """Ein einzelner Prüfungsversuch innerhalb eines Moduls.

    Die Klasse ist unveränderlich (``frozen=True``). Ein Modul kann seine
    Prüfungsleistungen daher nach außen herausgeben, ohne dass Aufrufer sie
    verändern können. Eine Bewertung erzeugt ein neues Objekt
    (:meth:`mit_bewertung`), das nur das besitzende Modul übernehmen kann.

    Typannotationen wie ``float | None`` dokumentieren lediglich die
    zulässigen Typen; Python prüft sie zur Laufzeit nicht. Die fachlichen
    Regeln werden deshalb in :meth:`__post_init__` explizit validiert. Das gilt
    für jede Erzeugung, also auch beim Einlesen gespeicherter Daten.

    Attributes:
        art: Prüfungsform, z. B. Klausur oder Portfolio.
        versuch: laufende Nummer des Versuchs (ab 1).
        datum: Prüfungsdatum; optional, z. B. wenn noch kein Termin feststeht.
        note: Note; ``None`` bedeutet „noch nicht bewertet“.
    """

    art: Pruefungsart
    versuch: int
    datum: date | None = None
    note: float | None = None

    def __post_init__(self) -> None:
        """Prüft die fachlichen Regeln, da Typannotationen nichts erzwingen."""
        if not isinstance(self.art, Pruefungsart):
            raise TypeError(f"art muss vom Typ Pruefungsart sein, nicht {type(self.art).__name__}")
        # bool ist in Python eine Unterklasse von int und wird daher explizit ausgeschlossen.
        if isinstance(self.versuch, bool) or not isinstance(self.versuch, int) or self.versuch < 1:
            raise ValueError(f"versuch muss eine ganze Zahl ab 1 sein, nicht {self.versuch!r}")
        if self.datum is not None and not isinstance(self.datum, date):
            raise TypeError("datum muss vom Typ datetime.date oder None sein")
        if self.note is not None:
            if isinstance(self.note, bool) or not isinstance(self.note, (int, float)):
                raise TypeError("note muss eine Zahl oder None sein")
            # Vergleich mit Toleranz statt ==, da Gleitkommazahlen nicht exakt sind.
            treffer = next((n for n in ZULAESSIGE_NOTEN if abs(float(self.note) - n) < 1e-9), None)
            if treffer is None:
                erlaubt = ", ".join(f"{n:.1f}".replace(".", ",") for n in ZULAESSIGE_NOTEN)
                raise ValueError(f"Unzulässige Note {str(self.note).replace('.', ',')}; erlaubt sind {erlaubt}")
            # Note normiert als float ablegen (z. B. 2 -> 2.0). object.__setattr__
            # ist nötig, weil die Dataclass eingefroren ist.
            object.__setattr__(self, "note", treffer)

    @property
    def bewertet(self) -> bool:
        """Abgeleitet: ``True``, sobald eine Note vorliegt."""
        return self.note is not None

    @property
    def bestanden(self) -> bool:
        """Abgeleitet: ``True``, wenn bewertet und Note höchstens 4,0."""
        return self.note is not None and self.note <= BESTEHENSGRENZE

    def mit_bewertung(self, note: float, datum: date | None = None) -> "Pruefungsleistung":
        """Liefert eine bewertete Kopie dieses Versuchs.

        ``dataclasses.replace`` ruft den Konstruktor auf, sodass die Note
        dabei ebenfalls validiert wird.

        Args:
            note: zu vergebende Note.
            datum: Prüfungsdatum; ohne Angabe bleibt das bisherige Datum erhalten.

        Raises:
            ValueError: wenn der Versuch bereits bewertet ist oder die Note unzulässig ist.
        """
        if self.bewertet:
            raise ValueError(f"Versuch {self.versuch} ist bereits bewertet")
        return replace(self, note=note, datum=datum if datum is not None else self.datum)
