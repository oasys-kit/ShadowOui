import sys

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


class UndulatorFull(ow_source.Source, WidgetDecorator):

    name = "Undulator"
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
    energy=Setting(10500.0)
    delta_e=Setting(20.0)

    file_to_write_out = 0


    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_sou = oasysgui.createTabPage(tabs_setting, "Source Setting")

        left_box_1 = oasysgui.widgetBox(tab_bas, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of rays", tooltip="Number of Rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "energy", "Photon energy [eV]", tooltip="Photon energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "delta_e", "Photon energy width [eV] (0=monochr.)", tooltip="Photon energy interval [eV] (0=monochromatic)", labelWidth=250, valueType=float, orientation="horizontal")

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


        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=120,
                     items=["None", "begin.dat","begin.dat+radiation.h5"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)


    def set_UseEmittances(self):
        self.box_use_emittances.setVisible(self.use_emittances_combo == 1)

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

            su = Undulator.initialize_as_vertical_undulator(K=0.25,period_length=0.032,periods_number=50)
            print(su.info())


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

            sourceundulator = SourceUndulator(name="shadowoui-full-undulator",
                            syned_electron_beam=ebeam,
                            syned_undulator=su,
                            FLAG_EMITTANCE=self.use_emittances_combo,FLAG_SIZE=0,
                            EMIN=self.energy-0.5*self.delta_e,EMAX=self.energy+0.5*self.delta_e,NG_E=3,
                            MAXANGLE=0.015,NG_T=51,NG_P=11,NG_J=20,
                            SEED=self.seed,NRAYS=self.number_of_rays,
                            code_undul_phot="internal")


            # sourceundulator.set_energy_monochromatic_at_resonance(0.98)

            print(sourceundulator.info())

            # #
            # # plot
            # #
            # if do_plots:
            # from srxraylib.plot.gol import plot_image, plot_scatter
            #
            # radiation,theta,phi = sourceundulator.get_radiation_polar()
            # plot_image(radiation[0],1e6*theta,phi,aspect='auto',title="intensity",xtitle="theta [urad]",ytitle="phi [rad]")
            #
            # radiation_interpolated,vx,vz = sourceundulator.get_radiation_interpolated_cartesian()
            # plot_image(radiation_interpolated[0],vx,vz,aspect='auto',title="intensity interpolated in cartesian grid",xtitle="vx",ytitle="vy")
            #
            # polarization = sourceundulator.result_radiation["polarization"]
            # plot_image(polarization[0],1e6*theta,phi,aspect='auto',title="polarization",xtitle="theta [urad]",ytitle="phi [rad]")

            shadow3_beam = sourceundulator.calculate_shadow3_beam(user_unit_to_m=self.workspace_units_to_m)

            print(sourceundulator.info())

            # from srxraylib.plot.gol import plot_image, plot_scatter
            # plot_scatter(1e6*shadow3_beam.rays[:,0],1e6*shadow3_beam.rays[:,2],title="real space",xtitle="X [um]",ytitle="Z [um]",show=False)
            # plot_scatter(1e6*shadow3_beam.rays[:,3],1e6*shadow3_beam.rays[:,5],title="divergence space",xtitle="X [urad]",ytitle="Z [urad]",show=True)



            if self.file_to_write_out >= 1:
                shadow3_beam.write("begin.dat")
                print("File written to disk: begin.dat")

            if self.file_to_write_out >= 2:
                SourceUndulatorInputOutput.write_file_undul_phot_h5(sourceundulator.result_radiation,file_out="radiation.h5",mode="w",entry_name="radiation")

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
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
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


    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                if not data._light_source is None:
                    if isinstance(data._light_source._magnetic_structure, synedu.Undulator):
                        light_source = data._light_source

                        self.energy =  round(light_source.get_magnetic_structure().resonance_energy(light_source._electron_beam.gamma()), 3)
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
