"""Entity-Klasse Studiengang – Einstiegspunkt des Objektgraphen."""

from dashboard.domain.modul import Modul
from dashboard.domain.semester import Semester
from dashboard.domain.ziele import Fristziel, Notenziel, Ziel


class Studiengang:
    """Der Studiengang mit seinen Semestern und Zielen.

    * Studiengang–Semester ist eine Komposition: Semester werden nur hier
      erzeugt (:meth:`semester_hinzufuegen`).
    * Es gibt genau **ein** Fristziel (Pflicht) und höchstens ein Notenziel.
      Dadurch sind verbleibende Monate und benötigtes Lerntempo eindeutig.

    Args:
        name: Bezeichnung des Studiengangs.
        benoetigte_ects: ECTS für den Abschluss (z. B. 180).
        fristziel: das Fristziel des Studiums.
        notenziel: optionales Notenziel.
    """

    def __init__(
        self,
        name: str,
        benoetigte_ects: int,
        fristziel: Fristziel,
        notenziel: Notenziel | None = None,
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name darf nicht leer sein")
        if isinstance(benoetigte_ects, bool) or not isinstance(benoetigte_ects, int) or benoetigte_ects <= 0:
            raise ValueError("benoetigte_ects muss eine positive ganze Zahl sein")
        if not isinstance(fristziel, Fristziel):
            raise TypeError("fristziel muss vom Typ Fristziel sein")
        if notenziel is not None and not isinstance(notenziel, Notenziel):
            raise TypeError("notenziel muss vom Typ Notenziel oder None sein")
        self._name = name.strip()
        self._benoetigte_ects = benoetigte_ects
        self._fristziel = fristziel
        self._notenziel = notenziel
        self._semester: list[Semester] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def benoetigte_ects(self) -> int:
        return self._benoetigte_ects

    @property
    def fristziel(self) -> Fristziel:
        return self._fristziel

    @property
    def notenziel(self) -> Notenziel | None:
        return self._notenziel

    @property
    def ziele(self) -> tuple[Ziel, ...]:
        """Alle Ziele; erlaubt die polymorphe Bewertung über die Oberklasse."""
        return (self._fristziel,) if self._notenziel is None else (self._fristziel, self._notenziel)

    @property
    def semester(self) -> tuple[Semester, ...]:
        """Semester aufsteigend nach Nummer."""
        return tuple(sorted(self._semester, key=lambda s: s.nummer))

    def semester_hinzufuegen(self, nummer: int) -> Semester:
        """Erzeugt ein neues Semester (Komposition) und gibt es zurück.

        Raises:
            ValueError: wenn die Semesternummer bereits existiert.
        """
        if any(s.nummer == nummer for s in self._semester):
            raise ValueError(f"Semester {nummer} existiert bereits")
        semester = Semester(nummer)
        self._semester.append(semester)
        return semester

    def alle_module(self) -> tuple[Modul, ...]:
        """Alle Module ohne Duplikate (ein Modul kann mehreren Semestern angehören)."""
        gesehen: dict[str, Modul] = {}
        for s in self.semester:
            for m in s.module:
                gesehen.setdefault(m.kuerzel, m)
        return tuple(gesehen.values())

    def finde_modul(self, kuerzel: str) -> Modul | None:
        """Sucht ein Modul über sein Kürzel (Groß-/Kleinschreibung egal)."""
        for m in self.alle_module():
            if m.kuerzel.casefold() == kuerzel.strip().casefold():
                return m
        return None

    def __repr__(self) -> str:
        return f"Studiengang({self._name!r}, {len(self._semester)} Semester)"
