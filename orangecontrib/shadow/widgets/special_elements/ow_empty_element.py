import sys
from orangewidget import gui
from orangewidget.settings import Setting
from PyQt5.QtWidgets import QApplication

from orangecontrib.shadow.widgets.gui import ow_optical_element
from orangecontrib.shadow.util import ShadowOpticalElement


class EmptyElement(ow_optical_element.OpticalElement):

    name = "Empty Element"
    description = "Shadow OE: Empty Element"
    icon = "icons/empty_element.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "Optical Elements"
    keywords = ["data", "file", "load", "read"]

    def __init__(self):
        graphical_Options=ow_optical_element.GraphicalOptions(is_empty=True)

        super().__init__(graphical_Options)

        self.file_to_write_out        = 3
        self.write_out_inc_ref_angles = 0

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    ################################################################
    #
    #  SHADOW MANAGEMENT
    #
    ################################################################

    def instantiateShadowOE(self):
        return ShadowOpticalElement.create_empty_oe()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EmptyElement()
    ow.show()
    a.exec_()
    ow.saveSettings()
