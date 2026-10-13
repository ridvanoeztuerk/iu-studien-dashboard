"""Service-Schicht: objektübergreifende Berechnungen über den Studiengang."""

from dashboard.service.fortschritt_service import FortschrittService
from dashboard.service.noten_service import NotenService

__all__ = ["FortschrittService", "NotenService"]
