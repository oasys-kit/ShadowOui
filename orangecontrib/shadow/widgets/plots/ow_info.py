import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QFileDialog
from Shadow import ShadowTools as ST
from orangewidget import gui
from oasys.widgets import gui as oasysgui, widget
from oasys.util.oasys_util import EmittingStream

from orangecontrib.shadow.util.python_script import PythonConsole
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowCompoundOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

from Shadow.ShadowLibExtensions import CompoundOE

class Info(widget.OWWidget):

    name = "Info"
    description = "Display Data: Info"
    icon = "icons/info.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 4
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

        window_width  = round(min(geom.width()*0.98, self.WIDGET_WIDTH))
        window_height = round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))

        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               window_width,
                               window_height))

        gen_box = gui.widgetBox(self.mainArea, "Beamline Info", addSpace=True, orientation="horizontal")

        tabs_setting = oasysgui.tabWidget(gen_box)
        tabs_setting.setFixedHeight(self.WIDGET_HEIGHT-60)
        tabs_setting.setFixedWidth(self.WIDGET_WIDTH-60)

        tab_sys = oasysgui.createTabPage(tabs_setting, "Sys Info")
        tab_sys_plot_side = oasysgui.createTabPage(tabs_setting, "Sys Plot (Side View)")
        tab_sys_plot_top = oasysgui.createTabPage(tabs_setting, "Sys Plot (Top View)")
        tab_mir = oasysgui.createTabPage(tabs_setting, "OE Info")
        tab_sou = oasysgui.createTabPage(tabs_setting, "Source Info")
        tab_dis = oasysgui.createTabPage(tabs_setting, "Distances Summary")
        tab_scr = oasysgui.createTabPage(tabs_setting, "Python Script")
        tab_out = oasysgui.createTabPage(tabs_setting, "System Output")

        self.sysInfo = oasysgui.textArea()
        self.sysInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)

        self.sysPlotSide = oasysgui.plotWindow(tab_sys_plot_side)
        self.sysPlotSide.setMaximumHeight(self.WIDGET_HEIGHT-100)

        self.sysPlotTop = oasysgui.plotWindow(tab_sys_plot_top)
        self.sysPlotTop.setMaximumHeight(self.WIDGET_HEIGHT-100)

        self.mirInfo = oasysgui.textArea()
        self.mirInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)
        self.sourceInfo = oasysgui.textArea()
        self.sourceInfo.setMaximumHeight(self.WIDGET_HEIGHT-100)
        self.distancesSummary = oasysgui.textArea()
        self.distancesSummary.setMaximumHeight(self.WIDGET_HEIGHT-100)
        self.pythonScript = oasysgui.textArea(readOnly=False)
        self.pythonScript.setMaximumHeight(self.WIDGET_HEIGHT - 300)

        sys_box = oasysgui.widgetBox(tab_sys, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_box.layout().addWidget(self.sysInfo)

        sys_plot_side_box = oasysgui.widgetBox(tab_sys_plot_side, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_plot_side_box.layout().addWidget(self.sysPlotSide)

        sys_plot_top_box = oasysgui.widgetBox(tab_sys_plot_top, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        sys_plot_top_box.layout().addWidget(self.sysPlotTop)

        mir_box = oasysgui.widgetBox(tab_mir, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        mir_box.layout().addWidget(self.mirInfo)

        source_box = oasysgui.widgetBox(tab_sou, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        source_box.layout().addWidget(self.sourceInfo)

        dist_box = oasysgui.widgetBox(tab_dis, "", addSpace=True, orientation="horizontal", height = self.WIDGET_HEIGHT-80, width = self.WIDGET_WIDTH-80)
        dist_box.layout().addWidget(self.distancesSummary)

        script_box = oasysgui.widgetBox(tab_scr, "", addSpace=True, orientation="vertical", height=self.WIDGET_HEIGHT - 80, width=self.WIDGET_WIDTH - 80)
        script_box.layout().addWidget(self.pythonScript)

        console_box = oasysgui.widgetBox(script_box, "", addSpace=True, orientation="vertical",
                                          height=150, width=self.WIDGET_WIDTH - 80)

        self.console = PythonConsole(self.__dict__, self)
        console_box.layout().addWidget(self.console)

        self.shadow_output = oasysgui.textArea()

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=self.WIDGET_HEIGHT - 80)
        out_box.layout().addWidget(self.shadow_output)

        #############################

        button_box = oasysgui.widgetBox(tab_scr, "", addSpace=True, orientation="horizontal")

        gui.button(button_box, self, "Run Script", callback=self.execute_script, height=40)
        gui.button(button_box, self, "Save Script to File", callback=self.save_script, height=40)

    def execute_script(self):
        self._script = str(self.pythonScript.toPlainText())
        self.console.write("\nRunning script:\n")
        self.console.push("exec(_script)")
        self.console.new_prompt(sys.ps1)

    def save_script(self):
        file_name = QFileDialog.getSaveFileName(self, "Save File to Disk", ".", "*.py")[0]

        if not file_name is None:
            if not file_name.strip() == "":
                file = open(file_name, "w")
                file.write(str(self.pythonScript.toPlainText()))
                file.close()

                QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                              "File " + file_name + " written to disk",
                                              QtWidgets.QMessageBox.Ok)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                self.input_beam = beam

                optical_element_list_start = []
                optical_element_list_end = []

                self.sysInfo.setText("")
                self.mirInfo.setText("")
                self.sourceInfo.setText("")
                self.distancesSummary.setText("")
                self.pythonScript.setText("")

                for history_element in self.input_beam.getOEHistory():
                    if not history_element._shadow_source_start is None:
                        optical_element_list_start.append(history_element._shadow_source_start.src)
                    elif not history_element._shadow_oe_start is None:
                        optical_element_list_start.append(history_element._shadow_oe_start._oe)

                    if not history_element._shadow_source_end is None:
                        optical_element_list_end.append(history_element._shadow_source_end.src)
                    elif not history_element._shadow_oe_end is None:
                        optical_element_list_end.append(history_element._shadow_oe_end._oe)


                    if not history_element._shadow_source_end is None:
                        try:
                            self.sourceInfo.append(history_element._shadow_source_end.src.sourcinfo())
                        except:
                            self.sourceInfo.append("Problem in calculating Source Info:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))
                    elif not history_element._shadow_oe_end is None:
                        try:
                            if isinstance(history_element._shadow_oe_end._oe, CompoundOE):
                                self.mirInfo.append(history_element._shadow_oe_end._oe.mirinfo())
                            else:
                                self.mirInfo.append(history_element._shadow_oe_end._oe.mirinfo(title="O.E. #" + str(history_element._oe_number)))
                        except:
                            self.sourceInfo.append("Problem in calculating Mir Info for O.E. #:" + str(history_element._oe_number) + "\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

                coe_end = ShadowCompoundOpticalElement.create_compound_oe(workspace_units_to_cm=self.workspace_units_to_cm)
                for oe in optical_element_list_end:
                    coe_end._oe.append(oe)

                try:
                    self.sysInfo.setText(coe_end._oe.sysinfo())
                except:
                    self.distancesSummary.setText("Problem in calculating SysInfo:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

                try:
                    dic = coe_end._oe.syspositions()

                    self.sysPlotSide.addCurve(dic["optical_axis_y"],dic["optical_axis_z"],symbol='o',replace=True)
                    self.sysPlotSide.setGraphXLabel("Y [%s]"%self.workspace_units_label)
                    self.sysPlotSide.setGraphYLabel("Z [%s]"%self.workspace_units_label)
                    self.sysPlotSide.setGraphTitle("Side View of optical axis")
                    self.sysPlotSide.replot()

                    self.sysPlotTop.addCurve(dic["optical_axis_y"],dic["optical_axis_x"],symbol='o',replace=True)
                    self.sysPlotTop.setGraphXLabel("Y [%s]"%self.workspace_units_label)
                    self.sysPlotTop.setGraphYLabel("X [%s]"%self.workspace_units_label)
                    self.sysPlotTop.setGraphTitle("Top View of optical axis")
                    self.sysPlotTop.replot()

                except:
                    self.distancesSummary.setText("Problem in calculating SysPlot:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

                try:
                    self.distancesSummary.setText(coe_end._oe.info())
                except:
                    self.distancesSummary.setText("Problem in calculating Distance Summary:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))

                try:
                    self.pythonScript.setText(ST.make_python_script_from_list(optical_element_list_start))
                except:
                    self.pythonScript.setText("Problem in writing python script:\n" + str(sys.exc_info()[0]) + ": " + str(sys.exc_info()[1]))
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()
