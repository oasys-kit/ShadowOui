__author__ = 'labx'

import os, sys, numpy

import orangecanvas.resources as resources
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.util.oasys_util import EmittingStream, TriggerIn
from oasys.util.oasys_objects import OasysThicknessErrorsData
import oasys.util.oasys_util as OU

from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPlot
from orangecontrib.shadow.util.shadow_objects import ShadowBeam

from PyQt5.QtGui import QImage, QPixmap,  QPalette, QFont, QColor, QTextCursor
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout, QMessageBox

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

from silx.gui.plot.ImageView import ImageView

from hybrid_methods.coherence.hybrid_screen import HybridListener, HybridScreenManager, \
    HybridCalculationType, HybridPropagationType, HybridDiffractionPlane, \
    HybridInputParameters, HybridCalculationResult, HybridGeometryAnalysis
from orangecontrib.shadow.widgets.special_elements.bl.shadow_hybrid_screen import ShadowHybridOE, ShadowHybridBeam, IMPLEMENTATION

class HybridScreenNew(AutomaticElement, HybridListener):
    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("Thickness Errors Data", OasysThicknessErrorsData, "setThicknessErrorProfiles")]

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

    name = "Hybrid Screen (Beta)"
    description = "Shadow HYBRID: Hybrid Screen (Beta)"
    icon = "icons/beta_hybrid_screen.png"
    maintainer = "Luca Rebuffi and Xianbo Shi"
    maintainer_email = "lrebuffi(@at@)anl.gov, xshi(@at@)aps.anl.gov"
    priority = 4
    category = "HYBRID"
    keywords = ["data", "file", "load", "read"]

    want_control_area = 1
    want_main_area = 1

    view_type = Setting(1)
    send_original_beam = Setting(0)

    diffraction_plane = Setting(1)
    calculation_type = Setting(2)

    focal_length_calculation = Setting(0)
    focal_length = Setting(0.0)
    focal_length_calculated = 0.0
    propagation_distance_calculation = Setting(0)
    propagation_distance = Setting(0.0)

    propagation_type = Setting(0)

    n_bins_x = Setting(100)
    n_bins_z = Setting(100)
    n_peaks = Setting(10)
    fft_n_pts = Setting(1e5)

    file_to_write_out = Setting(0)

    analyze_geometry = Setting(1)

    crl_error_profiles = Setting([])
    crl_material_data = Setting(0)
    crl_material = Setting("Be")
    crl_delta = Setting(1e-6)
    crl_scaling_factor = Setting(1.0)

    __input_beam = None
    __plotted_data = None

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

        view_box = oasysgui.widgetBox(plot_tab, "", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.view_type_combo = gui.comboBox(view_box_1, self, "view_type", label="Plot Results",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_PlotQuality, sendSelectedValue=False, orientation="horizontal")

        self.tabs = oasysgui.tabWidget(plot_tab)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(self.tabs_setting, "Basic Setting")
        tab_adv = oasysgui.createTabPage(self.tabs_setting, "Advanced Setting")

        box_1 = oasysgui.widgetBox(tab_bas, "Calculation Parameters", addSpace=True, orientation="vertical", height=120)

        self.cb_diffraction_plane = gui.comboBox(box_1, self, "diffraction_plane", label="Diffraction Plane", labelWidth=310,
                                                 items=["Sagittal", "Tangential", "Both (2D)", "Both (1D+1D)"],
                                                 callback=self.set_diffraction_plane,
                                                 sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(box_1, self, "calculation_type", label="Calculation", labelWidth=70,
                     items=["Diffraction by Simple Aperture",
                            "Diffraction by Mirror or Grating Size",
                            "Diffraction by Mirror Size + Figure Errors",
                            "Diffraction by Grating Size + Figure Errors",
                            "Diffraction by Lens/C.R.L./Transf. Size",
                            "Diffraction by Lens/C.R.L./Transf. Size + Thickness Errors"],
                     callback=self.set_calculation_type,
                     sendSelectedValue=False, orientation="vertical")

        gui.separator(box_1, 10)


        box_2 = oasysgui.widgetBox(tab_bas, "Numerical Control Parameters", addSpace=True, orientation="vertical", height=140)

        self.le_n_bins_x = oasysgui.lineEdit(box_2, self, "n_bins_x", "Number of bins for I(Sagittal) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_n_bins_z = oasysgui.lineEdit(box_2, self, "n_bins_z", "Number of bins for I(Tangential) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_n_peaks   = oasysgui.lineEdit(box_2, self, "n_peaks", "Number of diffraction peaks", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_fft_n_pts = oasysgui.lineEdit(box_2, self, "fft_n_pts", "Number of points for FFT", labelWidth=260, valueType=int, orientation="horizontal")

        box_3 = oasysgui.widgetBox(tab_adv, "Propagation Parameters", addSpace=True, orientation="vertical", height=240)

        self.cb_propagation_distance_calculation = gui.comboBox(box_3, self, "propagation_distance_calculation", label="Distance to image", labelWidth=150,
                                                                items=["Use O.E. Image Plane Distance", "Specify Value"],
                                                                callback=self.set_propagation_distance,
                                                                sendSelectedValue=False, orientation="horizontal")

        self.le_propagation_distance = oasysgui.lineEdit(box_3, self, "propagation_distance", "Distance to Image value", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(box_3)

        self.cb_propagation_type = gui.comboBox(box_3, self, "propagation_type", label="Propagation Type", labelWidth=310,
                                                items=["Far Field (Fraunhofer)", "Near Field (Fresnel)", "Both"],
                                                sendSelectedValue=False, orientation="horizontal", callback=self.set_propagation_type)

        self.cb_focal_length_calculation = gui.comboBox(box_3, self, "focal_length_calculation", label="Focal Length", labelWidth=180,
                                                        items=["Use O.E. Focal Distance", "Specify Value"],
                                                        callback=self.set_focal_length_calculation,
                                                        sendSelectedValue=False, orientation="horizontal")

        self.le_focal_length = oasysgui.lineEdit(box_3, self, "focal_length", "Focal Length value", labelWidth=200, valueType=float, orientation="horizontal")

        self.le_focal_length_calculated = oasysgui.lineEdit(box_3, self, "focal_length_calculated", "Focal Length calculated", labelWidth=200, valueType=float, orientation="horizontal")
        self.le_focal_length_calculated.setReadOnly(True)
        font = QFont(self.le_focal_length_calculated.font())
        font.setBold(True)
        self.le_focal_length_calculated.setFont(font)
        palette = QPalette(self.le_focal_length_calculated.palette()) # make a copy of the palette
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_focal_length_calculated.setPalette(palette)

        box_4 = oasysgui.widgetBox(tab_adv, "Calculation Congruence Parameters", addSpace=True, orientation="vertical", height=200)

        self.cb_analyze_geometry = gui.comboBox(box_4, self, "analyze_geometry", label="Analize geometry to avoid unuseful calculations", labelWidth=310,
                                                items=["No", "Yes"],
                                                sendSelectedValue=False, orientation="horizontal")


        gui.comboBox(box_4, self, "send_original_beam", label="Send Original Beam in case of failure", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        self.set_diffraction_plane()
        self.set_propagation_distance()
        self.set_calculation_type()
        self.set_propagation_type()

        self.initializeTabs()

        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=220,
                     items=["None", "Debug (star.xx)"],
                     sendSelectedValue=False,
                     orientation="horizontal")

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.set_PlotQuality()

    def after_change_workspace_units(self):
        label = self.le_focal_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_propagation_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def set_PlotQuality(self):
        self.progressBarInit()

        if not self.__plotted_data is None:
            try:
                self.initializeTabs()
                if self.view_type == 1: self.plot_results(self.__plotted_data)

            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception
        else:
            self.initializeTabs()

        self.progressBarFinished()

    def initializeTabs(self):
        self.tabs.clear()

        if self.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.TANGENTIAL]:
            if self.propagation_type == HybridPropagationType.BOTH:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field")]
            elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")]
            elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field")]
        elif self.diffraction_plane == HybridDiffractionPlane.BOTH_2D:
             self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field"),
                         gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")]
        elif self.diffraction_plane == HybridDiffractionPlane.BOTH_2X1D:
            if self.propagation_type == HybridPropagationType.BOTH:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (T)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")]
            elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence at Far Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Image Plane")]
            elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (S)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position at Near Field (T)"),
                            gui.createTabPage(self.tabs, "Distribution of Position at Near Field")]

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
                self.__input_beam = beam

                if self.is_automatic_run:
                    self.run_hybrid()

    def set_diffraction_plane(self):
        self.le_n_bins_x.setEnabled(self.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.BOTH_2X1D])
        self.le_n_bins_z.setEnabled(self.diffraction_plane in [HybridDiffractionPlane.TANGENTIAL, HybridDiffractionPlane.BOTH_2X1D])

        if self.calculation_type in [HybridCalculationType.MIRROR_OR_GRATING_SIZE,
                                     HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE,
                                     HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE] and self.diffraction_plane != HybridDiffractionPlane.BOTH_2D:
            self.cb_propagation_type.setEnabled(True)
        else:
            self.cb_propagation_type.setEnabled(False)
            self.propagation_type = HybridPropagationType.FAR_FIELD

        self.set_propagation_type()

    def set_calculation_type(self):
        if self.calculation_type in [HybridCalculationType.MIRROR_OR_GRATING_SIZE,
                                     HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE,
                                     HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE] and self.diffraction_plane != HybridDiffractionPlane.BOTH_2D:
            self.cb_propagation_type.setEnabled(True)
            self.cb_analyze_geometry.setEnabled(False)
            self.analyze_geometry = 0
        else:
            self.cb_propagation_type.setEnabled(False)
            self.cb_analyze_geometry.setEnabled(True)
            self.propagation_type = 0

        self.set_propagation_type()

        self.cb_diffraction_plane.setEnabled(True)

        if self.tabs_setting.count() == 3: self.tabs_setting.removeTab(2)

        if self.calculation_type == HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE:
            self.create_tab_thickness()
            self.diffraction_plane = HybridDiffractionPlane.BOTH_2D
            self.set_diffraction_plane()
            self.cb_diffraction_plane.setEnabled(False)

    def set_propagation_type(self):
        if self.propagation_type == HybridPropagationType.FAR_FIELD or self.propagation_type == HybridPropagationType.BOTH:
            self.cb_focal_length_calculation.setEnabled(False)
            self.le_focal_length.setEnabled(False)
        else:
            self.cb_focal_length_calculation.setEnabled(True)
            self.le_focal_length.setEnabled(True)

        self.set_focal_length_calculation()

    def set_focal_length_calculation(self):
         self.le_focal_length.setEnabled(self.focal_length_calculation == 1)

    def set_propagation_distance(self):
         self.le_propagation_distance.setEnabled(self.propagation_distance_calculation == 1)

    # --------------------------------------------------
    # HybridListener methods
    # --------------------------------------------------

    def status_message(self, message : str): self.setStatusMessage(message)
    def set_progress_bar(self, value):
        if value >= 100: self.progressBarFinished()
        elif value <= 0: self.progressBarInit()
        else:            self.progressBarSet(value)
    def warning_message(self, message : str): QMessageBox.warning(self, "Warning", str(message), QMessageBox.Ok)
    def error_message(self, message : str):   QMessageBox.critical(self, "Error", str(message), QMessageBox.Ok)

    def run_hybrid(self):
        try:
            self.setStatusMessage("")
            self.progressBarInit()
            self.initializeTabs()

            if ShadowCongruence.checkEmptyBeam(self.__input_beam):
                if ShadowCongruence.checkGoodBeam(self.__input_beam):
                    sys.stdout = EmittingStream(textWritten=self.write_stdout)

                    self.check_fields()

                    history_entry = self.__input_beam.getOEHistory(self.__input_beam._oe_number)

                    additional_parameters = {}

                    if self.calculation_type == HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE:
                        additional_parameters["crl_error_profiles"] = self.crl_error_profiles
                        if self.crl_material_data == 0: additional_parameters["crl_material"] = self.crl_material
                        else:                           additional_parameters["crl_delta"]    = self.crl_delta
                        additional_parameters["crl_scaling_factor"] = self.crl_scaling_factor

                    input_parameters = HybridInputParameters(listener=self,
                                                             beam=ShadowHybridBeam(beam=self.__input_beam,
                                                                                   length_units=self.workspace_units),
                                                             optical_element=ShadowHybridOE(optical_element=history_entry._shadow_oe_end,
                                                                                            name=history_entry._widget_class_name),
                                                             diffraction_plane=self.diffraction_plane,
                                                             propagation_type=self.propagation_type,
                                                             focal_length=self.focal_length if self.focal_length_calculation==1 else -1,
                                                             propagation_distance=self.propagation_distance if self.propagation_distance_calculation==1 else -1,
                                                             n_bins_x=int(self.n_bins_x),
                                                             n_bins_z = int(self.n_bins_z),
                                                             n_peaks = int(self.n_peaks),
                                                             fft_n_pts = int(self.fft_n_pts),
                                                             analyze_geometry=self.analyze_geometry==1,
                                                             random_seed=None, # TODO: add field
                                                             additional_parameters=additional_parameters)

                    try:
                        hybrid_screen = HybridScreenManager.Instance().create_hybrid_screen_manager(IMPLEMENTATION, self.calculation_type)

                        calculation_result = hybrid_screen.run_hybrid_method(input_parameters)

                        # PARAMETERS IN SET MODE
                        self.focal_length_calculated = input_parameters.focal_length
                        self.propagation_distance    = input_parameters.propagation_distance
                        self.n_bins_x                = int(input_parameters.n_bins_x)
                        self.n_bins_z                = int(input_parameters.n_bins_z)
                        self.n_peaks                 = int(input_parameters.n_peaks)
                        self.fft_n_pts               = int(input_parameters.fft_n_pts)

                        print(calculation_result.geometry_analysis)

                        self.__plotted_data = calculation_result

                        if not calculation_result.far_field_beam is None and calculation_result.near_field_beam is None: # TEMP : DEBUG MODE
                            if self.view_type==1: self.plot_results(calculation_result)

                            if self.propagation_type == HybridPropagationType.BOTH:
                                calculation_result.far_field_beam.wrapped_beam.setScanningData(self.__input_beam.scanned_variable_data)
                                calculation_result.near_field_beam.wrapped_beam.setScanningData(self.__input_beam.scanned_variable_data)
                                self.send("Output Beam (Far Field)", calculation_result.far_field_beam.wrapped_beam)
                                self.send("Output Beam (Near Field)", calculation_result.near_field_beam.wrapped_beam)
                            elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                                calculation_result.far_field_beam.wrapped_beam.setScanningData(self.__input_beam.scanned_variable_data)
                                self.send("Output Beam (Far Field)", calculation_result.far_field_beam.wrapped_beam)
                            elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                                calculation_result.near_field_beam.wrapped_beam.setScanningData(self.__input_beam.scanned_variable_data)
                                self.send("Output Beam (Near Field)", calculation_result.near_field_beam.wrapped_beam)

                        self.send("Trigger", TriggerIn(new_object=True))
                    except Exception as e:
                        if self.send_original_beam==1:
                            self.send("Output Beam (Far Field)", self.__input_beam.duplicate(history=True))
                            self.send("Trigger", TriggerIn(new_object=True))
                        else:
                            raise e
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.setStatusMessage("")
        self.progressBarFinished()

    def plot_results(self, calculation_result : HybridCalculationResult):
        geometry_analysis = calculation_result.geometry_analysis

        do_plot_sagittal   = True
        do_plot_tangential = True

        if not self.calculation_type in [HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE,
                                         HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE,
                                         HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE] \
                and self.analyze_geometry == 1:
            do_plot_sagittal   = not geometry_analysis.has_result(HybridGeometryAnalysis.BEAM_NOT_CUT_SAGITTALLY)
            do_plot_tangential = not geometry_analysis.has_result(HybridGeometryAnalysis.BEAM_NOT_CUT_TANGENTIALLY)

        if do_plot_sagittal or do_plot_tangential: self.setStatusMessage("Plotting Results")
        
        def plot_direction(direction="S", do_plot=True, progress=[84, 88, 92, 96], plot_beam=True):
            if direction=="S":
                ax         = "X"
                divergence = calculation_result.divergence_sagittal
                position   = calculation_result.position_sagittal
            else:
                ax         = "Z"
                divergence = calculation_result.divergence_tangential
                position   = calculation_result.position_tangential
                
            if do_plot:
                if self.propagation_type == HybridPropagationType.BOTH:
                    self.plot_histo_hybrid(progress[0], divergence, 0, title=u"\u2206" + ax + "p", xtitle=r'$\Delta$' + ax + 'p [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                    if plot_beam: self.plot_histo(calculation_result.far_field_beam.wrapped_beam, progress[1], 1, plot_canvas_index=1, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                    self.plot_histo_hybrid(progress[2], position, 2, title=u"\u2206" + ax, xtitle=r'$\Delta$' + ax + ' [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                    if plot_beam: self.plot_histo(calculation_result.near_field_beam.wrapped_beam, progress[3], 1, plot_canvas_index=3, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                    self.plot_histo_hybrid(progress[1], divergence, 0, title=u"\u2206" + ax + "p", xtitle=r'$\Delta$' + ax + 'p [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                    if plot_beam: self.plot_histo(calculation_result.far_field_beam.wrapped_beam, progress[3], 1, plot_canvas_index=1, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                    self.plot_histo_hybrid(progress[1], position, 2, title=u"\u2206" + ax, xtitle=r'$\Delta$' + ax + ' [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                    if plot_beam: self.plot_histo(calculation_result.far_field_beam.wrapped_beam, progress[3], 1, plot_canvas_index=3, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
            else:
                if self.propagation_type == HybridPropagationType.BOTH:
                    self.plot_emtpy(progress[0], 0)
                    if plot_beam: self.plot_emtpy(progress[1], 1)
                    self.plot_emtpy(progress[2], 2)
                    if plot_beam: self.plot_emtpy(progress[3], 3)
                else:
                    self.plot_emtpy(progress[1], 0)
                    if plot_beam: self.plot_emtpy(progress[3], 1)

        if self.diffraction_plane == HybridDiffractionPlane.SAGITTAL:      plot_direction("S", do_plot_sagittal)
        elif self.diffraction_plane == HybridDiffractionPlane.TANGENTIAL:  plot_direction("T", do_plot_tangential)
        elif self.diffraction_plane == HybridDiffractionPlane.BOTH_2D:
            if do_plot_sagittal and do_plot_tangential:
                self.plot_xy_hybrid(88, calculation_result.divergence_2D, plot_canvas_index=0, title="X',Z'",xtitle="X' [$\mu$rad]", ytitle="Z' [$\mu$rad]", var1=4, var2=6)
                self.plot_xy(calculation_result.far_field_beam.wrapped_beam, 96, 1, 3, plot_canvas_index=1, title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
            else:
                if do_plot_sagittal:
                    self.plot_histo_hybrid(88, calculation_result.divergence_sagittal, plot_canvas_index=0, title=u"\u2206" + "X'", xtitle="$\Delta$X' [$\mu$rad]", ytitle=r'Arbitrary Units', var=4)
                    self.plot_histo(calculation_result.far_field_beam.wrapped_beam, 96, 1, plot_canvas_index=1, title="X", xtitle=r'X [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                elif do_plot_tangential:
                    self.plot_histo_hybrid(88, calculation_result.divergence_tangential, 0, title=u"\u2206" + "Z'", xtitle="$\Delta$Z' [$\mu$rad]", ytitle=r'Arbitrary Units', var=6)
                    self.plot_histo(calculation_result.far_field_beam.wrapped_beam, 96, 3, plot_canvas_index=1, title="Z", xtitle=r'Z [$\mu$m]', ytitle=r'Number of Rays', xum=("Z [" + u"\u03BC" + "m]"))
                else:
                    self.plot_emtpy(88, 0)
                    self.plot_emtpy(96, 1)
        elif self.diffraction_plane == HybridDiffractionPlane.BOTH_2X1D:
            plot_direction("S", do_plot_sagittal,   progress=[82, 82, 84, 84], plot_beam=False)
            plot_direction("T", do_plot_tangential, progress=[86, 88, 94, 98], plot_beam=True)

    def check_fields(self):
        if self.focal_length_calculation == 1:         congruence.checkPositiveNumber(self.focal_length, "Focal Length value")
        if self.propagation_distance_calculation == 1: congruence.checkPositiveNumber(self.propagation_distance, "Distance to image value")

        if self.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.BOTH_2D]:
            congruence.checkStrictlyPositiveNumber(self.n_bins_x, "Number of bins for I(Sagittal) histogram")
        if self.diffraction_plane in [HybridDiffractionPlane.TANGENTIAL, HybridDiffractionPlane.BOTH_2D]:
            congruence.checkStrictlyPositiveNumber(self.n_bins_z, "Number of bins for I(Tangential) histogram")

        congruence.checkStrictlyPositiveNumber(self.n_peaks, "Number of diffraction peaks")
        congruence.checkStrictlyPositiveNumber(self.fft_n_pts, "Number of points for FFT")

        if self.calculation_type == HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE:
            if len(self.crl_error_profiles) == 0: raise ValueError("No Thickness error profile specified")
            if self.crl_material_data == 0: self.crl_material = congruence.checkEmptyString(self.crl_material, "Chemical Formula")
            else: congruence.checkStrictlyPositiveNumber(self.crl_delta, "Refractive Index (\u03b4)")
            congruence.checkPositiveNumber(self.crl_scaling_factor, "Thickness Error Scaling Factor")


    def write_stdout(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

    def setThicknessErrorProfiles(self, thickness_errors_data):
        try:
            thickness_error_profile_data_files = thickness_errors_data.thickness_error_profile_data_files

            if not thickness_error_profile_data_files is None:
                self.convert_thickness_error_files(thickness_error_profile_data_files)
                if self.calculation_type==HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE: self.refresh_files_text_area()
        except Exception as exception:
            QMessageBox.critical(self, "Error", exception.args[0], QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def convert_thickness_error_files(self, thickness_error_profile_data_files):
        self.crl_error_profiles = []

        for thickness_error_file in thickness_error_profile_data_files:
            xx, yy, zz = OU.read_surface_file(thickness_error_file)

            xx /= self.workspace_units_to_m
            yy /= self.workspace_units_to_m
            zz /= self.workspace_units_to_m

            filename, _ = os.path.splitext(os.path.basename(thickness_error_file))

            thickness_error_file = filename + "_hybrid.h5"

            OU.write_surface_file(zz, xx, yy, thickness_error_file)

            self.crl_error_profiles.append(thickness_error_file)

    def refresh_files_text_area(self):
        text = ""
        for file in self.crl_error_profiles: text += file + "\n"

        self.files_area.setText(text)

    def create_tab_thickness(self):
        tab_thick = oasysgui.createTabPage(self.tabs_setting, "Thickness Error")

        input_box = oasysgui.widgetBox(tab_thick, "Thickness Error Files", addSpace=True, orientation="vertical", height=390, width=self.CONTROL_AREA_WIDTH-20)

        gui.comboBox(input_box, self, "crl_material_data", label="Material Properties from", labelWidth=180,
                     items=["Chemical Formula", "Absorption Parameters"],
                     callback=self.set_crl_material_data,
                     sendSelectedValue=False, orientation="horizontal")

        self.input_box_1 = oasysgui.widgetBox(input_box, "", addSpace=False, orientation="vertical", width=self.CONTROL_AREA_WIDTH-40)
        self.input_box_2 = oasysgui.widgetBox(input_box, "", addSpace=False, orientation="vertical", width=self.CONTROL_AREA_WIDTH-40)

        oasysgui.lineEdit(self.input_box_1, self, "crl_material", "Chemical Formula", labelWidth=260, valueType=str, orientation="horizontal")
        oasysgui.lineEdit(self.input_box_2, self, "crl_delta", "Refractive Index (\u03b4)", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_crl_material_data()

        self.files_area = oasysgui.textArea(height=265)

        input_box.layout().addWidget(self.files_area)

        self.refresh_files_text_area()

        oasysgui.lineEdit(input_box, self, "crl_scaling_factor", "Thickness Error Scaling Factor", labelWidth=260, valueType=float, orientation="horizontal")

    def set_crl_material_data(self):
        self.input_box_1.setVisible(self.crl_material_data==0)
        self.input_box_2.setVisible(self.crl_material_data==1)

