"""Abstrakte Schnittstelle für das Speichern und Laden eines Studiengangs."""

from abc import ABC, abstractmethod

from dashboard.domain import Studiengang


class DatenFehler(Exception):
    """Gespeicherte Daten fehlen, sind unlesbar oder fachlich ungültig."""


class StudiengangRepository(ABC):
    """Kapselt die Persistenz (Dependency Inversion).

    Der Controller kennt nur diese Abstraktion. Eine andere Speicherform,
    z. B. SQLite, ließe sich als weitere Unterklasse ergänzen, ohne
    Controller oder Domain zu ändern.
    """

    @abstractmethod
    def lade(self) -> Studiengang:
        """Lädt den vollständigen Objektgraphen.

        Raises:
            DatenFehler: wenn die Daten nicht gelesen oder validiert werden können.
        """

    @abstractmethod
    def speichere(self, studiengang: Studiengang) -> None:
        """Speichert den vollständigen Objektgraphen."""
