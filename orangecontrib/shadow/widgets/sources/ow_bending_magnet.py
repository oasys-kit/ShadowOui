import sys

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.util.oasys_util import EmittingStream, TTYGrabber

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource
from orangecontrib.shadow.widgets.gui import ow_source

from syned.widget.widget_decorator import WidgetDecorator

import syned.beamline.beamline as synedb
import syned.storage_ring.magnetic_structures.bending_magnet as synedbm
import scipy.constants as codata

class BendingMagnet(ow_source.Source, WidgetDecorator):

    name = "Bending Magnet"
    description = "Shadow Source: Bending Magnet"
    icon = "icons/bending_magnet.png"
    priority = 2

    e_min=Setting(5000)
    e_max=Setting(100000)
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

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_sou = oasysgui.createTabPage(tabs_setting, "Source Setting")


        left_box_1 = oasysgui.widgetBox(tab_bas, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=260, valueType=int, orientation="horizontal")

        oasysgui.lineEdit(left_box_1, self, "seed", "Seed (0=clock)", tooltip="Seed", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_min", "Minimum Energy [eV]", tooltip="Minimum Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_max", "Maximum Energy [eV]", tooltip="Maximum Energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")
        gui.comboBox(left_box_1, self, "generate_polarization_combo", label="Generate Polarization", items=["Only Parallel", "Only Perpendicular", "Total"], labelWidth=260, orientation="horizontal")

        left_box_2 = oasysgui.widgetBox(tab_sou, "Machine Parameters", addSpace=True, orientation="vertical")

        self.le_sigma_x = oasysgui.lineEdit(left_box_2, self, "sigma_x", "Sigma X", labelWidth=260, tooltip="Sigma X", valueType=float, orientation="horizontal")
        self.le_sigma_z = oasysgui.lineEdit(left_box_2, self, "sigma_z", "Sigma Z", labelWidth=260, tooltip="Sigma Z", valueType=float, orientation="horizontal")
        self.le_emittance_x = oasysgui.lineEdit(left_box_2, self, "emittance_x", "Emittance X", labelWidth=260, tooltip="Emittance X", valueType=float, orientation="horizontal")
        self.le_emittance_z = oasysgui.lineEdit(left_box_2, self, "emittance_z", "Emittance Z", labelWidth=260, tooltip="Emittance Z", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_2, self, "energy", "Energy [GeV]", tooltip="Energy [GeV]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_distance_from_waist_x = oasysgui.lineEdit(left_box_2, self, "distance_from_waist_x", "Distance from Waist X", labelWidth=260, tooltip="Distance from Waist X", valueType=float, orientation="horizontal")
        self.le_distance_from_waist_z = oasysgui.lineEdit(left_box_2, self, "distance_from_waist_z", "Distance from Waist Z", labelWidth=260, tooltip="Distance from Waist Z", valueType=float, orientation="horizontal")

        left_box_3 = oasysgui.widgetBox(tab_sou, "Bending Magnet Parameters", addSpace=True, orientation="vertical")

        oasysgui.lineEdit(left_box_3, self, "magnetic_radius", "Magnetic Radius [m]", labelWidth=260, callback=self.calculateMagneticField, tooltip="Magnetic Radius [m]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "magnetic_field", "Magnetic Field [T]", labelWidth=260, callback=self.calculateMagneticRadius, tooltip="Magnetic Field [T]", valueType=float, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "horizontal_half_divergence_from", "Horizontal half-divergence [rads] From [+]", labelWidth=260, tooltip="Horizontal half-divergence [rads] From [+]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "horizontal_half_divergence_to", "Horizontal half-divergence [rads] To [-]", labelWidth=260, tooltip="Horizontal half-divergence [rads] To [-]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "max_vertical_half_divergence_from", "Max vertical half-divergence [rads] From [+]", labelWidth=260, tooltip="Max vertical half-divergence [rads] From [+]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_3, self, "max_vertical_half_divergence_to", "Max vertical half-divergence [rads] To [-]", labelWidth=260, tooltip="Max vertical half-divergence [rads] To [-]", valueType=float, orientation="horizontal")
        gui.comboBox(left_box_3, self, "calculation_mode_combo", label="Calculation Mode", items=["Precomputed", "Exact"], labelWidth=260, orientation="horizontal")

        left_box_4 = oasysgui.widgetBox(tab_bas, "Reject Rays", addSpace=True, orientation="vertical", height=130)

        gui.comboBox(left_box_4, self, "optimize_source", label="Optimize Source", items=["No", "Using file with phase/space volume)", "Using file with slit/acceptance"],
                     labelWidth=120, callback=self.set_OptimizeSource, orientation="horizontal")
        self.optimize_file_name_box = oasysgui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")


        file_box = oasysgui.widgetBox(self.optimize_file_name_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_optimize_file_name = oasysgui.lineEdit(file_box, self, "optimize_file_name", "File Name", labelWidth=100,  valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectOptimizeFile)

        oasysgui.lineEdit(self.optimize_file_name_box, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=280,  valueType=int, orientation="horizontal")

        self.set_OptimizeSource()

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
        self.magnetic_field=(1e9/codata.c)*self.energy/self.magnetic_radius

    def calculateMagneticRadius(self):
        self.magnetic_radius=(1e9/codata.c)*self.energy/self.magnetic_field

    def runShadowSource(self):
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

            shadow_src = ShadowSource.create_bm_src()

            self.populateFields(shadow_src)

            self.progressBarSet(10)

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

            self.setStatusMessage("Plotting Results")

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

    #def sendNewBeam(self, trigger):
    #    if trigger and trigger.new_object == True:
    #        self.runShadowSource()

    def setupUI(self):
        self.set_OptimizeSource()
        self.calculateMagneticField()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.e_min = congruence.checkPositiveNumber(self.e_min, "Minimum energy")
        self.e_max = congruence.checkPositiveNumber(self.e_max, "Maximum energy")
        congruence.checkLessThan(self.e_min, self.e_max,  "Minimum energy",  "Maximum energy")

        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Sigma x")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Sigma z")
        self.emittance_x = congruence.checkPositiveNumber(self.emittance_x, "Emittance x")
        self.emittance_z = congruence.checkPositiveNumber(self.emittance_z, "Emittance z")
        self.distance_from_waist_x = congruence.checkPositiveNumber(self.distance_from_waist_x, "Distance from waist x")
        self.distance_from_waist_z = congruence.checkPositiveNumber(self.distance_from_waist_z, "Distance from waist z")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.magnetic_radius = congruence.checkNumber(self.magnetic_radius, "Magnetic radius")
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
        shadow_src.src.F_OPD = 1
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
        shadow_src.src.R_ALADDIN = self.magnetic_radius / self.workspace_units_to_m
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

    def receive_syned_data(self, data):
        if not data is None:
            if isinstance(data, synedb.Beamline):
                if not data._light_source is None:
                    if isinstance(data._light_source._magnetic_structure, synedbm.BendingMagnet):
                        light_source = data._light_source

                        self.energy = light_source._electron_beam._energy_in_GeV
                        self.sigma_x, self.sigma_z = light_source._electron_beam.get_sigmas_real_space()
                        self.sigma_x /= self.workspace_units_to_m
                        self.sigma_z /= self.workspace_units_to_m
                        sigma_xp, sigma_zp = light_source._electron_beam.get_sigmas_divergence_space()
                        self.emittance_x = self.sigma_x * sigma_xp
                        self.emittance_z = self.sigma_z * sigma_zp

                        if light_source._magnetic_structure._radius > 0:
                            self.magnetic_radius=light_source._magnetic_structure._radius
                            self.calculateMagneticField()
                        elif light_source._magnetic_structure._magnetic_field > 0:
                            self.magnetic_field = light_source._magnetic_structure._magnetic_field
                            self.calculateMagneticRadius()
                    else:
                        raise ValueError("Syned light source not congruent")
                else:
                    raise ValueError("Syned data not correct: light source not present")
            else:
                raise ValueError("Syned data not correct")

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = BendingMagnet()
    ow.show()
    a.exec_()
    ow.saveSettings()
