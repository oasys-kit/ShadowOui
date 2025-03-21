import numpy

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QFont, QPalette, QColor

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from oasys.util.oasys_util import TriggerIn, TriggerOut

from orangewidget import widget
from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.widgets.gui.ow_generic_element import GenericElement

class OWBeamMovement(GenericElement):
    name = "Beam movements"
    description = "Shadow Beam Movement"
    icon = "icons/beam_movement.png"
    priority = 30.1

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},
               {"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    input_beam  = None
    output_beam = None

    want_main_area = 0

    #########################################################
    # Position
    #########################################################

    apply_flag     = Setting(1)
    translation_x  = Setting(0.0)
    translation_y  = Setting(0.0)
    translation_z  = Setting(0.0)
    rotation_x     = Setting(0.0)
    rotation_y     = Setting(0.0)
    rotation_z     = Setting(0.0)

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Move Shadow Beam", self)
        self.runaction.triggered.connect(self.moveBeam)
        self.addAction(self.runaction)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Move Shadow Beam", callback=self.moveBeam)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.resetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        #
        # tabs
        #
        self.tabs_control_area = oasysgui.tabWidget(self.controlArea)
        self.tabs_control_area.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_control_area.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_movement = oasysgui.createTabPage(self.tabs_control_area, "Movement")           # to be populated

        gui.comboBox(self.tab_movement, self, "apply_flag", label="Apply movements",
                     labelWidth=250, items=["Off", "On"], callback=self.update_panels,
                     sendSelectedValue=False, orientation="horizontal", tooltip="angles_respect_to")

        self.translation_box = oasysgui.widgetBox(self.tab_movement, "Translation", addSpace=True, orientation="vertical")
        self.rotation_box    = oasysgui.widgetBox(self.tab_movement, "Rotation", addSpace=True, orientation="vertical")


        self.le_translation_x = oasysgui.lineEdit(self.translation_box, self, "translation_x", "Translation along X", labelWidth=260, valueType=float, orientation="horizontal", tooltip="translation_x")
        self.le_translation_y = oasysgui.lineEdit(self.translation_box, self, "translation_y", "Translation along Y", labelWidth=260, valueType=float, orientation="horizontal", tooltip="translation_y")
        self.le_translation_z = oasysgui.lineEdit(self.translation_box, self, "translation_z", "Translation along Z", labelWidth=260, valueType=float, orientation="horizontal", tooltip="translation_z")

        oasysgui.lineEdit(self.rotation_box, self, "rotation_x", "Rotation along X [deg]", labelWidth=260, valueType=float, orientation="horizontal", tooltip="rotation_x")
        oasysgui.lineEdit(self.rotation_box, self, "rotation_y", "Rotation along Y [deg]", labelWidth=260, valueType=float, orientation="horizontal", tooltip="rotation_y")
        oasysgui.lineEdit(self.rotation_box, self, "rotation_z", "Rotation along Z [deg]", labelWidth=260, valueType=float, orientation="horizontal", tooltip="rotation_z")

        self.update_panels()

        gui.rubber(self.controlArea)

    def resetSettings(self):
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0

    def after_change_workspace_units(self):
        label = self.le_translation_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_translation_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_translation_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def update_panels(self):
        if self.apply_flag:
            self.translation_box.setVisible(True)
            self.rotation_box.setVisible(True)
        else:
            self.translation_box.setVisible(False)
            self.rotation_box.setVisible(False)


    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam) and \
                ShadowCongruence.checkGoodBeam(beam):
            self.input_beam = beam
        else:
            QMessageBox.critical(self, "Error", "No good rays or bad content", QMessageBox.Ok)
            return

        if self.is_automatic_run: self.moveBeam()

    def moveBeam(self):
        if not self.input_beam is None:
            def rotate(rays, theta, axis=1):
                theta1 = theta
                a1     = rays.copy()

                if axis == 1:   torot = [2, 3]
                elif axis == 2: torot = [1, 3]
                elif axis == 3: torot = [1, 2]

                costh = numpy.cos(theta1)
                sinth = numpy.sin(theta1)

                tstart = numpy.array([1, 4, 7, 16])

                for i in range(len(tstart)):
                    newaxis = axis + tstart[i] - 1
                    newaxisi = newaxis - 1
                    newtorot = torot + tstart[i] - 1
                    newtoroti = newtorot - 1

                    rays[:, newtoroti[0]] = a1[:, newtoroti[0]] * costh + a1[:, newtoroti[1]] * sinth
                    rays[:, newtoroti[1]] = -a1[:, newtoroti[0]] * sinth + a1[:, newtoroti[1]] * costh
                    rays[:, newaxisi] = a1[:, newaxisi]
            try:
                shadow_beam_out = self.input_beam.duplicate()

                if self.translation_x != 0.0: shadow_beam_out._beam.rays[:, 0] += self.translation_x
                if self.translation_y != 0.0: shadow_beam_out._beam.rays[:, 1] += self.translation_y
                if self.translation_z != 0.0: shadow_beam_out._beam.rays[:, 2] += self.translation_z

                if self.rotation_x != 0.0: rotate(shadow_beam_out._beam.rays, numpy.radians(self.rotation_x), axis=1)
                if self.rotation_y != 0.0: rotate(shadow_beam_out._beam.rays, numpy.radians(self.rotation_y), axis=2)
                if self.rotation_z != 0.0: rotate(shadow_beam_out._beam.rays, numpy.radians(self.rotation_z), axis=3)

                self.setStatusMessage("")

                self.send("Beam", shadow_beam_out)
                self.send("Trigger", TriggerIn(new_object=True))
            except Exception as e:
                self.setStatusMessage("")

                QMessageBox.critical(self, "Error", str(e), QMessageBox.Ok)