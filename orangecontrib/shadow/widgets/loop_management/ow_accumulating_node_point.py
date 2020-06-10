import copy
import numpy
import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import TriggerIn


from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

class AccumulatingLoopPoint(AutomaticElement):
    name = "Beam Accumulating Point"
    description = "User Defined: Beam Accumulating Point"
    icon = "icons/beam_accumulating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Accumulated Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": TriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    want_main_area = 0

    number_of_accumulated_rays = Setting(10000)
    kind_of_accumulation = Setting(0)

    current_number_of_rays = 0
    current_intensity = 0
    current_number_of_total_rays = 0
    current_number_of_lost_rays = 0

    keep_go_rays = Setting(1)

    #################################
    process_last = True
    #################################

    def __init__(self):
        super().__init__()

        self.setFixedWidth(570)
        self.setFixedHeight(410)

        self.controlArea.setFixedWidth(560)

        button_box = gui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal")

        self.start_button = gui.button(button_box, self, "Send Beam", callback=self.sendSignal)
        self.start_button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Accumulation", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Accumulating Loop Management", addSpace=False, orientation="vertical", height=260)

        gui.comboBox(left_box_1, self, "kind_of_accumulation", label="Accumulated Quantity", labelWidth=350,
                     items=["Number of Good Rays ", "Intensity of Good Rays"],
                     callback=self.set_KindOfAccumulation,
                     sendSelectedValue=False, orientation="horizontal")

        self.left_box_1_1 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", height=35)
        self.left_box_1_2 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical", height=35)

        oasysgui.lineEdit(self.left_box_1_1, self, "number_of_accumulated_rays", "Number of accumulated good rays\n(before sending signal)", labelWidth=350, valueType=float,
                           orientation="horizontal")

        oasysgui.lineEdit(self.left_box_1_2, self, "number_of_accumulated_rays", "Intenisty of accumulated good rays\n(before sending signal)", labelWidth=350, valueType=float,
                           orientation="horizontal")

        self.set_KindOfAccumulation()

        gui.comboBox(left_box_1, self, "keep_go_rays", label="Remove lost rays from beam", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.separator(left_box_1)

        le = oasysgui.lineEdit(left_box_1, self, "current_number_of_rays", "Current number of good rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        font = QtGui.QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QtGui.QPalette(le.palette())  # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        le.setPalette(palette)

        self.le_current_intensity = oasysgui.lineEdit(left_box_1, self, "current_intensity", "Current intensity", labelWidth=350, valueType=float, orientation="horizontal")
        self.le_current_intensity.setReadOnly(True)
        font = QtGui.QFont(self.le_current_intensity.font())
        font.setBold(True)
        self.le_current_intensity.setFont(font)
        palette = QtGui.QPalette(le.palette())  # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_current_intensity.setPalette(palette)

        le = oasysgui.lineEdit(left_box_1, self, "current_number_of_lost_rays", "Current number of lost rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        palette = QtGui.QPalette(le.palette())  # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark red'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        le.setPalette(palette)

        le = oasysgui.lineEdit(left_box_1, self, "current_number_of_total_rays", "Current number of total rays", labelWidth=350, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        palette = QtGui.QPalette(le.palette())  # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('black'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        le.setPalette(palette)


        gui.rubber(self.controlArea)

    def set_KindOfAccumulation(self):
        self.left_box_1_1.setVisible(self.kind_of_accumulation==0)
        self.left_box_1_2.setVisible(self.kind_of_accumulation==1)

    def sendSignal(self):
        self.send("Accumulated Beam", self.input_beam)
        self.send("Trigger", TriggerIn(interrupt=True))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the accumulated beam"):
            self.current_number_of_rays = 0
            self.current_intensity = 0.0
            self.current_number_of_lost_rays = 0
            self.current_number_of_total_rays = 0
            self.input_beam = None

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            proceed = True

            if not ShadowCongruence.checkGoodBeam(beam):
                if not ConfirmDialog.confirmed(parent=self, message="Beam contains bad values, skip it?"):
                    proceed = False

            if proceed:
                scanned_variable_data = beam.scanned_variable_data

                go = numpy.where(beam._beam.rays[:, 9] == 1)

                nr_good = len(beam._beam.rays[go])
                nr_total = len(beam._beam.rays)
                nr_lost = nr_total - nr_good
                intensity = beam._beam.histo1(1, nolost=1, ref=23)['intensity']

                self.current_number_of_rays += nr_good
                self.current_intensity += intensity
                self.le_current_intensity.setText("{:10.3f}".format(self.current_intensity))
                self.current_number_of_lost_rays += nr_lost
                self.current_number_of_total_rays += nr_total

                if (self.kind_of_accumulation == 0 and self.current_number_of_rays <= self.number_of_accumulated_rays) or \
                   (self.kind_of_accumulation == 1 and self.current_intensity <= self.number_of_accumulated_rays):
                    if self.keep_go_rays == 1:
                        beam._beam.rays = copy.deepcopy(beam._beam.rays[go])

                    if not self.input_beam is None:
                        self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                    else:
                        beam._beam.rays[:, 11] = numpy.arange(1, len(beam._beam.rays) + 1, 1) # ray_index
                        self.input_beam = beam

                    self.input_beam.setScanningData(scanned_variable_data)

                    self.send("Trigger", TriggerIn(new_object=True))
                else:
                    if self.is_automatic_run:
                        self.sendSignal()

                        self.current_number_of_rays = 0
                        self.current_intensity = 0.0
                        self.current_number_of_lost_rays = 0
                        self.current_number_of_total_rays = 0
                        self.input_beam = None
                    else:
                        QtWidgets.QMessageBox.critical(self, "Error",
                                                   "Number of Accumulated Rays reached, please push \'Send Signal\' button",
                                                   QtWidgets.QMessageBox.Ok)


if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = AccumulatingLoopPoint()
    ow.show()
    a.exec_()
    ow.saveSettings()
