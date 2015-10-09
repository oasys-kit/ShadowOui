import sys, numpy, copy

from PyQt4.QtGui import QTextEdit, QTextCursor, QApplication, QFileDialog, QScrollArea, QTableWidget, QTableWidgetItem, QFont, QPalette, QColor, \
    QMessageBox, QHeaderView
from PyQt4.QtCore import QRect, Qt
from oasys.widgets import widget
from orangewidget import gui
from orangewidget.settings import Setting
from Shadow import ShadowTools as ST

from matplotlib import cm
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowGui, ConfirmDialog

class OWxsh_waviness(widget.OWWidget):
    name = "xsh_waviness"
    id = "xsh_waviness"
    description = "xoppy application to compute..."
    icon = "icons/waviness.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 10
    category = ""
    keywords = ["xoppy", "xsh_waviness"]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    want_main_area = 1
    want_control_area = 1

    WIDGET_WIDTH = 1100
    WIDGET_HEIGHT = 650

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

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))))

        gen_box = ShadowGui.widgetBox(self.controlArea, "Waviness Parameters", addSpace=True, orientation="horizontal",
                                      width=500)

        tabs_setting = gui.tabWidget(gen_box)

        tab_input = ShadowGui.createTabPage(tabs_setting, "Input Parameter")
        tab_harmonics = ShadowGui.createTabPage(tabs_setting, "Harmonics")
        tab_out = ShadowGui.createTabPage(tabs_setting, "Output")

        self.input_box = ShadowGui.widgetBox(tab_input, "Inputs", addSpace=True, orientation="vertical", width=470)

        gui.button(self.input_box, self, "Load xsh_waviness input file ...", callback=self.load_inp_file)

        gui.separator(self.input_box)

        ShadowGui.lineEdit(self.input_box, self, "number_of_points_x", "Number of Points (<201)           X (width)",
                           labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(self.input_box, self, "number_of_points_y",
                           "                                                 Y (length)", labelWidth=300, valueType=int,
                           orientation="horizontal")

        gui.separator(self.input_box)

        ShadowGui.lineEdit(self.input_box, self, "dimension_x", "Dimensions [cm]                        X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.input_box, self, "dimension_y",
                           "                                                 Y (length)", labelWidth=300,
                           valueType=float, orientation="horizontal")

        gui.separator(self.input_box)

        ShadowGui.lineEdit(self.input_box, self, "estimated_slope_error", "Estimated slope error [arcsec]",
                           labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.input_box, self, "montecarlo_seed", "Monte Carlo initial seed", labelWidth=300,
                           valueType=int, orientation="horizontal")

        self.output_box = ShadowGui.widgetBox(tab_input, "Outputs", addSpace=True, orientation="vertical", width=470)

        self.select_file_box = ShadowGui.widgetBox(self.output_box, "", addSpace=True, orientation="horizontal")

        gui.separator(self.output_box)

        gui.button(self.output_box, self, "Write xsh_waviness input file (optional) ...", callback=self.write_inp_file)

        ShadowGui.lineEdit(self.select_file_box, self, "waviness_file_name", "Output File Name", labelWidth=120,
                           valueType=str, orientation="horizontal")

        self.harmonics_box = ShadowGui.widgetBox(tab_harmonics, "Harmonics", addSpace=True, orientation="vertical",
                                                 width=470, height=690)

        ShadowGui.lineEdit(self.harmonics_box, self, "harmonic_maximum_index", "Harmonic Maximum Index", labelWidth=300,
                           valueType=int, orientation="horizontal", callback=self.set_harmonics)

        gui.separator(self.harmonics_box)

        self.scrollarea = QScrollArea()
        self.scrollarea.setMaximumWidth(400)

        self.harmonics_box.layout().addWidget(self.scrollarea, alignment=Qt.AlignHCenter)

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = ShadowGui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=600)
        out_box.layout().addWidget(self.shadow_output)

        button_box = ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Waviness", callback=self.calculate_waviness)
        button.setFixedHeight(45)
        button.setFixedWidth(170)

        button = gui.button(button_box, self, "Generate Waviness File", callback=self.generate_waviness_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(200)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(120)

        gui.rubber(self.controlArea)

        self.figure = Figure(figsize=(600, 600))
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')

        self.axis.set_xlabel("X (cm)")
        self.axis.set_ylabel("Y (cm)")
        self.axis.set_zlabel("Z (µm)")

        self.figure_canvas = FigureCanvasQTAgg(self.figure)
        self.mainArea.layout().addWidget(self.figure_canvas)

        gui.rubber(self.mainArea)

    def restoreWidgetPosition(self):
        super().restoreWidgetPosition()

        self.table = QTableWidget(self.harmonic_maximum_index + 1, 3)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setResizeMode(QHeaderView.Fixed)

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
            QMessageBox.critical(self, "QMessageBox.critical()",
                                 message + "\nValue is reset to previous value",
                                 QMessageBox.Ok)

            table_item = QTableWidgetItem(previous_value)
            table_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(error_row_index, error_column_index, table_item)
            self.table.setCurrentCell(error_row_index, error_column_index)

        except Exception as exception:
            QMessageBox.critical(self, "QMessageBox.critical()",
                                 exception.args[0],
                                 QMessageBox.Ok)

    def set_harmonics(self):
        if self.harmonic_maximum_index < 0:
            QMessageBox.critical(self, "QMessageBox.critical()",
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
        file_name = QFileDialog.getOpenFileName(self, "Select a input file for XSH_WAVINESS", ".", "*.inp")

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

            file_name = self.waviness_file_name.strip().split(sep=".dat")[0] + ".inp"

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
            QMessageBox.critical(self, "QMessageBox.critical()",
                                 exception.args[0],
                                 QMessageBox.Ok)

    def calculate_waviness(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            xx, yy, zz = ST.waviness_calc(npointx=self.number_of_points_x,
                                          npointy=self.number_of_points_y,
                                          width=self.dimension_x,
                                          xlength=self.dimension_y,
                                          slp=self.estimated_slope_error,
                                          nharmonics=self.harmonic_maximum_index,
                                          iseed=self.montecarlo_seed,
                                          c=self.to_float_array(self.data["c"]),
                                          y=self.to_float_array(self.data["y"]),
                                          g=self.to_float_array(self.data["g"]))
            self.xx = xx
            self.yy = yy
            self.zz = zz

            self.axis.clear()

            x_to_plot, y_to_plot = numpy.meshgrid(xx, yy)
            z_to_plot = []

            for y_index in range(0, len(yy)):
                z_array = []
                for x_index in range(0, len(xx)):
                    z_array.append(1e4 * float(zz[x_index][y_index]))  # to micron
                z_to_plot.append(z_array)

            z_to_plot = numpy.array(z_to_plot)

            self.axis.plot_surface(x_to_plot, y_to_plot, z_to_plot,
                                   rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            slope, sloperms = ST.slopes(zz, xx, yy)

            title = ' Slope error rms in X direction: %f arcsec' % (sloperms[0]) + '\n' + \
                    '                                            : %f urad' % (sloperms[2]) + '\n' + \
                    ' Slope error rms in Y direction: %f arcsec' % (sloperms[1]) + '\n' + \
                    '                                            : %f urad' % (sloperms[3])

            self.axis.set_xlabel("X (cm)")
            self.axis.set_ylabel("Y (cm)")
            self.axis.set_zlabel("Z (µm)")
            self.axis.set_title(title)
            self.axis.mouse_init()

            self.figure_canvas.draw()

            QMessageBox.information(self, "QMessageBox.information()",
                                    "Waviness calculated: if the result is satisfactory,\nclick \'Generate Waviness File\' to complete the operation ",
                                    QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "QMessageBox.critical()",
                                 exception.args[0],
                                 QMessageBox.Ok)


    def generate_waviness_file(self):
        if not self.zz is None and not self.yy is None and not self.xx is None:
            if not self.waviness_file_name is None:
                self.waviness_file_name = self.waviness_file_name.strip()

                if self.waviness_file_name == "": raise Exception("Output File Name missing")
            else:
                raise Exception("Output File Name missing")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            ST.write_shadow_surface(self.zz.T, self.xx, self.yy, outFile=ShadowGui.checkFileName(self.waviness_file_name))
            QMessageBox.information(self, "QMessageBox.information()",
                                    "Waviness file " + self.waviness_file_name + " written on disk",
                                    QMessageBox.Ok)


            self.send("PreProcessor_Data", ShadowPreProcessorData(waviness_data_file=self.waviness_file_name,
                                                                  waviness_x_dim=self.dimension_x,
                                                                  waviness_y_dim=self.dimension_y))

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
                self.reload_harmonics_table()
            except:
                pass

    def check_fields(self):
        self.number_of_points_x = ShadowGui.checkStrictlyPositiveNumber(self.number_of_points_x, "Number of Points X")
        self.number_of_points_y = ShadowGui.checkStrictlyPositiveNumber(self.number_of_points_y, "Number of Points Y")

        self.dimension_x = ShadowGui.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
        self.dimension_y = ShadowGui.checkStrictlyPositiveNumber(self.dimension_y, "Dimension Y")

        self.estimated_slope_error = ShadowGui.checkPositiveNumber(self.estimated_slope_error, "Estimated slope error")
        self.montecarlo_seed = ShadowGui.checkPositiveNumber(self.montecarlo_seed, "Monte Carlo initial seed")

        self.harmonic_maximum_index = ShadowGui.checkPositiveNumber(self.harmonic_maximum_index,
                                                                    "Harmonic Maximum Index")

        if not self.waviness_file_name is None:
            self.waviness_file_name = self.waviness_file_name.strip()

            if self.waviness_file_name == "": raise Exception("Output File Name missing")
        else:
            raise Exception("Output File Name missing")


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWxsh_waviness()
    w.show()
    app.exec()
    w.saveSettings()
