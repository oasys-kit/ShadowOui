
from oasys.widgets import widget
from Orange.widgets import gui
from Orange.widgets.settings import Setting
from orangecontrib.shadow.util.shadow_util import ShadowGui
from orangecontrib.shadow.util.shadow_objects import ShadowBeam


from PyQt4 import QtGui


class BeamFileReader(widget.OWWidget):
    name = "Beam File Reader"
    description = "Utility: Beam File Reader"
    icon = "icons/beam_file_reader.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
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

        left_box_1 = ShadowGui.widgetBox(self.controlArea, "Beam File Selection", addSpace=True, orientation="vertical",
                                         width=570, height=60)

        figure_box = ShadowGui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal", width=550, height=50)

        self.le_beam_file_name = ShadowGui.lineEdit(figure_box, self, "beam_file_name", "Beam File Name",
                                                    labelWidth=100, valueType=str, orientation="horizontal")
        self.le_beam_file_name.setFixedWidth(350)

        pushButton = gui.button(figure_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        gui.separator(left_box_1, height=20)

        button = gui.button(self.controlArea, self, "Generate Beam", callback=self.calculate)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectFile(self):
        self.le_beam_file_name.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Open Beam File", ".", "*.*"))


    def calculate(self):
        beam_out = ShadowBeam()
        beam_out.loadFromFile(self.beam_file_name)

        self.send("Beam", beam_out)

