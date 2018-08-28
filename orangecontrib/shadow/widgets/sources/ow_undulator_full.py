import sys
import numpy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.widgets.gui import ow_source

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
import syned.storage_ring.magnetic_structures.undulator as synedu

from orangecontrib.shadow.util.undulator.SourceUndulator import SourceUndulator
from orangecontrib.shadow.util.undulator.SourceUndulatorInputOutput import SourceUndulatorInputOutput
from syned.storage_ring.electron_beam import ElectronBeam
from syned.storage_ring.magnetic_structures.undulator import Undulator

from silx.gui.plot.StackView import StackViewMainWindow
from silx.gui.plot import Plot2D

class UndulatorFull(ow_source.Source, WidgetDecorator):

    name = "Full Undulator"
    description = "Shadow Source: Full Undulator"
    icon = "icons/undulator_gaussian.png"
    priority = 5


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

    number_of_rays=Setting(5000)
    seed=Setting(6775431)
    photon_energy=Setting(10500.0)
    harmonic = Setting(1.0)
    set_at_resonance = Setting(0)
    delta_e=Setting(20.0)
    maxangle_urad = 15

    # advanced setting
    ng_t = Setting(51)
    ng_p = Setting(11)
    ng_j = Setting(20)
    ng_e = Setting(11)
    code_undul_phot = Setting(0)
    flag_size = Setting(0)
    coherent = Setting(0)

    # aux
    file_to_write_out = 0
    plot_aux_graph = 1
    sourceundulator = None


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
                    items=['User defined', 'Set to resonance/central cone'],
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
        oasysgui.lineEdit(left_box_5, self, "ng_e", "Points in Photon energy",       tooltip="Points in Photon energy",       labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_5, self, "ng_t", "Points in theta [elevation]",   tooltip="Points in theta [elevation]",   labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_5, self, "ng_e", "Points in phi [azimuthal]",     tooltip="Points in phi [azimuthal]",     labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_5, self, "ng_e", "Points in electron trajectory", tooltip="Points in electron trajectory", labelWidth=250, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_5, self, "code_undul_phot", label="Calculation method", labelWidth=120,
                     items=["internal", "pySRU","SRW"],sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(left_box_5, self, "flag_size", label="Radiation Size", labelWidth=120,
                     items=["point", "Gaussian"],sendSelectedValue=False, orientation="horizontal")

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


    def set_UseEmittances(self):
        self.box_use_emittances.setVisible(self.use_emittances_combo == 1)

    def set_UseResonance(self):
        self.box_photon_energy.setVisible(self.set_at_resonance == 0)
        self.box_maxangle_urad.setVisible(self.set_at_resonance == 0)
        self.box_harmonic.setVisible(self.set_at_resonance > 0)

    def set_PlotAuxGraphs(self):
        # self.progressBarInit()

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

                radiation,photon_energy, theta,phi = self.sourceundulator.get_radiation_polar()

                tabs_canvas_index = 0
                plot_canvas_index = 0
                polarization = self.sourceundulator.result_radiation["polarization"]


                if self.delta_e == 0.0:
                    self.plot_data2D(radiation[0], 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index, title="radiation (photons/s/0.1%bw/mm2)", xtitle="theta [urad]", ytitle="phi [rad]")

                    tabs_canvas_index += 1
                    self.plot_data2D(polarization[0], 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index, title="polarization (intens s/(s+p))", xtitle="theta [urad]", ytitle="phi [rad]")

                    tabs_canvas_index += 1
                    radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
                    self.plot_data2D(radiation_interpolated[0], 1e6*vx, 1e6*vz,
                                     tabs_canvas_index, plot_canvas_index, title="radiation", xtitle="vx [urad]", ytitle="vz [rad]")

                else:
                    self.plot_data3D(radiation, photon_energy, 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index, title="radiation (photons/s/0.1%bw/mm2)", xtitle="theta [urad]", ytitle="phi [rad]")

                    tabs_canvas_index += 1
                    self.plot_data3D(polarization, photon_energy, 1e6*theta, phi,
                                     tabs_canvas_index, plot_canvas_index, title="polarization (intens s/(s+p))", xtitle="theta [urad]", ytitle="phi [rad]")

                    tabs_canvas_index += 1
                    radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
                    self.plot_data3D(radiation_interpolated, photon_energy, 1e6*vx, 1e6*vz,
                                     tabs_canvas_index, plot_canvas_index, title="radiation", xtitle="vx [urad]", ytitle="vz [rad]")


                # plot_image(radiation[0],1e6*theta,phi,aspect='auto',title="intensity",xtitle="theta [urad]",ytitle="phi [rad]")
                #
                # radiation_interpolated,photon_energy,vx,vz = self.sourceundulator.get_radiation_interpolated_cartesian()
                # plot_image(radiation_interpolated[0],vx,vz,aspect='auto',title="intensity interpolated in cartesian grid",xtitle="vx",ytitle="vy")
                #
                # polarization = self.sourceundulator.result_radiation["polarization"]
                # plot_image(polarization[0],1e6*theta,phi,aspect='auto',title="polarization",xtitle="theta [urad]",ytitle="phi [rad]")



                # data = numpy.loadtxt("tmp.traj",skiprows=15)
                #
                # energy, flux, temp = srfunc.wiggler_spectrum(data.T,
                #                                              enerMin=self.e_min,
                #                                              enerMax=self.e_max,
                #                                              nPoints=500,
                #                                              electronCurrent=self.electron_current/1000,
                #                                              outFile="spectrum.dat",
                #                                              elliptical=False)
                #
                # self.plot_wiggler_histo(15,  data[:, 1], data[:, 7], plot_canvas_index=0, title="Magnetic Field (in vertical) Bz(Y)", xtitle=r'Y [m]', ytitle=r'B [T]')
                # self.plot_wiggler_histo(30,  data[:, 1], data[:, 6], plot_canvas_index=1, title="Electron Curvature", xtitle=r'Y [m]', ytitle=r'curvature [m^-1]')
                # self.plot_wiggler_histo(45,  data[:, 1], data[:, 3], plot_canvas_index=2, title="Electron Velocity BetaX(Y)", xtitle=r'Y [m]', ytitle=r'BetaX')
                # self.plot_wiggler_histo(60,  data[:, 1], data[:, 0], plot_canvas_index=3, title="Electron Trajectory X(Y)", xtitle=r'Y [m]', ytitle=r'X [m]')
                # self.plot_wiggler_histo(80, energy    , flux      , plot_canvas_index=4,
                #                         title="Wiggler Spectrum (current = " + str(self.electron_current) + " mA)",
                #                         xtitle=r'E [eV]', ytitle=r'Flux [phot/s/0.1%bw]', is_log_log=False)
                # self.plot_wiggler_histo(100, energy, flux*1e3*codata.e, plot_canvas_index=5,
                #                         title="Spectral Power (current = " + str(self.electron_current) + " mA)",
                #                         xtitle=r'E [eV]', ytitle=r'Spectral Power [W/eV]', is_log_log=False)
                #
                # print("\nTotal power (from integral of spectrum): %f W"%(numpy.trapz(flux*1e3*codata.e,x=energy)))
                # print("\nTotal number of photons (from integral of spectrum): %g"%(numpy.trapz(flux/(energy*1e-3),x=energy)))

            except Exception as exception:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           str(exception),
                    QtWidgets.QMessageBox.Ok)

    def plot_data3D(self, data3D, dataE, dataX, dataY, tabs_canvas_index, plot_canvas_index, title="", xtitle="", ytitle=""):

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

    def initializeUndulatorTabs(self):
        current_tab = self.undulator_tabs.currentIndex()

        size = len(self.undulator_tab)
        indexes = range(0, size)
        for index in indexes:
            self.undulator_tabs.removeTab(size-1-index)

        self.undulator_tab = [
            gui.createTabPage(self.undulator_tabs, "Radiation intensity (polar)"),
            gui.createTabPage(self.undulator_tabs, "Polarization (sigma/(sigma+pi) (polar)"),
            gui.createTabPage(self.undulator_tabs, "Radiation intensity (cartesian - interpolated)"),
        ]

        self.und_plot_canvas = [None,None,None]

        for tab in self.undulator_tab:
            tab.setFixedHeight(self.IMAGE_HEIGHT)
            tab.setFixedWidth(self.IMAGE_WIDTH)

        # self.undulator_plot_canvas = [None, None, None]

        self.undulator_tabs.setCurrentIndex(current_tab)


    def runShadowSource(self):

        self.setStatusMessage("")
        self.progressBarInit()

        try:
            print(">>>> ",self.workspace_units)
            print(">>>> ",self.workspace_units_label)
            print(">>>> ",self.workspace_units_to_m)
            print(">>>> ",self.workspace_units_to_cm)
            print(">>>> ",self.workspace_units_to_mm)
        except:
            self.workspace_units = 'm'
            self.workspace_units_label = 'm'
            self.workspace_units_to_m = 1.0
            self.workspace_units_to_cm = 1e2
            self.workspace_units_to_mm = 1e3

        print(">>>> workspace_units ",self.workspace_units)
        print(">>>> workspace_units_label ",self.workspace_units_label)
        print(">>>> workspace_units_to_m ",self.workspace_units_to_m)
        print(">>>> workspace_units_to_cm ",self.workspace_units_to_cm)
        print(">>>> workspace_units_to_mm ",self.workspace_units_to_mm)

        self.checkFields()

        self.progressBarSet(10)

        self.setStatusMessage("Running SHADOW")

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)
        if self.trace_shadow:
            grabber = TTYGrabber()
            grabber.start()

        self.progressBarSet(50)

        try:

            print("\n\n\n#\n# New run \n#\n\n\n")
            su = Undulator.initialize_as_vertical_undulator(K=self.K,period_length=self.period_length,
                                                    periods_number=self.periods_number)


            ebeam = ElectronBeam(energy_in_GeV=self.energy_in_GeV,
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

            self.sourceundulator = SourceUndulator(name="shadowOui-Full-Undulator",
                            syned_electron_beam=ebeam,
                            syned_undulator=su,
                            FLAG_EMITTANCE=self.use_emittances_combo,FLAG_SIZE=self.flag_size,
                            EMIN=self.photon_energy-0.5*self.delta_e,EMAX=self.photon_energy+0.5*self.delta_e,
                            NG_E=self.ng_e,
                            MAXANGLE=self.maxangle_urad*1e-3,NG_T=self.ng_t,NG_P=self.ng_p,NG_J=self.ng_j,
                            SEED=self.seed,NRAYS=self.number_of_rays,
                            code_undul_phot=codes[self.code_undul_phot])


            if self.set_at_resonance > 0:
                self.sourceundulator.set_energy_monochromatic_at_resonance(self.harmonic)
                if self.delta_e > 0.0:
                    e0 = self.sourceundulator.EMIN
                    self.sourceundulator.set_energy_box(e0-0.5*self.delta_e,e0+0.5*self.delta_e,self.ng_e)



            shadow3_beam = self.sourceundulator.calculate_shadow3_beam(user_unit_to_m=self.workspace_units_to_m,
                                                                       F_COHER=self.coherent)

            if self.plot_aux_graph:
                self.set_PlotAuxGraphs()

            print(self.sourceundulator.info())

            if self.file_to_write_out >= 1:
                shadow3_beam.write("begin.dat")
                print("File written to disk: begin.dat")

            if self.file_to_write_out >= 2:
                SourceUndulatorInputOutput.write_file_undul_phot_h5(self.sourceundulator.result_radiation,
                                            file_out="radiation.h5",mode="w",entry_name="radiation")

            beam_out = ShadowBeam(beam=shadow3_beam)

            self.progressBarSet(80)
            self.plot_results(beam_out)

            self.setStatusMessage("")
            self.send("Beam", beam_out)

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    # def sendNewBeam(self, trigger):
    #    if trigger and trigger.new_object == True:
    #        self.runShadowSource()

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
        self.periods_number = congruence.checkPositiveNumber(self.periods_number,"Numper of periods")

        self.ng_t = congruence.checkPositiveNumber(self.ng_t,"Numper of points in theta")
        self.ng_p = congruence.checkPositiveNumber(self.ng_p,"Numper of points in phi")
        self.ng_j = congruence.checkPositiveNumber(self.ng_j,"Numper of points in trajectory")
        self.ng_e = congruence.checkPositiveNumber(self.ng_e,"Numper of points in energy")


    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                if not data._light_source is None:
                    if isinstance(data._light_source._magnetic_structure, synedu.Undulator):
                        light_source = data._light_source

                        # self.photon_energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source._electron_beam.gamma()), 3)
                        self.set_at_resonance = 1
                        self.set_UseResonance()
                        self.delta_e = 0.0

                        self.energy_in_GeV = light_source.get_electron_beam().energy()
                        self.current = light_source.get_electron_beam().current()

                        x, xp, y, yp = light_source._electron_beam.get_sigmas_all()

                        self.sigma_x = x
                        self.sigma_z = y
                        self.sigma_divergence_x = xp
                        self.sigma_divergence_z = yp

                        self.period_length = light_source.get_magnetic_structure().period_length()
                        self.periods_number = light_source.get_magnetic_structure().number_of_periods() # in meter
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
