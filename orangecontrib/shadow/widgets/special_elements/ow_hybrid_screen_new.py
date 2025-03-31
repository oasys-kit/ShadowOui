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
              ("Thickness Errors Data", OasysThicknessErrorsData, "set_thickness_error_profiles")]

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

    propagation_type = Setting(0)

    n_bins_x = Setting(100)
    n_bins_z = Setting(100)
    n_peaks = Setting(10)
    fft_n_pts = Setting(1e5)

    analyze_geometry = Setting(1)

    crl_error_profiles = Setting([])
    crl_material_data = Setting(0)
    crl_material = Setting("Be")
    crl_delta = Setting(1e-6)
    crl_scaling_factor = Setting(1.0)
    crl_coords_to_m = Setting(1.0)
    crl_thickness_to_m = Setting(1.0)

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
                                            callback=self.set_plot_quality, sendSelectedValue=False, orientation="horizontal")

        self.tabs = oasysgui.tabWidget(plot_tab)

        self.tabs_setting = oasysgui.tabWidget(self.controlArea)
        self.tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        self.tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(self.tabs_setting, "Basic Setting")

        box_1 = oasysgui.widgetBox(tab_bas, "Calculation Parameters", addSpace=True, orientation="vertical", height=130)

        gui.comboBox(box_1, self, "calculation_type", label="Calculation", labelWidth=70,
                     items=["Diffraction by Simple Aperture",
                            "Diffraction by Mirror or Grating Size",
                            "Diffraction by Mirror Size + Figure Errors",
                            "Diffraction by Grating Size + Figure Errors",
                            "Diffraction by Lens Size",
                            "Diffraction by Lens Size + Thickness Errors",
                            "Diffraction by KB Size",
                            "Diffraction by KB Size + Figure Errors"],
                     callback=self.set_calculation_type,
                     sendSelectedValue=False, orientation="horizontal")

        self.cb_diffraction_plane = gui.comboBox(box_1, self, "diffraction_plane", label="Diffraction Plane", labelWidth=310,
                                                 items=["Sagittal", "Tangential", "Both (2D)", "Both (1D+1D)"],
                                                 callback=self.set_diffraction_plane,
                                                 sendSelectedValue=False, orientation="horizontal")

        self.cb_propagation_type = gui.comboBox(box_1, self, "propagation_type", label="Propagation Type", labelWidth=310,
                                                items=["Far Field", "Near Field", "Both"],
                                                sendSelectedValue=False, orientation="horizontal", callback=self.set_propagation_type)

        gui.separator(box_1)

        box_2 = oasysgui.widgetBox(tab_bas, "Numerical Control Parameters", addSpace=True, orientation="vertical", height=140)

        self.le_n_bins_x = oasysgui.lineEdit(box_2, self, "n_bins_x", "Number of bins for I(Sagittal) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_n_bins_z = oasysgui.lineEdit(box_2, self, "n_bins_z", "Number of bins for I(Tangential) histogram", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_n_peaks   = oasysgui.lineEdit(box_2, self, "n_peaks", "Number of diffraction peaks", labelWidth=260, valueType=int, orientation="horizontal")
        self.le_fft_n_pts = oasysgui.lineEdit(box_2, self, "fft_n_pts", "Number of points for FFT", labelWidth=260, valueType=int, orientation="horizontal")

        box_4 = oasysgui.widgetBox(tab_bas, "Calculation Congruence Parameters", addSpace=True, orientation="vertical", height=100)

        self.cb_analyze_geometry = gui.comboBox(box_4, self, "analyze_geometry", label="Analize geometry to avoid unuseful calculations", labelWidth=310,
                                                items=["No", "Yes"],
                                                sendSelectedValue=False, orientation="horizontal")


        gui.comboBox(box_4, self, "send_original_beam", label="Send Original Beam in case of failure", labelWidth=310,
                     items=["No", "Yes"],
                     sendSelectedValue=False, orientation="horizontal")

        self.set_calculation_type()

        self.initializeTabs()

        self.shadow_output = oasysgui.textArea(height=580, width=800)

        out_box = gui.widgetBox(out_tab, "System Output", addSpace=True, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        self.set_plot_quality()

    def set_plot_quality(self):
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
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field)"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position (Near Field)"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Far Field)"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Near Field)")]
            elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field)"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Far Field)")]
            elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Position (Near Field)"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Near Field)")]
        elif self.diffraction_plane == HybridDiffractionPlane.BOTH_2D:
             self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field)"),
                         gui.createTabPage(self.tabs, "Spatial Distribution (Far Field)")]
        elif self.diffraction_plane == HybridDiffractionPlane.BOTH_2X1D:
            if self.propagation_type == HybridPropagationType.BOTH:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field (S))"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position (Near Field (S))"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field (T))"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position (Near Field (T))"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Far Field)"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Near Field)")]
            elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field (S))"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Divergence (Far Field (T))"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Far Field)")]
            elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                self.tab = [gui.createTabPage(self.tabs, u"\u2206" + "Position (Near Field (S))"),
                            gui.createTabPage(self.tabs, u"\u2206" + "Position (Near Field (T))"),
                            gui.createTabPage(self.tabs, "Spatial Distribution (Near Field)")]

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

        factor1 = ShadowPlot.get_factor(var1, 1e2) # results are in m
        factor2 = ShadowPlot.get_factor(var2, 1e2) # results are in m

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

        factor = ShadowPlot.get_factor(var, 1e2) # results are in m

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

                if self.is_automatic_run: self.run_hybrid()

    def set_calculation_type(self):
        self.cb_diffraction_plane.setEnabled(True)
        self.cb_propagation_type.setEnabled(True)
        self.cb_analyze_geometry.setEnabled(True)

        if self.tabs_setting.count() == 2: self.tabs_setting.removeTab(1)

        if self.calculation_type == HybridCalculationType.SIMPLE_APERTURE:
            self.cb_propagation_type.setEnabled(False)
            self.propagation_type = HybridPropagationType.FAR_FIELD
        elif self.calculation_type in [HybridCalculationType.CRL_SIZE, HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE]:
            self.diffraction_plane = HybridDiffractionPlane.BOTH_2D
            self.propagation_type = HybridPropagationType.FAR_FIELD
            self.cb_diffraction_plane.setEnabled(False)
            self.cb_propagation_type.setEnabled(False)
            if self.calculation_type == HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE: self.create_tab_thickness()
        elif self.calculation_type in [HybridCalculationType.KB_SIZE, HybridCalculationType.KB_SIZE_AND_ERROR_PROFILE]:
            self.diffraction_plane = HybridDiffractionPlane.BOTH_2X1D
            self.cb_diffraction_plane.setEnabled(False)

        if self.diffraction_plane == HybridDiffractionPlane.BOTH_2D:
            self.cb_propagation_type.setEnabled(False)
            self.propagation_type = HybridPropagationType.FAR_FIELD

        if self.calculation_type in [HybridCalculationType.MIRROR_SIZE_AND_ERROR_PROFILE,
                                     HybridCalculationType.GRATING_SIZE_AND_ERROR_PROFILE,
                                     HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE,
                                     HybridCalculationType.KB_SIZE_AND_ERROR_PROFILE]:
            self.analyze_geometry = 0
            self.cb_analyze_geometry.setEnabled(False)

        self.set_diffraction_plane()
        self.set_propagation_type()

    def set_diffraction_plane(self):
        self.le_n_bins_x.setEnabled(self.diffraction_plane in [HybridDiffractionPlane.SAGITTAL, HybridDiffractionPlane.BOTH_2X1D, HybridDiffractionPlane.BOTH_2D])
        self.le_n_bins_z.setEnabled(self.diffraction_plane in [HybridDiffractionPlane.TANGENTIAL, HybridDiffractionPlane.BOTH_2X1D, HybridDiffractionPlane.BOTH_2D])

    def set_propagation_type(self): pass # maybe it can be useful again

    # --------------------------------------------------
    # HybridListener methods
    # --------------------------------------------------

    def status_message(self, message : str): self.setStatusMessage(message)
    def set_progress_value(self, value):
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

                    additional_parameters = {}

                    if self.calculation_type == HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE:
                        additional_parameters["crl_error_profiles"] = self.crl_error_profiles
                        if self.crl_material_data == 0: additional_parameters["crl_material"] = self.crl_material
                        else:                           additional_parameters["crl_delta"]    = self.crl_delta
                        additional_parameters["crl_scaling_factor"] = self.crl_scaling_factor
                        additional_parameters["crl_coords_to_m"]    = self.crl_coords_to_m
                        additional_parameters["crl_thickness_to_m"] = self.crl_thickness_to_m


                    if self.calculation_type in [HybridCalculationType.KB_SIZE, HybridCalculationType.KB_SIZE_AND_ERROR_PROFILE]:
                        if self.__input_beam.historySize() < 3: raise ValueError("Calculation with KB not possible: not enough elements in the beamline")

                        kb_mirror_1_history = self.__input_beam.getOEHistory(self.__input_beam._oe_number-1)
                        kb_mirror_2_history = self.__input_beam.getOEHistory(self.__input_beam._oe_number)

                        beam             = ShadowHybridBeam(beam=[kb_mirror_2_history._input_beam, self.__input_beam], length_units=self.workspace_units, history=True)
                        optical_element  = ShadowHybridOE(optical_element=[kb_mirror_1_history._shadow_oe_start, kb_mirror_2_history._shadow_oe_start], name="KB")
                    else:
                        history_entry = self.__input_beam.getOEHistory(self.__input_beam._oe_number)

                        beam             = ShadowHybridBeam(beam=self.__input_beam, length_units=self.workspace_units, history=True)
                        optical_element  = ShadowHybridOE(optical_element=history_entry._shadow_oe_end, name=history_entry._widget_class_name)

                    input_parameters = HybridInputParameters(listener=self,
                                                             beam=beam,
                                                             optical_element=optical_element,
                                                             diffraction_plane=self.diffraction_plane,
                                                             propagation_type=self.propagation_type,
                                                             n_bins_x=int(self.n_bins_x),
                                                             n_bins_z=int(self.n_bins_z),
                                                             n_peaks=int(self.n_peaks),
                                                             fft_n_pts=int(self.fft_n_pts),
                                                             analyze_geometry=self.analyze_geometry==1,
                                                             random_seed=None,  # TODO: add field
                                                             **additional_parameters)

                    try:
                        hybrid_screen = HybridScreenManager.Instance().create_hybrid_screen_manager(IMPLEMENTATION, self.calculation_type)

                        calculation_result = hybrid_screen.run_hybrid_method(input_parameters)

                        # PARAMETERS IN SET MODE
                        self.n_bins_x                                   = int(input_parameters.n_bins_x)
                        self.n_bins_z                                   = int(input_parameters.n_bins_z)
                        self.n_peaks                                    = int(input_parameters.n_peaks)
                        self.fft_n_pts                                  = int(input_parameters.fft_n_pts)

                        self.__plotted_data = calculation_result

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
        
        def plot_direction(direction="S", do_plot=True, progress=[84, 88, 92, 96], start_index=0, plot_shadow=True):
            if direction=="S":
                ax         = "X"
                divergence = calculation_result.divergence_sagittal
                position   = calculation_result.position_sagittal
                var        = 1
            else:
                ax         = "Z"
                divergence = calculation_result.divergence_tangential
                position   = calculation_result.position_tangential
                var        = 3

            if do_plot:
                if self.propagation_type == HybridPropagationType.BOTH:
                    self.plot_histo_hybrid(progress[0], divergence, start_index + 0,     title=u"\u2206" + ax + "p", xtitle=r'$\Delta$' + ax + 'p [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                    self.plot_histo_hybrid(progress[2], position,   start_index + 1, title=u"\u2206" + ax, xtitle=r'$\Delta$' + ax + ' [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                    if plot_shadow:
                        self.plot_histo(calculation_result.far_field_beam.wrapped_beam,  progress[1], var, plot_canvas_index=start_index + 2, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                        self.plot_histo(calculation_result.near_field_beam.wrapped_beam, progress[3], var, plot_canvas_index=start_index + 3, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                    self.plot_histo_hybrid(progress[1], divergence, start_index + 0, title=u"\u2206" + ax + "p", xtitle=r'$\Delta$' + ax + 'p [$\mu$rad]', ytitle=r'Arbitrary Units', var=4)
                    if plot_shadow:
                        self.plot_histo(calculation_result.far_field_beam.wrapped_beam, progress[3], var, plot_canvas_index=start_index + 1, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
                elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                    self.plot_histo_hybrid(progress[1], position, start_index + 0, title=u"\u2206" + ax, xtitle=r'$\Delta$' + ax + ' [$\mu$m]', ytitle=r'Arbitrary Units', var=1)
                    if plot_shadow:
                        self.plot_histo(calculation_result.near_field_beam.wrapped_beam, progress[3], var, plot_canvas_index=start_index + 1, title=ax, xtitle=r'' + ax + ' [$\mu$m]', ytitle=r'Number of Rays', xum=("X [" + u"\u03BC" + "m]"))
            else:
                if self.propagation_type == HybridPropagationType.BOTH:
                    self.plot_emtpy(progress[0], start_index + 0)
                    self.plot_emtpy(progress[1], start_index + 1)
                    if plot_shadow:
                        self.plot_emtpy(progress[2], start_index + 2)
                        self.plot_emtpy(progress[3], start_index + 3)
                else:
                    self.plot_emtpy(progress[1], start_index + 0)
                    if plot_shadow:
                        self.plot_emtpy(progress[3], start_index + 1)

        if   self.diffraction_plane == HybridDiffractionPlane.SAGITTAL:   plot_direction("S", do_plot_sagittal)
        elif self.diffraction_plane == HybridDiffractionPlane.TANGENTIAL: plot_direction("T", do_plot_tangential)
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
            plot_direction("S", do_plot_sagittal,   progress=[82, 82, 84, 84], plot_shadow=False)
            plot_direction("T", do_plot_tangential, progress=[86, 88, 94, 98], start_index=2 if self.propagation_type == HybridPropagationType.BOTH else 1, plot_shadow=False)

            if self.propagation_type == HybridPropagationType.BOTH:
                self.plot_xy(calculation_result.far_field_beam.wrapped_beam, 94, 1, 3, plot_canvas_index=4 if self.propagation_type == HybridPropagationType.BOTH else 2,
                             title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
                self.plot_xy(calculation_result.near_field_beam.wrapped_beam, 94, 1, 3, plot_canvas_index=5 if self.propagation_type == HybridPropagationType.BOTH else 3,
                             title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
            elif self.propagation_type == HybridPropagationType.FAR_FIELD:
                self.plot_xy(calculation_result.far_field_beam.wrapped_beam, 94, 1, 3, plot_canvas_index=4 if self.propagation_type == HybridPropagationType.BOTH else 2,
                             title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))
            elif self.propagation_type == HybridPropagationType.NEAR_FIELD:
                self.plot_xy(calculation_result.near_field_beam.wrapped_beam, 94, 1, 3, plot_canvas_index=4 if self.propagation_type == HybridPropagationType.BOTH else 2,
                             title="X,Z", xtitle=r'X [$\mu$m]', ytitle=r'Z [$\mu$m]', xum=("X [" + u"\u03BC" + "m]"), yum=("Z [" + u"\u03BC" + "m]"))

    def check_fields(self):
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

    def set_thickness_error_profiles(self, thickness_errors_data):
        try:
            thickness_error_profile_data_files = thickness_errors_data.thickness_error_profile_data_files

            if not thickness_error_profile_data_files is None:
                self.crl_error_profiles = [thickness_error_file for thickness_error_file in thickness_error_profile_data_files]
                if self.calculation_type==HybridCalculationType.CRL_SIZE_AND_ERROR_PROFILE: self.refresh_files_text_area()
        except Exception as exception:
            QMessageBox.critical(self, "Error", exception.args[0], QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def refresh_files_text_area(self):
        text = ""
        for file in self.crl_error_profiles: text += file + "\n"

        self.files_area.setText(text)

    def create_tab_thickness(self):
        tab_thick = oasysgui.createTabPage(self.tabs_setting, "Thickness Error")

        input_box = oasysgui.widgetBox(tab_thick, "Thickness Error Files", addSpace=True, orientation="vertical", height=450, width=self.CONTROL_AREA_WIDTH-20)

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

        oasysgui.lineEdit(input_box, self, "crl_thickness_to_m", label="Thickness conversion to m", labelWidth=260, orientation="horizontal", valueType=float)
        oasysgui.lineEdit(input_box, self, "crl_coords_to_m",   label="Coordinates conversion to m", labelWidth=260, orientation="horizontal", valueType=float)
        oasysgui.lineEdit(input_box, self, "crl_scaling_factor", "Thickness Error Scaling Factor", labelWidth=260, valueType=float, orientation="horizontal")

    def set_crl_material_data(self):
        self.input_box_1.setVisible(self.crl_material_data==0)
        self.input_box_2.setVisible(self.crl_material_data==1)

