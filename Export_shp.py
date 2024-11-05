from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog, QProgressDialog
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.core import QgsMapLayer, QgsProject, QgsCoordinateTransform, QgsCoordinateTransformContext, QgsCoordinateReferenceSystem, QgsVectorFileWriter, QgsFields, QgsField, QgsFeature
from qgis.utils import iface
import os

# Funkcja do eksportowania warstw do SHP
def export_shp(iface):
    # Funkcja do wyboru folderu zapisu
    def choose_output_folder():
        folder = QFileDialog.getExistingDirectory(None, "Wybierz folder zapisu SHP")
        return folder

    # Wybór folderu zapisu
    output_folder = choose_output_folder()
    if not output_folder:
        QMessageBox.information(None, "Anulowano", "Nie wybrano folderu.")
        return

    # Pobranie listy warstw z projektu
    layers = QgsProject.instance().mapLayers().values()
    selected_layers = [layer for layer in layers if layer.type() == QgsMapLayer.VectorLayer and layer in iface.layerTreeView().selectedLayers()]

    # Jeśli nie ma zaznaczonych warstw
    if not selected_layers:
        response = QMessageBox.question(None, "Zapis warstw", "Nie ma zaznaczonych warstw. Czy chcesz zapisać wszystkie warstwy z legendy?", QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            layers_to_save = [layer for layer in layers if layer.type() == QgsMapLayer.VectorLayer]
        else:
            QMessageBox.information(None, "Anulowano", "Eksport został anulowany.")
            return
    # Jeśli jest zaznaczona 1 warstwa
    elif len(selected_layers) == 1:
        layer_name = selected_layers[0].name()
        response = QMessageBox.question(None, "Zapis warstwy", f"Czy chcesz zapisać tylko warstwę: {layer_name}?", QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            layers_to_save = selected_layers
        else:
            QMessageBox.information(None, "Anulowano", "Eksport został anulowany.")
            return
    # Jeśli jest zaznaczonych więcej niż 1 warstwa
    else:
        response = QMessageBox.question(None, "Zapis warstw", "Czy chcesz wyeksportować tylko zaznaczone warstwy?", QMessageBox.Yes | QMessageBox.No)
        if response == QMessageBox.Yes:
            layers_to_save = selected_layers
        else:
            QMessageBox.information(None, "Anulowano", "Eksport został anulowany.")
            return

    # Jeśli są warstwy do zapisania
    if layers_to_save:
        # Zapytać o zapis stylów
        save_styles_response = QMessageBox.question(None, "Zapis stylów", "Czy chcesz zapisać również style warstw?", QMessageBox.Yes | QMessageBox.No)

        # Pasek postępu
        progress = QProgressDialog("Zapisywanie warstw...", "Anuluj", 0, len(layers_to_save))
        progress.setWindowModality(Qt.WindowModal)

        # Flaga dla opcji "Tak dla wszystkich" przy konwersji układu współrzędnych
        convert_all_crs = False
        # Flaga dla opcji "Tak dla wszystkich" przy nadpisywaniu plików
        overwrite_all = False

        # Zapis wybranych warstw
        for i, layer in enumerate(layers_to_save):
            # Aktualizacja paska postępu
            progress.setValue(i)
            if progress.wasCanceled():
                break

            # Sprawdzenie układu współrzędnych
            target_crs = QgsCoordinateReferenceSystem("EPSG:2180")
            transform_crs = False

            if layer.crs() != target_crs:
                if not convert_all_crs:
                    response = QMessageBox.question(None, "Przekonwertować układ współrzędnych?",
                                                    f"Warstwa '{layer.name()}' ma układ współrzędnych {layer.crs().authid()}. "
                                                    "Czy chcesz przekonwertować do EPSG:2180?",
                                                    QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll)
                    if response == QMessageBox.Yes:
                        transform_crs = True
                    elif response == QMessageBox.YesToAll:
                        transform_crs = True
                        convert_all_crs = True
                else:
                    transform_crs = True

            # Ustawienie ścieżki do zapisu
            output_path = os.path.join(output_folder, f"{layer.name()}.shp")

            # Sprawdzenie, czy plik o tej samej nazwie już istnieje
            if os.path.exists(output_path):
                if not overwrite_all:
                    overwrite_response = QMessageBox.question(None, "Nadpisywanie pliku",
                                                              f"Plik o nazwie {layer.name()}.shp już istnieje. Czy chcesz go nadpisać?",
                                                              QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll)
                    if overwrite_response == QMessageBox.No:
                        continue
                    elif overwrite_response == QMessageBox.YesToAll:
                        overwrite_all = True

            # Przekształcenie pól, aby obsłużyć ograniczenia formatu SHP
            fields = layer.fields()
            transformed_fields = QgsFields()

            for field in fields:
                if field.typeName() in ['String', 'Integer', 'Real', 'Date', 'Double', 'Boolean']:  # Obsługiwane typy przez SHP
                    transformed_fields.append(field)
                else:
                    # Konwersja nieobsługiwanych typów na String
                    transformed_fields.append(QgsField(field.name()[:10], QVariant.String))  # Ograniczenie długości nazwy pola do 10 znaków
                    print(f"Pole '{field.name()}' typu '{field.typeName()}' zostanie przekonwertowane na String.")

            # Tworzenie nowej warstwy i kopiowanie danych
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "ESRI Shapefile"
            options.fileEncoding = "UTF-8"
            if transform_crs:
                options.ct = QgsCoordinateTransform(layer.crs(), target_crs, QgsProject.instance())

            writer = QgsVectorFileWriter(output_path, "UTF-8", transformed_fields, layer.wkbType(), target_crs if transform_crs else layer.crs(), "ESRI Shapefile")

            if writer.hasError() != QgsVectorFileWriter.NoError:
                print(f"Błąd przy tworzeniu pliku SHP dla warstwy '{layer.name()}': {writer.errorMessage()}")

            # Iteracja przez funkcje (features) i przekształcanie danych
            for feature in layer.getFeatures():
                new_feature = QgsFeature()
                new_feature.setGeometry(feature.geometry())
                attributes = []

                for i, field in enumerate(fields):
                    if field.typeName() in ['String', 'Integer', 'Real', 'Date', 'Double', 'Boolean']:
                        attributes.append(feature.attributes()[i])
                    else:
                        # Konwersja nieobsługiwanych typów na String (użycie wartości wyświetlanej)
                        attributes.append(str(feature.attributes()[i]))

                new_feature.setAttributes(attributes)
                writer.addFeature(new_feature)

            del writer  # Zamykanie pliku SHP

            # Zapis stylu warstwy, jeśli użytkownik wybrał tak
            if save_styles_response == QMessageBox.Yes:
                style_path = os.path.join(output_folder, f"{layer.name()}.qml")
                layer.saveNamedStyle(style_path)

        # Ustawienie paska postępu na 100%
        progress.setValue(len(layers_to_save))

        # Wyświetlenie komunikatu o zakończeniu eksportu
        QMessageBox.information(None, "Eksport zakończony", "Eksport warstw został zakończony.")
