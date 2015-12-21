import sys

import numpy
from PyQt4.QtCore import QRect, Qt
from PyQt4.QtGui import QTextEdit, QTextCursor, QApplication, QFont, QPalette, QColor, \
    QMessageBox, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyMca5.PyMcaGui.plotting.PlotWindow import PlotWindow

from srxraylib.metrology import profiles_simulation, dabam
from Shadow import ShadowTools as ST
from matplotlib import cm
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from oasys.widgets.widget import OWWidget
from orangewidget import gui, widget
from orangewidget.settings import Setting

from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

try:
    from mpl_toolkits.mplot3d import Axes3D  # necessario per caricare i plot 3D
except:
    pass

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, EmittingStream

class OWdabam_height_profile(OWWidget):
    name = "DABAM Height Profile"
    id = "dabam_height_profile"
    description = "Calculation of mirror surface error profile"
    icon = "icons/dabam.png"
    author = "Luca Rebuffi"
    maintainer_email = "srio@esrf.eu; luca.rebuffi@elettra.eu"
    priority = 6
    category = ""
    keywords = ["dabam_height_profile"]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"}]

    want_main_area = 1
    want_control_area = 1

    WIDGET_WIDTH = 1100
    WIDGET_HEIGHT = 650

    IMAGE_WIDTH = 800
    IMAGE_HEIGHT = 800

    xx = None
    yy = None
    zz = None

    shape=Setting(0)
    slope_error_from = Setting(0.0)
    slope_error_to = Setting(1.5)
    dimension_y_from = Setting(0.0)
    dimension_y_to = Setting(200.0)

    use_undetrended = Setting(0)

    step_x = Setting(1.0)
    dimension_x = Setting(10.0)
    scale_factor_y = Setting(1.0)
    renormalize_y = Setting(1)
    error_type_y = Setting(0)
    rms_y = Setting(0.9)

    dabam_profile_index = Setting(1)

    heigth_profile_file_name = Setting('mirror.dat')

    tab=[]

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
                               round(min(geom.width() * 0.98, self.WIDGET_WIDTH)),
                               round(min(geom.height() * 0.95, self.WIDGET_HEIGHT))))

        # DABAM INITIALIZATION
        self.server = dabam.dabam()
        self.server.set_input_silent(True)

        gen_box = oasysgui.widgetBox(self.controlArea, "Error Profile Parameters", addSpace=True, orientation="horizontal",
                                      width=500)

        tabs_setting = gui.tabWidget(gen_box)

        tab_input = oasysgui.createTabPage(tabs_setting, "DABAM Input Parameters")

        tab_out = oasysgui.createTabPage(tabs_setting, "Output")

        input_box = oasysgui.widgetBox(tab_input, "Search Paramters", addSpace=True, orientation="vertical", width=470)

        gui.comboBox(input_box, self, "shape", label="Mirror Shape", labelWidth=300,
                     items=["All", "Plane", "Cylindrical", "Elliptical", "Toroidal", "Spherical"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(input_box)
        
        input_box_1 = oasysgui.widgetBox(input_box, "", addSpace=True, orientation="horizontal", width=450)

        oasysgui.lineEdit(input_box_1, self, "slope_error_from", "Slope Error From (" + u"\u03BC" + "rad)",
                           labelWidth=140, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(input_box_1, self, "slope_error_to", "To (" + u"\u03BC" + "rad)",
                           labelWidth=50, valueType=float, orientation="horizontal")

        input_box_2 = oasysgui.widgetBox(input_box, "", addSpace=True, orientation="horizontal", width=450)

        oasysgui.lineEdit(input_box_2, self, "dimension_y_from", "Mirror Length From (cm)",
                           labelWidth=140, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(input_box_2, self, "dimension_y_to", "To (cm)",
                           labelWidth=50, valueType=float, orientation="horizontal")

        button = gui.button(input_box, self, "Search", callback=self.search_profiles)
        button.setFixedHeight(25)
        button.setFixedWidth(450)

        table_box = oasysgui.widgetBox(tab_input, "Search Results", addSpace=True, orientation="vertical", width=470, height=300)

        gui.comboBox(table_box, self, "use_undetrended", label="Use Undetrended Profile", labelWidth=300,
                     items=["No", "Yes"], callback=self.table_item_clicked, sendSelectedValue=False, orientation="horizontal")

        gui.separator(table_box)

        self.scrollarea = QScrollArea()
        self.scrollarea.setMinimumWidth(450)

        table_box.layout().addWidget(self.scrollarea, alignment=Qt.AlignHCenter)

        self.table = QTableWidget(1, 5)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setResizeMode(QHeaderView.Fixed)

        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 110)

        horHeaders = ["Entry", "Shape", "Length [cm]", "Heights St.Dev. [nm]",  "Slopes St.Dev. [" + u"\u03BC" + "rad]"]

        self.table.setHorizontalHeaderLabels(horHeaders)
        self.table.resizeRowsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemClicked.connect(self.table_item_clicked)

        self.scrollarea.setWidget(self.table)
        self.scrollarea.setWidgetResizable(1)

        output_profile_box = oasysgui.widgetBox(tab_input, "Surface Generation Parameters", addSpace=True, orientation="vertical", height=190, width=470)

        oasysgui.lineEdit(output_profile_box, self, "dimension_x", "Width [cm]",
                           labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(output_profile_box, self, "step_x", "Step Width [cm]",
                           labelWidth=300, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(output_profile_box, self, "scale_factor_y", "Scale Factor for Length",
                           labelWidth=300, valueType=float, orientation="horizontal")

        gui.comboBox(output_profile_box, self, "renormalize_y", label="Renormalize Length Profile to different RMS", labelWidth=300,
                     items=["No", "Yes"], callback=self.set_RenormalizeY, sendSelectedValue=False, orientation="horizontal")

        self.output_profile_box_1 = oasysgui.widgetBox(output_profile_box, "", addSpace=True, orientation="vertical", width=450)

        gui.comboBox(self.output_profile_box_1, self, "error_type_y", label="Normalization to", labelWidth=270,
                     items=["Figure Error (nm)", "Slope Error (" + u"\u03BC" + "rad)"],
                     sendSelectedValue=False, orientation="horizontal")

        oasysgui.lineEdit(self.output_profile_box_1, self, "rms_y", "Rms Value",
                           labelWidth=300, valueType=float, orientation="horizontal")

        self.set_RenormalizeY()

        output_box = oasysgui.widgetBox(tab_input, "Outputs", addSpace=True, orientation="vertical", width=470)

        select_file_box = oasysgui.widgetBox(output_box, "", addSpace=True, orientation="horizontal")

        self.le_heigth_profile_file_name = oasysgui.lineEdit(select_file_box, self, "heigth_profile_file_name", "Output File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        pushButton = gui.button(select_file_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        self.shadow_output = QTextEdit()
        self.shadow_output.setReadOnly(True)

        out_box = oasysgui.widgetBox(tab_out, "System Output", addSpace=True, orientation="horizontal", height=600)
        out_box.layout().addWidget(self.shadow_output)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Height Profile", callback=self.calculate_heigth_profile)
        button.setFixedHeight(45)
        button.setFixedWidth(170)

        button = gui.button(button_box, self, "Generate Height Profile File", callback=self.generate_heigth_profile_file)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(200)

        button = gui.button(button_box, self, "Reset Fields", callback=self.call_reset_settings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(120)

        gui.rubber(self.controlArea)

        self.initializeTabs()

        gui.rubber(self.mainArea)


    def initializeTabs(self):
        self.tabs = gui.tabWidget(self.mainArea)

        self.tab = [gui.createTabPage(self.tabs, "Info"),
                    gui.createTabPage(self.tabs, "Heights Profile"),
                    gui.createTabPage(self.tabs, "Slopes Profile"),
                    gui.createTabPage(self.tabs, "PSD Heights"),
                    gui.createTabPage(self.tabs, "CSD Heights"),
                    gui.createTabPage(self.tabs, "ACF"),
                    gui.createTabPage(self.tabs, "Generated 2D Profile"),
        ]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas = [None, None, None, None, None, None]

        self.plot_canvas[0] = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.plot_canvas[0].setDefaultPlotLines(True)
        self.plot_canvas[0].setActiveCurveColor(color='darkblue')
        self.plot_canvas[0].setGraphXLabel("Y [cm]")
        self.plot_canvas[0].setGraphYLabel("Z [nm]")
        self.plot_canvas[0].setGraphTitle("Heights Profile")
        self.plot_canvas[0].setDrawModeEnabled(True, 'rectangle')
        self.plot_canvas[0].setZoomModeEnabled(True)

        self.plot_canvas[1] = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.plot_canvas[1].setDefaultPlotLines(True)
        self.plot_canvas[1].setActiveCurveColor(color='darkblue')
        self.plot_canvas[1].setGraphXLabel("Y [cm]")
        self.plot_canvas[1].setGraphYLabel("Zp [$\mu$rad]")
        self.plot_canvas[1].setGraphTitle("Slopes Profile")
        self.plot_canvas[1].setDrawModeEnabled(True, 'rectangle')
        self.plot_canvas[1].setZoomModeEnabled(True)

        self.plot_canvas[2] = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.plot_canvas[2].setDefaultPlotLines(True)
        self.plot_canvas[2].setActiveCurveColor(color='darkblue')
        self.plot_canvas[2].setGraphXLabel("f [m^-1]")
        self.plot_canvas[2].setGraphYLabel("PSD [m^3]")
        self.plot_canvas[2].setGraphTitle("Power Spectral Density of Heights Profile")
        self.plot_canvas[2].setDrawModeEnabled(True, 'rectangle')
        self.plot_canvas[2].setZoomModeEnabled(True)
        self.plot_canvas[2].setXAxisLogarithmic(True)
        self.plot_canvas[2].setYAxisLogarithmic(True)

        self.plot_canvas[3] = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.plot_canvas[3].setDefaultPlotLines(True)
        self.plot_canvas[3].setActiveCurveColor(color='darkblue')
        self.plot_canvas[3].setGraphXLabel("f [m^-1]")
        self.plot_canvas[3].setGraphYLabel("CSD [m^3]")
        self.plot_canvas[3].setGraphTitle("Cumulative Spectral Density of Heights Profile")
        self.plot_canvas[3].setDrawModeEnabled(True, 'rectangle')
        self.plot_canvas[3].setZoomModeEnabled(True)
        self.plot_canvas[3].setXAxisLogarithmic(True)

        self.plot_canvas[4] = PlotWindow(roi=False, control=False, position=False, plugins=False)
        self.plot_canvas[4].setDefaultPlotLines(True)
        self.plot_canvas[4].setActiveCurveColor(color='darkblue')
        self.plot_canvas[4].setGraphXLabel("Length [m]")
        self.plot_canvas[4].setGraphYLabel("ACF")
        self.plot_canvas[4].setGraphTitle("Autocovariance Function of Heights Profile")
        self.plot_canvas[4].setDrawModeEnabled(True, 'rectangle')
        self.plot_canvas[4].setZoomModeEnabled(True)

        self.figure = Figure(figsize=(self.IMAGE_WIDTH, self.IMAGE_HEIGHT))
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')

        self.axis.set_xlabel("X (cm)")
        self.axis.set_ylabel("Y (cm)")
        self.axis.set_zlabel("Z (nm)")

        self.plot_canvas[5] = FigureCanvasQTAgg(self.figure)

        self.profileInfo = QTextEdit()
        self.profileInfo.setReadOnly(True)
        self.profileInfo.setMinimumHeight(self.IMAGE_HEIGHT-10)
        self.profileInfo.setMaximumHeight(self.IMAGE_HEIGHT-10)
        self.profileInfo.setMinimumWidth(self.IMAGE_WIDTH-10)
        self.profileInfo.setMaximumWidth(self.IMAGE_WIDTH-10)

        profile_box = oasysgui.widgetBox(self.tab[0], "", addSpace=True, orientation="horizontal", height = self.IMAGE_HEIGHT, width = self.IMAGE_WIDTH)
        profile_box.layout().addWidget(self.profileInfo)

        for index in range(0, 6):
            self.tab[index+1].layout().addWidget(self.plot_canvas[index])

        self.tabs.setCurrentIndex(1)

    def plot_dabam_graph(self, plot_canvas_index, curve_name, x_values, y_values, xtitle, ytitle, color='blue', replace=True):
        self.plot_canvas[plot_canvas_index].addCurve(x_values, y_values, curve_name, symbol='', color=color, replace=replace) #'+', '^', ','
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].replot()

    def set_RenormalizeY(self):
        self.output_profile_box_1.setVisible(self.renormalize_y==1)

    def table_item_clicked(self):
        if self.table.selectionModel().hasSelection():
            row = self.table.selectionModel().selectedRows()[0].row()
            entry = int(self.table.item(row, 0).text())

            self.server.load(entry)

            self.profileInfo.setText(self.server.info_profiles())

            if self.use_undetrended == 0:
                self.plot_canvas[0].setGraphTitle("Heights Profile. St.Dev.=%.3f nm"%(self.server.stdev_profile_heights()*1e9))
                self.plot_canvas[1].setGraphTitle("Slopes Profile. St.Dev.=%.3f $\mu$rad"%(self.server.stdev_profile_slopes()*1e6))
                self.plot_dabam_graph(0, "heights_profile", 1e2*self.server.y, 1e9*self.server.zHeights, "Y [cm]", "Z [nm]")
                self.plot_dabam_graph(1, "slopes_profile", 1e2*self.server.y, 1e6*self.server.zSlopes, "Y [cm]", "Zp [$\mu$rad]")
            else:
                self.plot_canvas[0].setGraphTitle("Heights Profile. St.Dev.=%.3f nm"%(self.server.stdev_profile_heights()*1e9))
                self.plot_canvas[1].setGraphTitle("Slopes Profile. St.Dev.=%.3f $\mu$rad"%(self.server.stdev_profile_slopes()*1e6))
                self.plot_dabam_graph(0, "heights_profile", 1e2*self.server.y, 1e9*self.server.zHeightsUndetrended, "Y [cm]", "Z [nm]")
                self.plot_dabam_graph(1, "slopes_profile", 1e2*self.server.y, 1e6*self.server.zSlopesUndetrended, "Y [cm]", "Zp [$\mu$rad]")

            y = self.server.f**(self.server.powerlaw["hgt_pendent"])*10**self.server.powerlaw["hgt_shift"]
            i0 = self.server.powerlaw["index_from"]
            i1 = self.server.powerlaw["index_to"]
            beta = -self.server.powerlaw["hgt_pendent"]
            self.plot_canvas[2].setGraphTitle("Power Spectral Density of Heights Profile (beta=%.2f,Df=%.2f)"%(beta,(5-beta)/2))
            self.plot_dabam_graph(2, "psd_heights_2", self.server.f, self.server.psdHeights, "f [m^-1]", "PSD [m^3]")
            self.plot_dabam_graph(2, "psd_heights_1", self.server.f, y, "f [m^-1]", "PSD [m^3]", color='green', replace=False)
            self.plot_dabam_graph(2, "psd_heights_3", self.server.f[i0:i1], y[i0:i1], "f [m^-1]", "PSD [m^3]", color='red', replace=False)

            self.plot_dabam_graph(3, "csd", self.server.f,self.server.csd_heights(), "f [m^-1]", "CSD [m^3]")

            c1,c2,c3 = dabam.autocorrelationfunction(self.server.y,self.server.zHeights)
            self.plot_canvas[4].setGraphTitle("Autocovariance Function of Heights Profile.\nAutocorrelation Length (ACF=0.5)=%.3f m"%(c3))
            self.plot_dabam_graph(4, "acf", c1[0:-1], c2, "Length [m]", "Heights Autocovariance")

        if (self.tabs.currentIndex()==6): self.tabs.setCurrentIndex(1)

    def search_profiles(self):
        self.table.itemClicked.disconnect(self.table_item_clicked)
        self.table.clear()

        row_count = self.table.rowCount()
        for n in range(0, row_count):
            self.table.removeRow(0)

        profiles = dabam.dabam_summary_dictionary(surface=self.get_dabam_shape(),
                                                  slp_err_from=self.slope_error_from*1e-6,
                                                  slp_err_to=self.slope_error_to*1e-6,
                                                  length_from=self.dimension_y_from*1e-2,
                                                  length_to=self.dimension_y_to*1e-2)

        for index in range(0, len(profiles)):
            self.table.insertRow(0)

        for index in range(0, len(profiles)):
            table_item = QTableWidgetItem(str(profiles[index]["entry"]))
            table_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(index, 0, table_item)
            table_item = QTableWidgetItem(str(profiles[index]["surface"]))
            table_item.setTextAlignment(Qt.AlignLeft)
            self.table.setItem(index, 1, table_item)
            table_item = QTableWidgetItem(str(numpy.round(profiles[index]["length"]*1e2, 3)))
            table_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(index, 2, table_item)
            table_item = QTableWidgetItem(str(numpy.round(profiles[index]["hgt_err"]*1e9, 3)))
            table_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(index, 3, table_item)
            table_item = QTableWidgetItem(str(numpy.round(profiles[index]["slp_err"]*1e6, 3)))
            table_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(index, 4, table_item)

        horHeaders = ["Entry", "Shape", "Length [cm]", "Height Error [nm]",  "Slope Error [" + "\u03BC" + "rad]"]

        self.table.setHorizontalHeaderLabels(horHeaders)
        self.table.resizeRowsToContents()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.table.itemClicked.connect(self.table_item_clicked)

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
        try:
            if self.server.y is None: raise Exception("No Profile Selected")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            self.check_fields()

            combination = "EF"

            profile_1D_y_x = 1e2*self.server.y*self.scale_factor_y
            if self.use_undetrended == 0: profile_1D_y_y = 1e2*self.server.zHeights
            else: profile_1D_y_y = 1e2*self.server.zHeightsUndetrended

            if self.renormalize_y == 0:
                rms_y = None
            else:
                if self.error_type_y == profiles_simulation.FIGURE_ERROR:
                    rms_y = self.rms_y*1e-7 # from nm to cm
                else:
                    rms_y = self.rms_y*1e-6 # from urad to rad

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
            self.zz = zz # in cm

            self.axis.clear()

            x_to_plot, y_to_plot = numpy.meshgrid(xx, yy)
            z_to_plot = zz*1e7 #nm

            self.axis.plot_surface(x_to_plot, y_to_plot, z_to_plot,
                                   rstride=1, cstride=1, cmap=cm.autumn, linewidth=0.5, antialiased=True)

            slope, sloperms = ST.slopes(zz.T, xx, yy)

            slope_rms_x = sloperms[0]*1e6
            slope_rms_y = sloperms[1]*1e6

            title = ' Slope error rms in X direction: %f $\mu$rad' % (slope_rms_x) + '\n' + \
                    ' Slope error rms in Y direction: %f $\mu$rad' % (slope_rms_y)

            self.axis.set_xlabel("X (cm)")
            self.axis.set_ylabel("Y (cm)")
            self.axis.set_zlabel("Z (nm)")

            self.axis.set_title(title)
            self.axis.mouse_init()

            if not not_interactive_mode:
                try:
                    self.plot_canvas[5].draw()
                except:
                    pass

                self.tabs.setCurrentIndex(6)

                QMessageBox.information(self, "QMessageBox.information()",
                                        "Height Profile calculated: if the result is satisfactory,\nclick \'Generate Height Profile File\' to complete the operation ",
                                        QMessageBox.Ok)
        except Exception as exception:
            QMessageBox.critical(self, "Error",
                                 exception.args[0],
                                 QMessageBox.Ok)
            #raise exception

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

                self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=self.heigth_profile_file_name,
                                                                      error_profile_x_dim=self.dimension_x,
                                                                      error_profile_y_dim=1e2*(self.server.y[-1]-self.server.y[0])))
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
        self.le_heigth_profile_file_name.setText(oasysgui.selectFileFromDialog(self, self.heigth_profile_file_name, "Select Output File", file_extension_filter="*.dat"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWdabam_height_profile()
    w.show()
    app.exec()
    w.saveSettings()
