import os, copy
import sys

import numpy
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QSizePolicy
from PyQt5.QtGui import QTextCursor, QFont, QPalette, QColor, QPixmap

from Shadow import ShadowTools as ST
from matplotlib import cm
from oasys.widgets.gui import FigureCanvas3D
from matplotlib.figure import Figure

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import EmittingStream

try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData

class OWxsh_waviness(OWWidget):
    name = "Waviness"
    id = "xsh_waviness"
    description = "Calculation of mirror surface error profile"
    icon = "icons/waviness.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; lrebuffi@anl.gov"
    priority = 4
    category = ""
    keywords = ["xoppy", "xsh_waviness"]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    want_main_area = 1
    want_control_area = 1

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 645

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 618

    xx = None
    yy = None
    zz = None

    number_of_points_x = Setting(10)
    number_of_points_y = Setting(100)

    dimension_x = Setting(20.1)
    dimension_y = Setting(113.1)

    estimated_slope_error = Setting(0.9)
    montecarlo_seed = Setting(2387427)

    waviness_file_name = Setting('waviness.dat')

    harmonic_maximum_index = Setting(60)

    data = Setting({'c': ['0.3',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.3',
                          '0.0',
                          '0.0',
                          '0.3',
                          '0.0',
                          '0.0',
                          '0.5',
                          '0.0',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.2',
                          '0.9',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.4',
                          '0.0',
                          '0.0',
                          '0.4',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.6',
                          '0.6',
                          '0.0',
                          '0.4',
                          '0.4',
                          '0.0',
                          '0.4',
                          '0.4',
                          '0.1',
                          '0.4',
                          '0.4',
                          '0.1',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.3',
                          '0.3',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0'],
                    'y': ['0.0',
                          '-0.1',
                          '-0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.03',
                          '0.0',
                          '0.0',
                          '0.2',
                          '0.0',
                          '0.0',
                          '0.2',
                          '0.0',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.01',
                          '0.0',
                          '0.0',
                          '0.03',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.02',
                          '0.02',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.3',
                          '0.3',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0'],
                    'g': ['0.0',
                          '0.3',
                          '0.3',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.05',
                          '0.0',
                          '0.0',
                          '0.05',
                          '0.0',
                          '0.0',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.05',
                          '0.05',
                          '0.05',
                          '0.2',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.2',
                          '0.2',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.1',
                          '0.1',
                          '0.0',
                          '0.0',
                          '0.0',
                          '0.0']})

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "waviness_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Calculate Waviness", self)
        self.runaction.triggered.connect(self.calculate_waviness_ni)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Generate Waviness File", self)
        self.runaction.triggered.connect(self.generate_waviness_file)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.MAX_WIDTH)),
                               round(min(geom.height() * 0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate\nWaviness", callback=self.calculate_waviness)
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Generate\nWaviness File", callback=self.generate_waviness_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_input = oasysgui.createTabPage(tabs_setting, "Input Parameter")
        tab_harmonics = oasysgui.createTabPage(tabs_setting, "Harmonics")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        self.input_box = oasysgui.widgetBox(tab_input, "Inputs", addSpace=True, orientation="vertical")

        gui.button(self.input_box, self, "Load xsh_waviness input file ...", callback=self.load_inp_file)

        gui.separator(self.input_box)

        oasysgui.lineEdit(self.input_box, self, "number_of_points_x", "Number of Points (<201) X (width)",
                           labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.input_box, self, "number_of_points_y",
                           "Number of Points (<201) Y (length)", labelWidth=260, valueType=int,
                           orientation="horizontal")

        gui.separator(self.input_box)

        self.le_dimension_x = oasysgui.lineEdit(self.input_box, self, "dimension_x", "Dimensions X (width)",
                           labelWidth=260, valueType=float, orientation="horizontal")
        self.le_dimension_y = oasysgui.lineEdit(self.input_box, self, "dimension_y",
                           "Dimensions Y (length)", labelWidth=260,
                           valueType=float, orientation="horizontal")

        gui.separator(self.input_box)

        oasysgui.lineEdit(self.input_box, self, "estimated_slope_error", "Estimated slope error [arcsec]",
                           labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.input_box, self, "montecarlo_seed", "Monte Carlo initial seed", labelWidth=260,
                           valueType=int, orientation="horizontal")

        self.output_box = oasysgui.widgetBox(tab_input, "Outputs", addSpace=True, orientation="vertical")

        gui.button(self.output_box, self, "Write xsh_waviness input file (optional) ...", callback=self.write_inp_file)

        gui.separator(self.output_box)

        self.select_file_box = oasysgui.widgetBox(self.output_box, "", addSpace=True, orientation="horizontal")

        self.le_waviness_file_name = oasysgui.lineEdit(self.select_file_box, self, "waviness_file_name", "Output File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(self.select_file_box, self, "...", callback=self.selectFile)

        self.harmonics_box = oasysgui.widgetBox(tab_harmonics, "Harmonics", addSpace=True, orientation="vertical",
                                                 height=580)

        oasysgui.lineEdit(self.harmonics_box, self, "harmonic_maximum_index", "Harmonic Maximum Index", labelWidth=260,
                           valueType=int, orientation="horizontal", callback=self.set_harmonics)

        gui.separator(self.harmonics_box)

        self.scrollarea = QScrollArea()
        self.scrollarea.setMaximumWidth(400)

        self.harmonics_box.layout().addWidget(self.scrollarea, alignment=Qt.AlignHCenter)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=580)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

        self.figure = Figure(figsize=(600, 600))
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')

        self.axis.set_zlabel("Z [nm]")

        self.figure_canvas = FigureCanvas3D(ax=self.axis, fig=self.figure)
        self.mainArea.layout().addWidget(self.figure_canvas)

        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
        self.si_to_user_units = 1e2 / self.workspace_units_to_cm

        self.axis.set_xlabel("X [" + self.workspace_units_label + "]")
        self.axis.set_ylabel("Y [" + self.workspace_units_label + "]")

        label = self.le_dimension_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_dimension_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def restoreWidgetPosition(self):
        super().restoreWidgetPosition()

        self.table = QTableWidget(self.harmonic_maximum_index + 1, 3)
        self.table.setStyleSheet("background-color: white;")
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)

        for i in range(0, 3):
            self.table.setColumnWidth(i, 70)

        horHeaders = []
        verHeaders = []

        for n, key in enumerate(sorted(self.data.keys())):
            horHeaders.append(key)

            for m, item in enumerate(self.data[key]):
                table_item = QTableWidgetItem(str(item))
                table_item.setTextAlignment(Qt.AlignRight)
                self.table.setItem(m, n, table_item)
                verHeaders.append(str(m))

        self.table.setHorizontalHeaderLabels(horHeaders)
        self.table.setVerticalHeaderLabels(verHeaders)
        self.table.resizeRowsToContents()

        self.table.itemChanged.connect(self.table_item_changed)

        self.scrollarea.setWidget(self.table)
        self.scrollarea.setWidgetResizable(1)

        gui.rubber(self.controlArea)

    def reload_harmonics_table(self):
        horHeaders = []
        verHeaders = []

        self.table.itemChanged.disconnect(self.table_item_changed)

        self.table.clear()

        row_count = self.table.rowCount()

        for n in range(0, row_count):
            self.table.removeRow(0)

        for index in range(0, self.harmonic_maximum_index + 1):
            self.table.insertRow(0)

        for n, key in enumerate(sorted(self.data.keys())):
            horHeaders.append(key)

            for m, item in enumerate(self.data[key]):
                table_item = QTableWidgetItem(str(item))
                table_item.setTextAlignment(Qt.AlignRight)
                self.table.setItem(m, n, table_item)
                verHeaders.append(str(m))

        self.table.setHorizontalHeaderLabels(horHeaders)
        self.table.setVerticalHeaderLabels(verHeaders)

        self.table.resizeRowsToContents()

        for i in range(0, 3):
            self.table.setColumnWidth(i, 70)

        self.table.itemChanged.connect(self.table_item_changed)

    def table_item_changed(self):
        dict = {}
        message = ""
        error_row_index = -1
        error_column_index = -1
        previous_value = ""

        try:
            row_count = self.harmonic_maximum_index + 1

            for column_index in range(0, self.table.columnCount()):
                column_name = self.table.horizontalHeaderItem(column_index).data(0)

                row_content = []

                for row_index in range(0, row_count):
                    if not self.table.item(row_index, column_index) is None:
                        message = "Value at row " + str(
                            row_index) + " and column \'" + column_name + "\' is not numeric"
                        error_row_index = row_index
                        error_column_index = column_index
                        previous_value = self.data[column_name][row_index]

                        value = float(self.table.item(row_index, column_index).data(0))  # to raise exception

                        row_content.append(str(value))

                dict[column_name] = row_content

            self.data = dict
        except ValueError:
            QMessageBox.critical(self, "Error",
                                 message + "\nValue is reset to previous value",
                                 QMessageBox.Ok)

            table_item = QTableWidgetItem(previous_value)
            table_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(error_row_index, error_column_index, table_item)
            self.table.setCurrentCell(error_row_index, error_column_index)

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

    def set_harmonics(self):
        if self.harmonic_maximum_index < 0:
            QMessageBox.critical(self, "Error",
                                 "Harmonic Maximum Index should be a positive integer number",
                                 QMessageBox.Ok)
        else:
            row_count = len(self.data["c"])

            if self.harmonic_maximum_index + 1 > row_count:
                for n, key in enumerate(sorted(self.data.keys())):
                    for m in range(row_count, self.harmonic_maximum_index + 1):
                        self.data[key].append('0.0')
            else:
                for n, key in enumerate(sorted(self.data.keys())):
                    self.data[key] = copy.deepcopy(self.data[key][0: self.harmonic_maximum_index + 1])

            self.reload_harmonics_table()

    def load_inp_file(self):
        file_name = oasysgui.selectFileFromDialog(self, None, "Select a input file for XSH_WAVINESS", file_extension_filter="Input Files (*.inp)")

        if not file_name is None:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if not file_name.strip() == "":
                dict = ST.waviness_read(file=file_name)

                self.number_of_points_x = dict["npointx"]
                self.number_of_points_y = dict["npointy"]
                self.dimension_y = dict["xlength"]
                self.dimension_x = dict["width"]
                self.estimated_slope_error = dict["slp"]
                self.montecarlo_seed = dict["iseed"]
                self.waviness_file_name = dict["file"].strip('\n\r').strip()
                self.harmonic_maximum_index = dict["nharmonics"]

                self.data["c"] = self.to_str_array(dict["c"])
                self.data["y"] = self.to_str_array(dict["y"])
                self.data["g"] = self.to_str_array(dict["g"])

                self.reload_harmonics_table()

    def write_inp_file(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            file_name = congruence.checkFileName(self.waviness_file_name.split(sep=".dat")[0] + ".inp")

            dict = {}

            dict["npointx"] = self.number_of_points_x
            dict["npointy"] = self.number_of_points_y
            dict["xlength"] = self.dimension_y
            dict["width"] = self.dimension_x
            dict["slp"] = self.estimated_slope_error
            dict["iseed"] = self.montecarlo_seed
            dict["file"] = self.waviness_file_name.strip('\n\r')
            dict["nharmonics"] = self.harmonic_maximum_index

            dict["c"] = self.to_float_array(self.data["c"])
            dict["y"] = self.to_float_array(self.data["y"])
            dict["g"] = self.to_float_array(self.data["g"])

            ST.waviness_write(dict, file=file_name)

            QMessageBox.information(self, "QMessageBox.information()",
                                    "File \'" + file_name + "\' written to disk",
                                    QMessageBox.Ok)

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

    def calculate_waviness_ni(self):
        self.calculate_waviness(not_interactive_mode=True)

    def calculate_waviness(self, not_interactive_mode=False):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            xx, yy, zz = ST.waviness_calc(npointx=self.number_of_points_x,
                                          npointy=self.number_of_points_y,
                                          width=self.dimension_x * self.workspace_units_to_cm,
                                          xlength=self.dimension_y * self.workspace_units_to_cm,
                                          slp=self.estimated_slope_error,
                                          nharmonics=self.harmonic_maximum_index,
                                          iseed=self.montecarlo_seed,
                                          c=self.to_float_array(self.data["c"]),
                                          y=self.to_float_array(self.data["y"]),
                                          g=self.to_float_array(self.data["g"]))

            self.xx = xx / self.workspace_units_to_cm
            self.yy = yy / self.workspace_units_to_cm
            self.zz = zz / self.workspace_units_to_cm

            self.axis.clear()

            x_to_plot, y_to_plot = numpy.meshgrid(self.xx, self.yy)
            z_to_plot = []

            for y_index in range(0, len(yy)):
                z_array = []
                for x_index in range(0, len(xx)):
                    z_array.append(1e7 * float(zz[x_index][y_index]))  # to nm
                z_to_plot.append(z_array)

            z_to_plot = numpy.array(z_to_plot)

            self.axis.plot_surface(x_to_plot, y_to_plot, z_to_plot,
                                   rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            slope, sloperms = ST.slopes(zz, xx, yy)

            title = ' Slope error rms in X direction: %f $\mu$rad' % (sloperms[0]*1e6) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms[1]*1e6)

            self.axis.set_xlabel("X [" + self.workspace_units_label + "]")
            self.axis.set_ylabel("Y [" + self.workspace_units_label + "]")
            self.axis.set_zlabel("Z [nm]")
            self.axis.set_title(title)
            self.axis.mouse_init()

            if not not_interactive_mode:
                self.figure_canvas.draw()

                QMessageBox.information(self, "QMessageBox.information()",
                                        "Waviness calculated: if the result is satisfactory,\nclick \'Generate Waviness File\' to complete the operation ",
                                        QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

    def generate_waviness_file(self, not_interactive_mode=False):
        if not self.zz is None and not self.yy is None and not self.xx is None:
            try:
                congruence.checkDir(self.waviness_file_name)

                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                ST.write_shadow_surface(self.zz.T, self.xx, self.yy, outFile=congruence.checkFileName(self.waviness_file_name))
                if not not_interactive_mode:
                    QMessageBox.information(self, "QMessageBox.information()",
                                            "Waviness file " + self.waviness_file_name + " written on disk",
                                            QMessageBox.Ok)

                self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=self.waviness_file_name,
                                                                      error_profile_x_dim=self.dimension_x,
                                                                      error_profile_y_dim=self.dimension_y))
            except Exception as exception:
                QMessageBox.critical(self, "Error",
                                     exception.args[0],
                                     QMessageBox.Ok)

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
                self.reload_harmonics_table()
            except:
                pass

    def check_fields(self):
        self.number_of_points_x = congruence.checkStrictlyPositiveNumber(self.number_of_points_x, "Number of Points X")
        self.number_of_points_y = congruence.checkStrictlyPositiveNumber(self.number_of_points_y, "Number of Points Y")

        self.dimension_x = congruence.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
        self.dimension_y = congruence.checkStrictlyPositiveNumber(self.dimension_y, "Dimension Y")

        self.estimated_slope_error = congruence.checkPositiveNumber(self.estimated_slope_error, "Estimated slope error")
        self.montecarlo_seed = congruence.checkPositiveNumber(self.montecarlo_seed, "Monte Carlo initial seed")

        self.harmonic_maximum_index = congruence.checkPositiveNumber(self.harmonic_maximum_index,
                                                                    "Harmonic Maximum Index")

        congruence.checkDir(self.waviness_file_name)

    def to_float_array(self, string_array):
        float_array = []

        for index in range(len(string_array)):
            float_array.append(float(string_array[index]))

        return float_array

    def to_str_array(self, float_array):
        string_array = []

        for index in range(len(float_array)):
            string_array.append(str(float_array[index]))

        return string_array

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def selectFile(self):
        self.le_waviness_file_name.setText(oasysgui.selectFileFromDialog(self, self.waviness_file_name, "Select Output File", file_extension_filter="Data Files (*.dat)"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWxsh_waviness()
    w.show()
    app.exec()
    w.saveSettings()
