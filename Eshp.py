from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
import os

class Eshp:
    def __init__(self, iface):
        # Zapisz referencję do interfejsu QGIS
        self.iface = iface
        # Ścieżka do katalogu wtyczki
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        # Ścieżka do ikony
        icon_path = os.path.join(self.plugin_dir, 'icons', 'Eshp.png')

        # Sprawdzenie, czy plik ikony istnieje
        if not os.path.exists(icon_path):
            print(f"Ikona nie została znaleziona: {icon_path}")

        # Utwórz akcję z ikoną
        self.action = QAction(QIcon(icon_path), "Export Selected SHP", self.iface.mainWindow())

        # Podłącz funkcję, która zostanie wywołana po kliknięciu przycisku
        self.action.triggered.connect(self.export_selected_shp)

        # Dodaj akcję do paska narzędzi QGIS
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        # Usuń ikonę z paska narzędzi QGIS
        self.iface.removeToolBarIcon(self.action)

    def export_selected_shp(self):
        # Import funkcji eksportu
        from .Export_shp import export_shp
        # Wywołaj funkcję eksportu, przekazując interfejs
        export_shp(self.iface)
