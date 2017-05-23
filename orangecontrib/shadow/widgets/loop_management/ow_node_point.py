import sys

from orangewidget.widget import OWAction
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui
from oasys.widgets.gui import ConfirmDialog

from orangewidget import gui
from PyQt5 import QtGui, QtWidgets
from orangewidget.settings import Setting
from orangecontrib.shadow.util.shadow_objects import ShadowTriggerIn, ShadowTriggerOut

class LoopPoint(widget.OWWidget):

    name = "Loop Point"
    description = "User Defined: LoopPoint"
    icon = "icons/cycle.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "User Defined"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", ShadowTriggerIn, "passTrigger")]

    outputs = [{"name":"Trigger",
                "type":ShadowTriggerOut,
                "doc":"Trigger",
                "id":"Trigger"}]
    want_main_area = 0

    number_of_new_beams = Setting(1)
    current_new_beam = 0
    run_loop = True

    #################################
    process_last = True
    #################################

    def __init__(self):
        self.runaction = OWAction("Start Loop", self)
        self.runaction.triggered.connect(self.startLoop)
        self.addAction(self.runaction)

        self.runaction = OWAction("Interrupt", self)
        self.runaction.triggered.connect(self.stopLoop)
        self.addAction(self.runaction)

        self.setFixedWidth(400)
        self.setFixedHeight(185)

        button_box = gui.widgetBox(self.controlArea, "", addSpace=True, orientation="horizontal")

        self.start_button = gui.button(button_box, self, "Start Loop", callback=self.startLoop)
        self.start_button.setFixedHeight(45)

        stop_button = gui.button(button_box, self, "Interrupt", callback=self.stopLoop)
        stop_button.setFixedHeight(45)
        font = QtGui.QFont(stop_button.font())
        font.setBold(True)
        stop_button.setFont(font)
        palette = QtGui.QPalette(stop_button.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor('red'))
        stop_button.setPalette(palette) # assign new palette

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Loop Management", addSpace=True, orientation="vertical", width=380, height=100)

        oasysgui.lineEdit(left_box_1, self, "number_of_new_beams", "Number of new Beams", labelWidth=250, valueType=int, orientation="horizontal")

        self.le_current_new_beam = oasysgui.lineEdit(left_box_1, self, "current_new_beam", "Current New Beam", labelWidth=250, valueType=int, orientation="horizontal")
        self.le_current_new_beam.setReadOnly(True)
        font = QtGui.QFont(self.le_current_new_beam.font())
        font.setBold(True)
        self.le_current_new_beam.setFont(font)
        palette = QtGui.QPalette(self.le_current_new_beam.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        self.le_current_new_beam.setPalette(palette)


        gui.rubber(self.controlArea)

    def startLoop(self):
        self.current_new_beam = 1
        self.start_button.setEnabled(False)
        self.setStatusMessage("Running Beam " + str(self.current_new_beam) + " of " + str(self.number_of_new_beams))
        self.send("Trigger", ShadowTriggerOut(new_beam=True))

    def stopLoop(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Interruption of the Loop?"):
            self.run_loop = False
            self.setStatusMessage("Interrupted by user")
            #self.warning("Interrupted by user")

    def passTrigger(self, trigger):
        if self.run_loop:
            if trigger:
                if trigger.interrupt:
                    self.current_new_beam = 0
                    self.start_button.setEnabled(True)
                    self.setStatusMessage("")
                    self.send("Trigger", ShadowTriggerOut(new_beam=False))
                elif trigger.new_beam:
                    if self.current_new_beam < self.number_of_new_beams:
                        self.current_new_beam += 1
                        self.setStatusMessage("Running Beam " + str(self.current_new_beam) + " of " + str(self.number_of_new_beams))
                        self.start_button.setEnabled(False)
                        self.send("Trigger", ShadowTriggerOut(new_beam=True))
                    else:
                        self.current_new_beam = 0
                        self.start_button.setEnabled(True)
                        self.setStatusMessage("")
                        self.send("Trigger", ShadowTriggerOut(new_beam=False))
        else:
            self.current_new_beam = 0
            self.start_button.setEnabled(True)
            self.send("Trigger", ShadowTriggerOut(new_beam=False))
            #self.warning()
            self.setStatusMessage("")
            self.run_loop = True

if __name__ == "__main__":
    a = QtGui.QApplication(sys.argv)
    ow = LoopPoint()
    ow.show()
    a.exec_()
    ow.saveSettings()