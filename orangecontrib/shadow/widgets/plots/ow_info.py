import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication, QFileDialog
from PyQt4.QtCore import QRect

from orangewidget import widget, gui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowGui
from orangecontrib.shadow.util.python_script import PythonConsole

from Shadow import ShadowTools as ST

class Info(widget.OWWidget):

    name = "Info"
    description = "Display Data: Info"
    icon = "icons/info.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 3
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    WIDGET_WIDTH = 950
    WIDGET_HEIGHT = 650

    want_main_area=1
    want_control_area = 0

    input_beam=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height()*0.95, self.WIDGET_HEIGHT))))


        gen_box = gui.widgetBox(self.mainArea, "Beamline Info", addSpace=True, orientation="horizontal")

        tabs_setting = gui.tabWidget(gen_box)
        tabs_setting.setFixedHeight(self.WIDGET_HEIGHT-60)
        tabs_setting.setFixedWidth(self.WIDGET_WIDTH-60)

        tab_sys = ShadowGui.createTabPage(tabs_setting, "Sys Info")
        tab_mir = ShadowGui.createTabPage(tabs_setting, "OE Info")
        tab_sou = ShadowGui.createTabPage(tabs_setting, "Source Info")
        tab_scr = ShadowGui.createTabPage(tabs_setting, "Python Script")
        tab_out = ShadowGui.createTabPage(tabs_setting, "System Output")

        self.sysInfo = QtGui.QTextEdit()
        self.sysInfo.setReadOnly(True)
        self.sysInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)
        self.mirInfo = QtGui.QTextEdit()
        self.mirInfo.setReadOnly(True)
        self.mirInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)
        self.sourceInfo = QtGui.QTextEdit()
        self.sourceInfo.setReadOnly(True)
        self.sourceInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)
        self.pythonScript = QtGui.QTextEdit()
        self.pythonScript.setReadOnly(False)  # asked by Manolo
        self.pythonScript.setMaximumHeight(self.WIDGET_HEIGHT - 300)

        sys_box = ShadowGui.widgetBox(tab_sys, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_box.layout().addWidget(self.sysInfo)

        mir_box = ShadowGui.widgetBox(tab_mir, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        mir_box.layout().addWidget(self.mirInfo)

        source_box = ShadowGui.widgetBox(tab_sou, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        source_box.layout().addWidget(self.sourceInfo)

        script_box = ShadowGui.widgetBox(tab_scr, "", addSpace=True, orientation="vertical", height=self.WIDGET_HEIGHT - 80, width=self.WIDGET_WIDTH - 80)
        script_box.layout().addWidget(self.pythonScript)

        console_box = ShadowGui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
                                          height=150, width=self.WIDGET_WIDTH - 80)

        self.console = PythonConsole(self.__dict__, self)
        console_box.layout().addWidget(self.console)

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = ShadowGui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.WIDGET_HEIGHT - 80)
        out_box.layout().addWidget(self.shadow_output)

        #############################

        button_box = ShadowGui.widgetBox(tab_scr, "", addSpace=True, orientation="horizontal")

        gui.button(button_box, self, "Run Script", callback=self.execute_script, height=40)
        gui.button(button_box, self, "Save Script to File", callback=self.save_script, height=40)

    def execute_script(self):
        self._script = str(self.pythonScript.toPlainText())
        self.console.write("\nRunning script:\n")
        self.console.push("exec(_script)")
        self.console.new_prompt(sys.ps1)

    def save_script(self):
        file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", ".", "*.py")

        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.pythonScript.toPlainText()))
                file.close()

                QtGui.QMessageBox.information(self, "QMessageBox.information()",
                                              "File " + file_name + " written to disk",
                                              QtGui.QMessageBox.Ok)

    def setBeam(self, beam):
        if ShadowGui.checkEmptyBeam(beam):
            if ShadowGui.checkGoodBeam(beam):
                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                self.input_beam = beam

                self.sysInfo.setText("\n\n\n\n\nNot Available")

                optical_element_list = []

                for history_element in self.input_beam.getOEHistory():
                    if not history_element.shadow_source_start is None:
                        optical_element_list.append(history_element.shadow_source_start.src)
                    elif not history_element.shadow_oe_start is None:
                        optical_element_list.append(history_element.shadow_oe_start.oe)

                    if not history_element.shadow_source_end is None:
                        self.sourceInfo.append(history_element.shadow_source_end.src.sourcinfo())
                    elif not history_element.shadow_oe_end is None:
                        self.mirInfo.append(history_element.shadow_oe_end.oe.mirinfo(title="O.E. #" + str(history_element.oe_number)))

                self.pythonScript.setText(ST.make_python_script_from_list(optical_element_list))
            else:
                QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()
