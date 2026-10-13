"""Entity-Klasse Semester."""

from dashboard.domain.modul import Modul


class Semester:
    """Ein Semester laut Studienablaufplan.

    Semester und Modul stehen in einer **Aggregation**: Das Semester hält nur
    Referenzen auf Module, die unabhängig von ihm existieren. Ein Modul kann
    daher auch mehreren Semestern zugeordnet sein.

    Semester werden nur vom Studiengang erzeugt (siehe
    :meth:`Studiengang.semester_hinzufuegen`), da sie ohne Studiengang keine
    Bedeutung haben (Komposition Studiengang–Semester).

    Args:
        nummer: Semesternummer laut Studienablaufplan (ab 1).
    """

    def __init__(self, nummer: int) -> None:
        if isinstance(nummer, bool) or not isinstance(nummer, int) or nummer < 1:
            raise ValueError(f"nummer muss eine ganze Zahl ab 1 sein, nicht {nummer!r}")
        self._nummer = nummer
        self._module: list[Modul] = []

    @property
    def nummer(self) -> int:
        return self._nummer

    @property
    def module(self) -> tuple[Modul, ...]:
        """Zugeordnete Module als unveränderliche Kopie der Referenzliste."""
        return tuple(self._module)

    def modul_zuordnen(self, modul: Modul) -> None:
        """Ordnet ein bestehendes Modul diesem Semester zu.

        Raises:
            TypeError: wenn kein Modul übergeben wird.
            ValueError: wenn das Modul bereits zugeordnet ist.
        """
        if not isinstance(modul, Modul):
            raise TypeError("Es können nur Modul-Objekte zugeordnet werden")
        if any(m.kuerzel == modul.kuerzel for m in self._module):
            raise ValueError(f"{modul.kuerzel} ist Semester {self._nummer} bereits zugeordnet")
        self._module.append(modul)

    def __repr__(self) -> str:
        return f"Semester({self._nummer}, {len(self._module)} Module)"
