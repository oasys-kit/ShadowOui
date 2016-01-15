import sys

from PyQt4 import QtGui
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from srxraylib.sources import srfunc

from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerOut, ShadowBeam, \
    ShadowSource
from orangecontrib.shadow.widgets.gui import ow_source

class Wiggler(ow_source.Source):

    NONE_SPECIFIED = "NONE SPECIFIED"

    name = "Wiggler"
    description = "Shadow Source: Wiggler"
    icon = "icons/wiggler.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 3
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", ShadowTriggerOut, "sendNewBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    number_of_rays=Setting(5000)
    seed=Setting(5676561)
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
    use_emittances_combo=Setting(1)
    sigma_x=Setting(0.0078)
    sigma_z=Setting(0.0036)
    emittance_x=Setting(3.8E-7)
    emittance_z=Setting(3.8E-9)
    distance_from_waist_x=Setting(0.0)
    distance_from_waist_z=Setting(0.0)

    type_combo=Setting(0)

    number_of_periods=Setting(50)
    k_value=Setting(7.85)
    id_period=Setting(0.04)

    file_with_b_vs_y = Setting("wiggler.b")
    file_with_harmonics = Setting("wiggler.h")

    CONTROL_AREA_WIDTH = 505

    want_main_area=1

    def __init__(self):
        super().__init__()

        left_box_1 = oasysgui.widgetBox(self.controlArea, "Monte Carlo and Energy Spectrum", addSpace=True, orientation="vertical", height=320, width=self.CONTROL_AREA_WIDTH)

        oasysgui.lineEdit(left_box_1, self, "number_of_rays", "Number of Rays", tooltip="Number of Rays", labelWidth=300, valueType=int, orientation="horizontal")

        oasysgui.lineEdit(left_box_1, self, "seed", "Seed", tooltip="Seed", labelWidth=300, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_min", "Minimum Photon Energy [eV]", tooltip="Minimum Energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "e_max", "Maximum Photon Energy [eV]", tooltip="Maximum Energy [eV]", labelWidth=300, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_1, self, "optimize_source_combo", label="Optimize Source? (reject rays)", items=["No", "Using file with phase space volume", "Using slit/acceptance"], callback=self.set_OptimizeSource, labelWidth=280, orientation="horizontal")

        self.box_using_file_with_phase_space_volume = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_using_file_with_phase_space_volume, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=300, tooltip="Max number of rejected rays", valueType=int, orientation="horizontal")


        file_box = oasysgui.widgetBox(self.box_using_file_with_phase_space_volume, "", addSpace=True, orientation="horizontal", height=25)

        self.le_optimize_file_name = oasysgui.lineEdit(file_box, self, "file_with_phase_space_volume", "File with phase space volume", labelWidth=190, tooltip="File with phase space volume", valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectOptimizeFile)

        self.box_using_slit_acceptance = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_using_slit_acceptance, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=300, tooltip="Max number of rejected rays", valueType=int, orientation="horizontal")
        self.le_slit_distance = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "slit_distance", "--", labelWidth=300, tooltip="Slit Distance", valueType=float, orientation="horizontal")
        self.le_min_x = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "min_x", "--", labelWidth=300, tooltip="Min X/Min Xp", valueType=float, orientation="horizontal")
        self.le_max_x = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "max_x", "--", labelWidth=300, tooltip="Max X/Max Xp", valueType=float, orientation="horizontal")
        self.le_min_z = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "min_z", "--", labelWidth=300, tooltip="Min Z/Min Zp", valueType=float, orientation="horizontal")
        self.le_max_z = oasysgui.lineEdit(self.box_using_slit_acceptance, self, "max_z", "--", labelWidth=300, tooltip="Max Z/Max Zp", valueType=float, orientation="horizontal")

        self.set_OptimizeSource()

        left_box_2 = oasysgui.widgetBox(self.controlArea, "Machine Parameters", addSpace=True, orientation="vertical", height=240)

        oasysgui.lineEdit(left_box_2, self, "energy", "Electron Energy [GeV]", tooltip="Energy [GeV]", labelWidth=300, valueType=float, orientation="horizontal")

        gui.comboBox(left_box_2, self, "use_emittances_combo", label="Use Emittances?", items=["No", "Yes"], callback=self.set_UseEmittances, labelWidth=300, orientation="horizontal")

        self.box_use_emittances = oasysgui.widgetBox(left_box_2, "", addSpace=True, orientation="vertical")

        self.le_sigma_x = oasysgui.lineEdit(left_box_2, self, "sigma_x", "Sigma X", labelWidth=300, tooltip="Sigma X", valueType=float, orientation="horizontal")
        self.le_sigma_z = oasysgui.lineEdit(left_box_2, self, "sigma_z", "Sigma Z", labelWidth=300, tooltip="Sigma Z", valueType=float, orientation="horizontal")
        self.le_emittance_x = oasysgui.lineEdit(left_box_2, self, "emittance_x", "Emittance X", labelWidth=300, tooltip="Emittance X", valueType=float, orientation="horizontal")
        self.le_emittance_z = oasysgui.lineEdit(left_box_2, self, "emittance_z", "Emittance Z", labelWidth=300, tooltip="Emittance Z", valueType=float, orientation="horizontal")
        self.le_distance_from_waist_x = oasysgui.lineEdit(left_box_2, self, "distance_from_waist_x", "Distance from Waist X", labelWidth=300, tooltip="Distance from Waist X", valueType=float, orientation="horizontal")
        self.le_distance_from_waist_z = oasysgui.lineEdit(left_box_2, self, "distance_from_waist_z", "Distance from Waist Z", labelWidth=300, tooltip="Distance from Waist Z", valueType=float, orientation="horizontal")

        self.set_UseEmittances()

        left_box_3 = oasysgui.widgetBox(self.controlArea, "Wiggler Parameters", addSpace=True, orientation="vertical", height=140)

        gui.comboBox(left_box_3, self, "type_combo", label="Type", items=["conventional/sinusoidal", "B from file", "B from harmonics"], callback=self.set_Type, labelWidth=300, orientation="horizontal")

        oasysgui.lineEdit(left_box_3, self, "number_of_periods", "Number of Periods", labelWidth=300, tooltip="Number of Periods", valueType=int, orientation="horizontal")

        self.conventional_sinusoidal_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "k_value", "K value", labelWidth=300, tooltip="K value", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.conventional_sinusoidal_box, self, "id_period", "ID period [m]", labelWidth=300, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        self.b_from_file_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.b_from_file_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_b_vs_y = oasysgui.lineEdit(file_box, self, "file_with_b_vs_y", "File with B vs Y", labelWidth=150, tooltip="File with B vs Y", valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFileWithBvsY)

        self.b_from_harmonics_box = oasysgui.widgetBox(left_box_3, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.b_from_harmonics_box, self, "id_period", "ID period [m]", labelWidth=300, tooltip="ID period [m]", valueType=float, orientation="horizontal")

        file_box = oasysgui.widgetBox(self.b_from_harmonics_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_file_with_harmonics = oasysgui.lineEdit(file_box, self, "file_with_harmonics", "File with harmonics", labelWidth=150, tooltip="File with harmonics", valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFileWithHarmonics)


        self.set_Type()

        gui.separator(self.controlArea, height=10)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/Source", callback=self.runShadowSource)
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
        label.setText(label.text() + "  [" + self.workspace_units_label + "]")
        label = self.le_sigma_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [" + self.workspace_units_label + "]")
        label = self.le_emittance_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [rad." + self.workspace_units_label + "]")
        label = self.le_emittance_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [rad." + self.workspace_units_label + "]")
        label = self.le_distance_from_waist_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [" + self.workspace_units_label + "]")
        label = self.le_distance_from_waist_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + "  [" + self.workspace_units_label + "]")


    def set_OptimizeSource(self):
        self.box_using_file_with_phase_space_volume.setVisible(self.optimize_source_combo == 1)
        self.box_using_slit_acceptance.setVisible(self.optimize_source_combo == 2)

    def set_UseEmittances(self):
        self.box_use_emittances.setVisible(self.use_emittances_combo == 1)

    def set_Type(self):
        self.conventional_sinusoidal_box.setVisible(self.type_combo == 0)
        self.b_from_file_box.setVisible(self.type_combo == 1)
        self.b_from_harmonics_box.setVisible(self.type_combo == 2)

    def selectOptimizeFile(self):
        self.le_optimize_file_name.setText(oasysgui.selectFileFromDialog(self, self.file_with_phase_space_volume, "Open Optimize Source Parameters File"))

    def selectFileWithBvsY(self):
        self.le_file_with_b_vs_y.setText(oasysgui.selectFileFromDialog(self, self.file_with_b_vs_y, "Open File With B vs Y"))

    def selectFileWithHarmonics(self):
        self.le_file_with_harmonics.setText(oasysgui.selectFileFromDialog(self, self.file_with_harmonics, "Open File With Harmonics"))

    def runShadowSource(self):
        #self.error(self.error_id)
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

            wigFile = bytes(congruence.checkFileName("xshwig.sha"), 'utf-8')

            if self.type_combo == 0:
                inData = bytes("", 'utf-8')
            elif self.type_combo == 1:
                inData = bytes(congruence.checkFileName(self.file_with_b_vs_y), 'utf-8')
            elif self.type_combo == 2:
                inData = bytes(congruence.checkFileName(self.file_with_harmonics), 'utf-8')

            self.progressBarSet(10)
            #self.information(0, "Calculate electron trajectory")
            self.setStatusMessage("Calculate electron trajectory")

            (traj, pars) = srfunc.wiggler_trajectory(b_from=self.type_combo,
                                                     inData=inData,
                                                     nPer=self.number_of_periods,
                                                     nTrajPoints=501,
                                                     ener_gev=self.energy,
                                                     per=self.id_period,
                                                     kValue=self.k_value,
                                                     trajFile=congruence.checkFileName("tmp.traj"))

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

            shadow_src.src.NPOINT=self.number_of_rays
            shadow_src.src.ISTAR1=self.seed

            shadow_src.src.CONV_FACT = self.workspace_units_to_cm * 100 # from m to cm (or user unit)

            shadow_src.src.HDIV1 = 1.00000000000000
            shadow_src.src.HDIV2 = 1.00000000000000

            shadow_src.src.PH1=self.e_min
            shadow_src.src.PH2=self.e_max

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

                #self.information(0, "File written to disk: " + str(shadow_src.src.FILE_BOUND))
                self.setStatusMessage("File written to disk: " + str(shadow_src.src.FILE_BOUND))

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

            shadow_src.src.FILE_TRAJ = wigFile

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)
            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            self.progressBarSet(50)

            self.setStatusMessage("Running Shadow/Source")

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
        self.set_UseEmittances()
        self.set_Type()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")
        self.e_min = congruence.checkPositiveNumber(self.e_min, "Minimum energy")
        self.e_max = congruence.checkPositiveNumber(self.e_max, "Maximum energy")
        self.max_number_of_rejected_rays = congruence.checkPositiveNumber(self.max_number_of_rejected_rays,
                                                                         "Max Number of Rejected Rays")
        self.slit_distance = congruence.checkPositiveNumber(self.slit_distance, "Horizontal half-divergence from [+]")
        self.min_x = congruence.checkNumber(self.min_x, "Min X/Min Xp")
        self.max_x = congruence.checkNumber(self.max_x, "Max X/Max Xp")
        self.min_z = congruence.checkNumber(self.min_z, "Min X/Min Xp")
        self.max_z = congruence.checkNumber(self.max_z, "Max X/Max Xp")
        self.energy = congruence.checkPositiveNumber(self.energy, "Energy")
        self.sigma_x = congruence.checkPositiveNumber(self.sigma_x, "Sigma x")
        self.sigma_z = congruence.checkPositiveNumber(self.sigma_z, "Sigma z")
        self.emittance_x = congruence.checkPositiveNumber(self.emittance_x, "Emittance x")
        self.emittance_z = congruence.checkPositiveNumber(self.emittance_z, "Emittance z")
        self.distance_from_waist_x = congruence.checkNumber(self.distance_from_waist_x, "Distance from waist x")
        self.distance_from_waist_z = congruence.checkNumber(self.distance_from_waist_z, "Distance from waist z")
        self.number_of_periods = congruence.checkPositiveNumber(self.number_of_periods, "Number of periods")
        self.k_value = congruence.checkPositiveNumber(self.k_value, "K value")
        self.id_period = congruence.checkPositiveNumber(self.id_period, "ID period")

        if self.optimize_source_combo == 1:
            congruence.checkFile(self.file_with_phase_space_volume)

        if self.type_combo == 1:
            congruence.checkFile(self.file_with_b_vs_y)
        elif self.type_combo == 2:
            congruence.checkFile(self.file_with_harmonics)


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

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = Wiggler()
    ow.show()
    a.exec_()
    ow.saveSettings()
