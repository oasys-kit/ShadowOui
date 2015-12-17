import sys

from PyQt4 import QtGui
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QApplication, QFileDialog
from Shadow import ShadowTools as ST
from orangewidget import widget, gui
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.script.python_script import PythonConsole
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, EmittingStream, ShadowCompoundOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class FocNew  (widget.OWWidget):

    name = "FocNew"
    description = "Shadow: FocNew"
    icon = "icons/focnew.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    WIDGET_WIDTH = 950
    WIDGET_HEIGHT = 650

    want_main_area=1
    want_control_area = 1

    input_beam=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height()*0.95, self.WIDGET_HEIGHT))))


        gen_box = gui.widgetBox(self.mainArea, "Focnew Output", addSpace=True, orientation="horizontal")

        tabs_setting = gui.tabWidget(gen_box)
        tabs_setting.setFixedHeight(self.WIDGET_HEIGHT-60)
        tabs_setting.setFixedWidth(self.WIDGET_WIDTH-60)

        tab_sys = oasysgui.createTabPage(tabs_setting, "Sys Info")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.sysInfo = QtGui.QTextEdit()
        self.sysInfo.setReadOnly(True)
        self.sysInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)

        sys_box = oasysgui.widgetBox(tab_sys, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_box.layout().addWidget(self.sysInfo)

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.WIDGET_HEIGHT - 80)
        out_box.layout().addWidget(self.shadow_output)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                self.input_beam = beam




            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()
