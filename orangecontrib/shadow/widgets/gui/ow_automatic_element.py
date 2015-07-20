import sys

from oasys.widgets import widget

from Orange.widgets import gui
from Orange.widgets.settings import Setting

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QRect

from orangecontrib.shadow.util.shadow_util import ConfirmDialog

import xraylib

class AutomaticElement(widget.OWWidget):
    is_weird_shadow_bug_fixed = False

    want_main_area=1

    is_automatic_run = Setting(True)
    trace_shadow = Setting(False)

    error_id = 0
    warning_id = 0
    info_id = 0

    MAX_WIDTH = 1650
    MAX_HEIGHT = 880

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        box = gui.widgetBox(self.controlArea, "General Options", addSpace=True, orientation="horizontal")

        if show_automatic_box :
            gui.checkBox(box, self, 'is_automatic_run', 'Automatic Execution')

        gui.checkBox(box, self, 'trace_shadow', 'Display Shadow Output')


    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    #########################################################
    #
    # This xraylib call prevents an anomalous behaviour of
    # SHADOW due to some unexplained python problem (apparently on the C-binder).
    # It happens sometimes after installing new non-pip libraries
    # I don't know how and why, but this call to xraylib removes the
    # problem
    #
    #########################################################

    def fixWeirdShadowBug(self):
        if not AutomaticElement.is_weird_shadow_bug_fixed:
            try:
                xraylib.Refractive_Index_Re("LaB6", 10000, 4)
            except:
                pass

            AutomaticElement.is_weird_shadow_bug_fixed = True

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = AutomaticElement()
    ow.show()
    a.exec_()
    ow.saveSettings()