import os, sys
from PyQt5.QtWidgets import QApplication

import orangecanvas.resources as resources

from oasys.widgets.error_profile.ow_abstract_dabam_height_profile import OWAbstractDabamHeightProfile

from Shadow import ShadowTools as ST
from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData

class OWdabam_height_profile(OWAbstractDabamHeightProfile):
    name = "DABAM Height Profile"
    id = "dabam_height_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/dabam.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; lrebuffi@anl.gov"
    priority = 6
    category = ""
    keywords = ["dabam_height_profile"]

    outputs = [OWAbstractDabamHeightProfile.get_dabam_output(),
               {"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]


    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "dabam_height_profile_usage.png")

    def __init__(self):
        super().__init__()

    def after_change_workspace_units(self):
        self.si_to_user_units = 1 / self.workspace_units_to_m

        self.horHeaders = ["Entry", "Shape", "Length\n[" + self.get_axis_um() + "]", "Heights St.Dev.\n[nm]",  "Slopes St.Dev.\n[" + u"\u03BC" + "rad]"]
        self.table.setHorizontalHeaderLabels(self.horHeaders)
        self.plot_canvas[0].setGraphXLabel("Y [" + self.get_axis_um() + "]")
        self.plot_canvas[1].setGraphXLabel("Y [" + self.get_axis_um() + "]")
        self.axis.set_xlabel("X [" + self.get_axis_um() + "]")
        self.axis.set_ylabel("Y [" + self.get_axis_um() + "]")

        label = self.le_dimension_y_from.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_dimension_y_to.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_dimension_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_step_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_new_length_1.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_new_length_2.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def get_usage_path(self):
        return self.usage_path

    def get_axis_um(self):
        return self.workspace_units_label

    def write_error_profile_file(self):
        ST.write_shadow_surface(self.zz, self.xx, self.yy, self.heigth_profile_file_name)

    def send_data(self, dimension_x, dimension_y):
        self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=self.heigth_profile_file_name,
                                                              error_profile_x_dim=dimension_x,
                                                              error_profile_y_dim=dimension_y))

'''

import os, sys
import time
import numpy
import threading

from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QWidget, QLabel, QSizePolicy
from PyQt5.QtGui import QTextCursor,QFont, QPalette, QColor, QPainter, QBrush, QPen, QPixmap

from matplotlib import cm
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import orangecanvas.resources as resources

from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import EmittingStream

try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData

from srxraylib.metrology import profiles_simulation, dabam
from Shadow import ShadowTools as ST

class OWdabam_height_profile(OWWidget):
    name = "DABAM Height Profile"
    id = "dabam_height_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/dabam.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; lrebuffi@anl.gov"
    priority = 6
    category = ""
    keywords = ["dabam_height_profile"]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    want_main_area = 1
    want_control_area = 1

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 645

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 618

    xx = None
    yy = None
    zz = None

    entry_number = Setting(1)

    shape=Setting(0)
    slope_error_from = Setting(0.0)
    slope_error_to = Setting(1.5)
    dimension_y_from = Setting(0.0)
    dimension_y_to = Setting(200.0)

    use_undetrended = Setting(0)

    step_x = Setting(1.0)
    dimension_x = Setting(10.0)

    center_y = Setting(1)
    modify_y = Setting(0)
    new_length = Setting(200.0)
    filler_value = Setting(0.0)

    renormalize_y = Setting(1)
    error_type_y = Setting(0)
    rms_y = Setting(0.9)

    dabam_profile_index = Setting(1)

    heigth_profile_file_name = Setting('mirror.dat')

    tab=[]

    usage_path = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.gui"), "misc", "dabam_height_profile_usage.png")

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Calculate Height Profile", self)
        self.runaction.triggered.connect(self.calculate_heigth_profile_ni)
        self.addAction(self.runaction)

        self.runaction = widget.OWAction("Generate Height Profile File", self)
        self.runaction.triggered.connect(self.generate_heigth_profile_file_ni)
        self.addAction(self.runaction)

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.MAX_WIDTH)),
                               round(min(geom.height() * 0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        # DABAM INITIALIZATION
        self.server = dabam.dabam()
        self.server.set_input_silent(True)

        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Height\nProfile", callback=self.calculate_heigth_profile)
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Generate Height\nProfile File", callback=self.generate_heigth_profile_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(150)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        gui.separator(self.controlArea)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_input = oasysgui.createTabPage(tabs_setting, "DABAM Search Setting")
        tab_gener = oasysgui.createTabPage(tabs_setting, "DABAM Generation Setting")
        tab_out = oasysgui.createTabPage(tabs_setting, "Output")
        tab_usa = oasysgui.createTabPage(tabs_setting, "Use of the Widget")
        tab_usa.setStyleSheet("background-color: white;")

        usage_box = oasysgui.widgetBox(tab_usa, "", addSpace=True, orientation="horizontal")

        label = QLabel("")
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        label.setPixmap(QPixmap(self.usage_path))

        usage_box.layout().addWidget(label)

        manual_box = oasysgui.widgetBox(tab_input, "Manual Entry", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(manual_box, self, "entry_number", "Entry Number",
                           labelWidth=300, valueType=int, orientation="horizontal")

        gui.separator(manual_box)

        button = gui.button(manual_box, self, "Retrieve Profile", callback=self.retrieve_profile)
        button.setFixedHeight(35)
        button.setFixedWidth(self.CONTROL_AREA_WIDTH-35)

        input_box = oasysgui.widgetBox(tab_input, "Search Parameters", addSpace=True, orientation="vertical")

        gui.comboBox(input_box, self, "shape", label="Mirror Shape", labelWidth=300,
                     items=["All", "Plane", "Cylindrical", "Elliptical", "Toroidal", "Spherical"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(input_box)
        
        input_box_1 = oasysgui.widgetBox(input_box, "", addSpace=True, orientation="horizontal")

        oasysgui.lineEdit(input_box_1, self, "slope_error_from", "Slope Error From (" + u"\u03BC" + "rad)",
                           labelWidth=150, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(input_box_1, self, "slope_error_to", "To (" + u"\u03BC" + "rad)",
                           labelWidth=60, valueType=float, orientation="horizontal")

        input_box_2 = oasysgui.widgetBox(input_box, "", addSpace=True, orientation="horizontal")

        self.le_dimension_y_from = oasysgui.lineEdit(input_box_2, self, "dimension_y_from", "Mirror Length From",
                           labelWidth=150, valueType=float, orientation="horizontal")
        self.le_dimension_y_to = oasysgui.lineEdit(input_box_2, self, "dimension_y_to", "To",
                           labelWidth=60, valueType=float, orientation="horizontal")

        table_box = oasysgui.widgetBox(tab_input, "Search Results", addSpace=True, orientation="vertical", height=250)

        self.overlay_search = Overlay(table_box, self.search_profiles)
        self.overlay_search.hide()

        button = gui.button(input_box, self, "Search", callback=self.overlay_search.show)
        button.setFixedHeight(35)
        button.setFixedWidth(self.CONTROL_AREA_WIDTH-35)

        gui.comboBox(table_box, self, "use_undetrended", label="Use Undetrended Profile", labelWidth=300,
                     items=["No", "Yes"], callback=self.table_item_clicked, sendSelectedValue=False, orientation="horizontal")

        gui.separator(table_box)

        self.scrollarea = QScrollArea()
        self.scrollarea.setMinimumWidth(self.CONTROL_AREA_WIDTH-35)

        table_box.layout().addWidget(self.scrollarea, alignment=Qt.AlignHCenter)

        self.table = QTableWidget(1, 5)
        self.table.setStyleSheet("background-color: #FBFBFB;")
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table.verticalHeader().setVisible(False)

        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 80)

        self.table.resizeRowsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemClicked.connect(self.table_item_clicked)

        self.scrollarea.setWidget(self.table)
        self.scrollarea.setWidgetResizable(1)

        output_profile_box = oasysgui.widgetBox(tab_gener, "Surface Generation Parameters", addSpace=True, orientation="vertical", height=320)

        self.le_dimension_x = oasysgui.lineEdit(output_profile_box, self, "dimension_x", "Width",
                           labelWidth=300, valueType=float, orientation="horizontal")
        self.le_step_x = oasysgui.lineEdit(output_profile_box, self, "step_x", "Step Width",
                           labelWidth=300, valueType=float, orientation="horizontal")

        gui.comboBox(output_profile_box, self, "center_y", label="Center Profile in the middle of O.E.", labelWidth=300,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        gui.separator(output_profile_box)

        gui.comboBox(output_profile_box, self, "modify_y", label="Modify Length?", labelWidth=150,
                     items=["No", "Rescale to new length", "Fit to new length (fill or cut)"], callback=self.set_ModifyY, sendSelectedValue=False, orientation="horizontal")

        self.modify_box_1 = oasysgui.widgetBox(output_profile_box, "", addSpace=False, orientation="vertical", height=60)

        self.modify_box_2 = oasysgui.widgetBox(output_profile_box, "", addSpace=False, orientation="vertical", height=60)
        self.le_new_length_1 = oasysgui.lineEdit(self.modify_box_2, self, "new_length", "New Length", labelWidth=300, valueType=float, orientation="horizontal")

        self.modify_box_3 = oasysgui.widgetBox(output_profile_box, "", addSpace=False, orientation="vertical", height=60)
        self.le_new_length_2 = oasysgui.lineEdit(self.modify_box_3, self, "new_length", "New Length", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.modify_box_3, self, "filler_value", "Filler Value (if new length > profile length) [nm]", labelWidth=300, valueType=float, orientation="horizontal")

        self.set_ModifyY()

        gui.comboBox(output_profile_box, self, "renormalize_y", label="Renormalize Length Profile to different RMS", labelWidth=300,
                     items=["No", "Yes"], callback=self.set_RenormalizeY, sendSelectedValue=False, orientation="horizontal")

        self.output_profile_box_1 = oasysgui.widgetBox(output_profile_box, "", addSpace=False, orientation="vertical", height=60)
        self.output_profile_box_2 = oasysgui.widgetBox(output_profile_box, "", addSpace=False, orientation="vertical", height=60)

        gui.comboBox(self.output_profile_box_1, self, "error_type_y", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + u"\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.output_profile_box_1, self, "rms_y", "Rms Value",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.set_RenormalizeY()

        output_box = oasysgui.widgetBox(tab_gener, "Outputs", addSpace=True, orientation="vertical")

        select_file_box = oasysgui.widgetBox(output_box, "", addSpace=True, orientation="horizontal")

        self.le_heigth_profile_file_name = oasysgui.lineEdit(select_file_box, self, "heigth_profile_file_name", "Output File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(select_file_box, self, "...", callback=self.selectFile)

        self.shadow_output = oasysgui.textArea(height=400)

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=500)
        out_box.layout().addWidget(self.shadow_output)

        gui.rubber(self.controlArea)

        self.initializeTabs()

        gui.rubber(self.mainArea)

        self.overlay_search.raise_()

    def resizeEvent(self, event):
        self.overlay_search.resize(self.CONTROL_AREA_WIDTH - 15, 290)
        event.accept()

    def after_change_workspace_units(self):
        self.si_to_user_units = 1e2 / self.workspace_units_to_cm

        self.horHeaders = ["Entry", "Shape", "Length\n[" + self.workspace_units_label + "]", "Heights St.Dev.\n[nm]",  "Slopes St.Dev.\n[" + u"\u03BC" + "rad]"]
        self.table.setHorizontalHeaderLabels(self.horHeaders)
        self.plot_canvas[0].setGraphXLabel("Y [" + self.workspace_units_label + "]")
        self.plot_canvas[1].setGraphXLabel("Y [" + self.workspace_units_label + "]")
        self.axis.set_xlabel("X [" + self.workspace_units_label + "]")
        self.axis.set_ylabel("Y [" + self.workspace_units_label + "]")

        label = self.le_dimension_y_from.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_dimension_y_to.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_dimension_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_step_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_new_length_1.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_new_length_2.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def initializeTabs(self):
        self.tabs = oasysgui.tabWidget(self.mainArea)

        self.tab = [oasysgui.createTabPage(self.tabs, "Info"),
                    oasysgui.createTabPage(self.tabs, "Heights Profile"),
                    oasysgui.createTabPage(self.tabs, "Slopes Profile"),
                    oasysgui.createTabPage(self.tabs, "PSD Heights"),
                    oasysgui.createTabPage(self.tabs, "CSD Heights"),
                    oasysgui.createTabPage(self.tabs, "ACF"),
                    oasysgui.createTabPage(self.tabs, "Generated 2D Profile"),
        ]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas = [None, None, None, None, None, None]

        self.plot_canvas[0] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[0].setDefaultPlotLines(True)
        self.plot_canvas[0].setActiveCurveColor(color='blue')
        self.plot_canvas[0].setGraphYLabel("Z [nm]")
        self.plot_canvas[0].setGraphTitle("Heights Profile")
        self.plot_canvas[0].setInteractiveMode(mode='zoom')

        self.plot_canvas[1] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[1].setDefaultPlotLines(True)
        self.plot_canvas[1].setActiveCurveColor(color='blue')
        self.plot_canvas[1].setGraphYLabel("Zp [$\mu$rad]")
        self.plot_canvas[1].setGraphTitle("Slopes Profile")
        self.plot_canvas[1].setInteractiveMode(mode='zoom')

        self.plot_canvas[2] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[2].setDefaultPlotLines(True)
        self.plot_canvas[2].setActiveCurveColor(color='blue')
        self.plot_canvas[2].setGraphXLabel("f [m^-1]")
        self.plot_canvas[2].setGraphYLabel("PSD [m^3]")
        self.plot_canvas[2].setGraphTitle("Power Spectral Density of Heights Profile")
        self.plot_canvas[2].setInteractiveMode(mode='zoom')
        self.plot_canvas[2].setXAxisLogarithmic(True)
        self.plot_canvas[2].setYAxisLogarithmic(True)

        self.plot_canvas[3] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[3].setDefaultPlotLines(True)
        self.plot_canvas[3].setActiveCurveColor(color='blue')
        self.plot_canvas[3].setGraphXLabel("f [m^-1]")
        self.plot_canvas[3].setGraphYLabel("CSD [m^3]")
        self.plot_canvas[3].setGraphTitle("Cumulative Spectral Density of Heights Profile")
        self.plot_canvas[3].setInteractiveMode(mode='zoom')
        self.plot_canvas[3].setXAxisLogarithmic(True)

        self.plot_canvas[4] = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas[4].setDefaultPlotLines(True)
        self.plot_canvas[4].setActiveCurveColor(color='blue')
        self.plot_canvas[4].setGraphXLabel("Length [m]")
        self.plot_canvas[4].setGraphYLabel("ACF")
        self.plot_canvas[4].setGraphTitle("Autocovariance Function of Heights Profile")
        self.plot_canvas[4].setInteractiveMode(mode='zoom')

        self.figure = Figure(figsize=(self.IMAGE_HEIGHT, self.IMAGE_HEIGHT)) # QUADRATA!
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')
        self.axis.set_zlabel("Z [nm]")

        self.plot_canvas[5] = FigureCanvasQTAgg(self.figure)

        self.profileInfo = oasysgui.textArea(height=self.IMAGE_HEIGHT-5, width=400)

        profile_box = oasysgui.widgetBox(self.tab[0], "", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT, width=410)
        profile_box.layout().addWidget(self.profileInfo)

        for index in range(0, 6):
            self.tab[index+1].layout().addWidget(self.plot_canvas[index])

        self.tabs.setCurrentIndex(1)

    def plot_dabam_graph(self, plot_canvas_index, curve_name, x_values, y_values, xtitle, ytitle, color='blue', replace=True):
        self.plot_canvas[plot_canvas_index].addCurve(x_values, y_values, curve_name, symbol='', color=color, replace=replace) #'+', '^', ','
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].replot()

    def set_ModifyY(self):
        self.modify_box_1.setVisible(self.modify_y == 0)
        self.modify_box_2.setVisible(self.modify_y == 1)
        self.modify_box_3.setVisible(self.modify_y == 2)

    def set_RenormalizeY(self):
        self.output_profile_box_1.setVisible(self.renormalize_y==1)
        self.output_profile_box_2.setVisible(self.renormalize_y==0)

    def table_item_clicked(self):
        if self.table.selectionModel().hasSelection():
            if not self.table.rowCount() == 0:
                if not self.table.item(0, 0) is None:
                    row = self.table.selectionModel().selectedRows()[0].row()
                    self.entry_number = int(self.table.item(row, 0).text())

                    self.retrieve_profile()

    def retrieve_profile(self):
        try:
            if self.entry_number is None or self.entry_number <= 0:
                raise Exception("Entry number should be a strictly positive integer number")

            self.server.load(self.entry_number)
            self.profileInfo.setText(self.server.info_profiles())
            self.plot_canvas[0].setGraphTitle(
                "Heights Profile. St.Dev.=%.3f nm" % (self.server.stdev_profile_heights() * 1e9))
            self.plot_canvas[1].setGraphTitle(
                "Slopes Profile. St.Dev.=%.3f $\mu$rad" % (self.server.stdev_profile_slopes() * 1e6))
            if self.use_undetrended == 0:
                self.plot_dabam_graph(0, "heights_profile", self.si_to_user_units * self.server.y,
                                      1e9 * self.server.zHeights, "Y [" + self.workspace_units_label + "]", "Z [nm]")
                self.plot_dabam_graph(1, "slopes_profile", self.si_to_user_units * self.server.y, 1e6 * self.server.zSlopes,
                                      "Y [" + self.workspace_units_label + "]", "Zp [$\mu$rad]")
            else:
                self.plot_dabam_graph(0, "heights_profile", self.si_to_user_units * self.server.y,
                                      1e9 * self.server.zHeightsUndetrended, "Y [" + self.workspace_units_label + "]",
                                      "Z [nm]")
                self.plot_dabam_graph(1, "slopes_profile", self.si_to_user_units * self.server.y,
                                      1e6 * self.server.zSlopesUndetrended, "Y [" + self.workspace_units_label + "]",
                                      "Zp [$\mu$rad]")
            y = self.server.f ** (self.server.powerlaw["hgt_pendent"]) * 10 ** self.server.powerlaw["hgt_shift"]
            i0 = self.server.powerlaw["index_from"]
            i1 = self.server.powerlaw["index_to"]
            beta = -self.server.powerlaw["hgt_pendent"]
            self.plot_canvas[2].setGraphTitle(
                "Power Spectral Density of Heights Profile (beta=%.2f,Df=%.2f)" % (beta, (5 - beta) / 2))
            self.plot_dabam_graph(2, "psd_heights_2", self.server.f, self.server.psdHeights, "f [m^-1]", "PSD [m^3]")
            self.plot_dabam_graph(2, "psd_heights_1", self.server.f, y, "f [m^-1]", "PSD [m^3]", color='green',
                                  replace=False)
            self.plot_dabam_graph(2, "psd_heights_3", self.server.f[i0:i1], y[i0:i1], "f [m^-1]", "PSD [m^3]", color='red',
                                  replace=False)
            self.plot_dabam_graph(3, "csd", self.server.f, self.server.csd_heights(), "f [m^-1]", "CSD [m^3]")
            c1, c2, c3 = dabam.autocorrelationfunction(self.server.y, self.server.zHeights)
            self.plot_canvas[4].setGraphTitle(
                "Autocovariance Function of Heights Profile.\nAutocorrelation Length (ACF=0.5)=%.3f m" % (c3))
            self.plot_dabam_graph(4, "acf", c1[0:-1], c2, "Length [m]", "Heights Autocovariance")
            # surface error removal
            if not self.zz is None and not self.yy is None and not self.xx is None:
                self.xx = None
                self.yy = None
                self.zz = None
                self.axis.set_title("")
                self.axis.clear()
                self.plot_canvas[5].draw()

            if (self.tabs.currentIndex()==6): self.tabs.setCurrentIndex(1)

        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception


    def search_profiles(self):
        try:
            self.table.itemClicked.disconnect(self.table_item_clicked)
            self.table.clear()

            row_count = self.table.rowCount()
            for n in range(0, row_count):
                self.table.removeRow(0)

            self.table.setHorizontalHeaderLabels(self.horHeaders)

            profiles = dabam.dabam_summary_dictionary(surface=self.get_dabam_shape(),
                                                      slp_err_from=self.slope_error_from*1e-6,
                                                      slp_err_to=self.slope_error_to*1e-6,
                                                      length_from=self.dimension_y_from / self.si_to_user_units,
                                                      length_to=self.dimension_y_to / self.si_to_user_units)

            for index in range(0, len(profiles)):
                self.table.insertRow(0)

            for index in range(0, len(profiles)):
                table_item = QTableWidgetItem(str(profiles[index]["entry"]))
                table_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(index, 0, table_item)
                table_item = QTableWidgetItem(str(profiles[index]["surface"]))
                table_item.setTextAlignment(Qt.AlignLeft)
                self.table.setItem(index, 1, table_item)
                table_item = QTableWidgetItem(str(numpy.round(profiles[index]["length"]*self.si_to_user_units, 3)))
                table_item.setTextAlignment(Qt.AlignRight)
                self.table.setItem(index, 2, table_item)
                table_item = QTableWidgetItem(str(numpy.round(profiles[index]["hgt_err"]*1e9, 3)))
                table_item.setTextAlignment(Qt.AlignRight)
                self.table.setItem(index, 3, table_item)
                table_item = QTableWidgetItem(str(numpy.round(profiles[index]["slp_err"]*1e6, 3)))
                table_item.setTextAlignment(Qt.AlignRight)
                self.table.setItem(index, 4, table_item)

            self.table.setHorizontalHeaderLabels(self.horHeaders)
            self.table.resizeRowsToContents()
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

            self.table.itemClicked.connect(self.table_item_clicked)

            self.overlay_search.hide()

        except Exception as exception:
            self.overlay_search.hide()

            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

    def get_dabam_shape(self):
        if self.shape == 0: return None
        elif self.shape == 1: return "plane"
        elif self.shape == 2: return "cylindrical"
        elif self.shape == 3: return "elliptical"
        elif self.shape == 4: return "toroidal"
        elif self.shape == 5: return "spherical"

    def calculate_heigth_profile_ni(self):
        self.calculate_heigth_profile(not_interactive_mode=True)

    def calculate_heigth_profile(self, not_interactive_mode=False):
        import matplotlib
        print (matplotlib.__version__)

        try:
            if self.server.y is None: raise Exception("No Profile Selected")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            # PREVENTS CRASH WITH PYQT5
            if not not_interactive_mode:  self.tabs.setCurrentIndex(6)

            combination = "EF"

            if self.modify_y == 2:
                profile_1D_y_x_temp = self.si_to_user_units * self.server.y
                if self.use_undetrended == 0: profile_1D_y_y_temp = self.si_to_user_units * self.server.zHeights
                else: profile_1D_y_y_temp = self.si_to_user_units * self.server.zHeightsUndetrended

                first_coord = profile_1D_y_x_temp[0]
                second_coord  = profile_1D_y_x_temp[1]
                last_coord = profile_1D_y_x_temp[-1]
                step = numpy.abs(second_coord - first_coord)
                length = numpy.abs(last_coord - first_coord)
                n_points_old = len(profile_1D_y_x_temp)

                if self.new_length > length:
                    difference = self.new_length - length

                    n_added_points = int(difference/step)
                    if difference % step == 0:
                        n_added_points += 1
                    if n_added_points % 2 != 0:
                        n_added_points += 1


                    profile_1D_y_x = numpy.arange(n_added_points + n_points_old) * step
                    profile_1D_y_y = numpy.ones(n_added_points + n_points_old) * self.filler_value * 1e-9 * self.si_to_user_units
                    profile_1D_y_y[int(n_added_points/2) : n_points_old + int(n_added_points/2)] = profile_1D_y_y_temp
                elif self.new_length < length:
                    difference = length - self.new_length

                    n_removed_points = int(difference/step)
                    if difference % step == 0:
                        n_removed_points -= 1
                    if n_removed_points % 2 != 0:
                        n_removed_points -= 1

                    if n_removed_points >= 2:
                        profile_1D_y_x = profile_1D_y_x_temp[0 : (n_points_old - n_removed_points)]
                        profile_1D_y_y = profile_1D_y_y_temp[(int(n_removed_points/2) - 1) : (n_points_old - int(n_removed_points/2) - 1)]

                    else:
                        profile_1D_y_x = profile_1D_y_x_temp
                        profile_1D_y_y = profile_1D_y_y_temp
                else:
                    profile_1D_y_x = profile_1D_y_x_temp
                    profile_1D_y_y = profile_1D_y_y_temp

            else:
                if self.modify_y == 0:
                    profile_1D_y_x = self.si_to_user_units * self.server.y
                elif self.modify_y == 1:
                    scale_factor_y = self.new_length/(self.si_to_user_units * (max(self.server.y)-min(self.server.y)))
                    profile_1D_y_x = self.si_to_user_units * self.server.y * scale_factor_y

                if self.use_undetrended == 0: profile_1D_y_y = self.si_to_user_units * self.server.zHeights
                else: profile_1D_y_y = self.si_to_user_units * self.server.zHeightsUndetrended


            if self.center_y:
                first_coord = profile_1D_y_x[0]
                last_coord = profile_1D_y_x[-1]
                length = numpy.abs(last_coord - first_coord)

                profile_1D_y_x_temp = numpy.linspace(-length/2, length/2, len(profile_1D_y_x))

                profile_1D_y_x = profile_1D_y_x_temp

            if self.renormalize_y == 0:
                rms_y = None
            else:
                if self.error_type_y == profiles_simulation.FIGURE_ERROR:
                    rms_y = self.si_to_user_units * self.rms_y * 1e-9   # from nm to user units
                else:
                    rms_y = self.rms_y * 1e-6 # from urad to rad


            xx, yy, zz = profiles_simulation.simulate_profile_2D(combination = combination,
                                                                 error_type_l = self.error_type_y,
                                                                 rms_l = rms_y,
                                                                 x_l = profile_1D_y_x,
                                                                 y_l = profile_1D_y_y,
                                                                 mirror_width = self.dimension_x,
                                                                 step_w = self.step_x,
                                                                 rms_w = 0.0)

            self.xx = xx
            self.yy = yy
            self.zz = zz # in user units

            self.axis.clear()

            x_to_plot, y_to_plot = numpy.meshgrid(xx, yy)
            z_to_plot = zz * 1e9 / self.si_to_user_units #nm

            self.axis.plot_surface(x_to_plot, y_to_plot, z_to_plot,
                                   rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)


            sloperms = profiles_simulation.slopes(zz.T, xx, yy, return_only_rms=1)

            title = ' Slope error rms in X direction: %f $\mu$rad' % (sloperms[0]*1e6) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (sloperms[1]*1e6) + '\n' + \
                    ' Figure error rms in X direction: %f nm' % (round(zz[0, :].std()*1e9/self.si_to_user_units, 6)) + '\n' + \
                    ' Figure error rms in Y direction: %f nm' % (round(zz[:, 0].std()*1e9/self.si_to_user_units, 6))

            self.axis.set_xlabel("X [" + self.workspace_units_label + "]")
            self.axis.set_ylabel("Y [" + self.workspace_units_label + "]")
            self.axis.set_zlabel("Z [nm]")

            self.axis.set_title(title)

            self.axis.mouse_init()

            if not not_interactive_mode:
                try:
                    import matplotlib
                    if matplotlib.__version__ == "1.4.3":
                        self.plot_canvas[5].draw()
                except:
                    pass

                QMessageBox.information(self, "QMessageBox.information()",
                                        "Height Profile calculated: if the result is satisfactory,\nclick \'Generate Height Profile File\' to complete the operation ",
                                        QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def generate_heigth_profile_file_ni(self):
        self.generate_heigth_profile_file(not_interactive_mode=True)

    def generate_heigth_profile_file(self, not_interactive_mode=False):
        if not self.zz is None and not self.yy is None and not self.xx is None:
            try:
                congruence.checkDir(self.heigth_profile_file_name)

                sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                ST.write_shadow_surface(self.zz, self.xx, self.yy, outFile=congruence.checkFileName(self.heigth_profile_file_name))
                if not not_interactive_mode:
                    QMessageBox.information(self, "QMessageBox.information()",
                                            "Height Profile file " + self.heigth_profile_file_name + " written on disk",
                                            QMessageBox.Ok)
                if self.modify_y == 0:
                    dimension_y = self.si_to_user_units * (self.server.y[-1] - self.server.y[0])
                if self.modify_y == 1 or self.modify_y == 2:
                    dimension_y = self.new_length

                self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=self.heigth_profile_file_name,
                                                                      error_profile_x_dim=self.dimension_x,
                                                                      error_profile_y_dim=dimension_y))
            except Exception as exception:
                QMessageBox.critical(self, "Error",
                                     exception.args[0],
                                     QMessageBox.Ok)

    def call_reset_settings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            try:
                self.resetSettings()
            except:
                pass

    def check_fields(self):
        self.dimension_x = congruence.checkStrictlyPositiveNumber(self.dimension_x, "Dimension X")
        self.step_x = congruence.checkStrictlyPositiveNumber(self.step_x, "Step X")

        congruence.checkLessOrEqualThan(self.step_x, self.dimension_x/2, "Step Width", "Width/2")

        if self.modify_y == 1 or self.modify_y == 2:
            self.new_length = congruence.checkStrictlyPositiveNumber(self.new_length, "New Length")

        if self.renormalize_y == 1:
            self.rms_y = congruence.checkPositiveNumber(self.rms_y, "Rms Y")

        congruence.checkDir(self.heigth_profile_file_name)

    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def selectFile(self):
        self.le_heigth_profile_file_name.setText(oasysgui.selectFileFromDialog(self, self.heigth_profile_file_name, "Select Output File", file_extension_filter="Data Files (*.dat)"))


class Overlay(QWidget):

    def __init__(self, container_widget=None, target_method=None):

        QWidget.__init__(self, container_widget)
        self.container_widget = container_widget
        self.target_method = target_method
        palette = QPalette(self.palette())
        palette.setColor(palette.Background, Qt.transparent)
        self.setPalette(palette)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), QBrush(QColor(255, 255, 255, 127)))
        painter.setPen(QPen(Qt.NoPen))

        for i in range(1, 7):
            if self.position_index == i:
                painter.setBrush(QBrush(QColor(255, 165, 0)))
            else:
                painter.setBrush(QBrush(QColor(127, 127, 127)))
            painter.drawEllipse(
                self.width()/2 + 30 * numpy.cos(2 * numpy.pi * i / 6.0) - 10,
                self.height()/2 + 30 * numpy.sin(2 * numpy.pi * i / 6.0) - 10,
                20, 20)

            time.sleep(0.005)

        painter.end()

    def showEvent(self, event):
        self.timer = self.startTimer(0)
        self.counter = 0
        self.position_index = 0
        t = threading.Thread(target=self.target_method)
        t.start()

    def hideEvent(self, QHideEvent):
        self.killTimer(self.timer)

    def timerEvent(self, event):
        self.counter += 1
        self.position_index += 1
        if self.position_index == 7: self.position_index = 1
        self.update()
'''
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWdabam_height_profile()
    w.si_to_user_units = 100
    w.show()
    app.exec()
    w.saveSettings()
