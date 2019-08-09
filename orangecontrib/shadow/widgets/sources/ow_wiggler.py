import sys
import numpy, matplotlib
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber

import scipy.constants as codata

from srxraylib.sources import srfunc

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource
from orangecontrib.shadow.widgets.gui import ow_source

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
import syned.storage_ring.magnetic_structures.wiggler as synedw

class Wiggler(ow_source.Source, WidgetDecorator):
    name = "Wiggler"
    description = "Shadow Source: Wiggler"
    icon = "icons/wiggler.png"
    priority = 3

    NONE_SPECIFIED = "NONE SPECIFIED"

    plot_graph = Setting(0)

    e_min=Setting(5000)
    e_max=Setting(100000)
    optimize_source_combo=Setting(0)

    max_number_of_rejected_rays = Setting(10000000)

    slit_distance = Setting(1000.0)
    min_x = Setting(-1.0)
    max_x = Setting(1.0)
    min_z = Setting(-1.0)
    max_z = Setting(1.0)

    file_with_phase_space_volume = Setting(NONE_SPECIFIED)

    energy=Setting(6.04)
    electron_current = Setting(200)
    use_emittances_combo=Setting(1)
    sigma_x=Setting(0.0078)
    sigma_z=Setting(0.0036)
    emittance_x=Setting(3.8E-7)
    emittance_z=Setting(3.8E-9)
    distance_from_waist_x=Setting(0.0)
    distance_from_waist_z=Setting(0.0)

    shift_x_flag = Setting(0)
    shift_x_value =Setting(0.0)

    shift_betax_flag = Setting(0)
    shift_betax_value = Setting(0.0)

    type_combo=Setting(0)

    number_of_periods=Setting(50)
    k_value=Setting(7.85)
    id_period=Setting(0.04)

    file_with_b_vs_y = Setting("wiggler.b")
    file_with_harmonics = Setting("wiggler.h")

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_sou = oasysgui.createTabPage(tabs_setting, "Source Setting")

        left_box_1 = oasysgui.widgetBox(tab_bas, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical", height=140)

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=260, valueType=int, orientation="horizontal")

        oasysgui.lineEdit(left_box_1, self, "seed", "Seed (0=clock)", tooltip="Seed", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_min", "Minimum Photon Energy [eV]", tooltip="Minimum Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_max", "Maximum Photon Energy [eV]", tooltip="Maximum Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        ##############################

        left_box_4 = oasysgui.widgetBox(tab_bas, "Reject Rays", addSpace=True, orientation="vertical", height=220)


        gui.comboBox(left_box_4, self, "optimize_source_combo", label="Optimize Source", items=["No", "Using file with phase space volume", "Using slit/acceptance"],
                     callback=self.set_OptimizeSource, labelWidth=120, orientation="horizontal")

        self.box_using_file_with_phase_space_volume = oasysgui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_using_file_with_phase_space_volume, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=280, tooltip="Max number of rejected rays", valueType=int, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.box_using_file_with_phase_space_volume, "", addSpace=True, orientation="horizontal", height=25)

        self.le_optimize_file_name = oasysgui.lineEdit(file_box, self, "file_with_phase_space_volume", "File with phase space volume", labelWidth=210, tooltip="File with phase space volume", valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectOptimizeFile)

        self.box_using_slit_acceptance = oasysgui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_using_slit_acceptance, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=280, tooltip="Max number of rejected rays", valueType=int, orientation="horizontal")
        self.le_slit_distance = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "slit_distance", "--", labelWidth=280, tooltip="Slit Distance", valueType=float, orientation="horizontal")
        self.le_min_x = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "min_x", "--", labelWidth=280, tooltip="Min X/Min Xp", valueType=float, orientation="horizontal")
        self.le_max_x = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "max_x", "--", labelWidth=280, tooltip="Max X/Max Xp", valueType=float, orientation="horizontal")
        self.le_min_z = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "min_z", "--", labelWidth=280, tooltip="Min Z/Min Zp", valueType=float, orientation="horizontal")
        self.le_max_z = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "max_z", "--", labelWidth=280, tooltip="Max Z/Max Zp", valueType=float, orientation="horizontal")

        self.set_OptimizeSource()

        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=120,
                     items=["None", "Begin.dat", "Debug (begin.dat + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")

        left_box_2 = oasysgui.widgetBox(tab_sou, "Machine Parameters", addSpace=False, orientation="vertical", height=280)

        oasysgui.lineEdit(left_box_2, self, "energy", "Electron Energy [GeV]", tooltip="Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "electron_current", "Electron Current [mA]", tooltip="Electron Current [mA]", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_2, self, "use_emittances_combo", label="Use Emittances?", items=["No", "Yes"], callback=self.set_UseEmittances, labelWidth=260, orientation="horizontal")

        self.box_use_emittances = oasysgui.widgetBox(left_box_2, "", addSpace=False, orientation="vertical")

        self.le_sigma_x = oasysgui.lineEdit(self.box_use_emittances, self, "sigma_x", "Sigma X", labelWidth=260, tooltip="Sigma X", valueType=float, orientation="horizontal")
        self.le_sigma_z = oasysgui.lineEdit(self.box_use_emittances, self, "sigma_z", "Sigma Z", labelWidth=260, tooltip="Sigma Z", valueType=float, orientation="horizontal")
        self.le_emittance_x = oasysgui.lineEdit(self.box_use_emittances, self, "emittance_x", "Emittance X", labelWidth=260, tooltip="Emittance X", valueType=float, orientation="horizontal")
        self.le_emittance_z = oasysgui.lineEdit(self.box_use_emittances, self, "emittance_z", "Emittance Z", labelWidth=260, tooltip="Emittance Z", valueType=float, orientation="horizontal")
        self.le_distance_from_waist_x = oasysgui.lineEdit(self.box_use_emittances, self, "distance_from_waist_x", "Distance from Waist X", labelWidth=260, tooltip="Distance from Waist X", valueType=float, orientation="horizontal")
        self.le_distance_from_waist_z = oasysgui.lineEdit(self.box_use_emittances, self, "distance_from_waist_z", "Distance from Waist Z", labelWidth=260, tooltip="Distance from Waist Z", valueType=float, orientation="horizontal")

        self.set_UseEmittances()

        left_box_10 = oasysgui.widgetBox(tab_sou, "Electron Beam Parameters", addSpace=False, orientation="vertical", height=145)

        gui.comboBox(left_box_10, self, "shift_betax_flag", label="Shift Transversal Velocity", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_ShiftBetaXFlag, labelWidth=260, orientation="horizontal")
        self.shift_betax_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_betax_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_betax_value_box, self, "shift_betax_value", "Value", labelWidth=260, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_10, self, "shift_x_flag", label="Shift Transversal Coordinate", items=["No shift", "Half excursion", "Minimum", "Maximum", "Value at zero", "User value"], callback=self.set_ShiftXFlag, labelWidth=260, orientation="horizontal")
        self.shift_x_value_box = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        self.shift_x_value_box_hidden = oasysgui.widgetBox(left_box_10, "", addSpace=False, orientation="vertical", height=25)
        oasysgui.lineEdit(self.shift_x_value_box, self, "shift_x_value", "Value [m]", labelWidth=260, valueType=float, orientation="horizontal")


        self.set_ShiftXFlag()
        self.set_ShiftBetaXFlag()

        left_box_3 = oasysgui.widgetBox(tab_sou, "Wiggler Parameters", addSpace=False, orientation="vertical", height=145)

        gui.comboBox(left_box_3, self, "type_combo", label="Type", items=["conventional/sinusoidal", "B from file (y [m], Bz [T])", "B from harmonics"], callback=self.set_Type, labelWidth=220, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", labelWidth=260, tooltip="Number of Periods", valueType=int, orientation="horizontal")

        self.conventional_sinusoidal_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "k_value", "K value", labelWidth=260, tooltip="K value", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        self.b_from_file_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.b_from_file_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_b_vs_y = oasysgui.lineEdit(file_box, self, "file_with_b_vs_y", "File/Url with B vs Y", labelWidth=150, tooltip="File/Url with B vs Y", valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectFileWithBvsY)

        self.b_from_harmonics_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.b_from_harmonics_box, self, "id_period", "ID period [m]", labelWidth=260, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.b_from_harmonics_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_harmonics = oasysgui.lineEdit(file_box, self, "file_with_harmonics", "File/Url with harmonics", labelWidth=150, tooltip="File/Url with harmonics", valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectFileWithHarmonics)

        self.set_Type()

        gui.rubber(self.controlArea)

        wiggler_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, wiggler_plot_tab, "Wiggler Plots")

        view_box = oasysgui.widgetBox(wiggler_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.wiggler_view_type_combo = gui.comboBox(view_box_1, self, "plot_graph", label="Plot Graphs?",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_PlotGraphs, sendSelectedValue=False, orientation="horizontal")

        self.wiggler_tab = []
        self.wiggler_tabs = oasysgui.tabWidget(wiggler_plot_tab)

        self.initializeWigglerTabs()

        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
        label = self.le_slit_distance.parent().layout().itemAt(0).widget()
        label.setText("Slit Distance [" + self.workspace_units_label + "] (set 0 for angular acceptance)")

        label = self.le_min_x.parent().layout().itemAt(0).widget()
        label.setText("Min X [" + self.workspace_units_label + "]/Min Xp [rad]")
        label = self.le_max_x.parent().layout().itemAt(0).widget()
        label.setText("Max X [" + self.workspace_units_label + "]/Max Xp [rad]")
        label = self.le_min_z.parent().layout().itemAt(0).widget()
        label.setText("Min Z [" + self.workspace_units_label + "]/Min Zp [rad]")
        label = self.le_max_z.parent().layout().itemAt(0).widget()
        label.setText("Max Z [" + self.workspace_units_label + "]/Max Zp [rad]")

        label = self.le_sigma_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_sigma_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_emittance_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [rad." + self.workspace_units_label + "]")
        label = self.le_emittance_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [rad." + self.workspace_units_label + "]")
        label = self.le_distance_from_waist_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_distance_from_waist_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def initializeWigglerTabs(self):
        current_tab = self.wiggler_tabs.currentIndex()

        size = len(self.wiggler_tab)
        indexes = range(0, size)
        for index in indexes:
            self.wiggler_tabs.removeTab(size-1-index)

        self.wiggler_tab = [
            gui.createTabPage(self.wiggler_tabs, "Magnetic Field"),
            gui.createTabPage(self.wiggler_tabs, "Electron Curvature"),
            gui.createTabPage(self.wiggler_tabs, "Electron Velocity"),
            gui.createTabPage(self.wiggler_tabs, "Electron Trajectory"),
            gui.createTabPage(self.wiggler_tabs, "Wiggler Spectrum"),
            gui.createTabPage(self.wiggler_tabs, "Wiggler Spectral power")
        ]

        for tab in self.wiggler_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        self.wiggler_plot_canvas = [None, None, None, None, None, None]

        self.wiggler_tabs.setCurrentIndex(current_tab)

    def set_PlotGraphs(self):
        self.progressBarInit()

        if not self.plotted_beam==None:
            try:
                self.initializeWigglerTabs()

                self.plot_wiggler_results()
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

        self.progressBarFinished()

    def plot_wiggler_results(self):
        if self.plot_graph == 1:
            try:
                try:
                    congruence.checkFile("tmp.traj")
                except:
                    return

                data = numpy.loadtxt("tmp.traj",skiprows=15)

                energy, flux, temp = srfunc.wiggler_spectrum(data.T,
                                                             enerMin=self.e_min,
                                                             enerMax=self.e_max,
                                                             nPoints=500,
                                                             electronCurrent=self.electron_current/1000,
                                                             outFile="spectrum.dat",
                                                             elliptical=False)

                self.plot_wiggler_histo(15,  data[:, 1], data[:, 7], plot_canvas_index=0, title="Magnetic Field (in vertical) Bz(Y)", xtitle=r'Y [m]', ytitle=r'B [T]')
                self.plot_wiggler_histo(30,  data[:, 1], data[:, 6], plot_canvas_index=1, title="Electron Curvature", xtitle=r'Y [m]', ytitle=r'curvature [m^-1]')
                self.plot_wiggler_histo(45,  data[:, 1], data[:, 3], plot_canvas_index=2, title="Electron Velocity BetaX(Y)", xtitle=r'Y [m]', ytitle=r'BetaX')
                self.plot_wiggler_histo(60,  data[:, 1], data[:, 0], plot_canvas_index=3, title="Electron Trajectory X(Y)", xtitle=r'Y [m]', ytitle=r'X [m]')
                self.plot_wiggler_histo(80, energy    , flux      , plot_canvas_index=4,
                                        title="Wiggler Spectrum (current = " + str(self.electron_current) + " mA)",
                                        xtitle=r'E [eV]', ytitle=r'Flux [phot/s/0.1%bw]', is_log_log=False)
                self.plot_wiggler_histo(100, energy, flux*1e3*codata.e, plot_canvas_index=5,
                                        title="Spectral Power (current = " + str(self.electron_current) + " mA)",
                                        xtitle=r'E [eV]', ytitle=r'Spectral Power [W/eV]', is_log_log=False)

                print("\nTotal power (from integral of spectrum): %f W"%(numpy.trapz(flux*1e3*codata.e,x=energy)))
                print("\nTotal number of photons (from integral of spectrum): %g"%(numpy.trapz(flux/(energy*1e-3),x=energy)))

            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

    def plot_wiggler_histo(self, progressBarValue, x, y, plot_canvas_index, title, xtitle, ytitle, is_log_log=False):
        if self.wiggler_plot_canvas[plot_canvas_index] is None:
            self.wiggler_plot_canvas[plot_canvas_index] = oasysgui.plotWindow(roi=False, control=False, position=True)
            self.wiggler_plot_canvas[plot_canvas_index].setDefaultPlotLines(True)
            self.wiggler_plot_canvas[plot_canvas_index].setActiveCurveColor(color='blue')

            self.wiggler_tab[plot_canvas_index].layout().addWidget(self.wiggler_plot_canvas[plot_canvas_index])

        matplotlib.rcParams['axes.formatter.useoffset']='False'

        self.wiggler_plot_canvas[plot_canvas_index].addCurve(x, y, title, symbol='', color='blue', replace=True) #'+', '^', ','
        self.wiggler_plot_canvas[plot_canvas_index].setInteractiveMode(mode='zoom')

        if not title is None: self.wiggler_plot_canvas[plot_canvas_index].setGraphTitle(title)
        if not xtitle is None: self.wiggler_plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        if not ytitle is None: self.wiggler_plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)

        self.wiggler_plot_canvas[plot_canvas_index].replot()

        if is_log_log:
            order_of_magnitude_min = numpy.floor(numpy.log10(min(y)))
            order_of_magnitude_max = numpy.floor(numpy.log10(max(y)))

            if numpy.abs(order_of_magnitude_max - order_of_magnitude_min) > 0:
                factor = 1.2
                self.wiggler_plot_canvas[plot_canvas_index].setXAxisLogarithmic(True)
                self.wiggler_plot_canvas[plot_canvas_index].setYAxisLogarithmic(True)
            else:
                factor = 1.005
                self.wiggler_plot_canvas[plot_canvas_index].setXAxisLogarithmic(False)
                self.wiggler_plot_canvas[plot_canvas_index].setYAxisLogarithmic(False)
        else:
            factor = 1.0

        self.wiggler_plot_canvas[plot_canvas_index].setGraphYLimits(min(y), max(y)*factor)

        self.progressBarSet(progressBarValue)

    def set_OptimizeSource(self):
        self.box_using_file_with_phase_space_volume.setVisible(self.optimize_source_combo == 1)
        self.box_using_slit_acceptance.setVisible(self.optimize_source_combo == 2)

    def set_UseEmittances(self):
        self.box_use_emittances.setVisible(self.use_emittances_combo == 1)

    def set_Type(self):
        self.conventional_sinusoidal_box.setVisible(self.type_combo == 0)
        self.b_from_file_box.setVisible(self.type_combo == 1)
        self.b_from_harmonics_box.setVisible(self.type_combo == 2)

    def set_ShiftXFlag(self):
        self.shift_x_value_box.setVisible(self.shift_x_flag==5)
        self.shift_x_value_box_hidden.setVisible(self.shift_x_flag!=5)

    def set_ShiftBetaXFlag(self):
        self.shift_betax_value_box.setVisible(self.shift_betax_flag==5)
        self.shift_betax_value_box_hidden.setVisible(self.shift_betax_flag!=5)

    def selectOptimizeFile(self):
        self.le_optimize_file_name.setText(oasysgui.selectFileFromDialog(self, self.file_with_phase_space_volume, "Open Optimize Source Parameters File"))

    def selectFileWithBvsY(self):
        self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))

    def selectFileWithHarmonics(self):
        self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))

    def populateFields(self, shadow_src):
        shadow_src.src.NPOINT=self.number_of_rays
        shadow_src.src.ISTAR1=self.seed

        shadow_src.src.CONV_FACT = 1 / self.workspace_units_to_m

        shadow_src.src.HDIV1 = 1.00000000000000
        shadow_src.src.HDIV2 = 1.00000000000000

        shadow_src.src.PH1=self.e_min
        shadow_src.src.PH2=self.e_max

        shadow_src.src.F_OPD=1
        shadow_src.src.F_BOUND_SOUR = self.optimize_source_combo
        shadow_src.src.NTOTALPOINT = self.max_number_of_rejected_rays

        if self.optimize_source_combo == 1:
            shadow_src.src.FILE_BOUND = bytes(congruence.checkFileName(self.file_with_phase_space_volume), 'utf-8')
        elif self.optimize_source_combo == 2:
            shadow_src.src.FILE_BOUND = bytes(congruence.checkFileName("myslit.dat"), 'utf-8')

            f = open(congruence.checkFileName("myslit.dat"), "w")
            f.write("%e %e %e %e %e "%(self.slit_distance, self.min_x, self.max_x, self.min_z, self.max_z))
            f.write("\n")
            f.close()

        shadow_src.src.BENER=self.energy

        if self.use_emittances_combo == 0:
            shadow_src.src.SIGMAX=0
            shadow_src.src.SIGMAY=0
            shadow_src.src.SIGMAZ=0
            shadow_src.src.EPSI_X=0
            shadow_src.src.EPSI_Z=0
            shadow_src.src.EPSI_DX=0
            shadow_src.src.EPSI_DZ=0
        else:
            shadow_src.src.SIGMAX=self.sigma_x
            shadow_src.src.SIGMAY=0
            shadow_src.src.SIGMAZ=self.sigma_z
            shadow_src.src.EPSI_X=self.emittance_x
            shadow_src.src.EPSI_Z=self.emittance_z
            shadow_src.src.EPSI_DX=self.distance_from_waist_x
            shadow_src.src.EPSI_DZ=self.distance_from_waist_z

    def runShadowSource(self):
        #self.error(self.error_id)
        self.setStatusMessage("")
        self.progressBarInit()

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        if self.trace_shadow:
            grabber = TTYGrabber()
            grabber.start()

        try:
            self.checkFields()

            ###########################################
            # TODO: TO BE ADDED JUST IN CASE OF BROKEN
            #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
            #       TO TEST SHADOW
            self.fixWeirdShadowBug()
            ###########################################

            wigFile = bytes(congruence.checkFileName("xshwig.sha"), 'utf-8')

            if self.type_combo == 0:
                inData = ""
            elif self.type_combo == 1:
                inData = congruence.checkUrl(self.file_with_b_vs_y)
            elif self.type_combo == 2:
                inData = congruence.checkUrl(self.file_with_harmonics)

            self.progressBarSet(10)
            #self.information(0, "Calculate electron trajectory")

            self.shadow_output.setText("")

            self.setStatusMessage("Calculate electron trajectory")


            (traj, pars) = srfunc.wiggler_trajectory(b_from=self.type_combo,
                                                     inData=inData,
                                                     nPer=self.number_of_periods,
                                                     nTrajPoints=501,
                                                     ener_gev=self.energy,
                                                     per=self.id_period,
                                                     kValue=self.k_value,
                                                     trajFile=congruence.checkFileName("tmp.traj"),
                                                     shift_x_flag=self.shift_x_flag,
                                                     shift_x_value=self.shift_x_value,
                                                     shift_betax_flag=self.shift_betax_flag,
                                                     shift_betax_value=self.shift_betax_value)

            #
            # calculate cdf and write file for Shadow/Source
            #

            self.progressBarSet(20)
            #self.information(0, "Calculate cdf and write file for Shadow/Source")
            self.setStatusMessage("Calculate cdf and write file for Shadow/Source")

            srfunc.wiggler_cdf(traj,
                               enerMin=self.e_min,
                               enerMax=self.e_max,
                               enerPoints=1001,
                               outFile=wigFile,
                               elliptical=False)

            #self.information(0, "CDF written to file %s \n"%(wigFile))
            self.setStatusMessage("CDF written to file %s \n"%(str(wigFile)))

            self.progressBarSet(40)

            #self.information(0, "Set the wiggler parameters in the wiggler container")
            self.setStatusMessage("Set the wiggler parameters in the wiggler container")

            shadow_src = ShadowSource.create_wiggler_src()

            self.populateFields(shadow_src)

            shadow_src.src.FILE_TRAJ = wigFile


            self.progressBarSet(50)

            self.setStatusMessage("Running Shadow/Source")

            write_begin_file, write_start_file, write_end_file = self.get_write_file_options()

            beam_out = ShadowBeam.traceFromSource(shadow_src,
                                                  write_begin_file=write_begin_file,
                                                  write_start_file=write_start_file,
                                                  write_end_file=write_end_file)

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                   self.writeStdOut(row)

            #self.information(0, "Plotting Results")
            self.setStatusMessage("Plotting Results")

            self.progressBarSet(80)

            self.plot_results(beam_out, progressBarValue=80)

            self.setStatusMessage("Plotting Wiggler Data")

            self.plot_wiggler_results()

            #self.information()
            self.setStatusMessage("")

            self.send("Beam", beam_out)

            #
            # create python script for the preprocessors and display in the standard output
            #
            dict_parameters = {
                "b_from"               : self.type_combo,
                "inData"               : inData,
                "nPer"                 : self.number_of_periods,
                "nTrajPoints"          : 501,
                "ener_gev"             : self.energy,
                "per"                  : self.id_period,
                "kValue"               : self.k_value,
                "trajFile"             : "tmp.traj",
                "shift_x_flag"         : self.shift_x_flag,
                "shift_x_value"        : self.shift_x_value,
                "shift_betax_flag"     : self.shift_betax_flag,
                "shift_betax_value"    : self.shift_betax_value,
                "enerMin"              : self.e_min,
                "enerMax"              : self.e_max,
                "enerPoints"           : 1001,
                "outFile"              : wigFile,
                "elliptical"           : False,
                "electron_current_mA"  : self.electron_current,
            }

            # write python script in standard output
            print(self.script_template().format_map(dict_parameters))

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))


        self.progressBarFinished()

    #def sendNewBeam(self, trigger):
    #    if trigger and trigger.new_object == True:
    #        self.runShadowSource()

    def script_template(self):
        return """
#
# script to run the wiggler preprocessor (created by ShadowOui:Wiggler)
#
from srxraylib.sources import srfunc
  
(traj, pars) = srfunc.wiggler_trajectory(
    b_from            ={b_from},
    inData            ="{inData}",
    nPer              ={nPer},
    nTrajPoints       ={nTrajPoints},
    ener_gev          ={ener_gev},
    per               ={per},
    kValue            ={kValue},
    trajFile          ="{trajFile}",
    shift_x_flag      ={shift_x_flag},
    shift_x_value     ={shift_x_value},
    shift_betax_flag  ={shift_betax_flag},
    shift_betax_value ={shift_betax_value})

#
# calculate cdf and write file for Shadow/Source
#

srfunc.wiggler_cdf(traj,
    enerMin        ={enerMin},
    enerMax        ={enerMax},
    enerPoints     ={enerPoints},
    outFile        ={outFile},
    elliptical     ={elliptical})

calculate_spectrum = False 

if calculate_spectrum:
    e, f, w = srfunc.wiggler_spectrum(traj,
        enerMin={enerMin},
        enerMax={enerMax},
        nPoints=500,
        electronCurrent={electron_current_mA}*1e-3,
        outFile="spectrum.dat",
        elliptical={elliptical})
    from srxraylib.plot.gol import plot
    plot(e, f, xlog=False, ylog=False,show=False,
        xtitle="Photon energy [eV]",ytitle="Flux [Photons/s/0.1%bw]",title="Flux")
    plot(e, w, xlog=False, ylog=False,show=True,
        xtitle="Photon energy [eV]",ytitle="Spectral Power [E/eV]",title="Spectral Power")                     
#
# end script
#
"""


    def setupUI(self):
        self.set_OptimizeSource()
        self.set_UseEmittances()
        self.set_Type()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.e_min = congruence.checkPositiveNumber(self.e_min, "Minimum energy")
        self.e_max = congruence.checkPositiveNumber(self.e_max, "Maximum energy")
        congruence.checkLessThan(self.e_min, self.e_max,  "Minimum energy",  "Maximum energy")

        self.max_number_of_rejected_rays = congruence.checkPositiveNumber(self.max_number_of_rejected_rays,
                                                                         "Max Number of Rejected Rays")
        self.slit_distance = congruence.checkPositiveNumber(self.slit_distance, "Horizontal half-divergence from [+]")
        self.min_x = congruence.checkNumber(self.min_x, "Min X/Min Xp")
        self.max_x = congruence.checkNumber(self.max_x, "Max X/Max Xp")
        self.min_z = congruence.checkNumber(self.min_z, "Min X/Min Xp")
        self.max_z = congruence.checkNumber(self.max_z, "Max X/Max Xp")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.electron_current = congruence.checkPositiveNumber(self.electron_current, "Electron Current")
        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Sigma x")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Sigma z")
        self.emittance_x = congruence.checkPositiveNumber(self.emittance_x, "Emittance x")
        self.emittance_z = congruence.checkPositiveNumber(self.emittance_z, "Emittance z")
        self.distance_from_waist_x = congruence.checkNumber(self.distance_from_waist_x, "Distance from waist x")
        self.distance_from_waist_z = congruence.checkNumber(self.distance_from_waist_z, "Distance from waist z")
        self.number_of_periods = congruence.checkStrictlyPositiveNumber(self.number_of_periods, "Number of periods")
        self.k_value = congruence.checkStrictlyPositiveNumber(self.k_value, "K value")
        self.id_period = congruence.checkStrictlyPositiveNumber(self.id_period, "ID period")

        if self.optimize_source_combo == 1:
            congruence.checkFile(self.file_with_phase_space_volume)

        if self.type_combo == 1:
            congruence.checkUrl(self.file_with_b_vs_y)
        elif self.type_combo == 2:
            congruence.checkUrl(self.file_with_harmonics)

    def deserialize(self, shadow_file):
        if not shadow_file is None:
            try:
                self.number_of_rays=int(shadow_file.getProperty("NPOINT"))
                self.seed=int(shadow_file.getProperty("ISTAR1"))

                self.optimize_source_combo = int(shadow_file.getProperty("F_BOUND_SOUR"))
                if self.optimize_source_combo == 1:
                    self.file_with_phase_space_volume = str(shadow_file.getProperty("FILE_BOUND"))

                self.e_min=float(shadow_file.getProperty("PH1"))
                self.e_max=float(shadow_file.getProperty("PH2"))

                self.use_emittances_combo = 1

                self.sigma_x=float(shadow_file.getProperty("SIGMAX"))
                self.sigma_z=float(shadow_file.getProperty("SIGMAZ"))
                self.emittance_x=float(shadow_file.getProperty("EPSI_X"))
                self.emittance_z=float(shadow_file.getProperty("EPSI_Z"))
                self.energy=float(shadow_file.getProperty("BENER"))
                self.distance_from_waist_x=float(shadow_file.getProperty("EPSI_DX"))
                self.distance_from_waist_z=float(shadow_file.getProperty("EPSI_DZ"))

                if not shadow_file.getProperty("NTOTALPOINT") is None:
                    self.max_number_of_rejected_rays = int(shadow_file.getProperty("NTOTALPOINT"))
                else:
                    self.max_number_of_rejected_rays = 10000000
            except Exception as exception:
                raise BlockingIOError("Wiggler source failed to load, bad file format: " + exception.args[0])

            self.setupUI()

    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                if not data._light_source is None:
                    if isinstance(data._light_source._magnetic_structure, synedw.Wiggler):
                        light_source = data._light_source

                        self.energy = light_source._electron_beam._energy_in_GeV
                        self.electron_current = 1e3*light_source._electron_beam._current

                        self.use_emittances_combo = 1

                        self.sigma_x, self.sigma_z = light_source._electron_beam.get_sigmas_real_space()
                        self.sigma_x /= self.workspace_units_to_m
                        self.sigma_z /= self.workspace_units_to_m

                        sigma_xp, sigma_zp = light_source._electron_beam.get_sigmas_divergence_space()
                        self.emittance_x = self.sigma_x * sigma_xp
                        self.emittance_z = self.sigma_z * sigma_zp

                        self.type_combo = 0
                        self.number_of_periods = int(data._light_source._magnetic_structure._number_of_periods)
                        self.k_value = data._light_source._magnetic_structure._K_vertical
                        self.id_period = data._light_source._magnetic_structure._period_length # in meters

                        self.set_UseEmittances()
                        self.set_Type()
                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = Wiggler()
    ow.workspace_units_to_m = 1.0
    ow.workspace_units_to_cm = 100.0

    # test remote B file
    ow.file_with_b_vs_y = "https://raw.githubusercontent.com/srio/oasys_school/master/session1.1_xoppy/ID17_W150_SI.dat"
    ow.type_combo = 1
    ow.set_Type()
    ow.number_of_periods = 1

    ow.show()
    a.exec_()
    ow.saveSettings()
