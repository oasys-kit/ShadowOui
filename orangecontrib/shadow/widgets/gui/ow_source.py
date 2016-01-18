__author__ = 'labx'

from PyQt4.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget import widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowTriggerOut, ShadowBeam
from orangecontrib.shadow.widgets.gui import ow_generic_element


class Source(ow_generic_element.GenericElement):

    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", ShadowTriggerOut, "sendNewBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    file_to_write_out = Setting(0)

    want_main_area=1

    def __init__(self, show_automatic_box=False):
        super().__init__(show_automatic_box=show_automatic_box)

        self.runaction = widget.OWAction("Run Shadow/Source", self)
        self.runaction.triggered.connect(self.runShadowSource)
        self.addAction(self.runaction)

        self.general_options_box.setVisible(False)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/Source", callback=self.runShadowSource)
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

    def get_write_file_options(self):
        write_start_file = 0
        write_end_file = 0

        if self.file_to_write_out == 1:
            write_start_file = 1
            write_end_file = 1

        return write_start_file, write_end_file
