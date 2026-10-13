"""Repository-Schicht: Persistenz des Objektgraphen."""

from dashboard.repository.json_repository import JsonStudiengangRepository
from dashboard.repository.studiengang_repository import DatenFehler, StudiengangRepository

__all__ = ["DatenFehler", "JsonStudiengangRepository", "StudiengangRepository"]
