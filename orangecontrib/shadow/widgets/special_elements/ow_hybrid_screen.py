__author__ = 'labx'

import os, sys, numpy
import orangecanvas.resources as resources
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.util.oasys_util import EmittingStream, TriggerIn

from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.util.shadow_objects import ShadowBeam

from PyQt5.QtGui import QImage, QPixmap,  QPalette, QFont, QColor, QTextCursor
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QMessageBox

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement
from orangecontrib.shadow.widgets.special_elements import hybrid_control

from silx.gui.plot.ImageView import ImageView

class HybridScreen(AutomaticElement):

    inputs = [("Input Beam", ShadowBeam, "setBeam"),]

    outputs = [{"name":"Output Beam (Far Field)",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam_ff"},
               {"name":"Output Beam (Near Field)",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam_nf"},
               {"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    name = "Hybrid Screen"
    description = "Shadow HYBRID: Hybrid Screen"
    icon = "icons/hybrid_screen.png"
    maintainer = "Luca Rebuffi and Xianbo Shi"
    maintainer_email = "lrebuffi(@at@)anl.gov, xshi(@at@)aps.anl.gov"
    priority = 4
    category = "HYBRID"
    keywords = ["data", "file", "load", "read"]

    want_control_area = 1
    want_main_area = 1

    ghy_diff_plane = Setting(1)
    ghy_calcType = Setting(2)

    focal_length_calc = Setting(0)
    ghy_focallength = Setting(0.0)
    distance_to_image_calc = Setting(0)
    ghy_distance = Setting(0.0)

    ghy_nf = Setting(0)

    ghy_nbins_x = Setting(100)
    ghy_nbins_z = Setting(100)
    ghy_npeak = Setting(10)
    ghy_fftnpts = Setting(1e6)

    file_to_write_out = Setting(0)

    ghy_automatic = Setting(1)

    input_beam = None

    TABS_AREA_HEIGHT = 560
    CONTROL_AREA_WIDTH = 405

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 545

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Run Hybrid", self)
        self.runaction.triggered.connect(self.run_hybrid)
        self.addAction(self.runaction)

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run HYBRID", callback=self.run_hybrid)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        main_tabs = oasysgui.tabWidget(self.mainArea)
        plot_tab = oasysgui.createTabPage(main_tabs, "Plots")
        out_tab = oasysgui.createTabPage(main_tabs, "Output")

        self.tabs = oasysgui.tabWidget(plot_tab)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(tabs_setting, "Advanced Setting")

        box_1 = oasysgui.widgetBox(tab_bas, "Calculation Parameters", addSpace=True, orientation="vertical", height=110)

        gui.comboBox(box_1, self, "ghy_diff_plane", label="Diffraction Plane", labelWidth=310,
                     items=["Sagittal", "Tangential", "Both (2D)", "Both (1D+1D)"],
                     callback=self.set_DiffPlane,
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(box_1, self, "ghy_calcType", label="Calculation", labelWidth=70,
                     items=["Diffraction by Simple Aperture",
                            "Diffraction by Mirror or Grating Size",
                            "Diffraction by Mirror Size + Figure Errors",
                            "Diffraction by Grating Size + Figure Errors",
                            "Diffraction by Lens/C.R.L./Transfocator Size",],
                     callback=self.set_CalculationType,
                     sendSelectedValue=False, orientation="horizontal")

        gui.separator(box_1, 10)


        box_2 = oasysgui.widgetBox(tab_bas, "Numerical Control Parameters", addSpace=True, orientation="vertical", height=140)

        self.le_nbins_x = oasysgui.lineEdit(box_2, self, "ghy_nbins_x", "Number of bins for I(Sagittal) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_nbins_z = oasysgui.lineEdit(box_2, self, "ghy_nbins_z", "Number of bins for I(Tangential) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_npeak   = oasysgui.lineEdit(box_2, self, "ghy_npeak", "Number of diffraction peaks", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_fftnpts = oasysgui.lineEdit(box_2, self, "ghy_fftnpts", "Number of points for FFT", labelWidth=260, valueType=int, orientation="horizontal")

        box_3 = oasysgui.widgetBox(tab_adv, "Propagation Parameters", addSpace=True, orientation="vertical", height=200)


        self.cb_focal_length_calc = gui.comboBox(box_3, self, "focal_length_calc", label="Focal Length", labelWidth=180,
                     items=["Use O.E. Focal Distance", "Specify Value"],
                     callback=self.set_FocalLengthCalc,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_focal_length = oasysgui.lineEdit(box_3, self, "ghy_focallength", "Focal Length value", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(box_3)

        self.cb_distance_to_image_calc = gui.comboBox(box_3, self, "distance_to_image_calc", label="Distance to image", labelWidth=150,
                     items=["Use O.E. Image Plane Distance", "Specify Value"],
                     callback=self.set_DistanceToImageCalc,
                     sendSelectedValue=False, orientation="horizontal")

        self.le_distance_to_image = oasysgui.lineEdit(box_3, self, "ghy_distance", "Distance to Image value", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(box_3)

        self.cb_nf = gui.comboBox(box_3, self, "ghy_nf", label="Near Field Calculation", labelWidth=310,
                                             items=["No", "Yes"],
                                             sendSelectedValue=False, orientation="horizontal", callback=self.set_NF)


        box_4 = oasysgui.widgetBox(tab_adv, "Geometrical Parameters", addSpace=True, orientation="vertical", height=70)

        gui.comboBox(box_4, self, "ghy_automatic", label="Analize geometry to avoid unuseful calculations", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        self.set_DiffPlane()
        self.set_DistanceToImageCalc()
        self.set_CalculationType()
        self.set_NF()

        self.initializeTabs()

        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=220,
                     items=["None", "Debug (star.xx)"],
                     sendSelectedValue=False,
                     orientation="horizontal")

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

    def after_change_workspace_units(self):
        label = self.le_focal_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_distance_to_image.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def initializeTabs(self):
        self.tabs.clear()

        if self.ghy_diff_plane < 2:
            if self.ghy_nf == 1:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field")
                            ]
            else:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")
                            ]
        elif self.ghy_diff_plane == 2:
             self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                        gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")
                        ]
        elif self.ghy_diff_plane == 3:
            if self.ghy_nf == 1:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (T)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")
                            ]
            else:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")
                            ]

        for tab in self.tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas = [None, None, None, None, None, None]

    def plot_xy(self, beam_out, progressBarValue, var_x, var_y, plot_canvas_index, title, xtitle, ytitle, xum="", yum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedPlotWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_xy(beam_out._beam, var_x, var_y, title, xtitle, ytitle, xum=xum, yum=yum, conv=self.workspace_units_to_cm)

        self.progressBarSet(progressBarValue)

    def plot_histo(self, beam_out, progressBarValue, var, plot_canvas_index, title, xtitle, ytitle, xum=""):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ShadowPlot.DetailedHistoWidget()
            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.plot_canvas[plot_canvas_index].plot_histo(beam_out._beam, var, 1, None, 23, title, xtitle, ytitle, xum=xum, conv=self.workspace_units_to_cm)

        self.progressBarSet(progressBarValue)

    def plot_emtpy(self, progressBarValue, plot_canvas_index):
        if self.plot_canvas[plot_canvas_index] is None:
            widget = QWidget()
            widget.setLayout(QHBoxLayout())
            label = QLabel(widget)
            label.setPixmap(QPixmap(QImage(os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.special_elements"), "icons", "no_result.png"))))

            widget.layout().addWidget(label)

            self.plot_canvas[plot_canvas_index] = widget

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        self.progressBarSet(progressBarValue)

    def plot_xy_hybrid(self, progressBarValue, scaled_matrix, plot_canvas_index, title, xtitle, ytitle, var1, var2):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = ImageView()
            self.plot_canvas[plot_canvas_index].setColormap({"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256})
            self.plot_canvas[plot_canvas_index].setMinimumWidth(590)
            self.plot_canvas[plot_canvas_index].setMaximumWidth(590)

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        factor1 = ShadowPlot.get_factor(var1, self.workspace_units_to_cm)
        factor2 = ShadowPlot.get_factor(var2, self.workspace_units_to_cm)

        xmin, xmax = min(scaled_matrix.x_coord), max(scaled_matrix.x_coord)
        ymin, ymax = min(scaled_matrix.y_coord), max(scaled_matrix.y_coord)

        dim_x, dim_y = scaled_matrix.shape()

        origin = (xmin*factor1, ymin*factor2)
        scale = (abs((xmax-xmin)/dim_x)*factor1, abs((ymax-ymin)/dim_y)*factor2)

        data_to_plot = []
        for y_index in range(0, dim_y):
            x_values = []
            for x_index in range(0, dim_x):
                x_values.append(scaled_matrix.z_values[x_index, y_index])

            data_to_plot.append(x_values)

        self.plot_canvas[plot_canvas_index].setImage(numpy.array(data_to_plot), origin=origin, scale=scale)
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)

        self.progressBarSet(progressBarValue)


    def plot_histo_hybrid(self, progressBarValue, scaled_array, plot_canvas_index, title, xtitle, ytitle, var):
        if self.plot_canvas[plot_canvas_index] is None:
            self.plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')
            self.plot_canvas[plot_canvas_index].setInteractiveMode(mode='zoom')

            self.tab[plot_canvas_index].layout().addWidget(self.plot_canvas[plot_canvas_index])

        factor = ShadowPlot.get_factor(var, self.workspace_units_to_cm)

        self.plot_canvas[plot_canvas_index].addCurve(scaled_array.scale*factor, scaled_array.np_array, "crv_"+ytitle, symbol='', color="blue", replace=True) #'+', '^', ','
        self.plot_canvas[plot_canvas_index]._backend.ax.get_yaxis().get_major_formatter().set_useOffset(True)
        self.plot_canvas[plot_canvas_index]._backend.ax.get_yaxis().get_major_formatter().set_scientific(True)
        self.plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.plot_canvas[plot_canvas_index].setGraphTitle(title)
        self.plot_canvas[plot_canvas_index].replot()

        self.progressBarSet(progressBarValue)

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                if self.is_automatic_run:
                    self.run_hybrid()

    def set_DiffPlane(self):
        self.le_nbins_x.setEnabled(self.ghy_diff_plane == 0 or self.ghy_diff_plane == 2)
        self.le_nbins_z.setEnabled(self.ghy_diff_plane == 1 or self.ghy_diff_plane == 2)

        if self.ghy_calcType > 0 and self.ghy_calcType < 4 and self.ghy_diff_plane != 2:
            self.cb_nf.setEnabled(True)
        else:
            self.cb_nf.setEnabled(False)
            self.ghy_nf = 0

        self.set_NF()

    def set_CalculationType(self):
        if self.ghy_calcType > 0 and self.ghy_calcType < 4 and self.ghy_diff_plane != 2:
            self.cb_nf.setEnabled(True)
        else:
            self.cb_nf.setEnabled(False)
            self.ghy_nf = 0

        self.set_NF()

    def set_NF(self):
        if self.ghy_nf == 0:
            self.focal_length_calc = 0
            self.distance_to_image_calc = 0
            self.cb_focal_length_calc.setEnabled(False)
            self.le_focal_length.setEnabled(False)
        else:
            self.cb_focal_length_calc.setEnabled(True)
            self.le_focal_length.setEnabled(True)

        self.set_FocalLengthCalc()

    def set_FocalLengthCalc(self):
         self.le_focal_length.setEnabled(self.focal_length_calc == 1)

    def set_DistanceToImageCalc(self):
         self.le_distance_to_image.setEnabled(self.distance_to_image_calc == 1)

    def run_hybrid(self):
        try:
            self.setStatusMessage("")
            self.progressBarInit()
            self.initializeTabs()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    sys.stdout = EmittingStream(textWritten=self.write_stdout)

                    self.check_fields()

                    input_parameters = hybrid_control.HybridInputParameters()
                    input_parameters.ghy_lengthunit = self.workspace_units
                    input_parameters.widget = self
                    input_parameters.shadow_beam = self.input_beam
                    input_parameters.ghy_diff_plane = self.ghy_diff_plane + 1
                    input_parameters.ghy_calcType = self.ghy_calcType + 1

                    if self.distance_to_image_calc == 0:
                        input_parameters.ghy_distance = -1
                    else:
                        input_parameters.ghy_distance = self.ghy_distance

                    if self.focal_length_calc == 0:
                        input_parameters.ghy_focallength = -1
                    else:
                        input_parameters.ghy_focallength = self.ghy_focallength

                    if self.ghy_calcType != 0:
                        input_parameters.ghy_nf = self.ghy_nf
                    else:
                        input_parameters.ghy_nf = 0

                    input_parameters.ghy_nbins_x = int(self.ghy_nbins_x)
                    input_parameters.ghy_nbins_z = int(self.ghy_nbins_z)
                    input_parameters.ghy_npeak = int(self.ghy_npeak)
                    input_parameters.ghy_fftnpts = int(self.ghy_fftnpts)
                    input_parameters.file_to_write_out = self.file_to_write_out

                    input_parameters.ghy_automatic = self.ghy_automatic

                    calculation_parameters = hybrid_control.hy_run(input_parameters)

                    self.ghy_focallength = input_parameters.ghy_focallength
                    self.ghy_distance = input_parameters.ghy_distance
                    self.ghy_nbins_x = int(input_parameters.ghy_nbins_x)
                    self.ghy_nbins_z = int(input_parameters.ghy_nbins_z)
                    self.ghy_npeak   = int(input_parameters.ghy_npeak)
                    self.ghy_fftnpts = int(input_parameters.ghy_fftnpts)

                    if input_parameters.ghy_calcType == 3 or input_parameters.ghy_calcType == 4:
                        do_plot_x = True
                        do_plot_z = True
                    else:
                        if self.ghy_automatic == 1:
                            do_plot_x = not calculation_parameters.beam_not_cut_in_x
                            do_plot_z = not calculation_parameters.beam_not_cut_in_z
                        else:
                            do_plot_x = True
                            do_plot_z = True

                    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

                    if do_plot_x or do_plot_z:
                        self.setStatusMessage("Plotting Results")

                    if self.ghy_diff_plane == 0:
                        if do_plot_x:
                            if do_nf:
                                self.plot_histo_hybrid(84, calculation_parameters.dif_xp, 0, title=u"\u2206" + "Xp", xtitle=r'$\Delta$Xp [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo(calculation_parameters.ff_beam, 88, 1, plot_canvas_index=1, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                                self.plot_histo_hybrid(92, calculation_parameters.dif_x, 2, title=u"\u2206" + "X", xtitle=r'$\Delta$X [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                                self.plot_histo(calculation_parameters.nf_beam, 96, 1, plot_canvas_index=3, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_xp, 0, title=u"\u2206" + "Xp", xtitle=r'$\Delta$Xp [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo(calculation_parameters.ff_beam, 96, 1, plot_canvas_index=1, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                        else:
                            if do_nf:
                                self.plot_emtpy(84, 0)
                                self.plot_emtpy(88, 1)
                                self.plot_emtpy(92, 2)
                                self.plot_emtpy(96, 3)
                            else:
                                self.plot_emtpy(88, 0)
                                self.plot_emtpy(96, 1)
                    elif self.ghy_diff_plane == 1:
                        if do_plot_z:
                            if do_nf:
                                self.plot_histo_hybrid(84, calculation_parameters.dif_zp, 0, title=u"\u2206" + "Zp", xtitle=r'$\Delta$Zp [$\mu$rad]', ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo(calculation_parameters.ff_beam, 84, 3, plot_canvas_index=1, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                                self.plot_histo_hybrid(88, calculation_parameters.dif_z, 2, title=u"\u2206" + "Z", xtitle=r'$\Delta$Z [$\mu$m]', ytitle=r'Arbitrary Units', var=2)
                                self.plot_histo(calculation_parameters.nf_beam, 96, 3, plot_canvas_index=3, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_zp, 0, title=u"\u2206" + "Zp", xtitle=r'$\Delta$Zp [$\mu$rad]', ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo(calculation_parameters.ff_beam, 96, 3, plot_canvas_index=1, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                        else:
                            if do_nf:
                                self.plot_emtpy(84, 0)
                                self.plot_emtpy(88, 1)
                                self.plot_emtpy(92, 2)
                                self.plot_emtpy(96, 3)
                            else:
                                self.plot_emtpy(88, 0)
                                self.plot_emtpy(96, 1)

                    elif self.ghy_diff_plane == 2:
                        if do_plot_x and do_plot_z:
                            self.plot_xy_hybrid(88, calculation_parameters.dif_xpzp, plot_canvas_index=0, title="X',Z'",
                                            xtitle="X' [$\mu$rad]", ytitle="Z' [$\mu$rad]", var1=4, var2=6)
                            self.plot_xy(calculation_parameters.ff_beam, 96, 1, 3, plot_canvas_index=1, title="X,Z",
                                            xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))

                        else:
                            if do_plot_x:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_xp, plot_canvas_index=0, title=u"\u2206" + "X'", xtitle="$\Delta$X' [$\mu$rad]", ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo(calculation_parameters.ff_beam, 96, 1, plot_canvas_index=1, title="X",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                            elif do_plot_z:
                                print(type(calculation_parameters.dif_zp))

                                self.plot_histo_hybrid(88, calculation_parameters.dif_zp, 0, title=u"\u2206" + "Z'", xtitle="$\Delta$Z' [$\mu$rad]", ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo(calculation_parameters.ff_beam, 96, 3, plot_canvas_index=1, title="Z",
                                                xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_emtpy(88, 0)
                                self.plot_emtpy(96, 1)

                    elif self.ghy_diff_plane == 3:
                        if do_plot_x:
                            if do_nf:
                                self.plot_histo_hybrid(82, calculation_parameters.dif_xp, 0, title=u"\u2206" + "X'", xtitle="$\Delta$X' [$\mu$rad]", ytitle=r'Arbitrary Units', var=4)
                                self.plot_histo_hybrid(84, calculation_parameters.dif_x, 1, title=u"\u2206" + "X", xtitle=r'$\Delta$X [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                            else:
                                self.plot_histo_hybrid(84, calculation_parameters.dif_xp, 0, title=u"\u2206" + "X'", xtitle="$\Delta$X' [$\mu$rad]", ytitle=r'Arbitrary Units', var=4)
                        else:
                            if do_nf:
                                self.plot_emtpy(82, 0)
                                self.plot_emtpy(84, 1)
                            else:
                                self.plot_emtpy(84, 0)

                        if do_plot_z:
                            if do_nf:
                                self.plot_histo_hybrid(86, calculation_parameters.dif_zp, 2, title=u"\u2206" + "Z''", xtitle="$\Delta$Z' [$\mu$rad]", ytitle=r'Arbitrary Units', var=6)
                                self.plot_histo_hybrid(88, calculation_parameters.dif_z, 3, title=u"\u2206" + "Z", xtitle=r'$\Delta$Z [$\mu$m]', ytitle=r'Arbitrary Units', var=2)
                            else:
                                self.plot_histo_hybrid(88, calculation_parameters.dif_zp, 1, title=u"\u2206" + "Z'", xtitle="$\Delta$Z' [$\mu$rad]", ytitle=r'Arbitrary Units', var=6)
                        else:
                            if do_nf:
                                self.plot_emtpy(86, 2)
                                self.plot_emtpy(88, 3)
                            else:
                                self.plot_emtpy(88, 1)

                        if (do_plot_x or do_plot_z):
                            if do_nf:
                                self.plot_xy(calculation_parameters.nf_beam, 94, 1, 3, plot_canvas_index=4, title="X,Z",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                                self.plot_xy(calculation_parameters.ff_beam, 98, 1, 3, plot_canvas_index=5, title="X,Z",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                            else:
                                self.plot_xy(calculation_parameters.ff_beam, 96, 1, 3, plot_canvas_index=2, title="X,Z",
                                                xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                        else:
                            if do_nf:
                                self.plot_emtpy(94, 4)
                                self.plot_emtpy(98, 5)
                            else:
                                self.plot_emtpy(94, 0)

                    if not calculation_parameters.ff_beam is None:
                        calculation_parameters.ff_beam.setScanningData(self.input_beam.scanned_variable_data)

                    self.send("Output Beam (Far Field)", calculation_parameters.ff_beam)

                    if do_nf and not calculation_parameters.nf_beam is None:
                        calculation_parameters.nf_beam.setScanningData(self.input_beam.scanned_variable_data)

                        self.send("Output Beam (Near Field)", calculation_parameters.nf_beam)

                    self.send("Trigger", TriggerIn(new_object=True))
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.setStatusMessage("")
        self.progressBarFinished()

    def check_fields(self):
        if self.focal_length_calc == 1:
            congruence.checkPositiveNumber(self.ghy_focallength, "Focal Length value")

        if self.distance_to_image_calc == 1:
            congruence.checkPositiveNumber(self.ghy_distance, "Distance to image value")

        if self.ghy_diff_plane == 0 or self.ghy_diff_plane == 2:
            congruence.checkStrictlyPositiveNumber(self.ghy_nbins_x, "Number of bins for I(Sagittal) histogram")
        if self.ghy_diff_plane == 1 or self.ghy_diff_plane == 2:
            congruence.checkStrictlyPositiveNumber(self.ghy_nbins_z, "Number of bins for I(Tangential) histogram")

        congruence.checkStrictlyPositiveNumber(self.ghy_npeak, "Number of diffraction peaks")
        congruence.checkStrictlyPositiveNumber(self.ghy_fftnpts, "Number of points for FFT")

    def set_progress_bar(self, value):
        if value >= 100:
            self.progressBarFinished()
        elif value <=0:
            self.progressBarInit()
        else:
            self.progressBarSet(value)

    def status_message(self, message):
        self.setStatusMessage(message)

    def write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

