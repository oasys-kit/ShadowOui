import sys

import numpy
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QTextEdit, QTextCursor, QApplication, QFont, QPalette, QColor, \
    QMessageBox

from srxraylib.metrology import error_profile
from Shadow import ShadowTools as ST
from matplotlib import cm
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from oasys.widgets.widget import OWWidget
from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class OWaps_error_profile(OWWidget):
    name = "Surface Error Profile"
    id = "aps_error_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/aps.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 5
    category = ""
    keywords = ["aps_error_profile"]

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

    calculation_type=Setting(0)

    step_x = Setting(1.0)
    step_y = Setting(1.0)

    dimension_x = Setting(20.1)
    dimension_y = Setting(200.1)

    error_type = Setting(error_profile.FIGURE_ERROR)

    rms_x = Setting(0.1)
    montecarlo_seed_x = Setting(8787)

    rms_y = Setting(1)
    montecarlo_seed_y = Setting(8788)

    error_profile_1D_file_name = Setting("mirror_1D.dat")
    conversion_factor_x = Setting(0.1)
    conversion_factor_y = Setting(1e-6)

    error_profile_file_name = Setting('mirror.dat')

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Calculate Error Profile", self)
        self.runaction.triggered.connect(self.calculate_error_profile_ni)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Generate Error Profile File", self)
        self.runaction.triggered.connect(self.generate_error_profile_file_ni)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))))

        gen_box = oasysgui.widgetBox(self.controlArea, "Error Profile Parameters", addSpace=True, orientation="horizontal",
                                      width=500)

        tabs_setting = gui.tabWidget(gen_box)

        tab_input = oasysgui.createTabPage(tabs_setting, "Input Parameters")

        tab_out = oasysgui.createTabPage(tabs_setting, "Output")

        self.input_box = oasysgui.widgetBox(tab_input, "Input", addSpace=True, orientation="vertical", width=470)

        gui.comboBox(self.input_box, self, "calculation_type", label="Kind of Calculation", labelWidth=260,
                     items=["Complete 2D simulation", "2D simulation from 1D profile"],
                     callback=self.set_CalculationType, sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.input_box)

        self.calculation_type_box_1 = oasysgui.widgetBox(tab_input, "", addSpace=True, orientation="vertical", width=460, height=300)

        oasysgui.lineEdit(self.calculation_type_box_1, self, "dimension_x", "Dimensions [cm]                        X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.calculation_type_box_1, self, "dimension_y",
                           "                                                 Y (length)", labelWidth=300,
                           valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_1, self, "step_x", "Step [cm]                                   X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.calculation_type_box_1, self, "step_y",
                           "                                                 Y (length)", labelWidth=300, valueType=float,
                           orientation="horizontal")

        gui.separator(self.calculation_type_box_1)

        gui.comboBox(self.calculation_type_box_1, self, "error_type", label="Error Type", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + u"\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_1, self, "rms_x", "Rms                                          X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.calculation_type_box_1, self, "rms_y",
                           "                                                 Y (length)", labelWidth=300, valueType=float,
                           orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_1, self, "montecarlo_seed_x", "Monte Carlo initial seed        X (width)", labelWidth=300,
                           valueType=int, orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_1, self, "montecarlo_seed_y",
                           "                                                 Y (length)", labelWidth=300, valueType=int,
                           orientation="horizontal")

        self.calculation_type_box_2 = oasysgui.widgetBox(tab_input, "", addSpace=True, orientation="vertical", width=460, height=300)

        self.select_file_box_1 = oasysgui.widgetBox(self.calculation_type_box_2, "", addSpace=True, orientation="horizontal")

        self.le_error_profile_1D_file_name = oasysgui.lineEdit(self.select_file_box_1, self, "error_profile_1D_file_name", "1D Profile File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        pushButton = gui.button(self.select_file_box_1, self, "...")
        pushButton.clicked.connect(self.selectFile1D)


        oasysgui.lineEdit(self.calculation_type_box_2, self, "conversion_factor_x", "Conversion from user unit to cm     (Y)", labelWidth=300,
                           valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_2, self, "conversion_factor_y", "Conversion from user unit to cm/rad (Error)", labelWidth=300,
                           valueType=float, orientation="horizontal")

        gui.separator(self.calculation_type_box_2)

        oasysgui.lineEdit(self.calculation_type_box_2, self, "dimension_x", "Dimensions [cm]                        X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_2, self, "step_x", "Step [cm]                                   X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        gui.separator(self.calculation_type_box_2)

        gui.comboBox(self.calculation_type_box_2, self, "error_type", label="Error Type", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + u"\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.calculation_type_box_2)

        oasysgui.lineEdit(self.calculation_type_box_2, self, "rms_x", "Rms                                          X (width)",
                           labelWidth=300, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.calculation_type_box_2, self, "montecarlo_seed_x", "Monte Carlo initial seed        X (width)", labelWidth=300,
                           valueType=int, orientation="horizontal")

        self.set_CalculationType()

        self.output_box = oasysgui.widgetBox(tab_input, "Outputs", addSpace=True, orientation="vertical", width=470)

        self.select_file_box = oasysgui.widgetBox(self.output_box, "", addSpace=True, orientation="horizontal")

        self.le_error_profile_file_name = oasysgui.lineEdit(self.select_file_box, self, "error_profile_file_name", "Output File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        pushButton = gui.button(self.select_file_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=600)
        out_box.layout().addWidget(self.shadow_output)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Error Profile", callback=self.calculate_error_profile)
        button.setFixedHeight(45)
        button.setFixedWidth(170)

        button = gui.button(button_box, self, "Generate Error Profile File", callback=self.generate_error_profile_file)
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
        self.axis.set_zlabel("Z (cm)")

        self.figure_canvas = FigureCanvasQTAgg(self.figure)
        self.mainArea.layout().addWidget(self.figure_canvas)

        gui.rubber(self.mainArea)

    def set_CalculationType(self):
        self.calculation_type_box_1.setVisible(self.calculation_type==0)
        self.calculation_type_box_2.setVisible(self.calculation_type==1)

    def calculate_error_profile_ni(self):
        self.calculate_error_profile(not_interactive_mode=True)

    def calculate_error_profile(self, not_interactive_mode=False):
        try:
            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            if self.error_type == error_profile.FIGURE_ERROR:
                rms_x = self.rms_x*1e-7 # from nm to cm
                rms_y = self.rms_y*1e-7 # from nm to cm
            else:
                rms_x = self.rms_x*1e-6 # from urad to rad
                rms_y = self.rms_y*1e-6 # from urad to rad

            if self.calculation_type == 0:
                xx, yy, zz = error_profile.create_simulated_2D_profile_APS(self.dimension_y,
                                                                           self.step_y,
                                                                           self.montecarlo_seed_y,
                                                                           self.error_type,
                                                                           rms_y,
                                                                           self.dimension_x,
                                                                           self.step_x,
                                                                           self.montecarlo_seed_x,
                                                                           self.error_type,
                                                                           rms_x)
            else:
                profile_1D_x, profile_1D_y = numpy.loadtxt(self.error_profile_1D_file_name, delimiter='\t', unpack=True)

                xx, yy, zz = error_profile.create_2D_profile_from_1D(profile_1D_x*self.conversion_factor_x,
                                                                     profile_1D_y*self.conversion_factor_y,
                                                                     self.dimension_x,
                                                                     self.step_x,
                                                                     self.montecarlo_seed_x,
                                                                     self.error_type,
                                                                     rms_x)

            self.xx = xx
            self.yy = yy
            self.zz = zz # in cm

            self.axis.clear()

            x_to_plot, y_to_plot = numpy.meshgrid(xx, yy)

            self.axis.plot_surface(x_to_plot, y_to_plot, self.zz,
                                   rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            self.axis.set_xlabel("X (cm)")
            self.axis.set_ylabel("Y (cm)")
            self.axis.set_zlabel("Z (cm)")

            self.axis.set_title("Generated 2D Error Profile")
            self.axis.mouse_init()

            if not not_interactive_mode:
                self.figure_canvas.draw()

                QMessageBox.information(self, "QMessageBox.information()",
                                        "Error Profile calculated: if the result is satisfactory,\nclick \'Generate Error Profile File\' to complete the operation ",
                                        QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)
            #raise exception

    def generate_error_profile_file_ni(self):
        self.generate_error_profile_file(not_interactive_mode=True)

    def generate_error_profile_file(self, not_interactive_mode=False):
        if not self.zz is None and not self.yy is None and not self.xx is None:
            try:
                congruence.checkDir(self.error_profile_file_name)

                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                ST.write_shadow_surface(self.zz, self.xx, self.yy, outFile=congruence.checkFileName(self.error_profile_file_name))
                if not not_interactive_mode:
                    QMessageBox.information(self, "QMessageBox.information()",
                                            "Error Profile file " + self.error_profile_file_name + " written on disk",
                                            QMessageBox.Ok)

                self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=self.error_profile_file_name,
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
        if self.calculation_type == 0:
            self.dimension_x = congruence.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
            self.dimension_y = congruence.checkStrictlyPositiveNumber(self.dimension_y, "Dimension Y")
            self.step_x = congruence.checkStrictlyPositiveNumber(self.step_x, "Step X")
            self.step_y = congruence.checkStrictlyPositiveNumber(self.step_y, "Step Y")
            self.rms_x = congruence.checkPositiveNumber(self.rms_x, "Rms X")
            self.rms_y = congruence.checkPositiveNumber(self.rms_y, "Rms Y")
            self.montecarlo_seed_x = congruence.checkPositiveNumber(self.montecarlo_seed_x, "Monte Carlo initial seed X")
            self.montecarlo_seed_y = congruence.checkPositiveNumber(self.montecarlo_seed_y, "Monte Carlo initial seed y")
        else:
            congruence.checkFile(self.error_profile_1D_file_name)
            self.dimension_x = congruence.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
            self.step_x = congruence.checkStrictlyPositiveNumber(self.step_x, "Step X")
            self.rms_x = congruence.checkPositiveNumber(self.rms_x, "Rms X")
            self.montecarlo_seed_x = congruence.checkPositiveNumber(self.montecarlo_seed_x, "Monte Carlo initial seed X")

        congruence.checkDir(self.error_profile_file_name)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def selectFile1D(self):
        self.le_error_profile_1D_file_name.setText(oasysgui.selectFileFromDialog(self, self.error_profile_1D_file_name, "Select 1D Error Profile File", file_extension_filter="*.dat; *.txt"))

    def selectFile(self):
        self.le_error_profile_file_name.setText(oasysgui.selectFileFromDialog(self, self.error_profile_file_name, "Select Output File", file_extension_filter="*.dat"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWaps_error_profile()
    w.show()
    app.exec()
    w.saveSettings()
