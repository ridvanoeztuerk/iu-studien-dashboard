"""JSON-Implementierung des StudiengangRepository."""

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

from dashboard.domain import Fristziel, Modul, Notenziel, Pruefungsart, Studiengang
from dashboard.repository.studiengang_repository import DatenFehler, StudiengangRepository

#: Version des Dateiformats; erlaubt spätere Formatänderungen zu erkennen.
FORMAT_VERSION = 1


class JsonStudiengangRepository(StudiengangRepository):
    """Speichert den Studiengang als UTF-8-JSON-Datei.

    JSON kann nur Baumstrukturen abbilden. Weil ein Modul mehreren Semestern
    zugeordnet sein kann (Aggregation), werden Module einmal unter
    ``"module"`` gespeichert und von den Semestern nur über ihr Kürzel
    referenziert. Beim Laden entsteht so pro Kürzel genau ein Objekt.

    Beim Laden werden alle Objekte über ihre Konstruktoren und fachlichen
    Methoden aufgebaut. Damit greifen dieselben Validierungen wie im
    laufenden Programm, und fehlerhafte Dateien werden erkannt.

    Args:
        dateipfad: Pfad zur JSON-Datei.
    """

    def __init__(self, dateipfad: str | Path) -> None:
        self._dateipfad = Path(dateipfad)

    @property
    def dateipfad(self) -> Path:
        return self._dateipfad

    # --- Laden -------------------------------------------------------------------

    def lade(self) -> Studiengang:
        """Liest die Datei und baut den Objektgraphen auf.

        Raises:
            DatenFehler: bei fehlender Datei, ungültigem JSON oder ungültigen Werten.
        """
        try:
            text = self._dateipfad.read_text(encoding="utf-8")
        except FileNotFoundError as fehler:
            raise DatenFehler(f"Datendatei nicht gefunden: {self._dateipfad}") from fehler
        try:
            daten = json.loads(text)
            return self._aus_dict(daten)
        except json.JSONDecodeError as fehler:
            raise DatenFehler(f"Ungültiges JSON in {self._dateipfad.name}: {fehler}") from fehler
        except (KeyError, TypeError, ValueError) as fehler:
            raise DatenFehler(f"Ungültige Daten in {self._dateipfad.name}: {fehler}") from fehler

    @staticmethod
    def _datum(wert: str | None) -> date | None:
        return date.fromisoformat(wert) if wert else None

    def _aus_dict(self, daten: dict[str, Any]) -> Studiengang:
        if daten.get("format_version") != FORMAT_VERSION:
            raise ValueError(f"format_version {daten.get('format_version')!r} wird nicht unterstützt")

        fz = daten["fristziel"]
        fristziel = Fristziel(fz["bezeichnung"], date.fromisoformat(fz["startdatum"]),
                              date.fromisoformat(fz["zieldatum"]))
        nz = daten.get("notenziel")
        notenziel = Notenziel(nz["bezeichnung"], nz["zielwert"]) if nz else None
        sg_daten = daten["studiengang"]
        studiengang = Studiengang(sg_daten["name"], sg_daten["benoetigte_ects"], fristziel, notenziel)

        module: dict[str, Modul] = {}
        for md in daten["module"]:
            modul = Modul(md["kuerzel"], md["titel"], md["ects"], md.get("anerkannt", False))
            if modul.kuerzel in module:
                raise ValueError(f"Modul {modul.kuerzel} ist doppelt vorhanden")
            # Versuche über die Modul-Methoden nachspielen: Nummerierung und
            # Reihenfolge-Regeln (kein Versuch nach Bestehen usw.) werden so geprüft.
            for pd in md.get("pruefungsleistungen", []):
                versuch = modul.neuer_versuch(Pruefungsart[pd["art"]], self._datum(pd.get("datum")))
                if pd.get("versuch", versuch.versuch) != versuch.versuch:
                    raise ValueError(f"{modul.kuerzel}: Versuchsnummern müssen bei 1 beginnen und lückenlos sein")
                if pd.get("note") is not None:
                    modul.bewerte_versuch(versuch.versuch, pd["note"])
            module[modul.kuerzel] = modul

        for sd in daten["semester"]:
            semester = studiengang.semester_hinzufuegen(sd["nummer"])
            for kuerzel in sd["module"]:
                if kuerzel not in module:
                    raise ValueError(f"Semester {sd['nummer']} verweist auf unbekanntes Modul {kuerzel}")
                semester.modul_zuordnen(module[kuerzel])
        return studiengang

    # --- Speichern ---------------------------------------------------------------

    def speichere(self, studiengang: Studiengang) -> None:
        """Schreibt den Objektgraphen atomar.

        Es wird zunächst eine temporäre Datei geschrieben und diese dann
        ersetzt. Bricht das Programm beim Schreiben ab, bleibt die bisherige
        Datei unbeschädigt.
        """
        text = json.dumps(self._als_dict(studiengang), ensure_ascii=False, indent=2)
        self._dateipfad.parent.mkdir(parents=True, exist_ok=True)
        temp = self._dateipfad.with_suffix(self._dateipfad.suffix + ".tmp")
        temp.write_text(text + "\n", encoding="utf-8")
        os.replace(temp, self._dateipfad)

    @staticmethod
    def _als_dict(studiengang: Studiengang) -> dict[str, Any]:
        fz = studiengang.fristziel
        nz = studiengang.notenziel
        return {
            "format_version": FORMAT_VERSION,
            "studiengang": {"name": studiengang.name, "benoetigte_ects": studiengang.benoetigte_ects},
            "fristziel": {
                "bezeichnung": fz.bezeichnung,
                "startdatum": fz.startdatum.isoformat(),
                "zieldatum": fz.zieldatum.isoformat(),
            },
            "notenziel": {"bezeichnung": nz.bezeichnung, "zielwert": nz.zielwert} if nz else None,
            "module": [
                {
                    "kuerzel": m.kuerzel,
                    "titel": m.titel,
                    "ects": m.ects,
                    "anerkannt": m.anerkannt,
                    "pruefungsleistungen": [
                        {
                            "art": p.art.name,
                            "versuch": p.versuch,
                            "datum": p.datum.isoformat() if p.datum else None,
                            "note": p.note,
                        }
                        for p in m.pruefungsleistungen
                    ],
                }
                for m in studiengang.alle_module()
            ],
            "semester": [
                {"nummer": s.nummer, "module": [m.kuerzel for m in s.module]}
                for s in studiengang.semester
            ],
        }
