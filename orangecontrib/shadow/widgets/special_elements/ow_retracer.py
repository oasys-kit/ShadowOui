from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import TriggerIn

from orangecontrib.shadow.util.shadow_objects import ShadowOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.widgets.gui.ow_generic_element import GenericElement

class OWRetracer(GenericElement):
    name = "Retrace"
    id = "retrace"
    description = "Retrace"
    icon = "icons/retracer.png"
    priority = 20
    category = ""
    keywords = ["shadow", "gaussian"]

    inputs = [("Beam", ShadowBeam, "setBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},
               {"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    retrace_distance = Setting(0.0)

    input_beam = None

    def __init__(self):
        super().__init__()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Retrace", callback=self.retrace)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        gui.separator(self.controlArea)

        box = oasysgui.widgetBox(self.controlArea, "", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=550)

        main_box = oasysgui.widgetBox(box, "Shadow Beam Retrace", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=70)

        self.le_retrace_distance = oasysgui.lineEdit(main_box, self, "retrace_distance", "Retrace to ", labelWidth=280, valueType=float, orientation="horizontal")

    def setBeam(self, input_beam):
        if ShadowCongruence.checkEmptyBeam(input_beam):
            self.input_beam = input_beam

            if self.is_automatic_run:
                self.retrace()

    def after_change_workspace_units(self):
        label = self.le_retrace_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def retrace(self):
        try:
            if not self.input_beam is None:
                output_beam = self.input_beam.duplicate(history=True)

                empty_element = ShadowOpticalElement.create_empty_oe()

                empty_element._oe.DUMMY = 1.0 # self.workspace_units_to_cm

                empty_element._oe.T_SOURCE     = 0.0
                empty_element._oe.T_IMAGE      = self.retrace_distance
                empty_element._oe.T_INCIDENCE  = 0.0
                empty_element._oe.T_REFLECTION = 180.0
                empty_element._oe.ALPHA        = 0.0

                empty_element._oe.FWRITE = 3
                empty_element._oe.F_ANGLE = 0

                output_beam = ShadowBeam.traceFromOE(output_beam, empty_element, history=True)

                self.setStatusMessage("Plotting Results")

                self.plot_results(output_beam)

                self.setStatusMessage("")
                self.progressBarFinished()

                self.send("Beam", output_beam)
                self.send("Trigger", TriggerIn(new_object=True))
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception
