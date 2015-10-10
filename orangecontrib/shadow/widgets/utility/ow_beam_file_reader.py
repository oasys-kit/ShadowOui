import os

from oasys.widgets import widget
from orangewidget import gui
from orangewidget.settings import Setting

from orangecontrib.shadow.util.shadow_util import ShadowGui
from orangecontrib.shadow.util.shadow_objects import ShadowBeam


class BeamFileReader(widget.OWWidget):
    name = "Shadow File Reader"
    description = "Utility: Shadow File Reader"
    icon = "icons/beam_file_reader.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 2
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    want_main_area = 0

    beam_file_name = Setting("")

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"}, ]

    def __init__(self):
        self.setFixedWidth(590)
        self.setFixedHeight(150)

        left_box_1 = ShadowGui.widgetBox(self.controlArea, "Shadow File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=60)

        figure_box = ShadowGui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=50)

        self.le_beam_file_name = ShadowGui.lineEdit(figure_box, self, "beam_file_name", "Shadow File Name",
                                                    labelWidth=120, valueType=str, orientation="horizontal")
        self.le_beam_file_name.setFixedWidth(330)

        pushButton = gui.button(figure_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        gui.separator(left_box_1, height=20)

        button = gui.button(self.controlArea, self, "Read Shadow File", callback=self.read_file)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_beam_file_name.setText(ShadowGui.selectFileFromDialog(self, self.beam_file_name, "Open Shadow File"))

    def read_file(self):
        self.setStatusMessage("")

        beam_out = ShadowBeam()
        beam_out.loadFromFile(self.beam_file_name)

        path, file_name = os.path.split(self.beam_file_name)

        self.setStatusMessage("Current: " + file_name)

        self.send("Beam", beam_out)

