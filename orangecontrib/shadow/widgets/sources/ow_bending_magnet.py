import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowBeam, ShadowSource
from orangecontrib.shadow.widgets.gui import ow_source

class BendingMagnet(ow_source.Source):

    name = "Bending Magnet"
    description = "Shadow Source: Bending Magnet"
    icon = "icons/bending_magnet.png"
    priority = 2

    number_of_rays=Setting(5000)
    seed=Setting(6775431)
    e_min=Setting(5000)
    e_max=Setting(100000)
    store_optical_paths=Setting(1) # REMOVED FROM GUI: 1 AS DEFAULT
    sample_distribution_combo=Setting(0) # REMOVED FROM GUI: 0 AS DEFAULT
    generate_polarization_combo=Setting(2)

    sigma_x=Setting(0.0078)
    sigma_z=Setting(0.0036)
    emittance_x=Setting(3.8E-7)
    emittance_z=Setting(3.8E-9)
    energy=Setting(6.04)
    distance_from_waist_x=Setting(0.0)
    distance_from_waist_z=Setting(0.0)

    magnetic_radius=Setting(25.1772)
    magnetic_field=Setting(0.8)
    horizontal_half_divergence_from=Setting(0.0005)
    horizontal_half_divergence_to=Setting(0.0005)
    max_vertical_half_divergence_from=Setting(1.0)
    max_vertical_half_divergence_to=Setting(1.0)
    calculation_mode_combo = Setting(0)

    optimize_source=Setting(0)
    optimize_file_name = Setting("NONE SPECIFIED")
    max_number_of_rejected_rays = Setting(10000000)

    want_main_area=1

    def __init__(self):
        super().__init__()

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=300, valueType=int, orientation="horizontal")

        oasysgui.lineEdit(left_box_1, self, "seed", "Seed", tooltip="Seed", labelWidth=300, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_min", "Minimum Energy [eV]", tooltip="Minimum Energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_max", "Maximum Energy [eV]", tooltip="Maximum Energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")
        gui.comboBox(left_box_1, self, "generate_polarization_combo", label="Generate Polarization", items=["Only Parallel", "Only Perpendicular", "Total"], labelWidth=300, orientation="horizontal")

        left_box_2 = oasysgui.widgetBox(self.controlArea, "Machine Parameters", addSpace=True, orientation="vertical")

        self.le_sigma_x = oasysgui.lineEdit(left_box_2, self, "sigma_x", "Sigma X", labelWidth=300, tooltip="Sigma X", valueType=float, orientation="horizontal")
        self.le_sigma_z = oasysgui.lineEdit(left_box_2, self, "sigma_z", "Sigma Z", labelWidth=300, tooltip="Sigma Z", valueType=float, orientation="horizontal")
        self.le_emittance_x = oasysgui.lineEdit(left_box_2, self, "emittance_x", "Emittance X", labelWidth=300, tooltip="Emittance X", valueType=float, orientation="horizontal")
        self.le_emittance_z = oasysgui.lineEdit(left_box_2, self, "emittance_z", "Emittance Z", labelWidth=300, tooltip="Emittance Z", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "energy", "Energy [GeV]", tooltip="Energy [GeV]", labelWidth=300, valueType=float, orientation="horizontal")
        self.le_distance_from_waist_x = oasysgui.lineEdit(left_box_2, self, "distance_from_waist_x", "Distance from Waist X", labelWidth=300, tooltip="Distance from Waist X", valueType=float, orientation="horizontal")
        self.le_distance_from_waist_z = oasysgui.lineEdit(left_box_2, self, "distance_from_waist_z", "Distance from Waist Z", labelWidth=300, tooltip="Distance from Waist Z", valueType=float, orientation="horizontal")

        left_box_3 = oasysgui.widgetBox(self.controlArea, "Bending Magnet Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_3, self, "magnetic_radius", "Magnetic Radius [m]", labelWidth=300, callback=self.calculateMagneticField, tooltip="Magnetic Radius [m]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "magnetic_field", "Magnetic Field [T]", labelWidth=300, callback=self.calculateMagneticRadius, tooltip="Magnetic Field [T]", valueType=float, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "horizontal_half_divergence_from", "Horizontal half-divergence [rads] From [+]", labelWidth=300, tooltip="Horizontal half-divergence [rads] From [+]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "horizontal_half_divergence_to", "Horizontal half-divergence [rads] To [-]", labelWidth=300, tooltip="Horizontal half-divergence [rads] To [-]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "max_vertical_half_divergence_from", "Max vertical half-divergence [rads] From [+]", labelWidth=300, tooltip="Max vertical half-divergence [rads] From [+]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "max_vertical_half_divergence_to", "Max vertical half-divergence [rads] To [-]", labelWidth=300, tooltip="Max vertical half-divergence [rads] To [-]", valueType=float, orientation="horizontal")
        gui.comboBox(left_box_3, self, "calculation_mode_combo", label="Calculation Mode", items=["Precomputed", "Exact"], labelWidth=300, orientation="horizontal")

        left_box_4 = oasysgui.widgetBox(self.controlArea, "Reject Rays", addSpace=True, orientation="vertical")
        left_box_4.setFixedHeight(110)

        gui.comboBox(left_box_4, self, "optimize_source", label="Optimize Source", items=["No", "Using file with phase/space volume)", "Using file with slit/acceptance"], labelWidth=200,
                     callback=self.set_OptimizeSource, orientation="horizontal")
        self.optimize_file_name_box = oasysgui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")


        file_box = oasysgui.widgetBox(self.optimize_file_name_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_optimize_file_name = oasysgui.lineEdit(file_box, self, "optimize_file_name", "File Name", labelWidth=150,  valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectOptimizeFile)

        oasysgui.lineEdit(self.optimize_file_name_box, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=300,  valueType=int, orientation="horizontal")

        self.set_OptimizeSource()

        adv_other_box = oasysgui.widgetBox(self.controlArea, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=200,
                     items=["None", "Debug (start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
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

    def set_OptimizeSource(self):
        self.optimize_file_name_box.setVisible(self.optimize_source != 0)

    def selectOptimizeFile(self):
        self.le_optimize_file_name.setText(oasysgui.selectFileFromDialog(self, self.optimize_file_name, "Open Optimize Source Parameters File"))

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

            shadow_src = ShadowSource.create_bm_src()

            self.populateFields(shadow_src)

            self.progressBarSet(10)

            #self.information(0, "Running SHADOW")
            self.setStatusMessage("Running SHADOW")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            self.progressBarSet(50)

            write_start_file, write_end_file = self.get_write_file_options()

            beam_out = ShadowBeam.traceFromSource(shadow_src,
                                                  write_start_file=write_start_file,
                                                  write_end_file=write_end_file)

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
            QtGui.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtGui.QMessageBox.Ok)

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def sendNewBeam(self, trigger):
        if trigger and trigger.new_beam == True:
            self.runShadowSource()

    def setupUI(self):
        self.set_OptimizeSource()
        self.calculateMagneticField()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.e_min = congruence.checkPositiveNumber(self.e_min, "Minimum energy")
        self.e_max = congruence.checkPositiveNumber(self.e_max, "Maximum energy")
        if self.e_min > self.e_max: raise Exception("Energy min should be <= Energy max")
        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Sigma x")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Sigma z")
        self.emittance_x = congruence.checkPositiveNumber(self.emittance_x, "Emittance x")
        self.emittance_z = congruence.checkPositiveNumber(self.emittance_z, "Emittance z")
        self.distance_from_waist_x = congruence.checkPositiveNumber(self.distance_from_waist_x, "Distance from waist x")
        self.distance_from_waist_z = congruence.checkPositiveNumber(self.distance_from_waist_z, "Distance from waist z")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.magnetic_radius = congruence.checkPositiveNumber(self.magnetic_radius, "Magnetic radius")
        self.horizontal_half_divergence_from = congruence.checkPositiveNumber(self.horizontal_half_divergence_from,
                                                                             "Horizontal half-divergence from [+]")
        self.horizontal_half_divergence_to = congruence.checkPositiveNumber(self.horizontal_half_divergence_to,
                                                                           "Horizontal half-divergence to [-]")
        self.max_vertical_half_divergence_from = congruence.checkPositiveNumber(self.max_vertical_half_divergence_from,
                                                                               "Max vertical half-divergence from [+]")
        self.max_vertical_half_divergence_to = congruence.checkPositiveNumber(self.max_vertical_half_divergence_to,
                                                                             "Max vertical half-divergence to [-]")
        if self.optimize_source > 0:
            self.max_number_of_rejected_rays = congruence.checkPositiveNumber(self.max_number_of_rejected_rays,
                                                                             "Max number of rejected rays")
            congruence.checkFile(self.optimize_file_name)

    def populateFields(self, shadow_src):
        shadow_src.src.NPOINT = self.number_of_rays
        shadow_src.src.ISTAR1 = self.seed
        shadow_src.src.PH1 = self.e_min
        shadow_src.src.PH2 = self.e_max
        shadow_src.src.F_OPD = self.store_optical_paths
        shadow_src.src.F_SR_TYPE = self.sample_distribution_combo
        shadow_src.src.F_POL = 1 + self.generate_polarization_combo
        shadow_src.src.SIGMAX = self.sigma_x
        shadow_src.src.SIGMAZ = self.sigma_z
        shadow_src.src.EPSI_X = self.emittance_x
        shadow_src.src.EPSI_Z = self.emittance_z
        shadow_src.src.BENER = self.energy
        shadow_src.src.EPSI_DX = self.distance_from_waist_x
        shadow_src.src.EPSI_DZ = self.distance_from_waist_z
        shadow_src.src.R_MAGNET = self.magnetic_radius
        shadow_src.src.R_ALADDIN = self.magnetic_radius * 100
        shadow_src.src.HDIV1 = self.horizontal_half_divergence_from
        shadow_src.src.HDIV2 = self.horizontal_half_divergence_to
        shadow_src.src.VDIV1 = self.max_vertical_half_divergence_from
        shadow_src.src.VDIV2 = self.max_vertical_half_divergence_to
        shadow_src.src.FDISTR = 4 + 2 * self.calculation_mode_combo
        shadow_src.src.F_BOUND_SOUR = self.optimize_source
        if self.optimize_source > 0:
            shadow_src.src.FILE_BOUND = bytes(congruence.checkFileName(self.optimize_file_name), 'utf-8')
        shadow_src.src.NTOTALPOINT = self.max_number_of_rejected_rays

    def deserialize(self, shadow_file):
        if not shadow_file is None:
            try:
                self.number_of_rays=int(shadow_file.getProperty("NPOINT"))
                self.seed=int(shadow_file.getProperty("ISTAR1"))
                self.e_min=float(shadow_file.getProperty("PH1"))
                self.e_max=float(shadow_file.getProperty("PH2"))
                self.store_optical_paths=int(shadow_file.getProperty("F_OPD"))
                self.sample_distribution_combo=int(shadow_file.getProperty("F_SR_TYPE"))
                self.generate_polarization_combo=int(shadow_file.getProperty("F_POL"))-1

                self.sigma_x=float(shadow_file.getProperty("SIGMAX"))
                self.sigma_z=float(shadow_file.getProperty("SIGMAZ"))
                self.emittance_x=float(shadow_file.getProperty("EPSI_X"))
                self.emittance_z=float(shadow_file.getProperty("EPSI_Z"))
                self.energy=float(shadow_file.getProperty("BENER"))
                self.distance_from_waist_x=float(shadow_file.getProperty("EPSI_DX"))
                self.distance_from_waist_z=float(shadow_file.getProperty("EPSI_DZ"))

                self.magnetic_radius=float(shadow_file.getProperty("R_MAGNET"))
                self.horizontal_half_divergence_from=float(shadow_file.getProperty("HDIV1"))
                self.horizontal_half_divergence_to=float(shadow_file.getProperty("HDIV2"))
                self.max_vertical_half_divergence_from=float(shadow_file.getProperty("VDIV1"))
                self.max_vertical_half_divergence_to=float(shadow_file.getProperty("VDIV2"))
                self.calculation_mode_combo = (int(shadow_file.getProperty("FDISTR"))-4)/2

                self.optimize_source = int(shadow_file.getProperty("F_BOUND_SOUR"))
                self.optimize_file_name = str(shadow_file.getProperty("FILE_BOUND"))

                if not shadow_file.getProperty("NTOTALPOINT") is None:
                    self.max_number_of_rejected_rays = int(shadow_file.getProperty("NTOTALPOINT"))
                else:
                    self.max_number_of_rejected_rays = 10000000
            except Exception as exception:
                raise BlockingIOError("Bending magnet source failed to load, bad file format: " + exception.args[0])

            self.setupUI()

    
if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = BendingMagnet()
    ow.show()
    a.exec_()
    ow.saveSettings()
