import copy
import os
import random
import shutil
import sys
import time

import numpy
import orangecanvas.resources as resources
import scipy
import xraylib

from silx.gui.plot.PlotWindow import Plot2D

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtGui import QPalette, QColor, QFont
from orangewidget import gui, widget
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog
from oasys.util.oasys_util import EmittingStream, TTYGrabber, TriggerIn

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement, ShadowPreProcessorData
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowMath, ShadowPhysics, MathTextLabel
from orangecontrib.shadow.widgets.experimental_elements.random_generator import AbsorptionRandom, LorentzianRandom
from orangecontrib.shadow.widgets.gui import ow_automatic_element


class XRDCapillary(ow_automatic_element.AutomaticElement):
    name = "XRD Capillary"
    description = "Shadow OE: XRD Capillary"
    icon = "icons/xrd_capillary.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1
    category = "Experimental Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("PreProcessor Data", ShadowPreProcessorData, "setPreProcessorData"),
              ]

    outputs = [{"name":"Trigger",
                "type": TriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"},
               {"name":"Beam",
                "type": ShadowBeam,
                "doc":"Diffracted Beam",
                "id":"Beam"}]

    input_beam = None

    TABS_AREA_HEIGHT = 545

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 640

    capillary_diameter = Setting(0.3)
    capillary_thickness = Setting(10.0)
    capillary_material = Setting(0)
    sample_material = Setting(0)
    packing_factor = Setting(0.6)
    residual_average_size = Setting(0.0)
    positioning_error = Setting(0.0)

    horizontal_displacement = Setting(0.0)
    vertical_displacement = Setting(0.0)
    calculate_absorption = Setting(0.0)
    absorption_normalization_factor = 0.0

    shift_2theta = Setting(0.000)

    slit_1_vertical_displacement = Setting(0.0)
    slit_2_vertical_displacement = Setting(0.0)
    slit_1_horizontal_displacement = Setting(0.0)
    slit_2_horizontal_displacement = Setting(0.0)

    x_sour_offset = Setting(0.0)
    x_sour_rotation = Setting(0.000)
    y_sour_offset = Setting(0.0)
    y_sour_rotation = Setting(0.000)
    z_sour_offset = Setting(0.0)
    z_sour_rotation = Setting(0.000)

    detector_distance = Setting(0.0)

    diffracted_arm_type = Setting(0)

    slit_1_distance = Setting(0.0)
    slit_1_vertical_aperture = Setting(0.0)
    slit_1_horizontal_aperture = Setting(0.0)
    slit_2_distance = Setting(0.0)
    slit_2_vertical_aperture = Setting(0.0)
    slit_2_horizontal_aperture = Setting(0.0)

    acceptance_slit_distance = Setting(0.0)
    acceptance_slit_vertical_aperture = Setting(0.0)
    acceptance_slit_horizontal_aperture = Setting(0.0)
    analyzer_distance = Setting(0.0)
    analyzer_bragg_angle = Setting(0.0)
    rocking_curve_file = Setting("NONE SPECIFIED")
    mosaic_angle_spread_fwhm = Setting(0.000)

    area_detector_distance = Setting(0.0)
    area_detector_height = Setting(24.5)
    area_detector_width = Setting(28.9)
    area_detector_pixel_size = Setting(100.0)

    start_angle_na = Setting(10.0)
    stop_angle_na = Setting(120.0)
    step = Setting(0.002)
    start_angle = 0.0
    stop_angle = 0.0

    set_number_of_peaks = Setting(0)
    number_of_peaks = Setting(1)

    incremental = Setting(0)
    number_of_executions = Setting(1)
    current_execution = 0

    keep_result = Setting(0)
    number_of_origin_points = Setting(1)
    number_of_rotated_rays = Setting(5)
    normalize = Setting(1)
    degrees_around_peak = Setting(0.01)

    beam_energy = Setting(0.0)
    beam_wavelength = Setting(0.0)
    beam_units_in_use = Setting(0)

    output_file_name = Setting('XRD_Profile.xy')

    kind_of_fit = Setting(0)

    add_lorentz_polarization_factor = Setting(1)
    pm2k_fullprof = Setting(0)
    degree_of_polarization = Setting(0.95)
    monochromator_angle = Setting(14.223)

    add_debye_waller_factor = Setting(1)
    use_default_dwf = Setting(1)
    default_debye_waller_B = 0.0
    new_debye_waller_B = Setting(0.000)

    add_background = Setting(0)
    n_sigma=Setting(0)

    add_constant = Setting(0)
    constant_value = Setting(0.0)

    add_chebyshev = Setting(0)
    cheb_coeff_0 = Setting(0.0)
    cheb_coeff_1 = Setting(0.0)
    cheb_coeff_2 = Setting(0.0)
    cheb_coeff_3 = Setting(0.0)
    cheb_coeff_4 = Setting(0.0)
    cheb_coeff_5 = Setting(0.0)

    add_expdecay = Setting(0)
    expd_coeff_0 = Setting(0.0)
    expd_coeff_1 = Setting(0.0)
    expd_coeff_2 = Setting(0.0)
    expd_coeff_3 = Setting(0.0)
    expd_coeff_4 = Setting(0.0)
    expd_coeff_5 = Setting(0.0)
    expd_decayp_0 = Setting(0.0)
    expd_decayp_1 = Setting(0.0)
    expd_decayp_2 = Setting(0.0)
    expd_decayp_3 = Setting(0.0)
    expd_decayp_4 = Setting(0.0)
    expd_decayp_5 = Setting(0.0)

    average_absorption_coefficient = 0.0
    sample_transmittance = 0.0
    muR = 0.0

    caglioti_U = 0.0
    caglioti_V = 0.0
    caglioti_W = 0.0

    caglioti_a = 0.0
    caglioti_b = 0.0
    caglioti_c = 0.0

    run_simulation=True
    reset_button_pressed=False

    want_main_area=1
    plot_canvas=None

    twotheta_angles = []
    current_counts = []
    squared_counts = []
    points_per_bin = []
    counts = []
    caglioti_fits = []
    noise = []
    absorption_coefficients = []
    caglioti_angles = []
    caglioti_fwhm = []
    caglioti_fwhm_fit = []
    caglioti_eta = []
    caglioti_eta_fit = []
    caglioti_shift = []
    materials = []
    capillary_materials = []
    rocking_data = []

    random_generator_flat = random.Random()

    area_detector_beam = None

    def __init__(self):
        super().__init__()

        self.runaction = widget.OWAction("Run Simulation", self)
        self.runaction.triggered.connect(self.simulate)
        self.addAction(self.runaction)

        self.readCapillaryMaterialConfigurationFiles()
        self.readMaterialConfigurationFiles()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal", height=30)

        self.start_button = gui.button(button_box, self, "Simulate Diffraction", callback=self.simulate)
        self.start_button.setFixedHeight(25)

        self.background_button = gui.button(button_box, self, "Simulate Background", callback=self.simulateBackground)
        self.background_button.setFixedHeight(25)
        palette = QPalette(self.background_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('dark blue'))
        self.background_button.setPalette(palette) # assign new palette

        stop_button = gui.button(button_box, self, "Interrupt", callback=self.stopSimulation)
        stop_button.setFixedHeight(25)
        font = QFont(stop_button.font())
        font.setBold(True)
        stop_button.setFont(font)
        palette = QPalette(stop_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('red'))
        stop_button.setPalette(palette) # assign new palette

        button_box_2 = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal", height=25)

        self.reset_fields_button = gui.button(button_box_2, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(self.reset_fields_button.font())
        font.setItalic(True)
        self.reset_fields_button.setFont(font)
        self.reset_fields_button.setFixedHeight(25)
        self.reset_fields_button.setFixedWidth(128)

        self.reset_bkg_button = gui.button(button_box_2, self, "Reset Background", callback=self.resetBackground)
        self.reset_bkg_button.setFixedHeight(25)
        font = QFont(self.reset_bkg_button.font())
        font.setItalic(True)
        self.reset_bkg_button.setFont(font)
        palette = QPalette(self.reset_bkg_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('dark blue'))
        self.reset_bkg_button.setPalette(palette) # assign new palette
        self.reset_bkg_button.setFixedWidth(135)

        self.reset_button = gui.button(button_box_2, self, "Reset Simulation", callback=self.resetSimulation)
        self.reset_button.setFixedHeight(25)
        font = QFont(self.reset_button.font())
        font.setItalic(True)
        self.reset_button.setFont(font)
        palette = QPalette(self.reset_button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('red'))
        self.reset_button.setPalette(palette) # assign new palette

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        self.tab_simulation = oasysgui.createTabPage(tabs_setting, "Simulation")
        self.tab_physical = oasysgui.createTabPage(tabs_setting, "Experiment")
        self.tab_beam = oasysgui.createTabPage(tabs_setting, "Beam")
        self.tab_aberrations = oasysgui.createTabPage(tabs_setting, "Aberrations")
        self.tab_background = oasysgui.createTabPage(tabs_setting, "Background")
        self.tab_output = oasysgui.createTabPage(tabs_setting, "Output")

        #####################

        box_rays = oasysgui.widgetBox(self.tab_simulation, "Rays Generation", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_rays, self, "number_of_origin_points", "Number of Origin Points into the Capillary", labelWidth=320, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(box_rays, self, "number_of_rotated_rays", "Number of Generated Rays in the XRPD Arc", labelWidth=320, valueType=int, orientation="horizontal")

        gui.comboBox(box_rays, self, "normalize", label="Normalize", labelWidth=320, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

        box_simulation = oasysgui.widgetBox(self.tab_simulation, "Simulation Management", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(box_simulation, "", addSpace=False, orientation="horizontal", height=25)

        self.le_output_file_name = oasysgui.lineEdit(file_box, self, "output_file_name", "Output File Name", labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectOuputFile)

        gui.separator(box_simulation)

        gui.checkBox(box_simulation, self, "keep_result", "Keep Result")
        gui.checkBox(box_simulation, self, "incremental", "Incremental Simulation", callback=self.setIncremental)

        gui.separator(box_simulation)

        self.le_number_of_executions = oasysgui.lineEdit(box_simulation, self, "number_of_executions", "Number of Executions", labelWidth=320, valueType=int, orientation="horizontal")

        self.setIncremental()

        self.le_current_execution = oasysgui.lineEdit(box_simulation, self, "current_execution", "Current Execution", labelWidth=320, valueType=int, orientation="horizontal")
        self.le_current_execution.setReadOnly(True)
        font = QFont(self.le_current_execution.font())
        font.setBold(True)
        self.le_current_execution.setFont(font)
        palette = QPalette(self.le_current_execution.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        self.le_current_execution.setPalette(palette)

        box_ray_tracing = oasysgui.widgetBox(self.tab_simulation, "Ray Tracing Management", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_ray_tracing, self, "degrees_around_peak", "Degrees around Peak", labelWidth=320, valueType=float, orientation="horizontal")

        gui.separator(box_ray_tracing)

        gui.comboBox(box_ray_tracing, self, "beam_units_in_use", label="Units in use", labelWidth=320,
                     items=["eV", "Angstroms"],
                     callback=self.setBeamUnitsInUse, sendSelectedValue=False, orientation="horizontal")

        self.box_ray_tracing_1 = oasysgui.widgetBox(box_ray_tracing, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_ray_tracing_1, self, "beam_energy", "Beam energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

        self.box_ray_tracing_2 = oasysgui.widgetBox(box_ray_tracing, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_ray_tracing_2, self, "beam_wavelength", "Beam wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

        self.setBeamUnitsInUse()

        box_ipf = oasysgui.widgetBox(self.tab_simulation, "IPF Calculation Management", addSpace=False, orientation="vertical")

        gui.comboBox(box_ipf, self, "kind_of_fit", label="FWHM of Peaks Fitting Function", labelWidth=320,
                     items=["Gaussian", "Pseudo-Voigt"],
                     sendSelectedValue=False, orientation="horizontal")




        #####################

        tabs_experiment = oasysgui.tabWidget(self.tab_physical)
        tab_exp_1 = oasysgui.createTabPage(tabs_experiment, "Diffractometer")
        tab_exp_2 = oasysgui.createTabPage(tabs_experiment, "Scan")

        box_sample = oasysgui.widgetBox(tab_exp_1, "Sample Parameters", addSpace=False, orientation="vertical")

        box_capillary = oasysgui.widgetBox(box_sample, "", addSpace=False, orientation="horizontal")

        box_capillary_1 = oasysgui.widgetBox(box_capillary, "", addSpace=False, orientation="vertical", width=210)
        box_capillary_2 = oasysgui.widgetBox(box_capillary, "", addSpace=False, orientation="vertical", width=140)

        oasysgui.lineEdit(box_capillary_1, self, "capillary_diameter", "Capillary: Diameter [mm]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_capillary_2, self, "capillary_thickness", " Thickness [" + u"\u03BC" + "m]", valueType=float, orientation="horizontal")

        capillary_names = []

        for capillary_material in self.capillary_materials:
            capillary_names.append(capillary_material.name)

        gui.comboBox(box_sample, self, "capillary_material", label="Capillary Material", labelWidth=300, items=capillary_names, sendSelectedValue=False, orientation="horizontal")

        chemical_formulas = []

        for material in self.materials:
            chemical_formulas.append(material.chemical_formula)

        gui.comboBox(box_sample, self, "sample_material", label="Sample Material", items=chemical_formulas, labelWidth=260, sendSelectedValue=False, orientation="horizontal", callback=self.setSampleMaterial)

        oasysgui.lineEdit(box_sample, self, "packing_factor", "Packing Factor (0.0 ... 1.0)", labelWidth=300, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_sample, self, "residual_average_size", "Residual Average Size [" + u"\u03BC" + "m]", labelWidth=300, valueType=float, orientation="horizontal")

        box_2theta_arm = oasysgui.widgetBox(tab_exp_1, "2Theta Arm Parameters", addSpace=False, orientation="vertical", height=275)

        gui.comboBox(box_2theta_arm, self, "diffracted_arm_type", label="Diffracted Arm Setup", items=["Slits", "Analyzer", "Area Detector"], labelWidth=260, sendSelectedValue=False, orientation="horizontal", callback=self.setDiffractedArmType)

        self.box_2theta_arm_1 = oasysgui.widgetBox(box_2theta_arm, "", addSpace=False, orientation="vertical")

        self.le_detector_distance = oasysgui.lineEdit(self.box_2theta_arm_1, self, "detector_distance", "Detector Distance", labelWidth=270, tooltip="Detector Distance [cm]", valueType=float, orientation="horizontal")

        gui.separator(self.box_2theta_arm_1)

        self.le_slit_1_distance = oasysgui.lineEdit(self.box_2theta_arm_1, self, "slit_1_distance", "Slit 1 Distance from Goniometer Center", labelWidth=270, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_1, self, "slit_1_vertical_aperture", "Slit 1 Vertical Aperture [" + u"\u03BC" + "m]",  labelWidth=270, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_1, self, "slit_1_horizontal_aperture", "Slit 1 Horizontal Aperture [" + u"\u03BC" + "m]",  labelWidth=270, valueType=float, orientation="horizontal")

        gui.separator(self.box_2theta_arm_1)

        self.le_slit_2_distance = oasysgui.lineEdit(self.box_2theta_arm_1, self, "slit_2_distance", "Slit 2 Distance from Goniometer Center", labelWidth=270, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_1, self, "slit_2_vertical_aperture", "Slit 2 Vertical Aperture [" + u"\u03BC" + "m]", labelWidth=270, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_1, self, "slit_2_horizontal_aperture", "Slit 2 Horizontal Aperture [" + u"\u03BC" + "m]", labelWidth=270, valueType=float, orientation="horizontal")

        self.box_2theta_arm_2 = oasysgui.widgetBox(box_2theta_arm, "", addSpace=False, orientation="vertical")

        self.le_acceptance_slit_distance = oasysgui.lineEdit(self.box_2theta_arm_2, self, "acceptance_slit_distance", "Slit Distance from Goniometer Center", labelWidth=270, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_2, self, "acceptance_slit_vertical_aperture", "Slit Vertical Aperture [" + u"\u03BC" + "m]",  labelWidth=270, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_2, self, "acceptance_slit_horizontal_aperture", "Slit Horizontal Aperture [" + u"\u03BC" + "m]",  labelWidth=270, valueType=float, orientation="horizontal")

        gui.separator(self.box_2theta_arm_2)

        self.le_analyzer_distance = oasysgui.lineEdit(self.box_2theta_arm_2, self, "analyzer_distance", "Crystal Distance from Goniometer Center", labelWidth=280, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_2, self, "analyzer_bragg_angle", "Analyzer Incidence Angle [deg]", labelWidth=270, valueType=float, orientation="horizontal")

        file_box_2 = oasysgui.widgetBox(self.box_2theta_arm_2, "", addSpace=False, orientation="horizontal", height=25)

        self.le_rocking_curve_file = oasysgui.lineEdit(file_box_2, self, "rocking_curve_file", "Crystal Parameters File",  labelWidth=150, valueType=str, orientation="horizontal")

        gui.button(file_box_2, self, "...", callback=self.selectRockingCurveFile)

        oasysgui.lineEdit(self.box_2theta_arm_2, self, "mosaic_angle_spread_fwhm", "Mosaic Angle Spread FWHM [deg]", labelWidth=270, valueType=float, orientation="horizontal")

        self.box_2theta_arm_3 = oasysgui.widgetBox(box_2theta_arm, "", addSpace=False, orientation="vertical")

        gui.separator(self.box_2theta_arm_3)

        self.le_area_detector_distance = oasysgui.lineEdit(self.box_2theta_arm_3, self, "area_detector_distance", "Detector Distance",
                           labelWidth=270, valueType=float, orientation="horizontal")
        self.le_area_detector_height = oasysgui.lineEdit(self.box_2theta_arm_3, self, "area_detector_height", "Detector Height", labelWidth=270,
                           tooltip="Detector Height [cm]", valueType=float, orientation="horizontal")
        self.le_area_detector_width = oasysgui.lineEdit(self.box_2theta_arm_3, self, "area_detector_width", "Detector Width", labelWidth=270,
                           tooltip="Detector Width [cm]", valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_2theta_arm_3, self, "area_detector_pixel_size", "Pixel Size [" + u"\u03BC" + "m]", labelWidth=270,
                           tooltip="Pixel Size [" + u"\u03BC" + "m]", valueType=float, orientation="horizontal")

        box_scan = oasysgui.widgetBox(tab_exp_2, "Scan Parameters", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_scan, self, "start_angle_na", "Start Angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_scan, self, "stop_angle_na", "Stop Angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_scan, self, "step", "Step [deg]", labelWidth=260, valueType=float, orientation="horizontal")

        box_diffraction = oasysgui.widgetBox(tab_exp_2, "Diffraction Parameters", addSpace=False, orientation="vertical")

        gui.comboBox(box_diffraction, self, "set_number_of_peaks", label="set Number of Peaks", labelWidth=350, callback=self.setNumberOfPeaks, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")
        self.le_number_of_peaks = oasysgui.lineEdit(box_diffraction, self, "number_of_peaks", "Number of Peaks", labelWidth=320, valueType=int, orientation="horizontal")

        self.setNumberOfPeaks()

        #####################

        box_beam = oasysgui.widgetBox(self.tab_beam, "Lorentz-Polarization Factor", addSpace=False, orientation="vertical")

        gui.comboBox(box_beam, self, "add_lorentz_polarization_factor", label="Add Lorentz-Polarization Factor", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setPolarization)

        gui.separator(box_beam)

        self.box_polarization =  oasysgui.widgetBox(box_beam, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.box_polarization, self, "pm2k_fullprof", label="Kind of Calculation", labelWidth=340, items=["PM2K", "FULLPROF"], sendSelectedValue=False, orientation="horizontal", callback=self.setKindOfCalculation)

        self.box_degree_of_polarization_pm2k =  oasysgui.widgetBox(self.box_polarization, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_degree_of_polarization_pm2k, self, "degree_of_polarization", "Q Factor [(Ih-Iv)/(Ih+Iv)]", labelWidth=320, valueType=float, orientation="horizontal")
        self.box_degree_of_polarization_fullprof =  oasysgui.widgetBox(self.box_polarization, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_degree_of_polarization_fullprof, self, "degree_of_polarization", "K Factor", labelWidth=320, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.box_polarization, self, "monochromator_angle", "Monochromator Theta Angle [deg]", labelWidth=300, valueType=float, orientation="horizontal")

        self.setPolarization()

        box_beam_2 = oasysgui.widgetBox(self.tab_beam, "Debye-Waller Factor", addSpace=False, orientation="vertical")

        gui.comboBox(box_beam_2, self, "add_debye_waller_factor", label="Add Debye-Waller Factor", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setDebyeWallerFactor)

        gui.separator(box_beam_2)

        self.box_debye_waller =  oasysgui.widgetBox(box_beam_2, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.box_debye_waller, self, "use_default_dwf", label="Use Stored D.W.F. (B) [Angstrom-2]", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setUseDefaultDWF)

        self.box_use_default_dwf_1 =  oasysgui.widgetBox(self.box_debye_waller, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_use_default_dwf_1, self, "new_debye_waller_B", "Debye-Waller Factor (B)", labelWidth=300, valueType=float, orientation="horizontal")
        self.box_use_default_dwf_2 =  oasysgui.widgetBox(self.box_debye_waller, "", addSpace=False, orientation="vertical")
        le_dwf = oasysgui.lineEdit(self.box_use_default_dwf_2, self, "default_debye_waller_B", "Stored Debye-Waller Factor (B) [Angstrom-2]", labelWidth=300, valueType=float, orientation="horizontal")
        le_dwf.setReadOnly(True)
        font = QFont(le_dwf.font())
        font.setBold(True)
        le_dwf.setFont(font)
        palette = QPalette(le_dwf.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        le_dwf.setPalette(palette)

        self.setDebyeWallerFactor()

        #####################

        box_cap_aberrations = oasysgui.widgetBox(self.tab_aberrations, "Capillary Aberrations", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(box_cap_aberrations, self, "positioning_error", "Position Error % (wobbling)", labelWidth=320, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_cap_aberrations, self, "horizontal_displacement", "Horizontal Displacement [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_cap_aberrations, self, "vertical_displacement", "Vertical Displacement [" + u"\u03BC" + "m]", labelWidth=260, valueType=float, orientation="horizontal")
        gui.comboBox(box_cap_aberrations, self, "calculate_absorption", label="Calculate Absorption", labelWidth=350, items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.setAbsorption)

        box = oasysgui.widgetBox(self.tab_aberrations, "Detection System Aberrations", addSpace=False, orientation="horizontal")

        box_gon_aberrations = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", width=300)

        oasysgui.lineEdit(box_gon_aberrations, self, "x_sour_offset", "Offset along X [" + u"\u03BC" + "m]", labelWidth=180, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_gon_aberrations, self, "x_sour_rotation", "CW rotation around X [deg]", labelWidth=180, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(box_gon_aberrations, self, "y_sour_offset", "Offset along Y [" + u"\u03BC" + "m]", labelWidth=180, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_gon_aberrations, self, "y_sour_rotation", "CW rotation around Y [deg]", labelWidth=180, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(box_gon_aberrations, self, "z_sour_offset", "Offset along Z [" + u"\u03BC" + "m]", labelWidth=180, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(box_gon_aberrations, self, "z_sour_rotation", "CW rotation around Z [deg]", labelWidth=180, valueType=float, orientation="horizontal")

        box_gon_aberrations_button = oasysgui.widgetBox(box, "", addSpace=False, orientation="vertical", width=65)

        gui.button(box_gon_aberrations_button, self, "Show\nAxis\nSystem", callback=self.showAxisSystem, height=165)

        box_det_aberrations = oasysgui.widgetBox(self.tab_aberrations, "Detector Arm Aberrations", addSpace=False, orientation="vertical")

        self.slit_1_vertical_displacement_le = oasysgui.lineEdit(box_det_aberrations, self,
                                                                  "slit_1_vertical_displacement",
                                                                  "Slit 1 V Displacement [" + u"\u03BC" + "m]", labelWidth=260,
                                                                  valueType=float, orientation="horizontal")
        self.slit_1_horizontal_displacement_le = oasysgui.lineEdit(box_det_aberrations, self,
                                                                    "slit_1_horizontal_displacement",
                                                                    "Slit 1 H Displacement [" + u"\u03BC" + "m]", labelWidth=260,
                                                                    valueType=float, orientation="horizontal")
        self.slit_2_vertical_displacement_le = oasysgui.lineEdit(box_det_aberrations, self,
                                                                 "slit_2_vertical_displacement", "Slit 2 V Displacement [" + u"\u03BC" + "m]", labelWidth=260,
                                                                 valueType=float, orientation="horizontal")
        self.slit_2_horizontal_displacement_le = oasysgui.lineEdit(box_det_aberrations, self,
                                                                   "slit_2_horizontal_displacement", "Slit 2 H Displacement [" + u"\u03BC" + "m]", labelWidth=260,
                                                                   valueType=float, orientation="horizontal")

        #####################

        box_background = oasysgui.widgetBox(self.tab_background, "Background Parameters", addSpace=False,
                                             orientation="vertical", height=505)

        gui.comboBox(box_background, self, "add_background", label="Add Background", labelWidth=350, items=["No", "Yes"],
                     callback=self.setAddBackground, sendSelectedValue=False, orientation="horizontal")

        #gui.separator(box_background)

        self.box_background_1_hidden = oasysgui.widgetBox(box_background, "", addSpace=False, orientation="vertical")
        self.box_background_1 = oasysgui.widgetBox(box_background, "", addSpace=False, orientation="vertical")
        
        gui.comboBox(self.box_background_1, self, "n_sigma", label="Noise (Nr. Sigma)", labelWidth=347, items=["0.5", "1", "1.5", "2", "2.5", "3"], sendSelectedValue=False, orientation="horizontal")

        tabs_background = oasysgui.tabWidget(self.box_background_1)

        tab_constant = oasysgui.createTabPage(tabs_background, "Constant")
        tab_exponential = oasysgui.createTabPage(tabs_background, "Exponential")
        tab_chebyshev = oasysgui.createTabPage(tabs_background, "Chebyshev")

        self.box_background_const  = oasysgui.widgetBox(tab_constant, "Constant", addSpace=False, orientation="vertical")

        gui.checkBox(self.box_background_const, self, "add_constant", "add Background", callback=self.setConstant)
        #gui.separator(self.box_background_const)

        self.box_background_const_2 = oasysgui.widgetBox(self.box_background_const, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.box_background_const_2, self, "constant_value", "Value", labelWidth=240, valueType=float, orientation="horizontal")

        self.box_chebyshev = oasysgui.widgetBox(tab_chebyshev, "Chebyshev", addSpace=False, orientation="vertical")

        box_equation_che = oasysgui.widgetBox(self.box_chebyshev, "", addSpace=False, orientation="horizontal")

        gui.checkBox(box_equation_che, self, "add_chebyshev", "add Background", callback=self.setChebyshev)

        box_equation_che_1 = oasysgui.widgetBox(box_equation_che, "", addSpace=False, orientation="horizontal")
        box_equation_che_1.setLayout(QtWidgets.QVBoxLayout())
        box_equation_che_1.layout().addWidget(MathTextLabel(r'$\sum_{i=0}^{5}A_{i}T_{i}(2\theta) }$', 9, box_equation_che_1), alignment=Qt.AlignRight)

        self.box_chebyshev_2 = oasysgui.widgetBox(self.box_chebyshev, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_0", "A0", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_1", "A1", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_2", "A2", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_3", "A3", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_4", "A4", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_chebyshev_2, self, "cheb_coeff_5", "A5", labelWidth=240, valueType=float, orientation="horizontal")
         
        self.box_expdecay = oasysgui.widgetBox(tab_exponential, "Exponential Decay", addSpace=False, orientation="vertical")

        box_equation_exp = oasysgui.widgetBox(self.box_expdecay, "", addSpace=False, orientation="horizontal")

        gui.checkBox(box_equation_exp, self, "add_expdecay", "add Background", callback=self.setExpDecay)

        box_equation_exp_1 = oasysgui.widgetBox(box_equation_exp, "", addSpace=False, orientation="horizontal")
        box_equation_exp_1.setLayout(QtWidgets.QVBoxLayout())
        box_equation_exp_1.layout().addWidget(MathTextLabel(r'$\sum_{i=0}^{5}A_{i}e^{-H_{i}2\theta }$', 9, box_equation_exp_1), alignment=Qt.AlignRight)

        self.box_expdecay_2 = oasysgui.widgetBox(self.box_expdecay, "", addSpace=False, orientation="vertical")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_coeff_0", "A0", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_coeff_1", "A1", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_coeff_2", "A2", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_coeff_3", "A3", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_coeff_4", "A4", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_coeff_5", "A5", labelWidth=240, valueType=float, orientation="horizontal")
        gui.separator(self.box_expdecay_2, height=1)
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_decayp_0", "H0", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_decayp_1", "H1", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_decayp_2", "H2", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_decayp_3", "H3", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_decayp_4", "H4", labelWidth=240, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.box_expdecay_2, self, "expd_decayp_5", "H5", labelWidth=240, valueType=float, orientation="horizontal")

        self.setAddBackground()

        #####################

        self.shadow_output = oasysgui.textArea(height=400)

        out_box = gui.widgetBox(self.tab_output, "System Output", addSpace=False, orientation="horizontal")
        out_box.layout().addWidget(self.shadow_output)

        #####################

        gui.rubber(self.controlArea)

        self.plot_tabs = oasysgui.tabWidget(self.mainArea)

        # ---------------------------------------------

        self.tab_results_area = oasysgui.createTabPage(self.plot_tabs, "XRD 2D Pattern")

        self.area_image_box = gui.widgetBox(self.tab_results_area, "", addSpace=False, orientation="vertical")
        self.area_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.area_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.plot_canvas_area = Plot2D()
        self.plot_canvas_area.setGraphXLabel("X")
        self.plot_canvas_area.setGraphYLabel("Z")

        gui.separator(self.area_image_box)

        self.area_image_box.layout().addWidget(self.plot_canvas_area)

        #---------------------------------------------

        tab_results = oasysgui.createTabPage(self.plot_tabs, "XRD Pattern")
        tab_caglioti_fwhm = oasysgui.createTabPage(self.plot_tabs, "Instrumental Broadening")
        tab_caglioti_eta = oasysgui.createTabPage(self.plot_tabs, "Instrumental Peak Shape")
        tab_caglioti_shift = oasysgui.createTabPage(self.plot_tabs, "Instrumental Peak Shift")

        self.image_box = gui.widgetBox(tab_results, "", addSpace=False, orientation="vertical")
        self.image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.absorption_coefficient_box = gui.widgetBox(self.image_box, "", addSpace=False, orientation="vertical")
        self.absorption_coefficient_box.setFixedWidth(420)

        gui.separator(self.absorption_coefficient_box)
        aac = oasysgui.lineEdit(self.absorption_coefficient_box, self, "average_absorption_coefficient", "Sample Linear Absorption Coefficient [cm-1]", labelWidth=290, valueType=float, orientation="horizontal")
        tra = oasysgui.lineEdit(self.absorption_coefficient_box, self, "sample_transmittance", "Sample Transmittance [%]", labelWidth=290, valueType=float, orientation="horizontal")
        mur = oasysgui.lineEdit(self.absorption_coefficient_box, self, "muR",                            "muR", labelWidth=290, valueType=float, orientation="horizontal")

        tra.setReadOnly(True)
        font = QFont(tra.font())
        font.setBold(True)
        tra.setFont(font)
        palette = QPalette(tra.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        tra.setPalette(palette)

        aac.setReadOnly(True)
        font = QFont(aac.font())
        font.setBold(True)
        aac.setFont(font)
        palette = QPalette(aac.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        aac.setPalette(palette)

        mur.setReadOnly(True)
        font = QFont(mur.font())
        font.setBold(True)
        mur.setFont(font)
        palette = QPalette(mur.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        mur.setPalette(palette)

        self.setAbsorption()

        self.plot_canvas = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.plot_canvas.setGraphXLabel("2Theta [deg]")
        self.plot_canvas.setGraphYLabel("Intensity (arbitrary units)")
        self.plot_canvas.setDefaultPlotLines(True)
        self.plot_canvas.setActiveCurveColor(color='blue')

        self.image_box.layout().addWidget(self.plot_canvas)

        self.caglioti_fwhm_image_box = gui.widgetBox(tab_caglioti_fwhm, "", addSpace=False, orientation="vertical")
        self.caglioti_fwhm_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.caglioti_fwhm_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.caglioti_fwhm_coefficient_box = gui.widgetBox(self.caglioti_fwhm_image_box, "", addSpace=False, orientation="vertical")
        self.caglioti_fwhm_coefficient_box.setFixedWidth(200)

        gui.separator(self.caglioti_fwhm_coefficient_box)
        c_U = oasysgui.lineEdit(self.caglioti_fwhm_coefficient_box, self, "caglioti_U", "U", labelWidth=50, valueType=float, orientation="horizontal")
        c_V = oasysgui.lineEdit(self.caglioti_fwhm_coefficient_box, self, "caglioti_V", "V", labelWidth=50, valueType=float, orientation="horizontal")
        c_W = oasysgui.lineEdit(self.caglioti_fwhm_coefficient_box, self, "caglioti_W", "W", labelWidth=50, valueType=float, orientation="horizontal")

        c_U.setReadOnly(True)
        font = QFont(c_U.font())
        font.setBold(True)
        c_U.setFont(font)
        palette = QPalette(c_U.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_U.setPalette(palette)

        c_V.setReadOnly(True)
        font = QFont(c_V.font())
        font.setBold(True)
        c_V.setFont(font)
        palette = QPalette(c_V.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_V.setPalette(palette)

        c_W.setReadOnly(True)
        font = QFont(c_W.font())
        font.setBold(True)
        c_W.setFont(font)
        palette = QPalette(c_W.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_W.setPalette(palette)

        self.caglioti_fwhm_canvas = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.caglioti_fwhm_canvas.setGraphXLabel("2Theta [deg]")
        self.caglioti_fwhm_canvas.setGraphYLabel("FWHM [deg]")
        self.caglioti_fwhm_canvas.setDefaultPlotLines(True)
        self.caglioti_fwhm_canvas.setActiveCurveColor(color='blue')

        self.caglioti_fwhm_image_box.layout().addWidget(self.caglioti_fwhm_canvas)
        
        # --------------------------------------

        self.caglioti_eta_image_box = gui.widgetBox(tab_caglioti_eta, "", addSpace=False, orientation="vertical")
        self.caglioti_eta_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.caglioti_eta_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.caglioti_eta_coefficient_box = gui.widgetBox(self.caglioti_eta_image_box, "", addSpace=False, orientation="vertical")
        self.caglioti_eta_coefficient_box.setFixedWidth(200)

        gui.separator(self.caglioti_eta_coefficient_box)
        c_a = oasysgui.lineEdit(self.caglioti_eta_coefficient_box, self, "caglioti_a", "a", labelWidth=50, valueType=float, orientation="horizontal")
        c_b = oasysgui.lineEdit(self.caglioti_eta_coefficient_box, self, "caglioti_b", "b", labelWidth=50, valueType=float, orientation="horizontal")
        c_c = oasysgui.lineEdit(self.caglioti_eta_coefficient_box, self, "caglioti_c", "c", labelWidth=50, valueType=float, orientation="horizontal")

        c_a.setReadOnly(True)
        font = QFont(c_a.font())
        font.setBold(True)
        c_a.setFont(font)
        palette = QPalette(c_a.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_a.setPalette(palette)

        c_b.setReadOnly(True)
        font = QFont(c_b.font())
        font.setBold(True)
        c_b.setFont(font)
        palette = QPalette(c_b.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_b.setPalette(palette)

        c_c.setReadOnly(True)
        font = QFont(c_c.font())
        font.setBold(True)
        c_c.setFont(font)
        palette = QPalette(c_c.palette())
        palette.setColor(QPalette.Text, QColor('dark blue'))
        palette.setColor(QPalette.Base, QColor(243, 240, 160))
        c_c.setPalette(palette)

        self.caglioti_eta_canvas = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.caglioti_eta_canvas.setGraphXLabel("2Theta [deg]")
        self.caglioti_eta_canvas.setGraphYLabel("Eta")
        self.caglioti_eta_canvas.setDefaultPlotLines(True)
        self.caglioti_eta_canvas.setActiveCurveColor(color='blue')

        self.caglioti_eta_image_box.layout().addWidget(self.caglioti_eta_canvas)

        # ----------------------------------------

        self.caglioti_shift_image_box = gui.widgetBox(tab_caglioti_shift, "", addSpace=False, orientation="vertical")
        self.caglioti_shift_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.caglioti_shift_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.caglioti_shift_canvas = oasysgui.plotWindow(roi=False, control=False, position=True)
        self.caglioti_shift_canvas.setGraphXLabel("2Theta [deg]")
        self.caglioti_shift_canvas.setGraphYLabel("(2Theta_Bragg - 2Theta) [deg]")
        self.caglioti_shift_canvas.setDefaultPlotLines(True)
        self.caglioti_shift_canvas.setActiveCurveColor(color='blue')

        self.caglioti_shift_image_box.layout().addWidget(self.caglioti_shift_canvas)

        self.setDiffractedArmType()

        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
        self.micron_to_user_units = 1e-4 / self.workspace_units_to_cm
        self.micron_to_cm = 1e-4
        self.mm_to_user_units = 1e-1 / self.workspace_units_to_cm
        self.mm_to_cm = 1e-1
        self.micron_to_angstrom = 1e4

        label = self.le_detector_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_slit_1_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_slit_2_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        
        label = self.le_acceptance_slit_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_analyzer_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        
        label = self.le_area_detector_distance.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_area_detector_height.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_area_detector_width.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.simulate()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                self.rocking_curve_file=data.bragg_data_file


    ############################################################
    # GUI MANAGEMENT METHODS
    ############################################################

    def callResetSettings(self):
        super().callResetSettings()

        self.setIncremental()
        self.setNumberOfPeaks()
        self.setPolarization()
        self.setDebyeWallerFactor()
        self.setAddBackground()
        self.setAbsorption()

    def setAbsorption(self):
        self.absorption_coefficient_box.setVisible(self.calculate_absorption==1)

    def setTabsAndButtonsEnabled(self, enabled=True):
        self.tab_simulation.setEnabled(enabled)
        self.tab_physical.setEnabled(enabled)
        self.tab_beam.setEnabled(enabled)
        self.tab_aberrations.setEnabled(enabled)
        self.tab_background.setEnabled(enabled)
        self.tab_output.setEnabled(enabled)

        self.start_button.setEnabled(enabled)
        self.reset_fields_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

        if not enabled:
            self.background_button.setEnabled(False)
            self.reset_bkg_button.setEnabled(False)
        else:
            self.background_button.setEnabled(self.add_background == 1)
            self.reset_bkg_button.setEnabled(self.add_background == 1)

    def setSimulationTabsAndButtonsEnabled(self, enabled=True):
        self.tab_background.setEnabled(enabled)

        self.start_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)

        if not enabled:
            self.background_button.setEnabled(False)
            self.reset_bkg_button.setEnabled(False)
        else:
            self.background_button.setEnabled(self.add_background == 1)
            self.reset_bkg_button.setEnabled(self.add_background == 1)

    def setIncremental(self):
        self.le_number_of_executions.setEnabled(self.incremental == 1)

    def setBeamUnitsInUse(self):
        self.box_ray_tracing_1.setVisible(self.beam_units_in_use == 0)
        self.box_ray_tracing_2.setVisible(self.beam_units_in_use == 1)

    def setDiffractedArmType(self):
        self.box_2theta_arm_1.setVisible(self.diffracted_arm_type == 0)
        self.box_2theta_arm_2.setVisible(self.diffracted_arm_type == 1)
        self.box_2theta_arm_3.setVisible(self.diffracted_arm_type == 2)

        self.slit_1_vertical_displacement_le.setEnabled(self.diffracted_arm_type != 2)
        self.slit_1_horizontal_displacement_le.setEnabled(self.diffracted_arm_type != 2)

        self.slit_2_vertical_displacement_le.setEnabled(self.diffracted_arm_type == 0)
        self.slit_2_horizontal_displacement_le.setEnabled(self.diffracted_arm_type == 0)

        if self.diffracted_arm_type != 2:
            if (self.plot_tabs.count() == 5): self.plot_tabs.removeTab(0)
        else:
            if (self.plot_tabs.count() == 4): self.plot_tabs.insertTab(0, self.tab_results_area, "XRD Pattern 2D")

    def setNumberOfPeaks(self):
        self.le_number_of_peaks.setEnabled(self.set_number_of_peaks == 1)

    def setSampleMaterial(self):
        self.default_debye_waller_B = self.getDebyeWallerB(self.sample_material)

    def setKindOfCalculation(self):
        self.box_degree_of_polarization_pm2k.setVisible(self.pm2k_fullprof==0)
        self.box_degree_of_polarization_fullprof.setVisible(self.pm2k_fullprof==1)

    def setPolarization(self):
        self.box_polarization.setVisible(self.add_lorentz_polarization_factor == 1)
        if (self.add_lorentz_polarization_factor==1): self.setKindOfCalculation()

    def setUseDefaultDWF(self):
        self.box_use_default_dwf_1.setVisible(self.use_default_dwf==0)
        self.box_use_default_dwf_2.setVisible(self.use_default_dwf==1)

    def setDebyeWallerFactor(self):
        self.box_debye_waller.setVisible(self.add_debye_waller_factor == 1)
        if (self.add_debye_waller_factor==1):
            self.setUseDefaultDWF()
            self.setSampleMaterial()

    class ShowAxisSystemDialog(QDialog):

        def __init__(self, parent=None):
            QDialog.__init__(self, parent)
            self.setWindowTitle('Axis System')
            layout = QtWidgets.QVBoxLayout(self)
            label = QtWidgets.QLabel("")

            file = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.experimental_elements"), "misc", "axis.png")

            label.setPixmap(QtGui.QPixmap(file))

            bbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)

            bbox.accepted.connect(self.accept)
            layout.addWidget(label)
            layout.addWidget(bbox)


    def showAxisSystem(self):
        dialog = XRDCapillary.ShowAxisSystemDialog(parent=self)
        dialog.show()


    def setAddBackground(self):
        self.box_background_1_hidden.setVisible(self.add_background == 0)
        self.box_background_1.setVisible(self.add_background == 1)

        self.setConstant()
        self.setChebyshev()
        self.setExpDecay()
        self.background_button.setEnabled(self.add_background == 1)
        self.reset_bkg_button.setEnabled(self.add_background == 1)

    def setConstant(self):
        self.box_background_const_2.setEnabled(self.add_constant == 1)

    def setChebyshev(self):
        self.box_chebyshev_2.setEnabled(self.add_chebyshev == 1)
        
    def setExpDecay(self):
        self.box_expdecay_2.setEnabled(self.add_expdecay == 1)

    def plot2DResults(self):
        if not self.area_detector_beam is None:
            nbins_h = int(numpy.floor(self.area_detector_width / (self.area_detector_pixel_size * self.micron_to_user_units)))
            nbins_v = int(numpy.floor(self.area_detector_height / (self.area_detector_pixel_size * self.micron_to_user_units)))

            x_range = [-self.area_detector_width/2, self.area_detector_width/2]
            y_range = [-self.area_detector_height/2, self.area_detector_height/2]

            origin = (-self.area_detector_width/2, -self.area_detector_height/2)
            scale = ((self.area_detector_pixel_size * self.micron_to_user_units), (self.area_detector_pixel_size * self.micron_to_user_units))

            ticket = self.area_detector_beam._beam.histo2(1, 3, xrange=x_range, yrange=y_range, nbins_h=nbins_h, nbins_v=nbins_v, ref=23)
            normalized_data = (ticket['histogram'] / ticket['histogram'].max()) * 100000  # just for the quality of the plot

            # inversion of axis for pyMCA
            data_to_plot = []
            for y_index in range(0, nbins_v):
                x_values = []
                for x_index in range(0, nbins_h):
                    x_values.append(normalized_data[x_index][y_index])

                data_to_plot.append(x_values)

            self.plot_canvas_area.addImage(numpy.array(data_to_plot),
                                           origin=origin,
                                           scale=scale,
                                           colormap={"name":"gray", "normalization":"log", "autoscale":True, "vmin":0, "vmax":0, "colors":256})
            self.plot_canvas_area.setGraphXLabel("X [" + self.workspace_units_label + "]")
            self.plot_canvas_area.setGraphYLabel("Z [" + self.workspace_units_label + "]")
            self.plot_canvas_area.setKeepDataAspectRatio(True)

            #time.sleep(0.1)

    def plotResult(self, clear_caglioti=True, reflections=None):
        if not len(self.twotheta_angles)==0:
            data = numpy.add(self.counts, self.noise)

            if self.kind_of_fit == 0:
                fitting_function = "Gaussian"
            elif self.kind_of_fit == 1:
                fitting_function = "Pseudo-Voigt"

            self.plot_canvas.clearCurves()
            self.plot_canvas.addCurve(self.twotheta_angles, data, "XRD Diffraction pattern", symbol=',', color='blue', replace=True) #'+', '^',
            self.plot_canvas.setGraphTitle("Peaks fitting function: " + fitting_function)
            self.plot_canvas.setGraphXLabel("2Theta [deg]")
            self.plot_canvas.setGraphYLabel("Intensity (arbitrary units)")

            if clear_caglioti:
                self.caglioti_fwhm_canvas.clearCurves()
                self.caglioti_eta_canvas.clearCurves()
                self.caglioti_shift_canvas.clearCurves()

            if not reflections is None:
                self.populateCagliotisData(reflections)

                self.plot_canvas.addCurve(self.twotheta_angles, self.caglioti_fits, "Caglioti Fits", symbol=',', color='red', linestyle="--") #'+', '^',
                self.caglioti_fwhm_canvas.addCurve(self.caglioti_angles, self.caglioti_fwhm, "FWHM", symbol=',', color='blue', replace=True) #'+', '^',
                self.caglioti_eta_canvas.addCurve(self.caglioti_angles, self.caglioti_eta, "p.V. Mixing Factor", symbol=',', color='blue', replace=True) #'+', '^',
                self.caglioti_shift_canvas.addCurve(self.caglioti_angles, self.caglioti_shift, "Peak Shift", symbol=',', color='blue', replace=True) #'+', '^',
                self.caglioti_fwhm_canvas.setGraphXLabel("2Theta [deg]")
                self.caglioti_fwhm_canvas.setGraphYLabel("FWHM [deg]")
                self.caglioti_eta_canvas.setGraphXLabel("2Theta [deg]")
                self.caglioti_eta_canvas.setGraphYLabel("Eta")
                self.caglioti_shift_canvas.setGraphXLabel("2Theta [deg]")
                self.caglioti_shift_canvas.setGraphYLabel("(2Theta_Bragg - 2Theta) [deg]")

                if not (len(self.caglioti_angles) < 3):
                    try:
                        parameters, covariance_matrix = ShadowMath.caglioti_broadening_fit(data_x=self.caglioti_angles, data_y=self.caglioti_fwhm)

                        self.caglioti_U = round(parameters[0], 7)
                        self.caglioti_V = round(parameters[1], 7)
                        self.caglioti_W = round(parameters[2], 7)

                        self.caglioti_fwhm_fit = numpy.zeros(len(self.caglioti_angles))

                        for index in range(0, len(self.caglioti_angles)):
                            self.caglioti_fwhm_fit[index] = ShadowMath.caglioti_broadening_function(self.caglioti_angles[index], parameters[0], parameters[1], parameters[2])

                        self.caglioti_fwhm_canvas.addCurve(self.caglioti_angles, self.caglioti_fwhm_fit, symbol=',', color='red', linestyle="--") #'+', '^',
                    except:
                        self.caglioti_U = -1.000
                        self.caglioti_V = -1.000
                        self.caglioti_W = -1.000

                    try:
                        parameters, covariance_matrix = ShadowMath.caglioti_shape_fit(data_x=self.caglioti_angles, data_y=self.caglioti_eta)

                        self.caglioti_a = round(parameters[0], 7)
                        self.caglioti_b = round(parameters[1], 7)
                        self.caglioti_c = round(parameters[2], 7)

                        self.caglioti_eta_fit = numpy.zeros(len(self.caglioti_angles))

                        for index in range(0, len(self.caglioti_angles)):
                            self.caglioti_eta_fit[index] = ShadowMath.caglioti_shape_function(self.caglioti_angles[index], parameters[0], parameters[1], parameters[2])

                        self.caglioti_eta_canvas.addCurve(self.caglioti_angles, self.caglioti_eta_fit, symbol=',', color='red', linestyle="--") #'+', '^',
                    except:
                        self.caglioti_U = -1.000
                        self.caglioti_V = -1.000
                        self.caglioti_W = -1.000

                        self.caglioti_a = -1.000
                        self.caglioti_b = -1.000
                        self.caglioti_c = -1.000
                else:
                    self.caglioti_U = 0.000
                    self.caglioti_V = 0.000
                    self.caglioti_W = 0.000
                    self.caglioti_a = 0.000
                    self.caglioti_b = 0.000
                    self.caglioti_c = 0.000

    ############################################################
    # EVENT MANAGEMENT METHODS
    ############################################################

    def stopSimulation(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Interruption of the Simulation?"):
            self.run_simulation = False

    def resetBackground(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Simulated Background?"):
            cursor = range(0, len(self.noise))

            for angle_index in cursor:
                self.noise[angle_index] = 0

            self.plotResult(clear_caglioti=False)
            self.writeOutFile(reset=True)

    def resetSimulation(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Simulated Data?"):
            self.current_new_beam = 0

            cursor = range(0, len(self.counts))

            for angle_index in cursor:
                self.current_counts[angle_index] = 0.0
                self.counts[angle_index] = 0.0
                self.squared_counts[angle_index] = 0.0
                self.points_per_bin[angle_index] = 0

            cursor =  range(0, len(self.absorption_coefficients))

            for index in cursor:
                self.absorption_coefficients[index] = 0.0

            cursor = range(0, len(self.noise))

            for angle_index in cursor:
                self.noise[angle_index] = 0

            self.plotResult()
            self.plot_canvas_area.clearImages()
            self.writeOutFile(reset=True)

            self.setTabsAndButtonsEnabled(True)

            self.reset_button_pressed = True

    def checkFields(self):
        self.number_of_origin_points = congruence.checkStrictlyPositiveNumber(self.number_of_origin_points, "Number of Origin Points into the Capillary")
        self.number_of_rotated_rays = congruence.checkStrictlyPositiveNumber(self.number_of_rotated_rays, "Number of Generated Rays in the Powder Diffraction Arc")

        if self.incremental == 1:
            self.number_of_executions = congruence.checkStrictlyPositiveNumber(self.number_of_executions, "Number of Executions")

        congruence.checkDir(self.output_file_name)

        self.degrees_around_peak = congruence.checkStrictlyPositiveNumber(self.degrees_around_peak, "Degrees around Peak")

        if self.beam_units_in_use == 0:
            self.beam_energy = congruence.checkStrictlyPositiveNumber(self.beam_energy, "Beam Energy")
        else:
            self.beam_wavelength = congruence.checkStrictlyPositiveNumber(self.beam_wavelength, "Wavelength")

        #############

        self.capillary_diameter = congruence.checkStrictlyPositiveNumber(self.capillary_diameter, "Capillary Diameter")
        self.capillary_thickness = congruence.checkStrictlyPositiveNumber(self.capillary_thickness, "Capillary Thickness")
        self.packing_factor = congruence.checkStrictlyPositiveNumber(self.packing_factor, "Packing Factor")
        self.residual_average_size = congruence.checkPositiveNumber(self.residual_average_size, "Residual Average Size")

        if self.diffracted_arm_type == 0:
            self.detector_distance = congruence.checkStrictlyPositiveNumber(self.detector_distance, "Detector Distance")
            self.slit_1_distance = congruence.checkStrictlyPositiveNumber(self.slit_1_distance, "Slit 1 Distance from Goniometer Center")
            self.slit_1_vertical_aperture = congruence.checkStrictlyPositiveNumber(self.slit_1_vertical_aperture, "Slit 1 Vertical Aperture")
            self.slit_1_horizontal_aperture = congruence.checkStrictlyPositiveNumber(self.slit_1_horizontal_aperture, "Slit 1 Horizontal Aperture")
            self.slit_2_distance = congruence.checkStrictlyPositiveNumber(self.slit_2_distance, "Slit 2 Distance from Goniometer Center")
            self.slit_2_vertical_aperture = congruence.checkStrictlyPositiveNumber(self.slit_2_vertical_aperture, "Slit 2 Vertical Aperture")
            self.slit_2_horizontal_aperture = congruence.checkStrictlyPositiveNumber(self.slit_2_horizontal_aperture, "Slit 2 Horizontal Aperture")
            congruence.checkLessThan(self.slit_1_distance, self.slit_2_distance, "Slit 1 Distance from Goniometer Center", "Slit 2 Distance from Goniometer Center")
        elif self.diffracted_arm_type == 1:
            self.acceptance_slit_distance = congruence.checkStrictlyPositiveNumber(self.acceptance_slit_distance, "Slit Distance from Goniometer Center")
            self.acceptance_slit_vertical_aperture = congruence.checkStrictlyPositiveNumber(self.acceptance_slit_vertical_aperture, "Slit Vertical Aperture")
            self.acceptance_slit_horizontal_aperture = congruence.checkStrictlyPositiveNumber(self.acceptance_slit_horizontal_aperture, "Slit Horizontal Aperture")
            self.analyzer_distance = congruence.checkStrictlyPositiveNumber(self.analyzer_distance, "Crystal Distance from Goniometer Center")
            self.analyzer_bragg_angle = congruence.checkStrictlyPositiveNumber(self.analyzer_bragg_angle, "Analyzer Incidence Angle")
            congruence.checkLessThan(self.analyzer_bragg_angle, 90, "Analyzer Incidence Angle", "90 deg")
            congruence.checkFile(self.rocking_curve_file)
            self.mosaic_angle_spread_fwhm = congruence.checkPositiveNumber(self.mosaic_angle_spread_fwhm, "Mosaic Angle Spread FWHM")
            congruence.checkLessThan(self.acceptance_slit_distance, self.analyzer_distance, "Slit Distance from Goniometer Center", "Crystal Distance from Goniometer Center")
        elif self.diffracted_arm_type == 2:
            self.area_detector_distance = congruence.checkStrictlyPositiveNumber(self.area_detector_distance,
                                                                                "Detector Distance")
            self.area_detector_height = congruence.checkStrictlyPositiveNumber(self.area_detector_height,
                                                                              "Detector Height")
            self.area_detector_width = congruence.checkStrictlyPositiveNumber(self.area_detector_width, "Detector Width")
            self.area_detector_pixel_size = congruence.checkStrictlyPositiveNumber(self.area_detector_pixel_size,
                                                                                  "Pixel Size")

        self.start_angle_na = congruence.checkPositiveAngle(self.start_angle_na, "Start Angle")
        self.stop_angle_na = congruence.checkPositiveAngle(self.stop_angle_na, "Stop Angle")
        congruence.checkLessThan(self.start_angle_na, self.stop_angle_na, "Start Angle", "Stop Angle")
        congruence.checkLessThan(self.stop_angle_na, 180, "Stop Angle", "180 deg")
        self.step = congruence.checkPositiveAngle(self.step, "Step")

        if self.set_number_of_peaks == 1:
            self.number_of_peaks = congruence.checkStrictlyPositiveNumber(self.number_of_peaks, "Number of Peaks")

        #############

        if self.add_lorentz_polarization_factor == 1:
            if self.pm2k_fullprof == 0:
                self.degree_of_polarization = congruence.checkPositiveNumber(self.degree_of_polarization, "Q Factor")
            else:
                self.degree_of_polarization = congruence.checkPositiveNumber(self.degree_of_polarization, "K Factor")

            self.monochromator_angle = congruence.checkPositiveAngle(self.monochromator_angle, "Monochromator Theta Angle")
            congruence.checkLessThan(self.monochromator_angle, 90, "Monochromator Theta Angle", "90 deg")

        if self.add_debye_waller_factor == 1 and self.use_default_dwf == 0:
            self.new_debye_waller_B = congruence.checkPositiveNumber(self.new_debye_waller_B, "Debye-Waller Factor (B)")

        #############

        self.positioning_error = congruence.checkPositiveNumber(self.positioning_error, "Position Error")

        #############

        if self.add_constant == 1:
            self.constant_value = congruence.checkStrictlyPositiveNumber(self.constant_value, "Constant Background Value")

    ############################################################
    # MAIN METHOD - SIMULATION ALGORITHM
    ############################################################

    def simulate(self):
        try:
            if self.input_beam is None: raise Exception("No input beam, run the optical simulation first")
            elif not hasattr(self.input_beam._beam, "rays"): raise Exception("No good rays, modify the optical simulation")

            sys.stdout = EmittingStream(textWritten=self.writeStdOut)

            if self.trace_shadow:
                grabber = TTYGrabber()
                grabber.start()

            #self.error(self.error_id)

            go = numpy.where(self.input_beam._beam.rays[:,9] == 1)

            go_input_beam = ShadowBeam()
            go_input_beam._beam.rays = copy.deepcopy(self.input_beam._beam.rays[go])

            number_of_input_rays = len(go_input_beam._beam.rays)

            if number_of_input_rays == 0: raise Exception("No good rays, modify the optical simulation")

            self.random_generator_flat.seed()

            input_rays = range(0, number_of_input_rays)

            self.checkFields()

            self.backupOutFile()

            self.run_simulation = True
            self.setTabsAndButtonsEnabled(False)

            executions = range(0,1)

            if (self.incremental==1):
                executions = range(0, self.number_of_executions)

            ################################
            # ARRAYS FOR OUTPUT AND PLOTS

            steps = self.initialize()

            ################################
            # PARAMETERS CALCULATED ONCE

            # distances in CM

            capillary_radius = self.capillary_diameter*(1+self.positioning_error*0.01)*self.mm_to_user_units*0.5
            displacement_h = self.horizontal_displacement*self.micron_to_user_units
            displacement_v = self.vertical_displacement*self.micron_to_user_units

            self.D_1 = self.slit_1_distance
            self.D_2 = self.slit_2_distance

            self.horizontal_acceptance_slit_1 = self.slit_1_horizontal_aperture*self.micron_to_user_units
            self.vertical_acceptance_slit_1 = self.slit_1_vertical_aperture*self.micron_to_user_units
            self.horizontal_acceptance_slit_2 = self.slit_2_horizontal_aperture*self.micron_to_user_units
            self.vertical_acceptance_slit_2 = self.slit_2_vertical_aperture*self.micron_to_user_units

            self.slit_1_vertical_displacement_cm = self.slit_1_vertical_displacement*self.micron_to_user_units
            self.slit_2_vertical_displacement_cm = self.slit_2_vertical_displacement*self.micron_to_user_units
            self.slit_1_horizontal_displacement_cm = self.slit_1_horizontal_displacement*self.micron_to_user_units
            self.slit_2_horizontal_displacement_cm = self.slit_2_horizontal_displacement*self.micron_to_user_units

            self.x_sour_offset_cm = self.x_sour_offset*self.micron_to_user_units
            self.y_sour_offset_cm = self.y_sour_offset*self.micron_to_user_units
            self.z_sour_offset_cm = self.z_sour_offset*self.micron_to_user_units

            self.horizontal_acceptance_analyzer = self.acceptance_slit_horizontal_aperture*self.micron_to_user_units
            self.vertical_acceptance_analyzer = self.acceptance_slit_vertical_aperture*self.micron_to_user_units

            if self.beam_units_in_use == 0 : #eV
                avg_wavelength = ShadowPhysics.getWavelengthFromEnergy(self.beam_energy) # in Angstrom
            else:
                avg_wavelength = self.beam_wavelength # in Angstrom

            if self.set_number_of_peaks == 1:
                reflections = self.getReflections(self.sample_material, self.number_of_peaks, avg_wavelength=avg_wavelength)
            else:
                reflections = self.getReflections(self.sample_material, avg_wavelength=avg_wavelength)

            if len(reflections) == 0:
                raise Exception("No Bragg reflections in the angular acceptance of the scan/detector")

            if self.calculate_absorption == 1:
                self.absorption_normalization_factor = 1/self.getTransmittance(capillary_radius*2, avg_wavelength)

            ################################
            # EXECUTION CYCLES

            for execution in executions:
                if not self.run_simulation: break

                self.resetCurrentCounts(steps)

                self.le_current_execution.setText(str(execution+1))

                self.progressBarInit()

                if (self.incremental == 1 and self.number_of_executions > 1):
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(number_of_input_rays)+ " rays: " + str(execution+1) + " of " + str(self.number_of_executions))
                else:
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(number_of_input_rays)+ " rays")

                self.progressBarSet(0)

                bar_value, diffracted_rays = self.generateDiffractedRays(0,
                                                                         capillary_radius,
                                                                         displacement_h,
                                                                         displacement_v,
                                                                         go_input_beam,
                                                                         input_rays,
                                                                         (50/number_of_input_rays),
                                                                         reflections)

                self.average_absorption_coefficient = round(numpy.array(self.absorption_coefficients).mean(), 2) # cm-1
                self.muR = round(self.average_absorption_coefficient*self.capillary_diameter*0.5*self.mm_to_cm, 2) # distance in cm
                self.sample_transmittance = round(100*numpy.exp(-2 * self.muR), 2) # distance in cm

                if (self.incremental == 1 and self.number_of_executions > 1):
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(len(diffracted_rays))+ " diffracted rays: " + str(execution+1) + " of " + str(self.number_of_executions))
                else:
                    self.setStatusMessage("Running XRD Capillary Simulation on " + str(len(diffracted_rays))+ " diffracted rays")

                self.send("Beam", self.generateXRDPattern(bar_value, diffracted_rays, avg_wavelength, reflections))

            self.writeOutFile()

            self.progressBarSet(100)
            self.setSimulationTabsAndButtonsEnabled(True)

            self.setStatusMessage("")

            self.progressBarFinished()

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                    self.writeStdOut(row)

            if self.run_simulation == True:
                self.send("Trigger", TriggerIn(new_object=True))
            else:
                self.run_simulation=True
                self.send("Trigger", TriggerIn(interrupt=True))
        except PermissionError as exception:
            QtWidgets.QMessageBox.critical(self, "Permission Error", str(exception), QtWidgets.QMessageBox.Ok)

            self.setSimulationTabsAndButtonsEnabled(True)
            self.setStatusMessage("")
            self.progressBarFinished()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error", str(exception.args[0]), QtWidgets.QMessageBox.Ok)

            self.setSimulationTabsAndButtonsEnabled(True)
            self.setStatusMessage("")
            self.progressBarFinished()

            if self.IS_DEVELOP: raise exception

    #######################################################

    def simulateBackground(self):
        if self.input_beam is None: return

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        if len(self.twotheta_angles) == 0:
            self.initialize()

        if self.add_background ==  1:
            self.calculateBackground(0)
            self.plotResult(clear_caglioti=False)
            self.writeOutFile()

        self.progressBarFinished()

    ############################################################
    # SIMULATION ALGORITHM METHODS
    ############################################################

    def generateDiffractedRays(self, bar_value, capillary_radius, displacement_h, displacement_v, go_input_beam, input_rays, percentage_fraction, reflections):

        diffracted_rays = []

        no_prog = False

        for ray_index in input_rays:
            if not self.run_simulation: break
            # costruzione intersezione con capillare (interno ed esterno x assorbimento) + displacement del capillare

            Es_x = go_input_beam._beam.rays[ray_index, 6]
            Es_y = go_input_beam._beam.rays[ray_index, 7]
            Es_z = go_input_beam._beam.rays[ray_index, 8]
            k_mod = go_input_beam._beam.rays[ray_index, 10]
            Es_phi = go_input_beam._beam.rays[ray_index, 13]
            Ep_phi = go_input_beam._beam.rays[ray_index, 14]
            Ep_x = go_input_beam._beam.rays[ray_index, 15]
            Ep_y = go_input_beam._beam.rays[ray_index, 16]
            Ep_z = go_input_beam._beam.rays[ray_index, 17]

            wrong_numbers = numpy.isnan(Es_x) or numpy.isnan(Es_y) or numpy.isnan(Es_z) or \
                            numpy.isnan(Ep_x) or numpy.isnan(Ep_y) or numpy.isnan(Ep_z) or \
                            numpy.isnan(Es_phi) or numpy.isnan(Ep_phi) or numpy.isnan(k_mod)

            if not wrong_numbers:
                x_0 = go_input_beam._beam.rays[ray_index, 0]
                y_0 = go_input_beam._beam.rays[ray_index, 1]
                z_0 = go_input_beam._beam.rays[ray_index, 2]

                if (y_0 ** 2 + z_0 ** 2 < capillary_radius ** 2):
                    v_0_x = go_input_beam._beam.rays[ray_index, 3]
                    v_0_y = go_input_beam._beam.rays[ray_index, 4]
                    v_0_z = go_input_beam._beam.rays[ray_index, 5]

                    k_1 = v_0_y / v_0_x
                    k_2 = v_0_z / v_0_x

                    a = (k_1 ** 2 + k_2 ** 2)
                    b = 2 * (k_1 * (y_0 + displacement_h) + k_2 * (z_0 + displacement_v))
                    c = (y_0 ** 2 + z_0 ** 2 + 2 * displacement_h * y_0 + 2 * displacement_v * z_0) - \
                        capillary_radius ** 2 + (displacement_h ** 2 + displacement_v ** 2)

                    if (self.calculate_absorption == 1): c_2 = (
                                                               y_0 ** 2 + z_0 ** 2 + 2 * displacement_h * y_0 + 2 * displacement_v * z_0) - \
                                                               (capillary_radius + (
                                                               self.capillary_thickness * self.micron_to_user_units)) ** 2 + (
                                                               displacement_h ** 2 + displacement_v ** 2)

                    discriminant = b ** 2 - 4 * a * c
                    if (self.calculate_absorption == 1): discriminant_2 = b ** 2 - 4 * a * c_2

                    if discriminant > 0.0:
                        x_sol_1 = (-b - numpy.sqrt(discriminant)) / (2 * a)
                        x_1 = x_0 + x_sol_1
                        y_1 = y_0 + k_1 * x_sol_1
                        z_1 = z_0 + k_2 * x_sol_1

                        x_sol_2 = (-b + numpy.sqrt(discriminant)) / (2 * a)
                        x_2 = x_0 + x_sol_2
                        y_2 = y_0 + k_1 * x_sol_2
                        z_2 = z_0 + k_2 * x_sol_2

                        if (self.calculate_absorption == 1):
                            x_sol_1_out = (-b - numpy.sqrt(discriminant_2)) / (2 * a)
                            x_1_out = x_0 + x_sol_1_out
                            y_1_out = y_0 + k_1 * x_sol_1_out
                            z_1_out = z_0 + k_2 * x_sol_1_out

                            x_sol_2_out = (-b + numpy.sqrt(discriminant_2)) / (2 * a)
                            x_2_out = x_0 + x_sol_2_out
                            y_2_out = y_0 + k_1 * x_sol_2
                            z_2_out = z_0 + k_2 * x_sol_2

                        if (y_1 < y_2):
                            entry_point = [x_1, y_1, z_1]
                            if (self.calculate_absorption == 1): entry_point_out = [x_1_out, y_1_out, z_1_out]
                            exit_point = [x_2, y_2, z_2]
                        else:
                            entry_point = [x_2, y_2, z_2]
                            if (self.calculate_absorption == 1): entry_point_out = [x_2_out, y_2_out, z_2_out]
                            exit_point = [x_1, y_1, z_1]

                        path = ShadowMath.vector_modulus(ShadowMath.vector_difference(exit_point, entry_point))

                        x_axis = [1, 0, 0]
                        v_in = [v_0_x, v_0_y, v_0_z]

                        z_axis_ray = ShadowMath.vectorial_product(x_axis, v_in)
                        rotation_axis_diffraction = ShadowMath.vectorial_product(v_in, z_axis_ray)
                        rotation_axis_debye_circle = v_in

                        wavelength = ShadowPhysics.getWavelengthFromShadowK(k_mod) # in Angstrom

                        if self.calculate_absorption == 1:
                            mu = self.getLinearAbsorptionCoefficient(wavelength) # in cm-1
                            self.absorption_coefficients.append(mu)
                            random_generator_absorption = AbsorptionRandom(mu, path)

                        for origin_point_index in range(0, int(self.number_of_origin_points)):

                            if self.calculate_absorption == 1:
                                random_path = random_generator_absorption.random()
                            else:
                                random_path = path * self.random_generator_flat.random()

                            # calcolo di un punto casuale sul segmento congiungente.

                            x_point = entry_point[0] + random_path * v_in[0]
                            y_point = entry_point[1] + random_path * v_in[1]
                            z_point = entry_point[2] + random_path * v_in[2]

                            origin_point = [x_point, y_point, z_point]

                            for reflection in reflections:
                                if not self.run_simulation: break

                                ray_bragg_angle = self.calculateBraggAngle(reflection, wavelength)

                                delta_theta_darwin = (numpy.random.random() - 0.5) * self.calculateDarwinWidth(reflection, wavelength, ray_bragg_angle)  # darwin width fluctuations

                                if self.residual_average_size > 0:
                                    random_generator_size = LorentzianRandom(self.calculateBetaSize(wavelength, ray_bragg_angle))
                                    delta_theta_size = random_generator_size.random() # residual size effects
                                else:
                                    delta_theta_size = 0.0

                                twotheta_reflection = 2 * (ray_bragg_angle + delta_theta_darwin + delta_theta_size)

                                # rotazione del vettore d'onda pari all'angolo di bragg
                                #
                                # calcolo del vettore ruotato di 2theta bragg, con la formula di Rodrigues:
                                #
                                # k_diffracted = k * cos(2th) + (asse_rot x k) * sin(2th) + asse_rot*(asse_rot . k)(1 - cos(2th))
                                #

                                v_out_temp = ShadowMath.vector_rotate(rotation_axis_diffraction, twotheta_reflection, v_in)

                                # intersezione raggi con sfera di raggio distanza con il detector. le intersezioni con Z < 0 vengono rigettate
                                #
                                # retta P = origin_point + v t
                                #
                                # punto P0 minima distanza con il centro della sfera in 0,0,0
                                #
                                # (P0 - O) * v = 0 => P0 * v = 0 => (origin_point + v t0) * v = 0
                                #
                                # => t0 = - origin_point * v

                                t_0 = -1 * ShadowMath.scalar_product(origin_point, v_out_temp)
                                P_0 = ShadowMath.vector_sum(origin_point, ShadowMath.vector_multiply(v_out_temp, t_0))

                                b = ShadowMath.vector_modulus(P_0)
                                a = numpy.sqrt(self.detector_distance ** 2 - b ** 2)

                                # N.B. punti di uscita hanno solo direzione in avanti.
                                P_2 = ShadowMath.vector_sum(origin_point,
                                                            ShadowMath.vector_multiply(v_out_temp, t_0 + a))

                                # ok se P2 con z > 0
                                if (P_2[2] >= 0):

                                    #
                                    # genesi del nuovo raggio diffratto attenuato dell'intensità relativa e dell'assorbimento
                                    #

                                    delta_angles = self.calculateDeltaAngles()

                                    for delta_index in range(0, len(delta_angles)):

                                        delta_angle = delta_angles[delta_index]

                                        #
                                        # calcolo del vettore ruotato di delta, con la formula di Rodrigues:
                                        #
                                        # v_out_new = v_out * cos(delta) + (asse_rot x v_out ) * sin(delta) + asse_rot*(asse_rot . v_out )(1 - cos(delta))
                                        #
                                        # asse rot = v_in
                                        #

                                        v_out = ShadowMath.vector_rotate(rotation_axis_debye_circle, delta_angle, v_out_temp)

                                        reduction_factor = reflection.relative_intensity

                                        if (self.calculate_absorption == 1):
                                            reduction_factor = reduction_factor * self.calculateAbsorption(wavelength,
                                                                                                           entry_point,
                                                                                                           entry_point_out,
                                                                                                           origin_point,
                                                                                                           v_out,
                                                                                                           capillary_radius,
                                                                                                           displacement_h,
                                                                                                           displacement_v)

                                        reduction_factor = numpy.sqrt(reduction_factor)

                                        diffracted_ray_circle = numpy.zeros(18)

                                        diffracted_ray_circle[0] = origin_point[0]  # X
                                        diffracted_ray_circle[1] = origin_point[1]  # Y
                                        diffracted_ray_circle[2] = origin_point[2]  # Z
                                        diffracted_ray_circle[3] = v_out[0]  # director cos x
                                        diffracted_ray_circle[4] = v_out[1]  # director cos y
                                        diffracted_ray_circle[5] = v_out[2]  # director cos z
                                        diffracted_ray_circle[6] = Es_x * reduction_factor
                                        diffracted_ray_circle[7] = Es_y * reduction_factor
                                        diffracted_ray_circle[8] = Es_z * reduction_factor
                                        diffracted_ray_circle[9] = go_input_beam._beam.rays[ray_index, 9]  # good/lost
                                        diffracted_ray_circle[10] = k_mod  # |k|
                                        diffracted_ray_circle[11] = go_input_beam._beam.rays[ray_index, 11]  # ray index
                                        diffracted_ray_circle[12] = go_input_beam._beam.rays[ray_index, 12]  # optical path
                                        diffracted_ray_circle[13] = Es_phi
                                        diffracted_ray_circle[14] = Ep_phi
                                        diffracted_ray_circle[15] = Ep_x * reduction_factor
                                        diffracted_ray_circle[16] = Ep_y * reduction_factor
                                        diffracted_ray_circle[17] = Ep_z * reduction_factor

                                        diffracted_rays.append(diffracted_ray_circle)

                bar_value = bar_value + percentage_fraction

                if int(bar_value) % 5 == 0:
                    if not no_prog:
                        self.progressBarSet(bar_value)
                        no_prog = True
                else:
                    no_prog = False

        return bar_value, diffracted_rays

    def calculateBraggAngle(self, reflection, wavelength):
        crystal = self.getMaterialXraylibCrystal(self.sample_material)
        energy = ShadowPhysics.getEnergyFromWavelength(wavelength)/1000

        return xraylib.Bragg_angle(crystal, energy, reflection.h, reflection.k, reflection.l)

    def calculateDarwinWidth(self, reflection, wavelength, bragg_angle):
        crystal = self.getMaterialXraylibCrystal(self.sample_material)
        energy = ShadowPhysics.getEnergyFromWavelength(wavelength)/1000
        debyeWaller = 1.0
        asymmetry_factor = -1.0

        fH = xraylib.Crystal_F_H_StructureFactor(crystal, energy, reflection.h, reflection.k, reflection.l, debyeWaller, 1.0)

        codata = scipy.constants.codata.physical_constants
        codata_r, tmp1, tmp2 = codata["classical electron radius"]
        volume = crystal['volume'] # volume of  unit cell in cm^3

        cte = - (codata_r * 1e10) * wavelength * wavelength / (numpy.pi * volume)
        chiH = cte * fH

        return 2 * numpy.absolute(chiH) / numpy.sqrt(numpy.abs(asymmetry_factor)) / numpy.sin(2 * bragg_angle)

    def calculateBetaSize(self, wavelength, bragg_angle):
        return (wavelength * 4 / 3) / (self.residual_average_size * self.micron_to_angstrom * numpy.cos(bragg_angle))


    ############################################################

    def generateXRDPattern(self, bar_value, diffracted_rays, avg_wavelength, reflections):

        number_of_diffracted_rays = len(diffracted_rays)

        diffracted_beam = ShadowBeam()

        if (number_of_diffracted_rays > 0 and self.run_simulation):

            diffracted_beam._beam.rays = numpy.array(diffracted_rays)

            percentage_fraction = 50 / len(reflections)

            max_position = len(self.twotheta_angles) - 1

            twotheta_bragg = 0.0
            normalization = 1.0
            debye_waller_B = 1.0

            if self.add_lorentz_polarization_factor:
                if self.pm2k_fullprof == 0:
                    reflection_index = int(numpy.floor(len(reflections)/2))
                    twotheta_bragg = reflections[reflection_index].twotheta_bragg

                    normalization = self.calculateLPFactorPM2K(numpy.degrees(twotheta_bragg), twotheta_bragg/2)
                else:
                    normalization = self.calculateLPFactorFullProf((self.stop_angle - self.start_angle)/2)

            if self.add_debye_waller_factor:
                if self.use_default_dwf:
                    debye_waller_B = self.getDebyeWallerB(self.sample_material)
                else:
                    debye_waller_B = self.new_debye_waller_B

            statistic_factor = 1.0
            if self.normalize:
                statistic_factor = 1 / (self.number_of_origin_points * self.number_of_rotated_rays)

            if self.diffracted_arm_type == 2:
                diffracted_beam = self.traceTo2DDetector(bar_value, diffracted_beam, avg_wavelength, twotheta_bragg,
                                                         normalization, debye_waller_B, statistic_factor)
                if not diffracted_beam is None:
                    if ShadowCongruence.checkGoodBeam(diffracted_beam):
                        if self.area_detector_beam is None:
                            self.area_detector_beam = diffracted_beam
                        else:
                            self.area_detector_beam = ShadowBeam.mergeBeams(self.area_detector_beam, diffracted_beam)

                        # Creation of 1D pattern: weighted (with intensity) histogram of twotheta angles
                        x_coord = self.area_detector_beam._beam.rays[:, 0]
                        z_coord = self.area_detector_beam._beam.rays[:, 2]

                        r_coord = numpy.sqrt(x_coord ** 2 + z_coord ** 2)

                        twotheta_angles = numpy.degrees(numpy.arctan(r_coord / self.area_detector_distance))

                        intensity = self.area_detector_beam._beam.rays[:, 6] ** 2 + self.area_detector_beam._beam.rays[:, 7] ** 2 + self.area_detector_beam._beam.rays[:, 8] ** 2 + \
                                    self.area_detector_beam._beam.rays[:, 15] ** 2 + self.area_detector_beam._beam.rays[:, 16] ** 2 + self.area_detector_beam._beam.rays[:, 17] ** 2

                        maximum = numpy.max(intensity)

                        weights = (intensity / maximum)

                        histogram, edges = numpy.histogram(a=twotheta_angles, bins=numpy.append(self.twotheta_angles,
                                                                                                max(self.twotheta_angles) + self.step),
                                                           weights=weights)

                        self.counts = histogram

                self.plot2DResults()
                self.plotResult(reflections=reflections)
                self.writeOutFile()
            else:
                for reflection in reflections:
                    if not self.run_simulation: break

                    twotheta_bragg = reflection.twotheta_bragg

                    theta_lim_inf = numpy.degrees(twotheta_bragg) - self.degrees_around_peak
                    theta_lim_sup = numpy.degrees(twotheta_bragg) + self.degrees_around_peak

                    if (theta_lim_inf < self.stop_angle and theta_lim_sup > self.start_angle):
                        n_steps_inf = int(numpy.floor((max(theta_lim_inf, self.start_angle) - self.start_angle) / self.step))
                        n_steps_sup = int(numpy.ceil((min(theta_lim_sup, self.stop_angle) - self.start_angle) / self.step))

                        n_steps = n_steps_sup - n_steps_inf

                        if n_steps > 0:
                            percentage_fraction_2 = percentage_fraction/n_steps

                        no_prog = False

                        for step in range(0, n_steps):
                            if not self.run_simulation: break

                            angle_index = min(n_steps_inf + step, max_position)

                            if self.diffracted_arm_type == 0:
                                out_beam = self.traceFromSlits(diffracted_beam, angle_index)
                            elif self.diffracted_arm_type == 1:
                                out_beam = self.traceFromAnalyzer(diffracted_beam, angle_index)

                            go_rays = out_beam._beam.rays[numpy.where(out_beam._beam.rays[:,9] == 1)]

                            if (len(go_rays) > 0):
                                physical_coefficent = 1.0

                                if self.add_lorentz_polarization_factor:
                                    if self.pm2k_fullprof == 0:
                                        lorentz_polarization_factor = self.calculateLPFactorPM2K(
                                            self.twotheta_angles[angle_index], twotheta_bragg / 2,
                                            normalization=normalization)
                                    else:
                                        lorentz_polarization_factor = self.calculateLPFactorFullProf(
                                            self.twotheta_angles[angle_index], normalization=normalization)

                                    physical_coefficent = physical_coefficent * lorentz_polarization_factor

                                if self.add_debye_waller_factor:
                                    physical_coefficent = physical_coefficent * self.calculateDebyeWallerFactor(
                                        self.twotheta_angles[angle_index], avg_wavelength, debye_waller_B)

                                for ray_index in range(0, len(go_rays)):
                                    if not self.run_simulation: break

                                    intensity_i = go_rays[ray_index, 6]**2 + go_rays[ray_index, 7]**2 + go_rays[ray_index, 8]**2 + \
                                                  go_rays[ray_index, 15]**2 + go_rays[ray_index, 16]**2 + go_rays[ray_index, 17]**2

                                    if not numpy.isnan(physical_coefficent*intensity_i):
                                        self.current_counts[angle_index] = self.current_counts[angle_index] + \
                                                                           physical_coefficent * intensity_i * statistic_factor
                                        self.squared_counts[angle_index] = self.squared_counts[angle_index] + \
                                                                           (physical_coefficent * intensity_i * statistic_factor) **2
                                        self.points_per_bin[angle_index] = self.points_per_bin[angle_index] + 1

                            bar_value = bar_value + percentage_fraction_2

                            if int(bar_value) % 5 == 0:
                                if not no_prog:
                                    self.progressBarSet(bar_value)
                                    no_prog = True
                            else:
                                no_prog = False

                    for index in range(0, len(self.counts)):
                        self.counts[index] = self.counts[index] + self.current_counts[index]

                self.plotResult(reflections=reflections)
                self.writeOutFile()

            return diffracted_beam

    ############################################################

    def calculateDeltaAngles(self):

        if self.diffracted_arm_type == 0:
            width = self.slit_1_horizontal_aperture*self.micron_to_user_units*0.5
            delta_1 = numpy.arctan(width/self.D_1)

            width = self.slit_2_horizontal_aperture*self.micron_to_user_units*0.5
            delta_2 = numpy.arctan(width/self.D_2)

            delta = min(delta_1, delta_2)
        elif self.diffracted_arm_type == 1:
            width = self.acceptance_slit_horizontal_aperture*self.micron_to_user_units*0.5
            delta = numpy.arctan(width/self.acceptance_slit_distance)
        else:
            delta=numpy.pi

        delta_angles = []

        for index in range(0, int(self.number_of_rotated_rays)):
            delta_random = self.random_generator_flat.random()*delta
            discriminant = self.random_generator_flat.random()

            delta_angles.append(delta_random if discriminant < 0.5 else -delta_random)

        return delta_angles

    ############################################################
        
    def calculateBackground(self, bar_value):

        percentage_fraction = 50/len(self.twotheta_angles)

        cursor = range(0, len(self.twotheta_angles))

        self.n_sigma = 0.5*(1 + self.n_sigma)

        for angle_index in cursor:
            background = 0

            if (self.add_constant==1):
                background = ShadowPhysics.ConstatoBackgroundNoised(constant_value=self.constant_value,
                                                                    n_sigma=self.n_sigma,
                                                                    random_generator=self.random_generator_flat)

            if (self.add_chebyshev==1):
                coefficients = [self.cheb_coeff_0, self.cheb_coeff_1, self.cheb_coeff_2, self.cheb_coeff_3, self.cheb_coeff_4, self.cheb_coeff_5]
                
                background = background + ShadowPhysics.ChebyshevBackgroundNoised(coefficients=coefficients,
                                                                      twotheta=self.twotheta_angles[angle_index],
                                                                      n_sigma=self.n_sigma,
                                                                      random_generator=self.random_generator_flat)
                
            if (self.add_expdecay==1):
                coefficients = [self.expd_coeff_0, self.expd_coeff_1, self.expd_coeff_2, self.expd_coeff_3, self.expd_coeff_4, self.expd_coeff_5]
                decayparams = [self.expd_decayp_0, self.expd_decayp_1, self.expd_decayp_2, self.expd_decayp_3, self.expd_decayp_4, self.expd_decayp_5]
                
                background = background + ShadowPhysics.ExpDecayBackgroundNoised(coefficients=coefficients,
                                                                     decayparams=decayparams,
                                                                     twotheta=self.twotheta_angles[angle_index],
                                                                     n_sigma=self.n_sigma,
                                                                     random_generator=self.random_generator_flat)
            self.noise[angle_index] = self.noise[angle_index] + background

        bar_value = bar_value + percentage_fraction
        self.progressBarSet(bar_value)

    ############################################################

    def calculateSignal(self, angle_index):
        return round(self.counts[angle_index] + self.noise[angle_index], 2)

    ############################################################

    def calculateStatisticError(self, angle_index):
        error_on_counts = 0.0
        if self.points_per_bin[angle_index] > 0:
            error_on_counts = numpy.sqrt(max((self.counts[angle_index]**2-self.squared_counts[angle_index])/self.points_per_bin[angle_index], 0)) # RANDOM-GAUSSIAN

        error_on_noise = numpy.sqrt(self.noise[angle_index]) # POISSON

        return numpy.sqrt(error_on_counts**2 + error_on_noise**2)


    def populateCagliotisData(self, reflections):
        angles = []
        data_fwhm = []
        data_eta = []
        data_shift = []

        max_position = len(self.twotheta_angles) - 1

        for reflection in reflections:
            twotheta_bragg = numpy.degrees(reflection.twotheta_bragg)

            theta_lim_inf = twotheta_bragg - self.degrees_around_peak
            theta_lim_sup = twotheta_bragg + self.degrees_around_peak

            if (theta_lim_inf < self.stop_angle and theta_lim_sup > self.start_angle):
                n_steps_inf = int(numpy.floor((max(theta_lim_inf, self.start_angle) - self.start_angle) / self.step))
                n_steps_sup = int(numpy.ceil((min(theta_lim_sup, self.stop_angle) - self.start_angle) / self.step))

                n_steps = n_steps_sup - n_steps_inf

                angles_for_fit = []
                counts_for_fit = []

                for step in range(0, n_steps):
                    angle_index = min(n_steps_inf + step, max_position)

                    angles_for_fit.append(self.twotheta_angles[angle_index])
                    counts_for_fit.append(self.counts[angle_index])

                angles.append(twotheta_bragg)

                try:
                    if self.kind_of_fit == 0: # gaussian
                        parameters, covariance_matrix_pv = ShadowMath.gaussian_fit(angles_for_fit, counts_for_fit)

                        data_fwhm.append(parameters[3])
                        data_eta.append(0.0)
                        data_shift.append(twotheta_bragg-parameters[1])

                        for step in range(0, n_steps):
                            angle_index = min(n_steps_inf + step, max_position)

                            self.caglioti_fits[angle_index] = ShadowMath.gaussian_function(self.twotheta_angles[angle_index], parameters[0], parameters[1], parameters[2])
                    elif self.kind_of_fit == 1: # pseudo-voigt
                        parameters, covariance_matrix_pv = ShadowMath.pseudovoigt_fit(angles_for_fit, counts_for_fit)

                        data_fwhm.append(parameters[2])
                        data_eta.append(parameters[3])
                        data_shift.append(twotheta_bragg-parameters[1])

                        for step in range(0, n_steps):
                            angle_index = min(n_steps_inf + step, max_position)

                            self.caglioti_fits[angle_index] = ShadowMath.pseudovoigt_function(self.twotheta_angles[angle_index], parameters[0], parameters[1], parameters[2], parameters[3])

                except:
                    data_fwhm.append(-1.0)
                    data_eta.append(-1.0)
                    data_shift.append(0.0)

            self.caglioti_angles = angles
            self.caglioti_fwhm = data_fwhm
            self.caglioti_eta = data_eta
            self.caglioti_shift = data_shift

    ############################################################
    # PHYSICAL CALCULATIONS
    ############################################################

    def calculateAbsorption(self, wavelength, entry_point, entry_point_out, origin_point, direction_versor, capillary_radius, displacement_h, displacement_v):

        absorption = 0

        #
        # calcolo intersezione del raggio con superficie interna ed esterna del capillare:
        #
        # x = xo + x' t
        # y = yo + y' t
        # z = zo + z' t
        #
        # (y-dh)^2 + (z-dv)^2 = (Dc/2)^2
        # (y-dh)^2 + (z-dv)^2 = ((Dc+thickness)/2)^2

        x_0 = origin_point[0]
        y_0 = origin_point[1]
        z_0 = origin_point[2]

        k_1 = direction_versor[1]/direction_versor[0]
        k_2 = direction_versor[2]/direction_versor[0]

        #
        # parametri a b c per l'equazione a(x-x0)^2 + b(x-x0) + c = 0
        #

        a = (k_1**2 + k_2**2)
        b = 2*(k_1*(y_0+displacement_h) + k_2*(z_0+displacement_v))
        c = (y_0**2 + z_0**2 + 2*displacement_h*y_0 + 2*displacement_v*z_0) - capillary_radius**2 + (displacement_h**2 + displacement_v**2)
        c_2 = (y_0**2 + z_0**2 + 2*displacement_h*y_0 + 2*displacement_v*z_0) - (capillary_radius+(self.capillary_thickness*self.micron_to_user_units))**2 + (displacement_h**2 + displacement_v**2)

        discriminant = b**2 - 4*a*c
        discriminant_2 = b**2 - 4*a*c_2

        if (discriminant > 0):

            # equazioni risolte per x-x0
            x_1 = (-b + numpy.sqrt(discriminant))/(2*a) # (x-x0)_1
            x_2 = (-b - numpy.sqrt(discriminant))/(2*a) # (x-x0)_2

            x_1_out = (-b + numpy.sqrt(discriminant_2))/(2*a) # (x-x0)_1
            x_2_out = (-b - numpy.sqrt(discriminant_2))/(2*a) # (x-x0)_2

            x_sol = 0
            y_sol = 0
            z_sol = 0

            x_sol_out = 0
            y_sol_out = 0
            z_sol_out = 0

            # solutions only with z > 0 and
            # se y-y0 > 0 allora il versore deve avere y' > 0
            # se y-y0 < 0 allora il versore deve avere y' < 0

            z_1 = z_0 + k_2*x_1

            find_solution = False

            if (z_1 >= 0 or (z_1 < 0 and direction_versor[1] > 0)):
                if (numpy.sign((k_1*x_1))==numpy.sign(direction_versor[1])):
                    x_sol = x_1 + x_0
                    y_sol = y_0 + k_1*x_1
                    z_sol = z_1

                    x_sol_out = x_1_out + x_0
                    y_sol_out = y_0 + k_1*x_1_out
                    z_sol_out = z_0 + k_2*x_1_out

                    find_solution = True

            if not find_solution:
                z_2 = z_0 + k_2*x_2

                if (z_2 >= 0 or (z_1 < 0 and direction_versor[1] > 0)):
                    if (numpy.sign((k_1*x_2))==numpy.sign(direction_versor[1])):
                        x_sol = x_2 + x_0
                        y_sol = y_0 + k_1*x_2
                        z_sol = z_2

                        x_sol_out = x_2_out + x_0
                        y_sol_out = y_0 + k_1*x_2_out
                        z_sol_out = z_0 + k_2*x_2_out

                        find_solution = True

            if find_solution:
                exit_point = [x_sol, y_sol, z_sol]
                exit_point_out = [x_sol_out, y_sol_out, z_sol_out]

                distance = ShadowMath.point_distance(entry_point, origin_point) + ShadowMath.point_distance(origin_point, exit_point)
                distance *= self.workspace_units_to_cm
                distance_out = ShadowMath.point_distance(entry_point_out, entry_point) + ShadowMath.point_distance(exit_point, exit_point_out)
                distance_out *= self.workspace_units_to_cm

                absorption = self.getCapillaryTransmittance(distance_out, wavelength)*self.getTransmittance(distance, wavelength)*self.absorption_normalization_factor
            else:
                absorption = 0 # kill the ray

        return absorption

    ############################################################

    def getLinearAbsorptionCoefficient(self, wavelength):
        mu = xraylib.CS_Total_CP(self.getChemicalFormula(self.sample_material), ShadowPhysics.getEnergyFromWavelength(wavelength)/1000) # energy in KeV
        rho = self.getDensity(self.sample_material)*self.packing_factor

        return mu*rho

    def getCapillaryLinearAbsorptionCoefficient(self, wavelength): #in cm-1
        mu = xraylib.CS_Total_CP(self.getCapillaryChemicalFormula(self.capillary_material), ShadowPhysics.getEnergyFromWavelength(wavelength)/1000) # energy in KeV
        rho = self.getCapillaryDensity(self.capillary_material)

        return mu*rho

    def getTransmittance(self, path_in_cm, wavelength):
        return numpy.exp(-self.getLinearAbsorptionCoefficient(wavelength) * path_in_cm)

    def getCapillaryTransmittance(self, path_in_cm, wavelength):
        return numpy.exp(-self.getCapillaryLinearAbsorptionCoefficient(wavelength) * path_in_cm)

    ############################################################
    # PM2K

    def calculateLPFactorPM2K(self, twotheta_deg, bragg_angle, normalization=1.0):
        theta = numpy.radians(0.5*twotheta_deg)

        lorentz_factor = 1/(numpy.sin(theta)*numpy.sin(bragg_angle))

        if self.diffracted_arm_type == 0:
            theta_mon = numpy.radians(self.monochromator_angle)

            polarization_factor_num = (1 + self.degree_of_polarization) + ((1 - self.degree_of_polarization)*(numpy.cos(2*theta)**2)*(numpy.cos(2*theta_mon)**2))
            polarization_factor_den = 1 + numpy.cos(2*theta_mon)**2
        else:
            theta_mon = numpy.radians(self.analyzer_bragg_angle)

            polarization_factor_num = 1 + ((numpy.cos(2*theta)**2)*(numpy.cos(2*theta_mon)**2))
            polarization_factor_den = 2

        polarization_factor = polarization_factor_num/polarization_factor_den

        return lorentz_factor*polarization_factor/normalization

    ############################################################
    # FULL PROF

    def calculateLPFactorFullProf(self, twotheta_deg, normalization=1.0):
        theta_mon = numpy.radians(self.monochromator_angle)
        theta = numpy.radians(0.5*twotheta_deg)

        lorentz_factor = 1/(numpy.cos(theta)*numpy.sin(theta)**2)
        polarization_factor = ((1 - self.degree_of_polarization) + (self.degree_of_polarization*(numpy.cos(2*theta)**2)*(numpy.cos(2*theta_mon)**2)))/2

        return lorentz_factor*polarization_factor/normalization

    ############################################################

    def calculateDebyeWallerFactor(self, twotheta_deg, wavelength, B):

        theta = 0.5*numpy.radians(twotheta_deg)
        M = B*(numpy.sin(theta)/wavelength)**2

        return numpy.exp(-2*M)

    ############################################################
    # ACCESSORY METHODS
    ############################################################

    def traceFromAnalyzer(self, diffracted_beam, angle_index):

        input_beam = diffracted_beam.duplicate(history=False)

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY = self.workspace_units_to_cm

        empty_element._oe.T_SOURCE     = 0.0
        empty_element._oe.T_IMAGE      = self.analyzer_distance
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0-self.twotheta_angles[angle_index]
        empty_element._oe.ALPHA        = 0.0


        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = self.acceptance_slit_distance
        rx_slit[0] = self.horizontal_acceptance_analyzer
        rz_slit[0] = self.vertical_acceptance_analyzer
        cx_slit[0] = 0.0
        cz_slit[0] = 0.0


        empty_element._oe.set_screens(n_screen,
                                    i_screen,
                                    i_abs,
                                    sl_dis,
                                    i_slit,
                                    i_stop,
                                    k_slit,
                                    thick,
                                    file_abs,
                                    rx_slit,
                                    rz_slit,
                                    cx_slit,
                                    cz_slit,
                                    file_scr_ext)

        if (self.x_sour_offset != 0 or self.x_sour_rotation != 0 or
            self.y_sour_offset != 0 or self.y_sour_rotation != 0 or
            self.z_sour_offset != 0 or self.z_sour_rotation != 0):

            empty_element._oe.FSTAT = 1
            empty_element._oe.RTHETA=0
            empty_element._oe.RDSOUR=0
            empty_element._oe.ALPHA_S=0
            empty_element._oe.OFF_SOUX  = self.x_sour_offset * self.micron_to_user_units
            empty_element._oe.OFF_SOUY  = self.y_sour_offset * self.micron_to_user_units
            empty_element._oe.OFF_SOUZ  = self.z_sour_offset * self.micron_to_user_units
            empty_element._oe.X_SOUR = 0
            empty_element._oe.Y_SOUR = 0
            empty_element._oe.Z_SOUR = 0
            empty_element._oe.X_SOUR_ROT = -self.x_sour_rotation
            empty_element._oe.Y_SOUR_ROT = -self.y_sour_rotation
            empty_element._oe.Z_SOUR_ROT = -self.z_sour_rotation

        out_beam = ShadowBeam.traceFromOE(input_beam, empty_element, history=False)

        crystal = ShadowOpticalElement.create_plane_crystal()

        crystal._oe.DUMMY = self.workspace_units_to_cm

        crystal._oe.T_SOURCE     = 0
        crystal._oe.T_IMAGE      = 1
        crystal._oe.T_INCIDENCE  = 90-self.analyzer_bragg_angle
        crystal._oe.T_REFLECTION = 90-self.analyzer_bragg_angle
        crystal._oe.ALPHA        = 180

        crystal._oe.F_REFLEC = 0
        crystal._oe.F_CRYSTAL = 1
        crystal._oe.FILE_REFL = bytes(congruence.checkFileName(self.rocking_curve_file), 'utf-8')
        crystal._oe.F_REFLECT = 0
        crystal._oe.F_BRAGG_A = 0
        crystal._oe.A_BRAGG = 0.0
        crystal._oe.F_REFRACT = 0


        if (self.mosaic_angle_spread_fwhm > 0):
            crystal._oe.F_MOSAIC = 1
            crystal._oe.MOSAIC_SEED = 4000000 + 1000000*self.random_generator_flat.random()
            crystal._oe.SPREAD_MOS = self.mosaic_angle_spread_fwhm
            crystal._oe.THICKNESS = 1.0

        crystal._oe.F_CENTRAL=0

        crystal._oe.FHIT_C = 1
        crystal._oe.FSHAPE = 1
        crystal._oe.RLEN1  = 2.5
        crystal._oe.RLEN2  = 2.5
        crystal._oe.RWIDX1 = 2.5
        crystal._oe.RWIDX2 = 2.5

        crystal._oe.FWRITE = 3
        crystal._oe.F_ANGLE = 0

        return ShadowBeam.traceFromOE(out_beam, crystal, history=False)

    ############################################################

    def traceFromSlits(self, diffracted_beam, angle_index):

        input_beam = diffracted_beam.duplicate(history=False)

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY = self.workspace_units_to_cm

        empty_element._oe.T_SOURCE     = 0.0
        empty_element._oe.T_IMAGE      = self.analyzer_distance
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0-self.twotheta_angles[angle_index]
        empty_element._oe.ALPHA        = 0.0

        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        if (self.x_sour_offset != 0 or self.x_sour_rotation != 0 or
            self.y_sour_offset != 0 or self.y_sour_rotation != 0 or
            self.z_sour_offset != 0 or self.z_sour_rotation != 0):

            empty_element._oe.FSTAT = 1
            empty_element._oe.RTHETA=0
            empty_element._oe.RDSOUR=0
            empty_element._oe.ALPHA_S=0
            empty_element._oe.OFF_SOUX  = self.x_sour_offset * self.micron_to_user_units
            empty_element._oe.OFF_SOUY  = self.y_sour_offset * self.micron_to_user_units
            empty_element._oe.OFF_SOUZ  = self.z_sour_offset * self.micron_to_user_units
            empty_element._oe.X_SOUR = 0
            empty_element._oe.Y_SOUR = 0
            empty_element._oe.Z_SOUR = 0
            empty_element._oe.X_SOUR_ROT = -self.x_sour_rotation
            empty_element._oe.Y_SOUR_ROT = -self.y_sour_rotation
            empty_element._oe.Z_SOUR_ROT = -self.z_sour_rotation


        n_screen = 2
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 1, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = self.slit_1_distance
        rx_slit[0] = self.horizontal_acceptance_slit_1
        rz_slit[0] = self.vertical_acceptance_slit_1
        cx_slit[0] = 0.0 + self.slit_1_horizontal_displacement_cm
        cz_slit[0] = 0.0 + self.slit_1_vertical_displacement_cm

        sl_dis[1] = self.slit_2_distance
        rx_slit[1] = self.horizontal_acceptance_slit_2
        rz_slit[1] = self.vertical_acceptance_slit_2
        cx_slit[1] = 0.0 + self.slit_2_horizontal_displacement_cm
        cz_slit[1] = 0.0 + self.slit_2_vertical_displacement_cm

        empty_element._oe.set_screens(n_screen,
                                    i_screen,
                                    i_abs,
                                    sl_dis,
                                    i_slit,
                                    i_stop,
                                    k_slit,
                                    thick,
                                    file_abs,
                                    rx_slit,
                                    rz_slit,
                                    cx_slit,
                                    cz_slit,
                                    file_scr_ext)

        return ShadowBeam.traceFromOE(input_beam, empty_element, history=False)

    def traceTo2DDetector(self, bar_value, diffracted_beam, avg_wavelength, twotheta_bragg, normalization,
                          debye_waller_B, statistic_factor):

        input_beam = diffracted_beam.duplicate(history=False)

        empty_element = ShadowOpticalElement.create_empty_oe()

        empty_element._oe.DUMMY = self.workspace_units_to_cm

        empty_element._oe.T_SOURCE     = 0.0
        empty_element._oe.T_IMAGE = self.area_detector_distance
        empty_element._oe.T_INCIDENCE  = 0.0
        empty_element._oe.T_REFLECTION = 180.0
        empty_element._oe.ALPHA        = 0.0

        empty_element._oe.FWRITE = 3
        empty_element._oe.F_ANGLE = 0

        n_screen = 1
        i_screen = numpy.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_abs = numpy.zeros(10)
        i_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        i_stop = numpy.zeros(10)
        k_slit = numpy.zeros(10)
        thick = numpy.zeros(10)
        file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        rx_slit = numpy.zeros(10)
        rz_slit = numpy.zeros(10)
        sl_dis = numpy.zeros(10)
        file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
        cx_slit = numpy.zeros(10)
        cz_slit = numpy.zeros(10)

        sl_dis[0] = self.area_detector_distance
        rx_slit[0] = self.area_detector_width
        rz_slit[0] = self.area_detector_height
        cx_slit[0] = 0.0
        cz_slit[0] = 0.0

        empty_element._oe.set_screens(n_screen,
                                     i_screen,
                                     i_abs,
                                     sl_dis,
                                     i_slit,
                                     i_stop,
                                     k_slit,
                                     thick,
                                     file_abs,
                                     rx_slit,
                                     rz_slit,
                                     cx_slit,
                                     cz_slit,
                                     file_scr_ext)

        if (self.x_sour_offset != 0 or self.x_sour_rotation != 0 or
            self.y_sour_offset != 0 or self.y_sour_rotation != 0 or
            self.z_sour_offset != 0 or self.z_sour_rotation != 0):

            empty_element._oe.FSTAT = 1
            empty_element._oe.RTHETA=0
            empty_element._oe.RDSOUR=0
            empty_element._oe.ALPHA_S=0
            empty_element._oe.OFF_SOUX  = (self.x_sour_offset * self.micron_to_user_units) + self.area_detector_distance*numpy.tan(numpy.radians(self.z_sour_rotation))
            empty_element._oe.OFF_SOUY  = self.y_sour_offset * self.micron_to_user_units
            empty_element._oe.OFF_SOUZ  = (self.z_sour_offset * self.micron_to_user_units) + self.area_detector_distance*numpy.tan(numpy.radians(self.x_sour_rotation))
            empty_element._oe.X_SOUR = 0
            empty_element._oe.Y_SOUR = 0
            empty_element._oe.Z_SOUR = 0
            empty_element._oe.X_SOUR_ROT = self.x_sour_rotation
            empty_element._oe.Y_SOUR_ROT = self.y_sour_rotation
            empty_element._oe.Z_SOUR_ROT = self.z_sour_rotation

        out_beam = ShadowBeam.traceFromOE(input_beam, empty_element, history=False)

        go_rays = copy.deepcopy(out_beam._beam.rays[numpy.where(out_beam._beam.rays[:, 9] == 1)])

        percentage_fraction = 50 / len(go_rays)
        no_prog = False

        for ray_index in range(0, len(go_rays)):

            if not self.run_simulation: break

            physical_coefficent = statistic_factor

            x_coord = go_rays[ray_index, 0]
            z_coord = go_rays[ray_index, 2]

            r_coord = numpy.sqrt(x_coord ** 2 + z_coord ** 2)

            ray_twotheta_angle = numpy.degrees(numpy.arctan(r_coord / self.detector_distance))

            if self.add_lorentz_polarization_factor:
                if self.pm2k_fullprof == 0:
                    lorentz_polarization_factor = self.calculateLPFactorPM2K(ray_twotheta_angle, twotheta_bragg / 2,
                                                                             normalization=normalization)
                else:
                    lorentz_polarization_factor = self.calculateLPFactorFullProf(ray_twotheta_angle,
                                                                                 normalization=normalization)

                physical_coefficent = physical_coefficent * lorentz_polarization_factor

            if self.add_debye_waller_factor:
                physical_coefficent = physical_coefficent * self.calculateDebyeWallerFactor(ray_twotheta_angle,
                                                                                            avg_wavelength,
                                                                                            debye_waller_B)

            physical_coefficent = numpy.sqrt(physical_coefficent)

            Es_x = go_rays[ray_index, 6]
            Es_y = go_rays[ray_index, 7]
            Es_z = go_rays[ray_index, 8]
            Ep_x = go_rays[ray_index, 15]
            Ep_y = go_rays[ray_index, 16]
            Ep_z = go_rays[ray_index, 17]

            go_rays[ray_index, 6] = Es_x * physical_coefficent
            go_rays[ray_index, 7] = Es_y * physical_coefficent
            go_rays[ray_index, 8] = Es_z * physical_coefficent
            go_rays[ray_index, 15] = Ep_x * physical_coefficent
            go_rays[ray_index, 16] = Ep_y * physical_coefficent
            go_rays[ray_index, 17] = Ep_z * physical_coefficent

            intensity_i = go_rays[ray_index, 6] ** 2 + go_rays[ray_index, 7] ** 2 + go_rays[ray_index, 8] ** 2 + \
                          go_rays[ray_index, 15] ** 2 + go_rays[ray_index, 16] ** 2 + go_rays[ray_index, 17] **2

            if numpy.isnan(intensity_i):
                go_rays[ray_index, 9] = 0

            bar_value = bar_value + percentage_fraction

            if int(bar_value) % 5 == 0:
                if not no_prog:
                    self.progressBarSet(bar_value)
                    no_prog = True
            else:
                no_prog = False

        out_beam._beam.rays = copy.deepcopy(go_rays[numpy.where(go_rays[:, 9] == 1)])

        return out_beam


    ############################################################

    def initialize(self):
        steps = range(0, int(numpy.floor((self.stop_angle_na - self.start_angle_na) / self.step)) + 1)

        self.start_angle = self.start_angle_na #+ self.shift_2theta
        self.stop_angle = self.stop_angle_na #+ self.shift_2theta

        if self.keep_result == 0 or len(self.twotheta_angles) == 0 or self.reset_button_pressed:
            self.area_detector_beam = None
            self.twotheta_angles = []
            self.counts = []
            self.caglioti_fits = []
            self.noise = []
            self.squared_counts = []
            self.points_per_bin = []
            self.absorption_coefficients = []
            self.lorentz_polarization_factors = []
            self.debye_waller_factors = []

            for step_index in steps:
                self.twotheta_angles.append(self.start_angle + step_index * self.step)
                self.counts.append(0.0)
                self.caglioti_fits.append(0.0)
                self.noise.append(0.0)
                self.squared_counts.append(0.0)
                self.points_per_bin.append(0)
                self.lorentz_polarization_factors.append(1.0)
                self.debye_waller_factors.append(1.0)

            self.twotheta_angles = numpy.array(self.twotheta_angles)
            self.counts = numpy.array(self.counts)
            self.caglioti_fits = numpy.array(self.caglioti_fits)
            self.noise = numpy.array(self.noise)
            self.squared_counts = numpy.array(self.squared_counts)
            self.points_per_bin = numpy.array(self.points_per_bin)
            self.lorentz_polarization_factors = numpy.array(self.lorentz_polarization_factors)
            self.debye_waller_factors = numpy.array(self.debye_waller_factors)

        self.reset_button_pressed = False

        self.resetCurrentCounts(steps)

        return steps

    ############################################################

    def resetCurrentCounts(self, steps):
        self.current_counts = []
        for step_index in steps:
            self.current_counts.append(0.0)

    ############################################################

    def writeOutFile(self, reset=False):
        base_dir = os.path.dirname(self.output_file_name).strip()
        base_dir = base_dir if base_dir != "" else "."

        base_name = base_dir + "/" + os.path.splitext(os.path.basename(self.output_file_name))[0]

        if not os.path.exists(base_dir):
            if not reset:
                raise Exception("Base Directory '" + base_dir + "' does not exists")
        else:
            if not os.access(base_dir, os.W_OK):
                if not reset:
                    raise Exception("No writing permissions  on directory '" + base_dir + "'")
            else:
                out_file = open(self.output_file_name, "w")
                out_file.write("tth counts error\n")

                for angle_index in range(0, len(self.twotheta_angles)):
                    out_file.write(str(self.twotheta_angles[angle_index]) + " "
                                   + str(self.calculateSignal(angle_index)) + " "
                                   + str(self.calculateStatisticError(angle_index))
                                   + "\n")
                    out_file.flush()

                out_file.close()

                caglioti_1_out_file = open(base_name + "_InstrumentalBroadening.dat","w")
                caglioti_1_out_file.write("tth fwhm\n")

                for angle_index in range(0, len(self.caglioti_angles)):
                    caglioti_1_out_file.write(str(self.caglioti_angles[angle_index]) + " "
                                   + str(self.caglioti_fwhm[angle_index]) + "\n")
                    caglioti_1_out_file.flush()

                caglioti_1_out_file.close()

                caglioti_2_out_file = open(base_name + "_InstrumentalEta.dat","w")
                caglioti_2_out_file.write("tth eta\n")

                for angle_index in range(0, len(self.caglioti_angles)):
                    caglioti_2_out_file.write(str(self.caglioti_angles[angle_index]) + " "
                                   + str(self.caglioti_eta[angle_index]) + "\n")
                    caglioti_2_out_file.flush()

                caglioti_2_out_file.close()

                caglioti_3_out_file = open(base_name + "_InstrumentalPeakShift.dat","w")
                caglioti_3_out_file.write("tth peak_shift\n")

                for angle_index in range(0, len(self.caglioti_angles)):
                    caglioti_3_out_file.write(str(self.caglioti_angles[angle_index]) + " "
                                   + str(self.caglioti_shift[angle_index]) + "\n")
                    caglioti_3_out_file.flush()

                caglioti_3_out_file.close()

    ############################################################

    def backupOutFile(self):

        directory_out = os.getcwd() + '/Output'

        filename = str(self.output_file_name).strip()
        caglioti_1_filename = os.path.splitext(filename)[0] + "_InstrumentalBroadening.dat"
        caglioti_2_filename = os.path.splitext(filename)[0] + "_InstrumentalPeakShift.dat"

        srcfile = directory_out + '/' + filename
        srcfile_caglioti_1 = directory_out + '/' + caglioti_1_filename
        srcfile_caglioti_2 = directory_out + '/' + caglioti_2_filename

        bkpfile = directory_out + '/Last_Profile_BKP.xy'
        bkpfile_c1 = directory_out + '/Last_Profile_InstrumentalBroadening_BKP.dat'
        bkpfile_c2 = directory_out + '/Last_Profile_InstrumentalPeakShift_BKP.dat'

        if not os.path.exists(directory_out): return
        if os.path.exists(srcfile):
            if os.path.exists(bkpfile): os.remove(bkpfile)
            shutil.copyfile(srcfile, bkpfile)

        if os.path.exists(srcfile_caglioti_1):
            if os.path.exists(bkpfile_c1): os.remove(bkpfile_c1)
            shutil.copyfile(srcfile_caglioti_1, bkpfile_c1)

        if os.path.exists(srcfile_caglioti_2):
            if os.path.exists(bkpfile_c2): os.remove(bkpfile_c2)
            shutil.copyfile(srcfile_caglioti_2, bkpfile_c2)

    ############################################################
    # MATERIALS DB
    ############################################################

    def getCapillaryChemicalFormula(self, capillary_material):
        if capillary_material < len(self.capillary_materials):
            return self.capillary_materials[capillary_material].chemical_formula
        else:
            return None

    ############################################################

    def getCapillaryMaterialName(self, capillary_material):
        if capillary_material < len(self.capillary_materials):
            return self.capillary_materials[capillary_material].name
        else:
            return -1


    ############################################################

    def getCapillaryDensity(self, capillary_material):
        if capillary_material < len(self.capillary_materials):
            return self.capillary_materials[capillary_material].density
        else:
            return -1

    ############################################################

    def getChemicalFormula(self, material):
        if material < len(self.materials):
            return self.materials[material].chemical_formula
        else:
            return None

    ############################################################

    def getMaterialXraylibCrystal(self, material):
        if material < len(self.materials):
            return self.materials[material].xraylib_crystal
        else:
            return None

    ############################################################

    def getLatticeParameter(self, material):
        if material < len(self.materials):
            return self.materials[material].lattice_parameter
        else:
            return -1

    ############################################################

    def getDensity(self, material):
        if material < len(self.materials):
            return self.materials[material].density
        else:
            return -1

    ############################################################

    def getDebyeWallerB(self, material):
        if material < len(self.materials):
            return self.materials[material].debye_waller_B
        else:
            return None

    ############################################################

    def getReflections(self, material, number_of_peaks=-1, avg_wavelength=0.0):
        reflections = []

        detector_angular_acceptance = 180
        if self.diffracted_arm_type == 2:
            detector_angular_acceptance = max(numpy.arctan((self.area_detector_height/2)/self.area_detector_distance),
                                              numpy.arctan((self.area_detector_width/2)/self.area_detector_distance))

        if material < len(self.materials):
            total_reflections = self.materials[material].reflections
            added_peak = 0

            for reflection in total_reflections:
                if number_of_peaks > 0 and added_peak == number_of_peaks: break

                twotheta_bragg = 2*ShadowPhysics.calculateBraggAngle(avg_wavelength, reflection.h, reflection.k, reflection.l, self.getLatticeParameter(material))

                if twotheta_bragg < detector_angular_acceptance:
                    if numpy.degrees(twotheta_bragg) >= self.start_angle and numpy.degrees(twotheta_bragg) <= self.stop_angle:
                        reflection.twotheta_bragg = twotheta_bragg
                        reflections.append(reflection)
                        added_peak = added_peak + 1

        return reflections

    ############################################################

    def readCapillaryMaterialConfigurationFiles(self):
        self.capillary_materials = []

        foundMaterialFile = True
        materialIndex = 0

        directory_files = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.experimental_elements"), "data")

        try:
            while(foundMaterialFile):
                materialFileName =   os.path.join(directory_files, "sample_holder_material_" + str(materialIndex) + ".dat")

                if not os.path.exists(materialFileName):
                    foundMaterialFile = False
                else:
                    materialFile = open(materialFileName, "r")

                    rows = materialFile.readlines()

                    if (len(rows) == 3):
                        name = rows[0].split('#')[0].strip()
                        chemical_formula = rows[1].split('#')[0].strip()
                        density = float(rows[2].split('#')[0].strip())

                        current_material = CapillaryMaterial(name, chemical_formula, density)

                        self.capillary_materials.append(current_material)

                    materialIndex = materialIndex + 1

        except Exception as err:
            raise Exception("Problems reading Capillary Materials Configuration file: {0}".format(err))
        except:
            raise Exception("Unexpected error reading Capillary Materials Configuration file: ", sys.exc_info()[0])

    ############################################################

    def readMaterialConfigurationFiles(self):
        self.materials = []

        foundMaterialFile = True
        materialIndex = 0

        directory_files = os.path.join(resources.package_dirname("orangecontrib.shadow.widgets.experimental_elements"), "data")

        try:
            while(foundMaterialFile):
                materialFileName =  directory_files + "/material_" + str(materialIndex) + ".dat"

                if not os.path.exists(materialFileName):
                    foundMaterialFile = False
                else:
                    materialFile = open(materialFileName, "r")

                    rows = materialFile.readlines()

                    if (len(rows) > 3):

                        chemical_formula = rows[0].split('#')[0].strip()
                        density = float(rows[1].split('#')[0].strip())
                        debye_waller_B = float(rows[3].split('#')[0].strip())

                        current_material = Material(chemical_formula, density, debye_waller_B)

                        for index in range(4, len(rows)):
                            if not rows[index].strip() == "" and \
                               not rows[index].strip().startswith('#'):
                                row_elements = rows[index].split(',')

                                h = int(row_elements[0].strip())
                                k = int(row_elements[1].strip())
                                l = int(row_elements[2].strip())

                                relative_intensity = 1.0
                                form_factor_2 = 1.0

                                if (len(row_elements)>3):
                                    relative_intensity = float(row_elements[3].strip())
                                if (len(row_elements)>4):
                                    form_factor_2 = float(row_elements[4].strip())

                                reflection = Reflection(h, k, l, relative_intensity=relative_intensity, form_factor_2_mult=form_factor_2)

                                material_reflection_file = directory_files + "/reflections/material_" + str(materialIndex) + "_" + str(h) + str(k)+ str(l) + ".dat"

                                if os.path.exists(material_reflection_file):
                                    reflection.material_reflection_file = material_reflection_file

                                current_material.reflections.append(reflection)

                        self.materials.append(current_material)

                    materialIndex = materialIndex + 1

        except Exception as err:
            raise Exception("Problems reading Materials Configuration file: {0}".format(err))
        except:
            raise Exception("Unexpected error reading Materials Configuration file: ", sys.exc_info()[0])

    def selectOuputFile(self):
        self.le_output_file_name.setText(oasysgui.selectFileFromDialog(self, self.output_file_name, "Select Ouput File"))

    def selectRockingCurveFile(self):
        self.le_rocking_curve_file.setText(oasysgui.selectFileFromDialog(self, self.rocking_curve_file, "Open File with Crystal Parameters"))


    def writeStdOut(self, text):
        cursor = self.shadow_output.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(text)
        self.shadow_output.setTextCursor(cursor)
        self.shadow_output.ensureCursorVisible()

############################################################
############################################################
############################################################
############################################################

class RockingCurveElement:
    delta_theta=0.0
    intensity=0.0

    def __init__(self, delta_theta, intensity):
        self.delta_theta=delta_theta
        self.intensity=intensity

class CapillaryMaterial:
    name=""
    chemical_formula=""
    density=0.0

    def __init__(self, name, chemical_formula, density):
        self.name=name
        self.chemical_formula=chemical_formula
        self.density=density

class Material:
    xraylib_crystal = None
    chemical_formula=""
    density=0.0
    lattice_parameter=0.0
    debye_waller_B=0.0

    reflections = []

    def __init__(self, chemical_formula, density, debye_waller_B):
        self.chemical_formula=chemical_formula
        self.xraylib_crystal =  xraylib.Crystal_GetCrystal(chemical_formula)
        self.density=density
        self.lattice_parameter=self.xraylib_crystal['a']
        self.debye_waller_B=debye_waller_B
        self.reflections=[]

class Reflection:
    h=0
    k=0
    l=0
    relative_intensity=1.0
    form_factor_2_mult=0.0
    twotheta_bragg=0.0
    material_reflection_file = None

    def __init__(self, h, k, l, relative_intensity=1.0, form_factor_2_mult=0.0):
        self.h=h
        self.k=k
        self.l=l
        self.relative_intensity=relative_intensity
        self.form_factor_2_mult=form_factor_2_mult

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = XRDCapillary()
    ow.show()
    a.exec_()
    ow.saveSettings()
