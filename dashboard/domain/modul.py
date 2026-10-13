"""Entity-Klasse Modul."""

from datetime import date

from dashboard.domain.aufzaehlungen import Modulstatus, Pruefungsart
from dashboard.domain.pruefungsleistung import Pruefungsleistung


class Modul:
    """Ein Modul des Studiengangs mit seinen Prüfungsversuchen.

    Modul und Prüfungsleistung stehen in einer **Komposition**: Eine
    Prüfungsleistung gehört genau einem Modul und existiert nicht ohne es.
    Python kennt dafür kein Sprachmittel, deshalb wird die exklusive
    Zugehörigkeit über die Programmlogik abgesichert:

    * Prüfungsleistungen werden ausschließlich vom Modul erzeugt
      (:meth:`neuer_versuch`); es gibt keine Methode, um ein von außen
      erzeugtes Objekt einzuhängen.
    * Die interne Liste ist nicht öffentlich; nach außen wird nur ein
      unveränderliches ``tuple`` herausgegeben.
    * Prüfungsleistungen sind selbst unveränderlich. Externe Referenzen können
      den Zustand des Moduls also weder direkt noch indirekt verändern.
      Eine Bewertung läuft ausschließlich über :meth:`bewerte_versuch`.

    Args:
        kuerzel: eindeutiger Kurscode, z. B. ``"IREN01"``.
        titel: Bezeichnung des Moduls.
        ects: Anzahl der ECTS-Punkte (> 0).
        anerkannt: ``True``, wenn das Modul ohne Note angerechnet wurde.
    """

    def __init__(self, kuerzel: str, titel: str, ects: int, anerkannt: bool = False) -> None:
        if not isinstance(kuerzel, str) or not kuerzel.strip():
            raise ValueError("kuerzel darf nicht leer sein")
        if not isinstance(titel, str) or not titel.strip():
            raise ValueError("titel darf nicht leer sein")
        if isinstance(ects, bool) or not isinstance(ects, int) or ects <= 0:
            raise ValueError(f"ects muss eine positive ganze Zahl sein, nicht {ects!r}")
        if not isinstance(anerkannt, bool):
            raise TypeError("anerkannt muss vom Typ bool sein")
        self._kuerzel = kuerzel.strip()
        self._titel = titel.strip()
        self._ects = ects
        self._anerkannt = anerkannt
        self._pruefungsleistungen: list[Pruefungsleistung] = []

    # --- Lesezugriff -------------------------------------------------------------

    @property
    def kuerzel(self) -> str:
        """Kurscode; dient auch als Schlüssel beim Speichern."""
        return self._kuerzel

    @property
    def titel(self) -> str:
        return self._titel

    @property
    def ects(self) -> int:
        return self._ects

    @property
    def anerkannt(self) -> bool:
        return self._anerkannt

    @property
    def pruefungsleistungen(self) -> tuple[Pruefungsleistung, ...]:
        """Alle Versuche in zeitlicher Reihenfolge, als unveränderliche Kopie."""
        return tuple(self._pruefungsleistungen)

    # --- abgeleitete Attribute ---------------------------------------------------

    @property
    def bestanden(self) -> bool:
        """Abgeleitet: anerkannt oder mindestens ein bestandener Versuch."""
        return self._anerkannt or any(p.bestanden for p in self._pruefungsleistungen)

    @property
    def note(self) -> float | None:
        """Abgeleitet: Note des bestandenen Versuchs.

        ``None`` bei anerkannten Modulen (keine Note) und bei Modulen, die
        noch nicht bestanden sind.
        """
        for p in self._pruefungsleistungen:
            if p.bestanden:
                return p.note
        return None

    @property
    def offener_versuch(self) -> Pruefungsleistung | None:
        """Der angelegte, aber noch nicht bewertete Versuch (höchstens einer)."""
        for p in self._pruefungsleistungen:
            if not p.bewertet:
                return p
        return None

    @property
    def status(self) -> Modulstatus:
        """Abgeleitet: Bearbeitungsstand für die Anzeige im Dashboard."""
        if self._anerkannt:
            return Modulstatus.ANERKANNT
        if self.bestanden:
            return Modulstatus.BESTANDEN
        if self.offener_versuch is not None:
            return Modulstatus.IN_BEARBEITUNG
        if self._pruefungsleistungen:
            return Modulstatus.NICHT_BESTANDEN
        return Modulstatus.GEPLANT

    # --- fachliche Operationen ---------------------------------------------------

    def _pruefe_neuer_versuch_moeglich(self) -> None:
        """Prüft die Regeln für einen weiteren Versuch.

        Raises:
            ValueError: wenn das Modul anerkannt oder bereits bestanden ist
                oder noch ein unbewerteter Versuch offen ist.
        """
        if self._anerkannt:
            raise ValueError(f"{self._kuerzel} ist anerkannt; Prüfungsversuche sind nicht möglich")
        if self.bestanden:
            raise ValueError(f"{self._kuerzel} ist bereits bestanden")
        if self.offener_versuch is not None:
            raise ValueError(f"{self._kuerzel} hat noch einen unbewerteten Versuch")

    def neuer_versuch(self, art: Pruefungsart, datum: date | None = None) -> Pruefungsleistung:
        """Legt einen neuen, noch unbewerteten Prüfungsversuch an.

        Raises:
            ValueError: siehe :meth:`_pruefe_neuer_versuch_moeglich`.
        """
        self._pruefe_neuer_versuch_moeglich()
        versuch = Pruefungsleistung(art=art, versuch=len(self._pruefungsleistungen) + 1, datum=datum)
        self._pruefungsleistungen.append(versuch)
        return versuch

    def ergebnis_eintragen(self, art: Pruefungsart, note: float, datum: date | None = None) -> Pruefungsleistung:
        """Trägt ein Prüfungsergebnis ein (atomar).

        Ist ein Versuch offen, wird dieser bewertet; ``art`` wird dann nicht
        verwendet. Andernfalls entsteht ein neuer, bereits bewerteter Versuch.
        Das Objekt wird vollständig validiert, *bevor* es in die Liste
        aufgenommen wird. Bei einer unzulässigen Note bleibt das Modul daher
        unverändert.

        Raises:
            ValueError: bei unzulässiger Note oder Verstoß gegen die Versuchsregeln.
        """
        offen = self.offener_versuch
        if offen is not None:
            return self.bewerte_versuch(offen.versuch, note, datum)
        self._pruefe_neuer_versuch_moeglich()
        versuch = Pruefungsleistung(art, len(self._pruefungsleistungen) + 1, datum, note)
        self._pruefungsleistungen.append(versuch)
        return versuch

    def bewerte_versuch(self, versuch_nr: int, note: float, datum: date | None = None) -> Pruefungsleistung:
        """Trägt die Note für einen offenen Versuch ein.

        Das unveränderliche Objekt wird durch eine bewertete Kopie ersetzt.
        Eine zuvor herausgegebene Referenz zeigt weiterhin auf den alten,
        unbewerteten Stand und hat keinen Einfluss auf das Modul.

        Returns:
            die bewertete Prüfungsleistung.

        Raises:
            ValueError: wenn der Versuch nicht existiert, bereits bewertet ist
                oder die Note unzulässig ist.
        """
        for i, p in enumerate(self._pruefungsleistungen):
            if p.versuch == versuch_nr:
                bewertet = p.mit_bewertung(note, datum)
                self._pruefungsleistungen[i] = bewertet
                return bewertet
        raise ValueError(f"{self._kuerzel} hat keinen Versuch {versuch_nr}")

    def __repr__(self) -> str:
        return f"Modul({self._kuerzel!r}, {self._ects} ECTS, {self.status.value})"
