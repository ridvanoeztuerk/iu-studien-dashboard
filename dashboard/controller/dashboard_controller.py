"""Controller des Dashboards."""

from datetime import date

from dashboard.domain import Kennzahlen, Modulstatus, Pruefungsart, Studiengang, Zielstatus
from dashboard.dto import DashboardDatenDTO, ModulZeileDTO, ZielDTO
from dashboard.repository import StudiengangRepository
from dashboard.service import FortschrittService, NotenService

#: Höchstzahl automatisch erzeugter Hinweise unter „Nächste Schritte“.
MAX_HINWEISE = 6


def _de(wert: float, stellen: int) -> str:
    """Zahl mit deutschem Dezimalkomma für die Hinweistexte."""
    return f"{wert:.{stellen}f}".replace(".", ",")


class DashboardController:
    """Verbindet Repository, Services und Domain und liefert DTOs für die View.

    Der Controller enthält keine Berechnungslogik (die liegt in den Services)
    und keine Darstellungslogik (die liegt in der View). Er kennt das
    Repository nur über die abstrakte Klasse :class:`StudiengangRepository`.

    Args:
        repository: Persistenz für den Studiengang.
        fortschritt: Service für ECTS und Lerntempo.
        noten: Service für den Notendurchschnitt.
    """

    def __init__(
        self,
        repository: StudiengangRepository,
        fortschritt: FortschrittService,
        noten: NotenService,
    ) -> None:
        self._repository = repository
        self._fortschritt = fortschritt
        self._noten = noten
        self._studiengang: Studiengang | None = None

    def _lade(self) -> Studiengang:
        """Lädt den Studiengang beim ersten Zugriff (Lazy Loading)."""
        if self._studiengang is None:
            self._studiengang = self._repository.lade()
        return self._studiengang

    # --- Anzeige -----------------------------------------------------------------

    def bilde_kennzahlen(self, studiengang: Studiengang, stichtag: date) -> Kennzahlen:
        """Bündelt alle Service-Ergebnisse zu einem Stichtag im Wertobjekt Kennzahlen."""
        fz = studiengang.fristziel
        verbleibend = self._fortschritt.verbleibende_ects(studiengang)
        nz = studiengang.notenziel
        return Kennzahlen(
            erreichte_ects=self._fortschritt.erreichte_ects(studiengang),
            benoetigte_ects=studiengang.benoetigte_ects,
            verbleibende_ects=verbleibend,
            verbleibende_monate=self._fortschritt.verbleibende_monate(fz, stichtag),
            reales_tempo=self._fortschritt.reales_tempo(studiengang, fz, stichtag),
            benoetigte_ects_pro_monat=self._fortschritt.benoetigte_ects_pro_monat(studiengang, fz, stichtag),
            prognose_abschluss=self._fortschritt.prognostiziertes_abschlussdatum(studiengang, fz, stichtag),
            durchschnitt=self._noten.gewichteter_durchschnitt(studiengang),
            benoetigter_restdurchschnitt=(
                self._noten.benoetigter_restdurchschnitt(studiengang, nz.zielwert, verbleibend) if nz else None
            ),
        )

    def lade_dashboard_daten(self, stichtag: date) -> DashboardDatenDTO:
        """Erzeugt alle Daten für die Dashboard-Anzeige zu einem Stichtag."""
        sg = self._lade()
        kennzahlen = self.bilde_kennzahlen(sg, stichtag)
        # Polymorphie: Jedes Ziel bewertet sich selbst anhand derselben Kennzahlen.
        fristziel = ZielDTO(sg.fristziel.bezeichnung, sg.fristziel.bewerte(kennzahlen))
        notenziel = ZielDTO(sg.notenziel.bezeichnung, sg.notenziel.bewerte(kennzahlen)) if sg.notenziel else None
        zeilen = self._modulzeilen(sg)
        return DashboardDatenDTO(
            studiengang=sg.name,
            stichtag=stichtag,
            startdatum=sg.fristziel.startdatum,
            zieldatum=sg.fristziel.zieldatum,
            zielwert_note=sg.notenziel.zielwert if sg.notenziel else None,
            kennzahlen=kennzahlen,
            fristziel=fristziel,
            notenziel=notenziel,
            module=zeilen,
            naechste_schritte=self._naechste_schritte(zeilen, kennzahlen, fristziel, notenziel),
        )

    @staticmethod
    def _modulzeilen(studiengang: Studiengang) -> tuple[ModulZeileDTO, ...]:
        """Je Modul eine Zeile, zugeordnet zum ersten Semester, in dem es vorkommt."""
        zeilen: list[ModulZeileDTO] = []
        gesehen: set[str] = set()
        for semester in studiengang.semester:
            for m in semester.module:
                if m.kuerzel in gesehen:
                    continue
                gesehen.add(m.kuerzel)
                versuche = m.pruefungsleistungen
                zeilen.append(ModulZeileDTO(
                    semester=semester.nummer,
                    kuerzel=m.kuerzel,
                    titel=m.titel,
                    ects=m.ects,
                    status=m.status,
                    note=m.note,
                    versuche=len(versuche),
                    pruefungsart=versuche[-1].art.value if versuche else None,
                ))
        return tuple(zeilen)

    @staticmethod
    def _naechste_schritte(
        zeilen: tuple[ModulZeileDTO, ...],
        k: Kennzahlen,
        fristziel: ZielDTO,
        notenziel: ZielDTO | None,
    ) -> tuple[str, ...]:
        """Leitet konkrete Handlungshinweise aus Zielbewertung und Modulstatus ab.

        Reihenfolge nach Priorität: zuerst die gefährdeten Ziele, dann nicht
        bestandene und offene Prüfungen.
        """
        hinweise: list[str] = []
        if fristziel.status is Zielstatus.GEFAEHRDET:
            if k.benoetigte_ects_pro_monat is None:
                hinweise.append("Frist abgelaufen: Verlängerung beim Studierendensekretariat klären")
            else:
                hinweise.append(f"Ziel 1: Tempo von {_de(k.reales_tempo, 1)} auf "
                                f"{_de(k.benoetigte_ects_pro_monat, 1)} ECTS/Monat steigern")
        if notenziel is not None and k.benoetigter_restdurchschnitt is not None:
            rest = k.benoetigter_restdurchschnitt
            if rest < 1.0:
                hinweise.append("Ziel 2: Zielwert ist rechnerisch nicht mehr erreichbar")
            elif notenziel.status is Zielstatus.GEFAEHRDET:
                hinweise.append(f"Ziel 2: in den verbleibenden ECTS Ø {_de(rest, 2)} oder besser erreichen")
        for z in zeilen:
            if z.status is Modulstatus.NICHT_BESTANDEN:
                hinweise.append(f"{z.kuerzel}: Wiederholungsprüfung anmelden ({z.titel})")
            elif z.status is Modulstatus.IN_BEARBEITUNG and z.versuche > 1:
                hinweise.append(f"{z.kuerzel}: Wiederholungsprüfung ablegen ({z.versuche}. Versuch, {z.pruefungsart})")
        for z in zeilen:
            if z.status is Modulstatus.IN_BEARBEITUNG and z.versuche == 1:
                hinweise.append(f"{z.kuerzel}: {z.pruefungsart} abschließen")
        return tuple(hinweise[:MAX_HINWEISE])

    # --- Erfassung ---------------------------------------------------------------

    def module_mit_offenem_ergebnis(self) -> tuple[ModulZeileDTO, ...]:
        """Module, für die ein Prüfungsergebnis erfasst werden kann
        (in Bearbeitung, nicht bestanden oder geplant)."""
        offen = {Modulstatus.IN_BEARBEITUNG, Modulstatus.NICHT_BESTANDEN, Modulstatus.GEPLANT}
        return tuple(z for z in self._modulzeilen(self._lade()) if z.status in offen)

    def pruefungsergebnis_erfassen(
        self, kuerzel: str, art: Pruefungsart, note: float, datum: date | None
    ) -> str:
        """Trägt ein Prüfungsergebnis ein und speichert den Studiengang.

        Ist ein unbewerteter Versuch offen, wird dieser bewertet; andernfalls
        entsteht ein neuer Versuch. Die fachlichen Regeln (zulässige Note, kein
        Versuch nach Bestehen ...) prüft das Modul selbst; gespeichert wird nur,
        wenn die Erfassung erfolgreich war.

        Returns:
            Bestätigungstext für die Anzeige.

        Raises:
            ValueError: bei unbekanntem Kürzel oder Verstoß gegen fachliche Regeln.
        """
        sg = self._lade()
        modul = sg.finde_modul(kuerzel)
        if modul is None:
            raise ValueError(f"Unbekanntes Modul: {kuerzel}")
        bewertet = modul.ergebnis_eintragen(art, note, datum)
        self._repository.speichere(sg)
        ergebnis = "bestanden" if bewertet.bestanden else "nicht bestanden"
        return f"{modul.kuerzel}, Versuch {bewertet.versuch}: Note {_de(bewertet.note, 1)} ({ergebnis}) gespeichert."
