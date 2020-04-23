#
# TODO: plot electron trajectory
#


import sys
import numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import TriggerOut, EmittingStream, TTYGrabber

from orangecontrib.shadow.widgets.gui import ow_source

from syned.widget.widget_decorator import WidgetDecorator
import syned.beamline.beamline as synedb
import syned.storage_ring.magnetic_structures.undulator as synedu
from syned.storage_ring.electron_beam import ElectronBeam
from syned.storage_ring.magnetic_structures.undulator import Undulator

from silx.gui.plot.StackView import StackViewMainWindow
from silx.gui.plot import Plot2D

from orangecontrib.shadow.util.undulator.source_undulator import SourceUndulator
from orangecontrib.shadow.util.undulator.source_undulator_input_output import SourceUndulatorInputOutput
from Shadow import Beam as Shadow3Beam
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOEHistoryItem

class UndulatorFull(ow_source.Source, WidgetDecorator):

    name = "Full Undulator"
    description = "Shadow Source: Full Undulator"
    icon = "icons/undulator.png"
    priority = 4


    K = Setting(0.25)
    period_length = Setting(0.032)
    periods_number = Setting(50)

    energy_in_GeV = Setting(6.04)
    current = Setting(0.2)
    use_emittances_combo=Setting(1)
    sigma_x = Setting(400e-6)
    sigma_z = Setting(10e-6)
    sigma_divergence_x = Setting(10e-06)
    sigma_divergence_z = Setting(4e-06)

    number_of_rays = Setting(5000)
    seed = Setting(6775431)
    photon_energy = Setting(10500.0)
    harmonic = Setting(1.0)
    set_at_resonance = Setting(0)
    delta_e = Setting(1000.0)
    maxangle_urad = Setting(15)

    # advanced setting
    ng_t = Setting(51)
    ng_p = Setting(11)
    ng_j = Setting(20)
    ng_e = Setting(11)
    code_undul_phot = Setting(0) # 0=internal 1=pySRU 2=SRW
    flag_size = Setting(1) # 0=Point 1=Gaussian 2=backpropagate divergences
    coherent = Setting(0)  # 0=No 1=Yes

    # aux
    file_to_write_out = 0
    plot_aux_graph = 1
    sourceundulator = None

    add_power = False
    power_step = None

    inputs = [("Trigger", TriggerOut, "sendNewBeam2")]
    WidgetDecorator.append_syned_input_data(inputs)

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_sou = oasysgui.createTabPage(tabs_setting, "Source Setting")
        tab_grid = oasysgui.createTabPage(tabs_setting, "Advanced Settings")

        left_box_1 = oasysgui.widgetBox(tab_bas, "Monte Carlo", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of rays", tooltip="Number of Rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")

        left_box_2 = oasysgui.widgetBox(tab_sou, "Machine Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_2, self, "energy_in_GeV", "Energy [GeV]", labelWidth=250, tooltip="Energy [GeV]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "current", "Current [A]", labelWidth=250, tooltip="Current [A]", valueType=float, orientation="horizontal")

        gui.comboBox(left_box_2, self, "use_emittances_combo", label="Use Emittances?", items=["No", "Yes"], callback=self.set_UseEmittances, labelWidth=260, orientation="horizontal")

        self.box_use_emittances = oasysgui.widgetBox(left_box_2, "", addSpace=False, orientation="vertical")


        self.le_sigma_x = oasysgui.lineEdit(self.box_use_emittances, self, "sigma_x", "Size RMS H [m]", labelWidth=250, tooltip="Size RMS H [m]", valueType=float, orientation="horizontal")
        self.le_sigma_z = oasysgui.lineEdit(self.box_use_emittances, self, "sigma_z", "Size RMS V [m]", labelWidth=250, tooltip="Size RMS V [m]", valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.box_use_emittances, self, "sigma_divergence_x", "Divergence RMS H [rad]", labelWidth=250, tooltip="Divergence RMS H [rad]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_use_emittances, self, "sigma_divergence_z", "Divergence RMS V [rad]", labelWidth=250, tooltip="Divergence RMS V [rad]", valueType=float, orientation="horizontal")

        self.set_UseEmittances()

        left_box_3 = oasysgui.widgetBox(tab_sou, "Undulator Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_3, self, "K", "K", labelWidth=250, tooltip="Undulator Deflection Parameter K", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "period_length", "period Length [m]", labelWidth=250, tooltip="Undulator Period Length [m]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "periods_number", "Number of periods", labelWidth=250, tooltip="Number of periods", valueType=int, orientation="horizontal")

        left_box_4 = oasysgui.widgetBox(tab_sou, "Photon energy", addSpace=True, orientation="vertical")

        #
        gui.comboBox(left_box_4, self, "set_at_resonance",
                     label="Set photon energy", addSpace=False,
                    items=['User defined', 'Set to resonance'],
                    valueType=int, orientation="horizontal", labelWidth=250,callback=self.set_UseResonance)

        self.box_photon_energy = gui.widgetBox(left_box_4)
        oasysgui.lineEdit(self.box_photon_energy, self, "photon_energy", "Photon energy [eV] (center)",
                        tooltip="Photon energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")

        self.box_harmonic = gui.widgetBox(left_box_4)
        oasysgui.lineEdit(self.box_harmonic, self, "harmonic", "Photon energy [N x Resonance]; N: ",
                        tooltip="Photon energy [N x Resonance]; N: ", labelWidth=250, valueType=float, orientation="horizontal")

        self.box_maxangle_urad = gui.widgetBox(left_box_4)
        oasysgui.lineEdit(self.box_maxangle_urad, self, "maxangle_urad", "Max elevation angle for radiation [urad]",
                          tooltip="Max elevation angle for radiation theta [urad]", labelWidth=250, valueType=float, orientation="horizontal")

        self.set_UseResonance()


        #self.box_photon_energy.setEnabled(False)

        oasysgui.lineEdit(left_box_4, self, "delta_e", "Photon energy width [eV] (0=monochr.)", tooltip="Photon energy interval [eV] (0=monochromatic)", labelWidth=250, valueType=float, orientation="horizontal")

        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=120,
                     items=["None", "begin.dat","begin.dat+radiation.h5"],
                     sendSelectedValue=False, orientation="horizontal")


        # advanced
        left_box_5 = oasysgui.widgetBox(tab_grid, "Advanced Settings", addSpace=True, orientation="vertical")
    # ng_t = 51
    # ng_p = 11
    # ng_j = 20
    # ng_e = 11
    # code_undul_phot = 0
    # flag_size = 0
        oasysgui.lineEdit(left_box_5, self, "ng_e", "Points in Photon energy (if polychromatic)",       tooltip="Points in Photon energy",       labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_5, self, "ng_t", "Points in theta [elevation]",   tooltip="Points in theta [elevation]",   labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_5, self, "ng_p", "Points in phi [azimuthal]",     tooltip="Points in phi [azimuthal]",     labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_5, self, "ng_j", "Points in electron trajectory", tooltip="Points in electron trajectory", labelWidth=260, valueType=int, orientation="horizontal")

        gui.comboBox(left_box_5, self, "code_undul_phot", label="Calculation method", labelWidth=120,
                     items=["internal", "pySRU","SRW"],sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(left_box_5, self, "flag_size", label="Radiation Size", labelWidth=120,
                     items=["point", "Gaussian", "Far field backpropagated"],sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(left_box_5, self, "coherent", label="Coherent beam", labelWidth=120,
                     items=["No", "Yes"],sendSelectedValue=False, orientation="horizontal")

        gui.rubber(self.controlArea)


        undulator_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)

        self.main_tabs.insertTab(1, undulator_plot_tab, "Undulator Plots")

        view_box = oasysgui.widgetBox(undulator_plot_tab, "Plotting Style", addSpace=False, orientation="horizontal")
        view_box_1 = oasysgui.widgetBox(view_box, "", addSpace=False, orientation="vertical", width=350)

        self.undulator_view_type_combo = gui.comboBox(view_box_1, self, "plot_aux_graph", label="Plot Graphs?",
                                            labelWidth=220,
                                            items=["No", "Yes"],
                                            callback=self.set_PlotAuxGraphs, sendSelectedValue=False, orientation="horizontal")

        self.undulator_tab = []
        self.undulator_tabs = oasysgui.tabWidget(undulator_plot_tab)

        self.initializeUndulatorTabs()

        gui.rubber(self.mainArea)

    def sendNewBeam2(self, trigger):
        self.power_step = None
        self.add_power = False

        try:
            if trigger and trigger.new_object == True:
                if trigger.has_additional_parameter("seed_increment"):
                    self.seed += trigger.get_additional_parameter("seed_increment")

                if trigger.has_additional_parameter("energy_value") and trigger.has_additional_parameter("energy_step"):
                    self.set_at_resonance = 0
                    self.photon_energy = trigger.get_additional_parameter("energy_value")
                    self.delta_e = trigger.get_additional_parameter("energy_step")
                    self.power_step = trigger.get_additional_parameter("power_step")

                    self.set_UseResonance()

                    self.add_power = True

                self.runShadowSource()
        except:
            pass

    def set_UseEmittances(self):
        self.box_use_emittances.setVisible(self.use_emittances_combo == 1)

    def set_UseResonance(self):
        self.box_photon_energy.setVisible(self.set_at_resonance == 0)
        self.box_maxangle_urad.setVisible(self.set_at_resonance == 0)
        self.box_harmonic.setVisible(self.set_at_resonance > 0)

    def set_PlotAuxGraphs(self):
        # self.progressBarInit()

        self.initializeUndulatorTabs() # update number of tabs if monochromatic/polychromatic

        if self.sourceundulator is not None:
            try:
                self.initializeUndulatorTabs()

                self.plot_undulator_results()
            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

        # self.progressBarFinished()

    def plot_undulator_results(self):
        if self.plot_aux_graph == 1:
            try:

                radiation,photon_energy,theta,phi = self.sourceundulator.get_radiation_polar()

                tabs_canvas_index = 0
                plot_canvas_index = 0
                polarization = self.sourceundulator.get_result_polarization()


                if self.delta_e == 0.0:
                    self.plot_data2D(radiation[0], 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index, title="radiation (photons/s/eV/rad2)", xtitle="theta [urad]", ytitle="phi [rad]")

                    tabs_canvas_index += 1
                    self.plot_data2D(polarization[0], 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index, title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]")

                    tabs_canvas_index += 1
                    radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
                    self.plot_data2D(radiation_interpolated[0], 1e6*vx, 1e6*vz,
                                     tabs_canvas_index, plot_canvas_index, title="radiation", xtitle="vx [urad]", ytitle="vz [rad]")

                    tabs_canvas_index += 1
                    x,y = self.sourceundulator.get_photon_size_distribution()
                    self.plot_data1D(x*1e6,y,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="Photon emission size distribution", xtitle="Distance [um]", ytitle="Intensity [arbitrary units]")

                else:
                    self.plot_data3D(radiation, photon_energy, 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="radiation (photons/s/eV/rad2)", xtitle="theta [urad]", ytitle="phi [rad]",
                                     callback_for_title=self.get_title_for_stack_view_flux)

                    tabs_canvas_index += 1
                    self.plot_data3D(polarization, photon_energy, 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="polarization |Es|/(|Es|+|Ep|)", xtitle="theta [urad]", ytitle="phi [rad]",
                                     callback_for_title=self.get_title_for_stack_view_polarization)

                    tabs_canvas_index += 1
                    radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
                    self.plot_data3D(radiation_interpolated, photon_energy, 1e6*vx, 1e6*vz,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="radiation", xtitle="vx [urad]", ytitle="vz [rad]",
                                     callback_for_title=self.get_title_for_stack_view_flux)

                    tabs_canvas_index += 1
                    x,y = self.sourceundulator.get_photon_size_distribution()
                    self.plot_data1D(x*1e6,y,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="Photon emission size distribution", xtitle="Distance [um]", ytitle="Intensity [arbitrary units]")
                    #
                    # if polychromatic, plot power density
                    #

                    intens_xy,vx,vz = self.sourceundulator.get_power_density_interpolated_cartesian()

                    tabs_canvas_index += 1
                    self.plot_data2D(1e-6*intens_xy,1e6*vx,1e6*vz,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="power density W/mrad2", xtitle="vx [urad]", ytitle="vz [rad]")


                    #
                    # if polychromatic, plot flux(energy)
                    #


                    flux,spectral_power,photon_energy = self.sourceundulator.get_flux_and_spectral_power()

                    tabs_canvas_index += 1
                    self.plot_data1D(photon_energy,flux,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="Flux", xtitle="Photon Energy [eV]", ytitle="Flux [photons/s/0.1%bw]")


                    tabs_canvas_index += 1
                    self.plot_data1D(photon_energy,spectral_power,
                                     tabs_canvas_index, plot_canvas_index,
                                     title="Spectral Power", xtitle="Photon Energy [eV]", ytitle="Spectral Power [W/eV]")

                    print("\n\n")
                    # print("Total power (integral [sum] of spectral power) [W]: ",spectral_power.sum()*(photon_energy[1]-photon_energy[0]))
                    print("Total power (integral [trapz] of spectral power) [W]: ",numpy.trapz(spectral_power,photon_energy))
                    print("Total number of photons (integral [trapz] of flux): ",numpy.trapz(flux/(1e-3*photon_energy),photon_energy))
                    print("\n\n")




            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

    def get_title_for_stack_view_flux(self,idx):
        photon_energy = self.sourceundulator.get_result_photon_energy()
        return "Units: Photons/s/eV/rad2; Photon energy: %8.3f eV"%(photon_energy[idx])


    #
    # these are plottting routines hacked from xoppy code TODO: promote to higher level/superclass ?
    #
    def get_title_for_stack_view_polarization(self,idx):
        photon_energy = self.sourceundulator.get_result_photon_energy()
        return "|Es| / (|Es|+|Ep|); Photon energy: %8.3f eV"%(photon_energy[idx])

    def plot_data3D(self, data3D, dataE, dataX, dataY, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle="",
                    callback_for_title=(lambda idx: "")):

        for i in range(1+self.undulator_tab[tabs_canvas_index].layout().count()):
            self.undulator_tab[tabs_canvas_index].layout().removeItem(self.undulator_tab[tabs_canvas_index].layout().itemAt(i))

        ##self.tab[tabs_canvas_index].layout().removeItem(self.tab[tabs_canvas_index].layout().itemAt(0))


        xmin = numpy.min(dataX)
        xmax = numpy.max(dataX)
        ymin = numpy.min(dataY)
        ymax = numpy.max(dataY)


        stepX = dataX[1]-dataX[0]
        stepY = dataY[1]-dataY[0]
        if len(dataE) > 1: stepE = dataE[1]-dataE[0]
        else: stepE = 1.0

        if stepE == 0.0: stepE = 1.0
        if stepX == 0.0: stepX = 1.0
        if stepY == 0.0: stepY = 1.0

        dim0_calib = (dataE[0],stepE)
        dim1_calib = (ymin, stepY)
        dim2_calib = (xmin, stepX)


        data_to_plot = numpy.swapaxes(data3D,1,2)

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.und_plot_canvas[plot_canvas_index] = StackViewMainWindow()
        self.und_plot_canvas[plot_canvas_index].setGraphTitle(title)
        self.und_plot_canvas[plot_canvas_index].setLabels(["Photon Energy [eV]",ytitle,xtitle])
        self.und_plot_canvas[plot_canvas_index].setColormap(colormap=colormap)
        self.und_plot_canvas[plot_canvas_index].setStack(numpy.array(data_to_plot),
                                                     calibrations=[dim0_calib, dim1_calib, dim2_calib] )

        self.und_plot_canvas[plot_canvas_index].setTitleCallback( callback_for_title )
        self.undulator_tab[tabs_canvas_index].layout().addWidget(self.und_plot_canvas[plot_canvas_index])



    def plot_data2D(self, data2D, dataX, dataY, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle=""):

        for i in range(1+self.undulator_tab[tabs_canvas_index].layout().count()):
            self.undulator_tab[tabs_canvas_index].layout().removeItem(self.undulator_tab[tabs_canvas_index].layout().itemAt(i))

        origin = (dataX[0],dataY[0])
        scale = (dataX[1]-dataX[0],dataY[1]-dataY[0])

        data_to_plot = data2D.T

        colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

        self.und_plot_canvas[plot_canvas_index] = Plot2D()
        self.und_plot_canvas[plot_canvas_index].resetZoom()
        self.und_plot_canvas[plot_canvas_index].setXAxisAutoScale(True)
        self.und_plot_canvas[plot_canvas_index].setYAxisAutoScale(True)
        self.und_plot_canvas[plot_canvas_index].setGraphGrid(False)
        self.und_plot_canvas[plot_canvas_index].setKeepDataAspectRatio(True)
        self.und_plot_canvas[plot_canvas_index].yAxisInvertedAction.setVisible(False)
        self.und_plot_canvas[plot_canvas_index].setXAxisLogarithmic(False)
        self.und_plot_canvas[plot_canvas_index].setYAxisLogarithmic(False)
        self.und_plot_canvas[plot_canvas_index].getMaskAction().setVisible(False)
        self.und_plot_canvas[plot_canvas_index].getRoiAction().setVisible(False)
        self.und_plot_canvas[plot_canvas_index].getColormapAction().setVisible(False)
        self.und_plot_canvas[plot_canvas_index].setKeepDataAspectRatio(False)



        self.und_plot_canvas[plot_canvas_index].addImage(numpy.array(data_to_plot),
                                                     legend="",
                                                     scale=scale,
                                                     origin=origin,
                                                     colormap=colormap,
                                                     replace=True)

        self.und_plot_canvas[plot_canvas_index].setActiveImage("")
        self.und_plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.und_plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.und_plot_canvas[plot_canvas_index].setGraphTitle(title)

        self.undulator_tab[tabs_canvas_index].layout().addWidget(self.und_plot_canvas[plot_canvas_index])

    def plot_data1D(self, dataX, dataY, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle=""):

        self.undulator_tab[tabs_canvas_index].layout().removeItem(self.undulator_tab[tabs_canvas_index].layout().itemAt(0))

        self.und_plot_canvas[plot_canvas_index] = oasysgui.plotWindow()

        self.und_plot_canvas[plot_canvas_index].addCurve(dataX, dataY,)

        self.und_plot_canvas[plot_canvas_index].resetZoom()
        self.und_plot_canvas[plot_canvas_index].setXAxisAutoScale(True)
        self.und_plot_canvas[plot_canvas_index].setYAxisAutoScale(True)
        self.und_plot_canvas[plot_canvas_index].setGraphGrid(False)

        self.und_plot_canvas[plot_canvas_index].setXAxisLogarithmic(False)
        self.und_plot_canvas[plot_canvas_index].setYAxisLogarithmic(False)
        self.und_plot_canvas[plot_canvas_index].setGraphXLabel(xtitle)
        self.und_plot_canvas[plot_canvas_index].setGraphYLabel(ytitle)
        self.und_plot_canvas[plot_canvas_index].setGraphTitle(title)

        self.undulator_tab[tabs_canvas_index].layout().addWidget(self.und_plot_canvas[plot_canvas_index])

    #
    # end plotting routines
    #

    def initializeUndulatorTabs(self):
        current_tab = self.undulator_tabs.currentIndex()

        size = len(self.undulator_tab)
        indexes = range(0, size)
        for index in indexes:
            self.undulator_tabs.removeTab(size-1-index)

        if self.delta_e == 0.0:
            self.undulator_tab = [
                gui.createTabPage(self.undulator_tabs, "Radiation intensity (polar)"),
                gui.createTabPage(self.undulator_tabs, "Polarization (polar)"),
                gui.createTabPage(self.undulator_tabs, "Radiation intensity (cartesian - interpolated)"),
                gui.createTabPage(self.undulator_tabs, "Photon source size"),
            ]

            self.und_plot_canvas = [None,None,None,None,]
        else:
            self.undulator_tab = [
                gui.createTabPage(self.undulator_tabs, "Radiation (polar)"),
                gui.createTabPage(self.undulator_tabs, "Polarization (polar)"),
                gui.createTabPage(self.undulator_tabs, "Radiation (interpolated)"),
                gui.createTabPage(self.undulator_tabs, "Photon source size"),
                gui.createTabPage(self.undulator_tabs, "Power Density (interpolated)"),
                gui.createTabPage(self.undulator_tabs, "Flux"),
                gui.createTabPage(self.undulator_tabs, "Spectral Power"),
            ]

            self.und_plot_canvas = [None,None,None,None,None,None,None,]

        for tab in self.undulator_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        # self.undulator_plot_canvas = [None, None, None]

        self.undulator_tabs.setCurrentIndex(current_tab)


    def runShadowSource(self):

        self.setStatusMessage("")
        self.progressBarInit()

        # this is to be able to start the widget out of Oasys
        try:
            tmp = self.workspace_units
        except:
            self.workspace_units = 'm'
            self.workspace_units_label = 'm'
            self.workspace_units_to_m = 1.0
            self.workspace_units_to_cm = 1e2
            self.workspace_units_to_mm = 1e3


        self.checkFields()

        self.progressBarSet(10)

        self.setStatusMessage("Running SHADOW")

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        if self.trace_shadow:
            grabber = TTYGrabber()
            grabber.start()

        self.progressBarSet(50)

        try:
            self.shadow_output.setText("")
            su = Undulator.initialize_as_vertical_undulator(
                K=self.K,
                period_length=self.period_length,
                periods_number=int(self.periods_number))


            ebeam = ElectronBeam(
                energy_in_GeV=self.energy_in_GeV,
                energy_spread = 0.0,
                current = self.current,
                number_of_bunches = 1,
                moment_xx=(self.sigma_x)**2,
                moment_xxp=0.0,
                moment_xpxp=(self.sigma_divergence_x)**2,
                moment_yy=(self.sigma_z)**2,
                moment_yyp=0.0,
                moment_ypyp=(self.sigma_divergence_z)**2 )

            print(ebeam.info())


            codes = ["internal","pySRU","SRW"]
            selected_code = codes[self.code_undul_phot]

            self.sourceundulator = SourceUndulator(
                name="shadowOui-Full-Undulator",
                syned_electron_beam=ebeam,
                syned_undulator=su,
                flag_emittance=self.use_emittances_combo,
                flag_size=self.flag_size,
                emin=1000, # to be set later
                emax=1001, # to be set later
                ng_e=2,    # to be set later
                maxangle=self.maxangle_urad*1e-6,
                ng_t=self.ng_t,
                ng_p=self.ng_p,
                ng_j=self.ng_j,
                code_undul_phot=selected_code)

            if self.set_at_resonance == 0:
                if self.delta_e == 0:
                    self.sourceundulator.set_energy_box(self.photon_energy,self.photon_energy,1)
                else:
                    self.sourceundulator.set_energy_box(self.photon_energy-0.5*self.delta_e,
                                                        self.photon_energy+0.5*self.delta_e,self.ng_e)
            else:
                self.sourceundulator.set_energy_monochromatic_at_resonance(self.harmonic)
                if self.delta_e > 0.0:
                    e0,e1,ne = self.sourceundulator.get_energy_box()
                    self.sourceundulator.set_energy_box(e0-0.5*self.delta_e,e0+0.5*self.delta_e,self.ng_e)

            rays = self.sourceundulator.calculate_rays(
                user_unit_to_m=self.workspace_units_to_m,
                F_COHER=self.coherent,
                SEED=self.seed,
                NRAYS=self.number_of_rays)

            if self.plot_aux_graph:
                self.set_PlotAuxGraphs()

            print(self.sourceundulator.info())

            shadow3_beam = Shadow3Beam(N=rays.shape[0])
            shadow3_beam.rays = rays

            if self.file_to_write_out >= 1:
                shadow3_beam.write("begin.dat")
                print("File written to disk: begin.dat")

            if self.file_to_write_out >= 2:
                SourceUndulatorInputOutput.write_file_undul_phot_h5(self.sourceundulator.get_result_dictionary(),
                                            file_out="radiation.h5",mode="w",entry_name="radiation")

            beam_out = ShadowBeam(beam=shadow3_beam)
            beam_out.getOEHistory().append(ShadowOEHistoryItem())

            if self.add_power:
                additional_parameters = {}

                pd, vx, vy = self.sourceundulator.get_power_density_interpolated_cartesian()

                total_power = self.power_step if self.power_step > 0 else pd.sum()*(vx[1]-vx[0])*(vy[1]-vy[0])

                additional_parameters["total_power"]        = total_power
                additional_parameters["photon_energy_step"] = self.delta_e

                beam_out.setScanningData(ShadowBeam.ScanningData("photon_energy",
                                                                 self.photon_energy,
                                                                 "Energy for Power Calculation",
                                                                 "eV",
                                                                 additional_parameters))

            if self.delta_e == 0.0:
                beam_out.set_initial_flux(self.sourceundulator.get_flux()[0])

            self.progressBarSet(80)
            self.plot_results(beam_out)

            #
            # create python script for creating the shadow3 beam and display the script in the standard output
            #
            dict_parameters = {
                "K"                  : self.K,
                "period_length"      : self.period_length,
                "periods_number"     : self.periods_number,
                "energy_in_GeV"      : self.energy_in_GeV,
                "energy_spread"      : 0.0,
                "current"            : self.current,
                "number_of_bunches"  : 1,
                "moment_xx"          : (self.sigma_x) ** 2,
                "moment_xxp"         : 0.0,
                "moment_xpxp"        : (self.sigma_divergence_x) ** 2,
                "moment_yy"          : (self.sigma_z) ** 2,
                "moment_yyp"         : 0.0,
                "moment_ypyp"        : (self.sigma_divergence_z) ** 2,
                "name"               : "shadowOui-Full-Undulator",
                "flag_emittance"     : self.use_emittances_combo,
                "flag_size"          : self.flag_size,
                "emin"               : 1000,  # to be set later
                "emax"               : 1001,  # to be set later
                "ng_e"               : 2,  # to be set later
                "maxangle"           : self.maxangle_urad * 1e-6,
                "ng_t"               : self.ng_t,
                "ng_p"               : self.ng_p,
                "ng_j"               : self.ng_j,
                "code_undul_phot"    : selected_code,
                "user_unit_to_m"     : self.workspace_units_to_m,
                "F_COHER"            : self.coherent,
                "SEED"               : self.seed,
                "NRAYS"              : self.number_of_rays,
                "EMIN": self.sourceundulator._EMIN,
                "EMAX": self.sourceundulator._EMAX,
                "NG_E": self.sourceundulator._NG_E,
                "MAXANGLE": self.sourceundulator._MAXANGLE,

            }

            # write python script in standard output
            print(self.script_template().format_map(dict_parameters))


            self.setStatusMessage("")
            self.send("Beam", beam_out)

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    def script_template(self):
     return """
#
# script to calculate the shadow3 beam for the full undulator (created by ShadowOui:UndulatorFull\)
#
from syned.storage_ring.electron_beam import ElectronBeam
from syned.storage_ring.magnetic_structures.undulator import Undulator
from orangecontrib.shadow.util.undulator.source_undulator import SourceUndulator
import Shadow
from Shadow import Beam as Shadow3Beam

su = Undulator.initialize_as_vertical_undulator(
    K={K},
    period_length={period_length},
    periods_number={periods_number})


ebeam = ElectronBeam(
    energy_in_GeV={energy_in_GeV},
    energy_spread = {energy_spread},
    current = {current},
    number_of_bunches = {number_of_bunches},
    moment_xx   ={moment_xx},
    moment_xxp  ={moment_xxp},
    moment_xpxp ={moment_xpxp},
    moment_yy  ={moment_yy},
    moment_yyp ={moment_yyp},
    moment_ypyp={moment_ypyp})

print(ebeam.info())

sourceundulator = SourceUndulator(
    name="{name}",
    syned_electron_beam=ebeam,
    syned_undulator=su,
    flag_emittance={flag_emittance},
    flag_size={flag_size},
    emin       = {emin},
    emax       = {emax},
    ng_e       = {ng_e},
    maxangle   = {maxangle},
    ng_t={ng_t},
    ng_p={ng_p},
    ng_j={ng_j},
    code_undul_phot="{code_undul_phot}")
    
sourceundulator._EMIN = {EMIN}
sourceundulator._EMAX = {EMAX}
sourceundulator._NG_E = {NG_E}
sourceundulator._MAXANGLE = {MAXANGLE}

rays = sourceundulator.calculate_rays(
    user_unit_to_m={user_unit_to_m},
    F_COHER={F_COHER},
    SEED={SEED},
    NRAYS={NRAYS})

print(sourceundulator.info())

beam = Shadow3Beam(N=rays.shape[0])
beam.rays = rays

Shadow.ShadowTools.plotxy(beam,1,3,nbins=101,nolost=1,title="Real space")
# Shadow.ShadowTools.plotxy(beam,1,4,nbins=101,nolost=1,title="Phase space X")
# Shadow.ShadowTools.plotxy(beam,3,6,nbins=101,nolost=1,title="Phase space Z")
    
#
# end script
#
"""


    def sendNewBeam(self, trigger):
       if trigger and trigger.new_object == True:
           self.runShadowSource()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.photon_energy = congruence.checkPositiveNumber(self.photon_energy, "Energy")
        self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")

        self.energy_in_GeV = congruence.checkPositiveNumber(self.energy_in_GeV,"Energy [GeV]")
        self.current = congruence.checkPositiveNumber(self.current,"Current [A]")

        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Size RMS H")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Size RMS V")
        self.sigma_divergence_x = congruence.checkPositiveNumber(self.sigma_divergence_x, "Divergence RMS H")
        self.sigma_divergence_z = congruence.checkPositiveNumber(self.sigma_divergence_z, "Divergence RMS V")

        self.K = congruence.checkPositiveNumber(self.K,"K")
        self.period_length = congruence.checkPositiveNumber(self.period_length,"period length [m]")
        self.periods_number = congruence.checkStrictlyPositiveNumber(self.periods_number,"Number of periods")

        self.ng_t = int( congruence.checkStrictlyPositiveNumber(self.ng_t,"Number of points in theta") )
        self.ng_p = int( congruence.checkStrictlyPositiveNumber(self.ng_p,"Number of points in phi") )
        self.ng_j = int( congruence.checkStrictlyPositiveNumber(self.ng_j,"Number of points in trajectory") )
        self.ng_e = int( congruence.checkStrictlyPositiveNumber(self.ng_e,"Number of points in energy") )


    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                if not data.get_light_source() is None:
                    if isinstance(data.get_light_source().get_magnetic_structure(), synedu.Undulator):
                        light_source = data.get_light_source()

                        # self.photon_energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source.get_electron_beam().gamma()), 3)
                        self.set_at_resonance = 1
                        self.set_UseResonance()
                        self.delta_e = 0.0

                        self.energy_in_GeV = light_source.get_electron_beam().energy()
                        self.current = light_source.get_electron_beam().current()

                        x, xp, y, yp = light_source.get_electron_beam().get_sigmas_all()

                        self.sigma_x = x
                        self.sigma_z = y
                        self.sigma_divergence_x = xp
                        self.sigma_divergence_z = yp

                        self.period_length = light_source.get_magnetic_structure().period_length()
                        self.periods_number = int(light_source.get_magnetic_structure().number_of_periods()) # in meter
                        self.K = light_source.get_magnetic_structure().K_vertical()
                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = UndulatorFull()
    ow.show()
    a.exec_()
    ow.saveSettings()
