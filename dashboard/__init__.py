"""Studien-Dashboard: Prototyp zur Überwachung des eigenen Studienfortschritts.

Das Paket ist nach einem Schichtenmodell aufgebaut:

* ``domain``     – Fachklassen (Studiengang, Semester, Modul, Prüfungsleistung, Ziele)
* ``service``    – objektübergreifende Berechnungen (ECTS, Lerntempo, Notendurchschnitt)
* ``repository`` – Speichern und Laden des Objektgraphen (JSON)
* ``dto``        – Datenübergabe zwischen Controller und View
* ``controller`` – steuert den Ablauf und verbindet die Schichten
* ``view``       – Ausgabe auf der Kommandozeile und Benutzereingaben
"""

__version__ = "1.0.0"
