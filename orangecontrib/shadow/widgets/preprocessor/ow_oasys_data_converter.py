import os, numpy

from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets import widget

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from oasys.util.oasys_objects import OasysPreProcessorData, OasysSurfaceData

from Shadow import ShadowTools as ST
from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData


class OWOasysDataConverter(widget.OWWidget):
    name = "Oasys Surface Data Converter"
    id = "oasysDataConverter"
    description = "Oasys Surface Data Converter"
    icon = "icons/oasys_data_converter.png"
    priority = 0
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("Oasys PreProcessorData", OasysPreProcessorData, "set_input"),
              ("Oasys Surface Data", OasysSurfaceData, "set_input")]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    CONTROL_AREA_WIDTH = 605

    want_main_area = 0

    oasys_data = None

    def __init__(self):
        super().__init__()


        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)


        label = gui.label(self.controlArea, self, "From Oasys Surface To Shadow Surface")
        font = QFont(label.font())
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(14)
        label.setFont(font)
        palette = QPalette(label.palette()) # make a copy of the palette
        palette.setColor(QPalette.Foreground, QColor('Dark Blue'))
        label.setPalette(palette) # assign new palette

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_surface, height=45)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.oasys_data = input_data

            self.convert_surface()

    def convert_surface(self):
        if not self.oasys_data is None:
            try:
                if isinstance(self.oasys_data, OasysPreProcessorData):
                    error_profile_data = self.oasys_data.error_profile_data
                    surface_data = error_profile_data.surface_data
                    error_profile_data_file = surface_data.surface_data_file

                    filename, file_extension = os.path.splitext(error_profile_data_file)

                    if (file_extension==".hd5" or file_extension==".hdf5" or file_extension==".hdf" or file_extension==".h5"):
                        error_profile_data_file = filename + "_shadow.dat"

                    ST.write_shadow_surface(surface_data.zz/self.workspace_units_to_m,
                                            numpy.round(surface_data.xx/self.workspace_units_to_m, 6),
                                            numpy.round(surface_data.yy/self.workspace_units_to_m, 6),
                                            error_profile_data_file)

                    self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=error_profile_data_file,
                                                                          error_profile_x_dim=error_profile_data.error_profile_x_dim/self.workspace_units_to_m,
                                                                          error_profile_y_dim=error_profile_data.error_profile_y_dim/self.workspace_units_to_m))
                elif isinstance(self.oasys_data, OasysSurfaceData):
                    surface_data_file = self.oasys_data.surface_data_file

                    filename, file_extension = os.path.splitext(surface_data_file)

                    if (file_extension==".hd5" or file_extension==".hdf5" or file_extension==".hdf" or file_extension==".h5"):
                        surface_data_file = filename + "_shadow.dat"

                    ST.write_shadow_surface(self.oasys_data.zz/self.workspace_units_to_m,
                                            numpy.round(self.oasys_data.xx/self.workspace_units_to_m, 6),
                                            numpy.round(self.oasys_data.yy/self.workspace_units_to_m, 6),
                                            surface_data_file)

                    error_profile_x_dim = abs(self.oasys_data.xx[-1] - self.oasys_data.xx[0])/self.workspace_units_to_m
                    error_profile_y_dim = abs(self.oasys_data.yy[-1] - self.oasys_data.yy[0])/self.workspace_units_to_m

                    self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=surface_data_file,
                                                                          error_profile_x_dim=error_profile_x_dim,
                                                                          error_profile_y_dim=error_profile_y_dim))



            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception
