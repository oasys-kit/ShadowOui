import numpy
import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource
from orangecontrib.shadow.widgets.gui import ow_source

from srxraylib.sources import srfunc

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
import syned.storage_ring.magnetic_structures.undulator as synedu

class UndulatorGaussian(ow_source.Source, WidgetDecorator):

    name = "Undulator Gaussian"
    description = "Shadow Source: Undulator Gaussian"
    icon = "icons/ugaussian.png"
    priority = 5

    energy=Setting(15000.0)
    delta_e=Setting(1500.0)

    sigma_x=Setting(0.0001)
    sigma_z=Setting(0.0001)
    sigma_divergence_x=Setting(1e-06)
    sigma_divergence_z=Setting(1e-06)

    undulator_length=Setting(4.0)

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_sou = oasysgui.createTabPage(tabs_setting, "Source Setting")

        left_box_1 = oasysgui.widgetBox(tab_bas, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "seed", "Seed", tooltip="Seed (0=clock)", labelWidth=250, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "energy", "Set undulator to energy [eV]", tooltip="Set undulator to energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "delta_e", "Delta Energy [eV]", tooltip="Delta Energy [eV]", labelWidth=250, valueType=float, orientation="horizontal")

        left_box_2 = oasysgui.widgetBox(tab_sou, "Machine Parameters", addSpace=True, orientation="vertical")

        self.le_sigma_x = oasysgui.lineEdit(left_box_2, self, "sigma_x", "Size RMS H", labelWidth=250, tooltip="Size RMS H", valueType=float, orientation="horizontal")
        self.le_sigma_z = oasysgui.lineEdit(left_box_2, self, "sigma_z", "Size RMS V", labelWidth=250, tooltip="Size RMS V", valueType=float, orientation="horizontal")

        oasysgui.lineEdit(left_box_2, self, "sigma_divergence_x", "Divergence RMS H [rad]", labelWidth=250, tooltip="Divergence RMS H [rad]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "sigma_divergence_z", "Divergence RMS V [rad]", labelWidth=250, tooltip="Divergence RMS V [rad]", valueType=float, orientation="horizontal")

        left_box_3 = oasysgui.widgetBox(tab_sou, "Undulator Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_3, self, "undulator_length", "Undulator Length [m]", labelWidth=250, tooltip="Undulator Length [m]", valueType=float, orientation="horizontal")

        adv_other_box = oasysgui.widgetBox(tab_bas, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=120,
                     items=["None", "Begin.dat", "Debug (begin.dat + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
        label = self.le_sigma_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_sigma_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def calculateMagneticField(self):
        self.magnetic_radius=abs(self.magnetic_radius)
        if self.magnetic_radius > 0:
           self.magnetic_field=3.334728*self.energy/self.magnetic_radius


    def calculateMagneticRadius(self):
        if self.magnetic_field > 0:
           self.magnetic_radius=3.334728*self.energy/self.magnetic_field

    def runShadowSource(self):
        #self.error(self.error_id)
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

            ###########################################
            # TODO: TO BE ADDED JUST IN CASE OF BROKEN
            #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
            #       TO TEST SHADOW
            self.fixWeirdShadowBug()
            ###########################################

            shadow_src = ShadowSource.create_undulator_gaussian_src()

            self.populateFields(shadow_src)

            self.progressBarSet(10)

            #self.information(0, "Running SHADOW")
            self.setStatusMessage("Running SHADOW")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            self.progressBarSet(50)

            write_begin_file, write_start_file, write_end_file = self.get_write_file_options()

            beam_out = ShadowBeam.traceFromSource(shadow_src,
                                                  write_begin_file=write_begin_file,
                                                  write_start_file=write_start_file,
                                                  write_end_file=write_end_file,
                                                  widget_class_name=self.__class__.name)

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                   self.writeStdOut(row)

            #self.information(0, "Plotting Results")
            self.setStatusMessage("Plotting Results")

            self.progressBarSet(80)
            self.plot_results(beam_out)

            #self.information()
            self.setStatusMessage("")

            self.send("Beam", beam_out)
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

            if self.IS_DEVELOP: raise exception

        self.progressBarFinished()

    #def sendNewBeam(self, trigger):
    #    if trigger and trigger.new_object == True:
    #        self.runShadowSource()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.delta_e = congruence.checkPositiveNumber(self.delta_e, "Delta Energy")
        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Size RMS H")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Size RMS V")
        self.sigma_divergence_x = congruence.checkPositiveNumber(self.sigma_divergence_x, "Divergence RMS H")
        self.sigma_divergence_z = congruence.checkPositiveNumber(self.sigma_divergence_z, "Divergence RMS V")
        self.undulator_length = congruence.checkPositiveNumber(self.undulator_length, "Undulator Length")

    def populateFields(self, shadow_src):
        shadow_src.src.NPOINT = self.number_of_rays
        shadow_src.src.ISTAR1 = self.seed
        (new_sigma_x, new_sigma_z, new_sigdi_x, new_sigdi_z) = self.getPhotonSizes(sigma_x=self.sigma_x,
                                                                                   sigma_z=self.sigma_z,
                                                                                   sigdi_x=self.sigma_divergence_x,
                                                                                   sigdi_z=self.sigma_divergence_z,
                                                                                   undulator_E0=self.energy,
                                                                                   undulator_length=self.undulator_length)
        shadow_src.src.PH1 = self.energy - (self.delta_e * 0.5)
        shadow_src.src.PH2 = self.energy + (self.delta_e * 0.5)
        shadow_src.src.F_OPD = 1
        shadow_src.src.F_SR_TYPE = 0
        shadow_src.src.SIGMAX = new_sigma_x
        shadow_src.src.SIGMAZ = new_sigma_z
        shadow_src.src.SIGDIX = new_sigdi_x
        shadow_src.src.SIGDIZ = new_sigdi_z

    def getPhotonSizes(self, sigma_x=1e-4, sigma_z=1e-4, sigdi_x=1e-6, sigdi_z=1e-6, undulator_E0=15000.0, undulator_length=4.0):
        user_unit_to_m = self.workspace_units_to_cm * 1e-2

        lambda1 = srfunc.m2ev/undulator_E0

        # calculate sizes of the photon undulator beam
        # see formulas 25 & 30 in Elleaume (Onaki & Elleaume)
        s_phot = 2.740/(4e0*numpy.pi)*numpy.sqrt(undulator_length*lambda1)
        sp_phot = 0.69*numpy.sqrt(lambda1/undulator_length)

        photon_h = numpy.sqrt(numpy.power(sigma_x*user_unit_to_m,2) + numpy.power(s_phot,2) )
        photon_v = numpy.sqrt(numpy.power(sigma_z*user_unit_to_m,2) + numpy.power(s_phot,2) )
        photon_hp = numpy.sqrt(numpy.power(sigdi_x,2) + numpy.power(sp_phot,2) )
        photon_vp = numpy.sqrt(numpy.power(sigdi_z,2) + numpy.power(sp_phot,2) )

        txt = ""
        txt += "Photon single electron emission at wavelength %f A: \n"%(lambda1*1e10)
        txt += "    sigma_u:      %g um \n"%(1e6*s_phot)
        txt += "    sigma_uprime: %g urad \n" %(1e6*sp_phot)
        txt += "Electron sizes: \n"
        txt += "    sigma_x: %g um \n"%(1e6*sigma_x*user_unit_to_m)
        txt += "    sigma_z: %g um \n" %(1e6*sigma_z*user_unit_to_m)
        txt += "    sigma_x': %g urad \n"%(1e6*sigdi_x)
        txt += "    sigma_z': %g urad \n" %(1e6*sigdi_z)
        txt += "Photon source sizes (convolution): \n"
        txt += "    Sigma_x: %g um \n"%(1e6*photon_h)
        txt += "    Sigma_z: %g um \n" %(1e6*photon_v)
        txt += "    Sigma_x': %g urad \n"%(1e6*photon_hp)
        txt += "    Sigma_z': %g urad \n" %(1e6*photon_vp)

        # print(txt)
        self.writeStdOut(txt)


        return (photon_h/user_unit_to_m, photon_v/user_unit_to_m, photon_hp,photon_vp)


    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                if not data._light_source is None:
                    if isinstance(data._light_source._magnetic_structure, synedu.Undulator):
                        light_source = data._light_source

                        self.energy =  round(light_source._magnetic_structure.resonance_energy(light_source._electron_beam.gamma()), 3)
                        self.delta_e = 0.0

                        x, xp, y, yp = light_source._electron_beam.get_sigmas_all()

                        self.sigma_x = x/self.workspace_units_to_m
                        self.sigma_z = y/self.workspace_units_to_m
                        self.sigma_divergence_x = xp
                        self.sigma_divergence_z = yp
                        self.undulator_length = light_source._magnetic_structure._period_length*light_source._magnetic_structure._number_of_periods # in meter
                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = UndulatorGaussian()
    ow.workspace_units_to_cm = 100.0
    ow.show()
    a.exec_()
    ow.saveSettings()
