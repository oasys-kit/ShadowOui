import sys
import numpy
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from Shadow import ShadowTools as ST
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.widgets.gui import ow_automatic_element

from Shadow.ShadowLibExtensions import CompoundOE

class FocNew(ow_automatic_element.AutomaticElement):

    name = "FocNew"
    description = "Shadow: FocNew"
    icon = "icons/focnew.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 5
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 675

    want_main_area=1
    want_control_area = 1

    input_beam=None

    image_plane=Setting(0)
    image_plane_new_position=Setting(10.0)
    image_plane_rel_abs_position=Setting(0)

    mode = Setting(0)
    center_x = Setting(0.0)
    center_z = Setting(0.0)

    y_range=Setting(0)
    y_range_min=Setting(-10.0)
    y_range_max=Setting(10.0)
    y_npoints=Setting(1001)

    plot_canvas_x=None
    plot_canvas_z=None
    plot_canvas_t=None

    def __init__(self, show_automatic_box=True):
        super().__init__()

        gui.button(self.controlArea, self, "Calculate", callback=self.calculate, height=45)

        general_box = oasysgui.widgetBox(self.controlArea, "General Settings", addSpace=True, orientation="vertical", width=self.CONTROL_AREA_WIDTH-8, height=220)

        gui.comboBox(general_box, self, "mode", label="Mode", labelWidth=250,
                                     items=["Center at Origin",
                                            "Center at Baricenter",
                                            "Define Center..."],
                                     callback=self.set_Center, sendSelectedValue=False, orientation="horizontal")

        self.center_box = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical", height=50)
        self.center_box_empty = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical", height=50)

        self.le_center_x = oasysgui.lineEdit(self.center_box, self, "center_x", "Center X", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_center_z = oasysgui.lineEdit(self.center_box, self, "center_z", "Center Z", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_Center()

        gui.comboBox(general_box, self, "y_range", label="Y Range",labelWidth=250,
                                     items=["<Default>",
                                            "Set.."],
                                     callback=self.set_YRange, sendSelectedValue=False, orientation="horizontal")

        self.yrange_box = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical", height=100)
        self.yrange_box_empty = oasysgui.widgetBox(general_box, "", addSpace=False, orientation="vertical",  height=100)

        self.le_y_range_min = oasysgui.lineEdit(self.yrange_box, self, "y_range_min", "Y min", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_y_range_max = oasysgui.lineEdit(self.yrange_box, self, "y_range_max", "Y max", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.yrange_box, self, "y_npoints", "Points", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_YRange()

        screen_box = oasysgui.widgetBox(self.controlArea, "Screen Position Settings", addSpace=True, orientation="vertical", height=110)

        self.image_plane_combo = gui.comboBox(screen_box, self, "image_plane", label="Position of the Image",
                                            items=["On Image Plane", "Retraced"], labelWidth=260,
                                            callback=self.set_ImagePlane, sendSelectedValue=False, orientation="horizontal")

        self.image_plane_box = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", height=110)
        self.image_plane_box_empty = oasysgui.widgetBox(screen_box, "", addSpace=True, orientation="vertical", height=110)

        oasysgui.lineEdit(self.image_plane_box, self, "image_plane_new_position", "Image Plane new Position", labelWidth=220, valueType=float, orientation="horizontal")

        gui.comboBox(self.image_plane_box, self, "image_plane_rel_abs_position", label="Position Type", labelWidth=250,
                     items=["Absolute", "Relative"], sendSelectedValue=False, orientation="horizontal")

        self.set_ImagePlane()

        gui.separator(self.controlArea, height=200)

        tabs_setting = oasysgui.tabWidget(self.mainArea)
        tabs_setting.setFixedHeight(self.IMAGE_HEIGHT+5)
        tabs_setting.setFixedWidth(self.IMAGE_WIDTH)

        tab_info = oasysgui.createTabPage(tabs_setting, "Focnew Info")
        tab_scan = oasysgui.createTabPage(tabs_setting, "Focnew Scan")

        self.focnewInfo = oasysgui.textArea(height=self.IMAGE_HEIGHT-35)

        info_box = oasysgui.widgetBox(tab_info, "", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT-20, width = self.IMAGE_WIDTH-20)
        info_box.layout().addWidget(self.focnewInfo)

        self.image_box = gui.widgetBox(tab_scan, "Scan", addSpace=True, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT-30)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH-20)

    def after_change_workspace_units(self):
        label = self.le_center_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_center_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_y_range_min.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_y_range_max.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def set_Center(self):
        self.center_box.setVisible(self.mode == 2)
        self.center_box_empty.setVisible(self.mode < 2)

    def set_YRange(self):
        self.yrange_box.setVisible(self.y_range == 1)
        self.yrange_box_empty.setVisible(self.y_range == 0)

    def set_ImagePlane(self):
        self.image_plane_box.setVisible(self.image_plane==1)
        self.image_plane_box_empty.setVisible(self.image_plane==0)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.calculate()
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def calculate(self):
        if ShadowCongruence.checkEmptyBeam(self.input_beam):
            if ShadowCongruence.checkGoodBeam(self.input_beam):

                beam_to_analize = self.input_beam._beam

                if self.image_plane == 1:
                    new_shadow_beam = self.input_beam.duplicate(history=False)
                    dist = 0.0

                    if self.image_plane_rel_abs_position == 1:  # relative
                        dist = self.image_plane_new_position
                    else:  # absolute
                        historyItem = self.input_beam.getOEHistory(oe_number=self.input_beam._oe_number)

                        if historyItem is None: image_plane = 0.0
                        elif self.input_beam._oe_number == 0: image_plane = 0.0
                        else:
                            if isinstance(historyItem._shadow_oe_end._oe, CompoundOE):
                                image_plane = historyItem._shadow_oe_end._oe.list[-1].T_IMAGE
                            else:
                                image_plane = historyItem._shadow_oe_end._oe.T_IMAGE

                        dist = self.image_plane_new_position - image_plane

                    new_shadow_beam._beam.retrace(dist)

                    beam_to_analize = new_shadow_beam._beam

                if self.mode==2:
                    center=[self.center_x, self.center_z]
                else:
                    center=[0.0, 0.0]

                if self.y_range == 1:
                    if self.y_range_min >= self.y_range_max:
                        raise Exception("Y range min cannot be greater or than Y range max")

                ticket = ST.focnew(beam_to_analize, mode=self.mode, center=center)

                self.focnewInfo.setText(ticket["text"])

                if self.plot_canvas_x is None:
                    self.plot_canvas_x = oasysgui.plotWindow(roi=False, control=False, position=True)
                    self.plot_canvas_x.setDefaultPlotLines(True)
                    self.plot_canvas_x.setActiveCurveColor(color='blue')
                    self.plot_canvas_x.setInteractiveMode(mode='zoom')
                    self.plot_canvas_x.toolBar().setVisible(False)

                    self.plot_canvas_z = oasysgui.plotWindow(roi=False, control=False, position=True)
                    self.plot_canvas_z.setDefaultPlotLines(True)
                    self.plot_canvas_z.setActiveCurveColor(color='red')
                    self.plot_canvas_z.setInteractiveMode(mode='zoom')
                    self.plot_canvas_z.toolBar().setVisible(False)

                    self.plot_canvas_t = oasysgui.plotWindow(roi=False, control=False, position=True)
                    self.plot_canvas_t.setDefaultPlotLines(True)
                    self.plot_canvas_t.setActiveCurveColor(color='green')
                    self.plot_canvas_t.setInteractiveMode(mode='zoom')
                    self.plot_canvas_t.toolBar().setVisible(False)

                    gridLayout = QtWidgets.QGridLayout()

                    gridLayout.addWidget(self.plot_canvas_x, 0, 0)
                    gridLayout.addWidget(self.plot_canvas_z, 0, 1)
                    gridLayout.addWidget(self.plot_canvas_t, 1, 0)

                    widget = QtWidgets.QWidget()
                    widget.setLayout(gridLayout)

                    self.image_box.layout().addWidget(widget)

                if self.y_range == 0:
                    y = numpy.linspace(-10.0, 10.0, 1001)
                else:
                    y = numpy.linspace(self.y_range_min, self.y_range_max, int(self.y_npoints))

                pos = [0.25, 0.15, 0.7, 0.75]

                self.plot_canvas_x.addCurve(y, 2.35*ST.focnew_scan(ticket["AX"], y)*ShadowPlot.get_factor(1, self.workspace_units_to_cm), "x (tangential)", symbol='', color="blue", replace=True) #'+', '^', ','
                self.plot_canvas_x._backend.ax.get_yaxis().get_major_formatter().set_useOffset(True)
                self.plot_canvas_x._backend.ax.get_yaxis().get_major_formatter().set_scientific(True)
                self.plot_canvas_x._backend.ax.set_position(pos)
                self.plot_canvas_x._backend.ax2.set_position(pos)
                self.plot_canvas_x.setGraphXLabel("Y [" + self.workspace_units_label + "]")
                self.plot_canvas_x.setGraphYLabel("2.35*<X> [$\mu$m]")
                self.plot_canvas_x._backend.ax.set_title("X", horizontalalignment='left')
                self.plot_canvas_x.replot()

                self.plot_canvas_z.addCurve(y, 2.35*ST.focnew_scan(ticket["AZ"], y)*ShadowPlot.get_factor(3, self.workspace_units_to_cm), "z (sagittal)", symbol='', color="red", replace=False) #'+', '^', ','
                self.plot_canvas_z._backend.ax.get_yaxis().get_major_formatter().set_useOffset(True)
                self.plot_canvas_z._backend.ax.get_yaxis().get_major_formatter().set_scientific(True)
                self.plot_canvas_z._backend.ax.set_position(pos)
                self.plot_canvas_z._backend.ax2.set_position(pos)
                self.plot_canvas_z.setGraphXLabel("Y [" + self.workspace_units_label + "]")
                self.plot_canvas_z.setGraphYLabel("2.35*<Z> [$\mu$m]")
                self.plot_canvas_z._backend.ax.set_title("Z", horizontalalignment='left')
                self.plot_canvas_z.replot()

                self.plot_canvas_t.addCurve(y, 2.35*ST.focnew_scan(ticket["AT"], y)*ShadowPlot.get_factor(1, self.workspace_units_to_cm), "combined x,z", symbol='', color="green", replace=True) #'+', '^', ','
                self.plot_canvas_t._backend.ax.get_yaxis().get_major_formatter().set_useOffset(True)
                self.plot_canvas_t._backend.ax.get_yaxis().get_major_formatter().set_scientific(True)
                self.plot_canvas_t._backend.ax.set_position(pos)
                self.plot_canvas_t._backend.ax2.set_position(pos)
                self.plot_canvas_t.setGraphXLabel("Y [" + self.workspace_units_label + "]")
                self.plot_canvas_t.setGraphYLabel("2.35*<X,Z> [$\mu$m]")
                self.plot_canvas_t._backend.ax.set_title("X,Z (Combined)", horizontalalignment='left')
                self.plot_canvas_t.replot()


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
