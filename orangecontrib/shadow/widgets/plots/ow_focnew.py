import sys
import numpy
from PyQt4 import QtGui
from PyQt4.QtCore import QRect
from PyQt4.QtGui import QApplication
from Shadow import ShadowTools as ST
from orangewidget import widget, gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, EmittingStream
from orangecontrib.shadow.util.shadow_util import ShadowCongruence
from orangecontrib.shadow.widgets.gui import ow_automatic_element

from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow

class FocNew(ow_automatic_element.AutomaticElement):

    name = "FocNew"
    description = "Shadow: FocNew"
    icon = "icons/focnew.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    WIDGET_WIDTH = 1260
    WIDGET_HEIGHT = 700

    IMAGE_WIDTH = 800
    IMAGE_HEIGHT = 500

    want_main_area=1
    want_control_area = 1

    input_beam=None

    mode = Setting(0)
    center_x = Setting(0.0)
    center_z = Setting(0.0)

    plot_canvas=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height()*0.95, self.WIDGET_HEIGHT))))

        general_box = oasysgui.widgetBox(self.controlArea, "General Settings", addSpace=True, orientation="vertical", width=410, height=150)

        gui.comboBox(general_box, self, "mode", label="Mode", labelWidth=250,
                                     items=["Center at Origin",
                                            "Center at Baricenter",
                                            "Define Center..."],
                                     callback=self.set_Center, sendSelectedValue=False, orientation="horizontal")

        self.center_box = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)
        self.center_box_empty = oasysgui.widgetBox(general_box, "", addSpace=True, orientation="vertical", width=390, height=100)

        gui.separator(self.center_box)

        oasysgui.lineEdit(self.center_box, self, "center_x", "Center X [cm]", labelWidth=220, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.center_box, self, "center_z", "Center Z [cm]", labelWidth=220, valueType=float, orientation="horizontal")

        self.set_Center()

        gui.separator(self.controlArea, height=400)

        gui.button(self.controlArea, self, "Calculate", callback=self.calculate, height=45)

        gen_box = gui.widgetBox(self.mainArea, "Focnew Output", addSpace=True, orientation="horizontal")

        tabs_setting = gui.tabWidget(gen_box)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT+5)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_info = oasysgui.createTabPage(tabs_setting, "Focnew Info")
        tab_scan = oasysgui.createTabPage(tabs_setting, "Focnew Scan")

        self.focnewInfo = QtGui.QTextEdit()
        self.focnewInfo.setReadOnly(True)
        self.focnewInfo.setMaximumHeight(self.IMAGE_HEIGHT-35)

        info_box = oasysgui.widgetBox(tab_info, "", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT-20, width = self.IMAGE_WIDTH-20)
        info_box.layout().addWidget(self.focnewInfo)

        self.image_box = gui.widgetBox(tab_scan, "Scan", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH-20)

        self.shadow_output = QtGui.QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(self.mainArea, "System Output", addSpace=True, orientation="horizontal", height=125)
        out_box.layout().addWidget(self.shadow_output)

    def set_Center(self):
        self.center_box.setVisible(self.mode == 2)
        self.center_box_empty.setVisible(self.mode < 2)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                self.input_beam = beam

                if self.is_automatic_run:
                    self.calculate()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def calculate(self):
        if ShadowCongruence.checkEmptyBeam(self.input_beam):
            if ShadowCongruence.checkGoodBeam(self.input_beam):
                if self.mode==2:
                    center=[self.center_x, self.center_z]
                else:
                    center=[0.0, 0.0]

                ticket = ST.focnew(self.input_beam._beam, mode=self.mode, center=center)

                self.focnewInfo.setText(ticket["text"])

                if self.plot_canvas is None:
                    self.plot_canvas = PlotWindow(roi=False, control=False, position=False, plugins=False)
                    self.plot_canvas.setDefaultPlotLines(True)
                    self.plot_canvas.setActiveCurveColor(color='blue')
                    self.plot_canvas.setDrawModeEnabled(True, 'rectangle')
                    self.plot_canvas.setZoomModeEnabled(True)
                    self.image_box.layout().addWidget(self.plot_canvas)


                y = numpy.linspace(-1.0, 1.0, 101)

                self.plot_canvas.addCurve(y, 2.35*ST.focnew_scan(ticket["AX"], y), "x (tangential)", symbol='', color="blue", replace=True) #'+', '^', ','
                self.plot_canvas.addCurve(y, 2.35*ST.focnew_scan(ticket["AZ"], y), "z (sagittal)", symbol='', color="red", replace=False) #'+', '^', ','
                self.plot_canvas.addCurve(y, 2.35*ST.focnew_scan(ticket["AT"], y), "combined x,z", symbol='', color="green", replace=False) #'+', '^', ','
                self.plot_canvas.setActiveCurve("x (tangential)")
                self.plot_canvas._plot.graph.ax.legend()
                self.plot_canvas.setGraphXLabel("Y [cm]")
                self.plot_canvas.setGraphYLabel("2.35*<Variable> [cm]")
                self.plot_canvas.setGraphTitle("Focnew Scan")

                self.plot_canvas.replot()


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FocNew()
    w.show()
    app.exec()
    w.saveSettings()
