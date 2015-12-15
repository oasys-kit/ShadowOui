__author__ = 'labx'

import sys
import threading

from oasys.widgets import gui as oasysgui
from orangewidget import gui
from orangewidget.settings import Setting

from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, EmittingStream

from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow.widgets.special_elements import hybrid_control

class HybridScreen(AutomaticElement):

    inputs = [("Input Beam", ShadowBeam, "setBeam"),]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},]

    name = "Hybrid Screen"
    description = "Shadow HYBRID: Hybrid Screen"
    icon = "icons/hybrid_screen.png"
    maintainer = "Luca Rebuffi and Xianbo Shi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu, xshi(@at@)aps.anl.gov"
    priority = 3
    category = "HYBRID"
    keywords = ["data", "file", "load", "read"]

    want_control_area = 1
    want_main_area = 1

    ghy_diff_plane = Setting(1)
    ghy_calcType = Setting(2)

    focal_length_calc = Setting(0)
    ghy_focallength = Setting(0.0)
    distance_to_image_calc = Setting(0)
    ghy_distance = Setting(0.0)

    ghy_usemirrorfile = Setting(0)
    ghy_mirrorfile = Setting("mirror.dat")
    ghy_profile_dimension = Setting(1)

    ghy_nf = Setting(0)

    ghy_nbins_x = Setting(39)
    ghy_nbins_z = Setting(39)
    ghy_npeak = Setting(10)
    ghy_fftnpts = Setting(1e6)

    input_beam = None

    def __init__(self):
        super().__init__()

        tabs_setting = oasysgui.tabWidget(self.controlArea)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Hybrid Setting")

        box_1 = oasysgui.widgetBox(tab_bas, "Calculation Parameters", addSpace=True, orientation="vertical", height=350)

        gui.comboBox(box_1, self, "ghy_diff_plane", label="Diffraction Plane", labelWidth=350,
                     items=["X", "Z"],
                     callback=self.set_DiffPlane,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(box_1, self, "ghy_calcType", label="Calculation Type", labelWidth=200,
                     items=["Simple Aperture", "Focusing Optical Element", "Focusing Optical Element with Slope Errors"],
                     callback=self.set_CalculationType,
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_1, 10)

        self.cb_focal_length_calc = gui.comboBox(box_1, self, "focal_length_calc", label="Focal Length", labelWidth=200,
                     items=["Use O.E. Focal Distance (SIMAG)", "Specify Value"],
                     callback=self.set_FocalLengthCalc,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_focal_length = oasysgui.lineEdit(box_1, self, "ghy_focallength", "Focal Length Value", labelWidth=200, valueType=float, orientation="horizontal")

        self.cb_distance_to_image_calc = gui.comboBox(box_1, self, "distance_to_image_calc", label="Distance to image", labelWidth=200,
                     items=["Use O.E. Image Plane Distance (T_IMAGE)", "Specify Value"],
                     callback=self.set_DistanceToImageCalc,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_distance_to_image = oasysgui.lineEdit(box_1, self, "ghy_distance", "Distance to image value", labelWidth=200, valueType=float, orientation="horizontal")


        self.cb_usemirrorfile = gui.comboBox(box_1, self, "ghy_usemirrorfile", label="Mirror figure Error", labelWidth=200,
                                             items=["Embedded in Shadow OE", "From External File"],
                                             callback=self.set_MirrorFile,
                                             sendSelectedValue=False, orientation="horizontal")


        self.select_file_box = oasysgui.widgetBox(box_1, "", addSpace=True, orientation="horizontal")


        self.le_mirrorfile = oasysgui.lineEdit(self.select_file_box, self, "ghy_mirrorfile", "Mirror Figure Error File", labelWidth=200, valueType=str, orientation="horizontal")


        pushButton = gui.button(self.select_file_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        self.cb_profile_dimension = gui.comboBox(box_1, self, "ghy_profile_dimension", label="Profile Dimension", labelWidth=350,
                                                 items=["1D", "2D"],
                                                 sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_1)

        self.cb_nf = gui.comboBox(box_1, self, "ghy_nf", label="Near Field Calculation", labelWidth=350,
                                             items=["No", "Yes"],
                                             callback=self.set_MirrorFile,
                                             sendSelectedValue=False, orientation="horizontal")


        box_2 = oasysgui.widgetBox(tab_bas, "Numerical Control Parameters", addSpace=True, orientation="vertical", height=150)

        self.le_nbins_x = oasysgui.lineEdit(box_2, self, "ghy_nbins_x", "Number of bins for I(X) histogram", labelWidth=250, valueType=float, orientation="horizontal")
        self.le_nbins_z = oasysgui.lineEdit(box_2, self, "ghy_nbins_z", "Number of bins for I(Z) histogram", labelWidth=250, valueType=float, orientation="horizontal")
        self.le_npeak   = oasysgui.lineEdit(box_2, self, "ghy_npeak", "Number of diffraction peaks", labelWidth=250, valueType=float, orientation="horizontal")
        self.le_fftnpts = oasysgui.lineEdit(box_2, self, "ghy_fftnpts", "Number of points for FFT", labelWidth=250, valueType=float, orientation="horizontal")

        self.set_DiffPlane()
        self.set_DistanceToImageCalc()
        self.set_CalculationType()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run HYBRID", callback=self.run_hybrid)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        tabs_2 = oasysgui.tabWidget(self.mainArea, height=700)

        tab_2_1 = oasysgui.createTabPage(tabs_2, "FF Delta Divergence")
        tab_2_3 = oasysgui.createTabPage(tabs_2, "X,Z at FF")
        tab_2_2 = oasysgui.createTabPage(tabs_2, "NF Delta Position")
        tab_2_4 = oasysgui.createTabPage(tabs_2, "X,Z at NF")

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = gui.widgetBox(self.mainArea, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.shadow_output.setFixedHeight(100)
        self.shadow_output.setFixedWidth(850)



    def selectFile(self):
        self.le_mirrorfile.setText(oasysgui.selectFileFromDialog(self, self.ghy_mirrorfile, "Select Mirror Error File", file_extension_filter="*.dat; *.txt"))

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.run_hybrid()

    def set_DiffPlane(self):
        self.le_nbins_x.setEnabled(self.ghy_diff_plane == 0 or self.ghy_diff_plane == 2)
        self.le_nbins_z.setEnabled(self.ghy_diff_plane == 1 or self.ghy_diff_plane == 2)

    def set_FocalLengthCalc(self):
         self.le_focal_length.setEnabled(self.focal_length_calc == 1)

    def set_DistanceToImageCalc(self):
         self.le_distance_to_image.setEnabled(self.distance_to_image_calc == 1)

    def set_CalculationType(self):
        self.cb_focal_length_calc.setEnabled(self.ghy_calcType != 0)
        self.le_focal_length.setEnabled(self.ghy_calcType != 0)
        self.cb_usemirrorfile.setEnabled(self.ghy_calcType == 2)
        self.select_file_box.setEnabled(self.ghy_calcType == 2)
        self.cb_profile_dimension.setEnabled(self.ghy_calcType == 2)
        self.cb_nf.setEnabled(self.ghy_calcType != 0)

        if self.ghy_calcType != 0:
            self.set_FocalLengthCalc()

        if self.ghy_calcType == 2:
            self.set_MirrorFile()


    def set_MirrorFile(self):
        self.select_file_box.setEnabled(self.ghy_usemirrorfile == 1)
        self.cb_profile_dimension.setEnabled(self.ghy_usemirrorfile == 1)

    def run_hybrid(self):
        try:
            sys.stdout = EmittingStream(textWritten=self.write_stdout)

            input_parameters = hybrid_control.HybridInputParameters()
            input_parameters.widget = self
            input_parameters.shadow_beam = self.input_beam
            input_parameters.ghy_diff_plane = self.ghy_diff_plane + 1
            input_parameters.ghy_calcType = self.ghy_calcType + 1

            input_parameters.ghy_focallength = self.ghy_focallength
            input_parameters.ghy_distance = self.ghy_distance

            #input_parameters.ghy_lengthunit = 2

            if self.ghy_usemirrorfile == 0:
                input_parameters.ghy_mirrorfile == None
            else:
                input_parameters.ghy_mirrorfile = self.ghy_mirrorfile

            input_parameters.ghy_profile_dimension = self.ghy_profile_dimension

            if self.ghy_calcType != 0:
                input_parameters.ghy_nf = self.ghy_nf
            else:
                input_parameters.ghy_nf = 0

            input_parameters.ghy_nbins_x = self.ghy_nbins_x
            input_parameters.ghy_nbins_z = self.ghy_nbins_z
            input_parameters.ghy_npeak = self.ghy_npeak
            input_parameters.ghy_fftnpts = self.ghy_fftnpts

            output_beam, calculation_parameters = hybrid_control.hy_run(input_parameters)

            self.ghy_focallength = input_parameters.ghy_focallength
            self.ghy_distance = input_parameters.ghy_distance
            self.ghy_nbins_x = input_parameters.ghy_nbins_x
            self.ghy_nbins_z = input_parameters.ghy_nbins_z
            self.ghy_npeak   = input_parameters.ghy_npeak
            self.ghy_fftnpts = input_parameters.ghy_fftnpts

            self.send("Beam", output_beam)
        except Exception as exception:
            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            QtGui.QMessageBox.critical(self, "Error", str(exception.args[0]), QtGui.QMessageBox.Ok)

            #raise exception

    def set_progress_bar(self, value):
        if value >= 100:
            self.progressBarFinished()
        elif value <=0:
            self.progressBarInit()
        else:
            self.progressBarSet(value)

    def status_message(self, message):
        self.setStatusMessage(message)

    def write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

