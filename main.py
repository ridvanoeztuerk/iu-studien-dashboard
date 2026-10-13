"""Startskript des Studien-Dashboards.

Aufruf:  python main.py            (Dashboard mit Menü)
         python main.py --help     (alle Optionen)
"""

import sys

if sys.version_info < (3, 10):
    sys.exit("Das Studien-Dashboard benötigt Python 3.10 oder neuer (getestet mit 3.14).")

from dashboard.app import DashboardApp  # noqa: E402  (Import erst nach der Versionsprüfung)

if __name__ == "__main__":
    sys.exit(DashboardApp().start())
