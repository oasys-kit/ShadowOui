import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSettings
from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui, congruence
from oasys.widgets.widget import OWWidget

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class BeamFileWriter(OWWidget):
    name = "Shadow File Writer"
    description = "Utility: Shadow File Writer"
    icon = "icons/beam_file_writer.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 3
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    beam_file_name = Setting("")
    is_automatic_run= Setting(1)

    send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

    if send_footprint_beam:
        inputs = [("Input Beam", object, "setBeam")]
    else:
        inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"}, ]

    input_beam = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Write Shadow File", self)
        self.runaction.triggered.connect(self.write_file)
        self.addAction(self.runaction)

        self.setFixedWidth(590)
        self.setFixedHeight(190)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Shadow File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=110)

        gui.checkBox(left_box_1, self, 'is_automatic_run', 'Automatic Execution')

        gui.separator(left_box_1, height=10)

        figure_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=35)

        self.le_beam_file_name = oasysgui.lineEdit(figure_box, self, "beam_file_name", "Shadow File Name",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_beam_file_name.setFixedWidth(330)

        gui.button(figure_box, self, "...", callback=self.selectFile)

        button = gui.button(self.controlArea, self, "Write Shadow File", callback=self.write_file)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_beam_file_name.setText(oasysgui.selectFileFromDialog(self, self.beam_file_name, "Open Shadow File"))

    def setBeam(self, beam):
        send_footprint_beam = QSettings().value("output/send-footprint", 0, int) == 1

        if send_footprint_beam and isinstance(beam, list):
            self.input_beam = beam[1]
        elif ShadowCongruence.checkEmptyBeam(beam) and ShadowCongruence.checkGoodBeam(beam):
            self.input_beam = beam
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No good rays or bad content", QtWidgets.QMessageBox.Ok)
            return

        if self.is_automatic_run: self.write_file()

    def write_file(self):
        self.setStatusMessage("")

        try:
            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    if congruence.checkFileName(self.beam_file_name):
                        self.input_beam.writeToFile(self.beam_file_name)

                        path, file_name = os.path.split(self.beam_file_name)

                        self.setStatusMessage("File Out: " + file_name)

                        self.send("Beam", self.input_beam)
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", "No good rays or bad content", QtWidgets.QMessageBox.Ok)
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception), QtWidgets.QMessageBox.Ok)


