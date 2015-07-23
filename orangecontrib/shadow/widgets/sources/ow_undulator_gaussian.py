import sys, numpy

from orangewidget import gui
from orangewidget.settings import Setting
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_generic_element
from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerOut, ShadowBeam, \
    ShadowSource
from orangecontrib.shadow.util.shadow_util import ShadowGui

class UndulatorGaussian(ow_generic_element.GenericElement):

    name = "Undulator Gaussian"
    description = "Shadow Source: Undulator Gaussian"
    icon = "icons/undulator_gaussian.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", ShadowTriggerOut, "sendNewBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    number_of_rays=Setting(5000)
    seed=Setting(6775431)

    energy=Setting(15000.0)
    delta_e=Setting(1500.0)

    sigma_x=Setting(0.0001)
    sigma_z=Setting(0.0001)
    sigma_divergence_x=Setting(1e-06)
    sigma_divergence_z=Setting(1e-06)

    undulator_length=Setting(4.0)

    want_main_area=1

    def __init__(self):
        super().__init__(show_automatic_box=False)

        left_box_1 = ShadowGui.widgetBox(self.controlArea, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(left_box_1, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(left_box_1, self, "seed", "Seed", tooltip="Seed", labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(left_box_1, self, "energy", "Set undulator to energy [eV]", tooltip="Set undulator to energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(left_box_1, self, "delta_e", "Delta Energy [eV]", tooltip="Delta Energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")

        left_box_2 = ShadowGui.widgetBox(self.controlArea, "Machine Parameters", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(left_box_2, self, "sigma_x", "Size RMS H [cm]", labelWidth=300, tooltip="Size RMS H [cm]", valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(left_box_2, self, "sigma_z", "Size RMS V [cm]", labelWidth=300, tooltip="Size RMS V [cm]", valueType=float, orientation="horizontal")

        ShadowGui.lineEdit(left_box_2, self, "sigma_divergence_x", "Divergence RMS H [rad]", labelWidth=300, tooltip="Divergence RMS H [rad]", valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(left_box_2, self, "sigma_divergence_z", "Divergence RMS V [rad]", labelWidth=300, tooltip="Divergence RMS V [rad]", valueType=float, orientation="horizontal")

        left_box_3 = ShadowGui.widgetBox(self.controlArea, "Undulator Parameters", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(left_box_3, self, "undulator_length", "Undulator Length [m]", labelWidth=300, tooltip="Undulator Length [m]", valueType=float, orientation="horizontal")

        gui.separator(self.controlArea, height=345)

        button_box = ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/trace", callback=self.runShadowSource)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(100)

        gui.rubber(self.controlArea)

        gui.rubber(self.mainArea)

    def calculateMagneticField(self):
        self.magnetic_radius=abs(self.magnetic_radius)
        if self.magnetic_radius > 0:
           self.magnetic_field=3.334728*self.energy/self.magnetic_radius


    def calculateMagneticRadius(self):
        if self.magnetic_field > 0:
           self.magnetic_radius=3.334728*self.energy/self.magnetic_field

    def runShadowSource(self):
        self.error(self.error_id)
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

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

            beam_out = ShadowBeam.traceFromSource(shadow_src)

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
            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                       str(exception),
                QtGui.QMessageBox.Ok)

            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def sendNewBeam(self, trigger):
        if trigger and trigger.new_beam == True:
            self.runShadowSource()

    def checkFields(self):
        self.number_of_rays = ShadowGui.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = ShadowGui.checkPositiveNumber(self.seed, "Seed")
        self.energy = ShadowGui.checkPositiveNumber(self.energy, "Energy")
        self.delta_e = ShadowGui.checkPositiveNumber(self.delta_e, "Delta Energy")
        self.sigma_x = ShadowGui.checkPositiveNumber(self.sigma_x, "Size RMS H")
        self.sigma_z = ShadowGui.checkPositiveNumber(self.sigma_z, "Size RMS V")
        self.sigma_divergence_x = ShadowGui.checkPositiveNumber(self.sigma_divergence_x, "Divergence RMS H")
        self.sigma_divergence_z = ShadowGui.checkPositiveNumber(self.sigma_divergence_z, "Divergence RMS V")
        self.undulator_length = ShadowGui.checkPositiveNumber(self.undulator_length, "Undulator Length")

    def populateFields(self, shadow_src):
        shadow_src.src.NPOINT = self.number_of_rays
        shadow_src.src.ISTAR1 = self.seed
        (new_sigma_x, new_sigma_z, new_sigdi_x, new_sigdi_z) = self.getPhotonSizes(sigma_x=self.sigma_x,
                                                                                   sigma_z=self.sigma_z,
                                                                                   sigdi_x=self.sigma_divergence_x,
                                                                                   sigdi_z=self.sigma_divergence_z,
                                                                                   undulator_E0=self.energy,
                                                                                   undulator_length=self.undulator_length,
                                                                                   user_unit=1)
        shadow_src.src.PH1 = self.energy - (self.delta_e * 0.5)
        shadow_src.src.PH2 = self.energy + (self.delta_e * 0.5)
        shadow_src.src.F_OPD = 1
        shadow_src.src.F_SR_TYPE = 0
        shadow_src.src.SIGMAX = new_sigma_x
        shadow_src.src.SIGMAZ = new_sigma_z
        shadow_src.src.SIGDIX = new_sigdi_x
        shadow_src.src.SIGDIZ = new_sigdi_z

    def getPhotonSizes(self, sigma_x=1e-4, sigma_z=1e-4, sigdi_x=1e-6, sigdi_z=1e-6, undulator_E0=15000.0, undulator_length=4.0, user_unit=1):
        user_unit_to_m = 1.0

        if user_unit == 0:
            user_unit_to_m = 1e-3
        elif user_unit == 1:
            user_unit_to_m = 1e-2

        codata_c = numpy.array(299792458.0)
        codata_h = numpy.array(6.62606957e-34)
        codata_ec = numpy.array(1.602176565e-19)
        m2ev = codata_c*codata_h/codata_ec

        lambda1 = m2ev/undulator_E0

        # calculate sizes of the photon undulator beam
        # see formulas 25 & 30 in Elleaume (Onaki & Elleaume)
        s_phot = 2.740/(4e0*numpy.pi)*numpy.sqrt(undulator_length*lambda1)
        sp_phot = 0.69*numpy.sqrt(lambda1/undulator_length)

        photon_h = numpy.sqrt(numpy.power(sigma_x*user_unit_to_m,2) + numpy.power(s_phot,2) )
        photon_v = numpy.sqrt(numpy.power(sigma_z*user_unit_to_m,2) + numpy.power(s_phot,2) )
        photon_hp = numpy.sqrt(numpy.power(sigdi_x,2) + numpy.power(sp_phot,2) )
        photon_vp = numpy.sqrt(numpy.power(sigdi_z,2) + numpy.power(sp_phot,2) )

        return (photon_h/user_unit_to_m, photon_v/user_unit_to_m, photon_hp,photon_vp)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = UndulatorGaussian()
    ow.show()
    a.exec_()
    ow.saveSettings()
