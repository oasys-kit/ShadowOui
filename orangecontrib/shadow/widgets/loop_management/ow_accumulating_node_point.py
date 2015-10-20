import copy
import numpy
import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets.gui import ConfirmDialog

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowTriggerIn
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

class AccumulatingLoopPoint(AutomaticElement):
    name = "Beam Accumulating Point"
    description = "User Defined: Beam Accumulating Point"
    icon = "icons/beam_accumulating.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 3
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Accumulated Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": ShadowTriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    want_main_area = 0

    number_of_accumulated_rays = Setting(10000)

    current_number_of_rays = 0
    current_number_of_total_rays = 0
    current_number_of_lost_rays = 0

    keep_go_rays = Setting(1)

    #################################
    process_last = True
    #################################

    def __init__(self):
        super().__init__()

        self.setFixedWidth(500)
        self.setFixedHeight(350)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Accumulating Loop Management", addSpace=True, orientation="vertical", height=200)

        oasysgui.lineEdit(left_box_1, self, "number_of_accumulated_rays", "Number of accumulated good rays\n(before sending signal)", labelWidth=350, valueType=int,
                           orientation="horizontal")

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

        gui.rubber(self.controlArea)

    def sendSignal(self):
        self.send("Accumulated Beam", self.input_beam)
        self.send("Trigger", ShadowTriggerIn(new_beam=True))

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the accumulated beam"):
            self.current_number_of_rays = 0
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
                go = numpy.where(beam._beam.rays[:, 9] == 1)

                nr_good = len(beam._beam.rays[go])
                nr_total = len(beam._beam.rays)
                nr_lost = nr_total - nr_good

                self.current_number_of_rays = self.current_number_of_rays + nr_good
                self.current_number_of_lost_rays = self.current_number_of_lost_rays + nr_lost
                self.current_number_of_total_rays = self.current_number_of_total_rays + nr_total

                if self.current_number_of_rays <= self.number_of_accumulated_rays:
                    if self.keep_go_rays == 1:
                        beam._beam.rays = copy.deepcopy(beam._beam.rays[go])

                    if not self.input_beam is None:
                        self.input_beam = ShadowBeam.mergeBeams(self.input_beam, beam)
                    else:
                        self.input_beam = beam

                    self.send("Trigger", ShadowTriggerIn(new_beam=True))
                else:
                    if self.is_automatic_run:
                        self.sendSignal()

                        self.current_number_of_rays = 0
                        self.current_number_of_lost_rays = 0
                        self.current_number_of_total_rays = 0
                        self.input_beam = None
                    else:
                        QtGui.QMessageBox.critical(self, "Error",
                                                   "Number of Accumulated Rays reached, please push \'Send Signal\' button",
                                                   QtGui.QMessageBox.Ok)


if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = AccumulatingLoopPoint()
    ow.show()
    a.exec_()
    ow.saveSettings()
