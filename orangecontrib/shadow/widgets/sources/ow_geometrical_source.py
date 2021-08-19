import sys

import numpy
import scipy.stats as stats
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.exchange import DataExchangeObject
from oasys.util.oasys_util import EmittingStream, TTYGrabber, TriggerIn, TriggerOut

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource
from orangecontrib.shadow.util.shadow_util import ShadowPhysics
from orangecontrib.shadow.widgets.gui import ow_source

class GeometricalSource(ow_source.Source):
    name = "Geometrical Source"
    description = "Shadow Source: Geometrical Source"
    icon = "icons/geometrical.png"
    priority = 1

    inputs = [("Trigger", TriggerOut, "sendNewBeam"),
              ("ExchangeData", DataExchangeObject, "acceptExchangeData")]

    spatial_type = Setting(0)

    rect_width = Setting(0.1)
    rect_height = Setting(0.2)
    ell_semiaxis_x = Setting(0.1)
    ell_semiaxis_z = Setting(0.2)
    gauss_sigma_x = Setting(0.001)
    gauss_sigma_z = Setting(0.001)

    angular_distribution = Setting(0)

    horizontal_div_x_plus = Setting(5.0e-7)
    horizontal_div_x_minus = Setting(5.0e-7)
    vertical_div_z_plus = Setting(5.0e-6)
    vertical_div_z_minus = Setting(5.0e-6)

    angular_distribution_limits = Setting(0)

    horizontal_lim_x_plus = Setting(1.0e-5)
    horizontal_lim_x_minus = Setting(1.0e-5)
    vertical_lim_z_plus = Setting(1.0e-5)
    vertical_lim_z_minus = Setting(1.0e-5)
    horizontal_sigma_x = Setting(0.001)
    vertical_sigma_z = Setting(0.0001)

    cone_internal_half_aperture = Setting(0.0)
    cone_external_half_aperture = Setting(0.0)

    depth = Setting(0)

    source_depth_y = Setting(0.2)
    sigma_y = Setting(0.001)

    photon_energy_distribution = Setting(0)

    units=Setting(0)

    single_line_value = Setting(1000.0)
    number_of_lines = Setting(0)

    line_value_1 = Setting(1000.0)
    line_value_2 = Setting(1010.0)
    line_value_3 = Setting(0.0)
    line_value_4 = Setting(0.0)
    line_value_5 = Setting(0.0)
    line_value_6 = Setting(0.0)
    line_value_7 = Setting(0.0)
    line_value_8 = Setting(0.0)
    line_value_9 = Setting(0.0)
    line_value_10 = Setting(0.0)

    uniform_minimum = Setting(1000.0)
    uniform_maximum = Setting(1010.0)

    line_int_1 = Setting(0.0)
    line_int_2 = Setting(0.0)
    line_int_3 = Setting(0.0)
    line_int_4 = Setting(0.0)
    line_int_5 = Setting(0.0)
    line_int_6 = Setting(0.0)
    line_int_7 = Setting(0.0)
    line_int_8 = Setting(0.0)
    line_int_9 = Setting(0.0)
    line_int_10 = Setting(0.0)

    gaussian_central_value = Setting(0.0)
    gaussian_sigma = Setting(0.0)
    gaussian_minimum = Setting(0.0)
    gaussian_maximum = Setting(0.0)

    user_defined_file = Setting("energy_spectrum.dat")
    user_defined_minimum = Setting(0.0)
    user_defined_maximum = Setting(0.0)
    user_defined_spectrum_binning = Setting(10000)
    user_defined_refining_factor  = Setting(5)

    polarization = Setting(1)
    coherent_beam = Setting(0)
    phase_diff = Setting(0.0)
    polarization_degree = Setting(1.0)

    optimize_source=Setting(0)
    optimize_file_name = Setting("NONESPECIFIED")
    max_number_of_rejected_rays = Setting(10000000)

    def __init__(self):
        super().__init__()

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_basic = oasysgui.createTabPage(tabs_setting, "Basic Setting")
        tab_geometry = oasysgui.createTabPage(tabs_setting, "Geometry Setting")
        tab_energy = oasysgui.createTabPage(tabs_setting, "Energy/Polarization Setting")

        ##############################
        # MONTECARLO

        left_box_1 = oasysgui.widgetBox(tab_basic, "Montecarlo", addSpace=True, orientation="vertical", height=100)

        gui.separator(left_box_1)

        self.sample_box_1 = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.sample_box_1, self, "number_of_rays", "Number of Random Rays", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.sample_box_1, self, "seed", "Seed (0=clock)", labelWidth=260, valueType=int, orientation="horizontal")


        ##############################
        # GEOMETRY

        left_box_2 = oasysgui.widgetBox(tab_geometry, "", addSpace=True, orientation="vertical", height=550)

        gui.separator(left_box_2)

        ######

        spatial_type_box = oasysgui.widgetBox(left_box_2, "Spatial Type", addSpace=True, orientation="vertical", height=120)

        gui.comboBox(spatial_type_box, self, "spatial_type", label="Spatial Type", labelWidth=355,
                     items=["Point", "Rectangle", "Ellipse", "Gaussian"], orientation="horizontal", callback=self.set_SpatialType)

        gui.separator(spatial_type_box)

        self.spatial_type_box_1 = oasysgui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        self.le_rect_width  = oasysgui.lineEdit(self.spatial_type_box_1, self, "rect_width", "Width", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_rect_height = oasysgui.lineEdit(self.spatial_type_box_1, self, "rect_height", "Height", labelWidth=260, valueType=float, orientation="horizontal")

        self.spatial_type_box_2 = oasysgui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        self.le_ell_semiaxis_x = oasysgui.lineEdit(self.spatial_type_box_2, self, "ell_semiaxis_x", "Semi-Axis X", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_ell_semiaxis_z = oasysgui.lineEdit(self.spatial_type_box_2, self, "ell_semiaxis_z", "Semi-Axis Z", labelWidth=260, valueType=float, orientation="horizontal")

        self.spatial_type_box_3 = oasysgui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        self.le_gauss_sigma_x = oasysgui.lineEdit(self.spatial_type_box_3, self, "gauss_sigma_x", "Sigma X", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_gauss_sigma_z = oasysgui.lineEdit(self.spatial_type_box_3, self, "gauss_sigma_z", "Sigma Z", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_SpatialType()

        angular_distribution_box = oasysgui.widgetBox(left_box_2, "Angular Distribution", addSpace=True, orientation="vertical", height=260)

        gui.comboBox(angular_distribution_box, self, "angular_distribution", label="Angular Distribution", labelWidth=355,
                     items=["Flat", "Uniform", "Gaussian", "Conical"], orientation="horizontal", callback=self.set_AngularDistribution)

        gui.separator(angular_distribution_box)

        self.angular_distribution_box_1 = oasysgui.widgetBox(angular_distribution_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.angular_distribution_box_1, self, "horizontal_div_x_plus", "Horizontal Divergence X(+) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.angular_distribution_box_1, self, "horizontal_div_x_minus", "Horizontal Divergence X(-) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.angular_distribution_box_1, self, "vertical_div_z_plus", "Vertical Divergence Z(+) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.angular_distribution_box_1, self, "vertical_div_z_minus", "Vertical Divergence Z(-) [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        self.angular_distribution_box_2 = oasysgui.widgetBox(angular_distribution_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.angular_distribution_box_2, self, "angular_distribution_limits", label="Angular Distribution Limits", labelWidth=355,
                     items=["No Limits", "Horizontal", "Vertical", "Both"], orientation="horizontal", callback=self.set_AngularDistributionLimits)

        self.le_horizontal_lim_x_plus = oasysgui.lineEdit(self.angular_distribution_box_2, self, "horizontal_lim_x_plus", "Horizontal Limit X(+) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_horizontal_lim_x_minus = oasysgui.lineEdit(self.angular_distribution_box_2, self, "horizontal_lim_x_minus", "Horizontal Limit X(-) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_vertical_lim_z_plus = oasysgui.lineEdit(self.angular_distribution_box_2, self, "vertical_lim_z_plus", "Vertical Limit Z(+) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        self.le_vertical_lim_z_minus = oasysgui.lineEdit(self.angular_distribution_box_2, self, "vertical_lim_z_minus", "Vertical Limit Z(-) [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.angular_distribution_box_2, self, "horizontal_sigma_x", "Horizontal Sigma (X) [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.angular_distribution_box_2, self, "vertical_sigma_z", "Vertical Sigma (Z) [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        self.angular_distribution_box_3 = oasysgui.widgetBox(angular_distribution_box, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.angular_distribution_box_3, self, "cone_internal_half_aperture", "Cone Internal Half-Aperture [rad]", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.angular_distribution_box_3, self, "cone_external_half_aperture", "Cone External Half-Aperture [rad]", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_AngularDistribution()

        depth_box = oasysgui.widgetBox(left_box_2, "Depth", addSpace=True, orientation="vertical", height=100)

        gui.comboBox(depth_box, self, "depth", label="Depth", labelWidth=355,
                     items=["Off", "Uniform", "Gaussian"], orientation="horizontal", callback=self.set_Depth)

        gui.separator(depth_box, 1)

        self.depth_box_1 = oasysgui.widgetBox(depth_box, "", addSpace=False, orientation="vertical")

        self.le_source_depth_y = oasysgui.lineEdit(self.depth_box_1, self, "source_depth_y", "Source Depth (Y)", labelWidth=260, valueType=float, orientation="horizontal")

        self.depth_box_2 = oasysgui.widgetBox(depth_box, "", addSpace=False, orientation="vertical")

        self.le_sigma_y = oasysgui.lineEdit(self.depth_box_2, self, "sigma_y", "Sigma Y", labelWidth=260, valueType=float, orientation="horizontal")

        self.set_Depth()

        ##############################
        # ENERGY

        left_box_3 = oasysgui.widgetBox(tab_energy, "", addSpace=False, orientation="vertical", height=640)

        ######

        energy_wavelength_box = oasysgui.widgetBox(left_box_3, "Energy/Wavelength", addSpace=False, orientation="vertical", height=430)

        gui.comboBox(energy_wavelength_box, self, "photon_energy_distribution", label="Photon Energy Distribution", labelWidth=260,
                     items=["Single Line", "Several Lines", "Uniform", "Relative Intensities", "Gaussian", "User Defined"], orientation="horizontal", callback=self.set_PhotonEnergyDistribution)

        gui.comboBox(energy_wavelength_box, self, "units", label="Units", labelWidth=260,
                     items=["Energy/eV", "Wavelength/Å"], orientation="horizontal", callback=self.set_PhotonEnergyDistribution)

        self.ewp_box_5 = oasysgui.widgetBox(energy_wavelength_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.ewp_box_5, self, "number_of_lines", label="Number of Lines", labelWidth=330,
                     items=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], orientation="horizontal", callback=self.set_NumberOfLines)

        container =  oasysgui.widgetBox(energy_wavelength_box, "", addSpace=False, orientation="horizontal")
        self.container_left =  oasysgui.widgetBox(container, "", addSpace=False, orientation="vertical")
        self.container_right =  oasysgui.widgetBox(container, "", addSpace=False, orientation="vertical")

        self.ewp_box_1 = oasysgui.widgetBox(self.container_left, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.ewp_box_1, self, "single_line_value", "Value", labelWidth=260, valueType=float, orientation="horizontal")

        self.ewp_box_2 = oasysgui.widgetBox(self.container_left, "Values", addSpace=False, orientation="vertical")

        self.le_line_value_1 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_1", "Line 1", valueType=float, orientation="horizontal")
        self.le_line_value_2 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_2", "Line 2", valueType=float, orientation="horizontal")
        self.le_line_value_3 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_3", "Line 3", valueType=float, orientation="horizontal")
        self.le_line_value_4 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_4", "Line 4", valueType=float, orientation="horizontal")
        self.le_line_value_5 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_5", "Line 5", valueType=float, orientation="horizontal")
        self.le_line_value_6 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_6", "Line 6", valueType=float, orientation="horizontal")
        self.le_line_value_7 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_7", "Line 7", valueType=float, orientation="horizontal")
        self.le_line_value_8 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_8", "Line 8", valueType=float, orientation="horizontal")
        self.le_line_value_9 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_9", "Line 9", valueType=float, orientation="horizontal")
        self.le_line_value_10 = oasysgui.lineEdit(self.ewp_box_2, self, "line_value_10", "Line 10", valueType=float, orientation="horizontal")

        self.ewp_box_3 = oasysgui.widgetBox(self.container_left, "", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.ewp_box_3, self, "uniform_minimum", "Minimum Energy/Wavelength", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_3, self, "uniform_maximum", "Maximum Energy/Wavelength", labelWidth=260, valueType=float, orientation="horizontal")

        self.ewp_box_4 = oasysgui.widgetBox(self.container_right, "Relative Intensities", addSpace=False, orientation="vertical")
        
        self.le_line_int_1 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_1", "Int 1", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_2 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_2", "Int 2", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_3 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_3", "Int 3", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_4 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_4", "Int 4", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_5 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_5", "Int 5", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_6 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_6", "Int 6", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_7 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_7", "Int 7", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_8 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_8", "Int 8", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_9 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_9", "Int 9", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_10 = oasysgui.lineEdit(self.ewp_box_4, self, "line_int_10", "Int 10", labelWidth=100, valueType=float, orientation="horizontal")

        self.ewp_box_6 = oasysgui.widgetBox(energy_wavelength_box, "Gaussian", addSpace=False, orientation="vertical")

        oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_central_value", "Central Value", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_sigma", "Sigma", labelWidth=260, valueType=float, orientation="horizontal")

        gui.separator(self.ewp_box_6)

        oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_minimum", "Minimum Energy/Wavelength", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_6, self, "gaussian_maximum", "Maximum Energy/Wavelength", labelWidth=260, valueType=float, orientation="horizontal")

        self.ewp_box_7 = oasysgui.widgetBox(energy_wavelength_box, "User Defined", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.ewp_box_7, "", addSpace=True, orientation="horizontal", height=25)

        self.le_user_defined_file = oasysgui.lineEdit(file_box, self, "user_defined_file", "Spectrum File",
                                                    labelWidth=100, valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectFile)

        gui.separator(self.ewp_box_7)

        oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_minimum", "Minimum Energy/Wavelength", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_maximum", "Maximum Energy/Wavelength", labelWidth=260, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_spectrum_binning", "Minimum Nr. of Bins of Input Spectrum", labelWidth=260, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_7, self, "user_defined_refining_factor", "Refining Factor", labelWidth=260, valueType=int, orientation="horizontal")

        self.set_PhotonEnergyDistribution()

        polarization_box = oasysgui.widgetBox(left_box_3, "Polarization", addSpace=False, orientation="vertical")

        gui.comboBox(polarization_box, self, "polarization", label="Polarization", labelWidth=310,
                     items=["No", "Yes"], orientation="horizontal", callback=self.set_Polarization)

        self.ewp_box_8 = oasysgui.widgetBox(polarization_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.ewp_box_8, self, "coherent_beam", label="Coherent Beam", labelWidth=310,
                     items=["No", "Yes"], orientation="horizontal")

        oasysgui.lineEdit(self.ewp_box_8, self, "phase_diff", "Phase Difference [deg,0=linear,+90=ell/right]", labelWidth=310, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(self.ewp_box_8, self, "polarization_degree", "Polarization Degree [cos_s/(cos_s+sin_s)]", labelWidth=310, valueType=float, orientation="horizontal")

        self.set_Polarization()

        ##############################

        left_box_4 = oasysgui.widgetBox(tab_basic, "Reject Rays", addSpace=True, orientation="vertical", height=130)

        gui.comboBox(left_box_4, self, "optimize_source", label="Optimize Source", items=["No", "Using file with phase/space volume)", "Using file with slit/acceptance"],
                     labelWidth=120, callback=self.set_OptimizeSource, orientation="horizontal")
        self.optimize_file_name_box = oasysgui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")

        file_box = oasysgui.widgetBox(self.optimize_file_name_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_optimize_file_name = oasysgui.lineEdit(file_box, self, "optimize_file_name", "File Name", labelWidth=100,  valueType=str, orientation="horizontal")

        gui.button(file_box, self, "...", callback=self.selectOptimizeFile)

        oasysgui.lineEdit(self.optimize_file_name_box, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=280,  valueType=int, orientation="horizontal")

        self.set_OptimizeSource()

        adv_other_box = oasysgui.widgetBox(tab_basic, "Optional file output", addSpace=False, orientation="vertical")

        gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=120,
                     items=["None", "Begin.dat", "Debug (begin.dat + start.xx/end.xx)"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.rubber(self.controlArea)
        gui.rubber(self.mainArea)

    def after_change_workspace_units(self):
        label = self.le_rect_width.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_rect_height.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_ell_semiaxis_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_ell_semiaxis_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_gauss_sigma_x.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_gauss_sigma_z.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_source_depth_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_sigma_y.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

    def is_scanning_enabled(self):
        return True

    def check_source_options(self, variable_name):
        if variable_name in ["gaussian_central_value",
                             "gaussian_sigma",
                             "gaussian_minimum",
                             "gaussian_maximum"]:
            self.photon_energy_distribution = 4
            self.set_PhotonEnergyDistribution()
        elif variable_name in ["uniform_minimum",
                               "uniform_maximum"]:
            self.photon_energy_distribution = 2
            self.set_PhotonEnergyDistribution()
        elif variable_name in ["single_line_value"]:
            self.photon_energy_distribution = 0
            self.set_PhotonEnergyDistribution()
        elif variable_name in ["line_value_1",
                               "line_value_2",
                               "line_value_3",
                               "line_value_4",
                               "line_value_5",
                               "line_value_6",
                               "line_value_7",
                               "line_value_8",
                               "line_value_9",
                               "line_value_10"]:
            self.photon_energy_distribution = 1
            self.set_PhotonEnergyDistribution()
        elif variable_name in ["rect_width",
                               "rect_height"]:
            self.spatial_type = 1
            self.set_SpatialType()
        elif variable_name in ["ell_semiaxis_x",
                               "ell_semiaxis_z"]:
            self.spatial_type = 2
            self.set_SpatialType()
        elif variable_name in ["gauss_sigma_x",
                               "gauss_sigma_z"]:
            self.spatial_type = 3
            self.set_SpatialType()
        elif variable_name in ["horizontal_div_x_plus",
                               "horizontal_div_x_minus",
                               "vertical_div_z_plus",
                               "vertical_div_z_minus"]:
            if not self.angular_distribution in [0, 1]: self.angular_distribution = 0
            self.set_AngularDistribution()
        elif variable_name in ["horizontal_sigma_x",
                               "vertical_sigma_z",
                               "horizontal_lim_x_plus",
                               "horizontal_lim_x_minus",
                               "vertical_lim_z_plus",
                               "vertical_lim_z_minus"]:
            self.angular_distribution = 2
            self.set_AngularDistribution()
        elif variable_name in ["cone_internal_half_aperture",
                               "cone_external_half_aperture"]:
            self.angular_distribution = 3
            self.set_AngularDistribution()

    def callResetSettings(self):
        super().callResetSettings()

        self.set_Sampling()
        self.set_SpatialType()
        self.set_AngularDistribution()
        self.set_Depth()
        self.set_PhotonEnergyDistribution()
        self.set_Polarization()

    def set_OptimizeSource(self):
        self.optimize_file_name_box.setVisible(self.optimize_source != 0)

    def set_SpatialType(self):
        self.spatial_type_box_1.setVisible(self.spatial_type == 1)
        self.spatial_type_box_2.setVisible(self.spatial_type == 2)
        self.spatial_type_box_3.setVisible(self.spatial_type == 3)

    def set_AngularDistributionLimits(self):
        self.le_horizontal_lim_x_plus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 2)
        self.le_horizontal_lim_x_minus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 2)
        self.le_vertical_lim_z_plus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 1)
        self.le_vertical_lim_z_minus.setEnabled(self.angular_distribution_limits != 0 and self.angular_distribution_limits != 1)

    def set_AngularDistribution(self):
        self.angular_distribution_box_1.setVisible(self.angular_distribution == 0 or self.angular_distribution == 1)
        self.angular_distribution_box_2.setVisible(self.angular_distribution == 2)
        self.angular_distribution_box_3.setVisible(self.angular_distribution == 3)

        if self.angular_distribution == 2:
            self.set_AngularDistributionLimits()

    def set_Depth(self):
        self.depth_box_1.setVisible(self.depth == 1)
        self.depth_box_2.setVisible(self.depth == 2)

    def set_PhotonEnergyDistribution(self):
        self.ewp_box_1.setVisible(self.photon_energy_distribution == 0)
        self.ewp_box_2.setVisible(self.photon_energy_distribution == 1 or self.photon_energy_distribution == 3)
        self.ewp_box_3.setVisible(self.photon_energy_distribution == 2)
        self.ewp_box_4.setVisible(self.photon_energy_distribution == 3)
        self.ewp_box_5.setVisible(self.photon_energy_distribution == 1 or self.photon_energy_distribution == 3)
        self.ewp_box_6.setVisible(self.photon_energy_distribution == 4)
        self.ewp_box_7.setVisible(self.photon_energy_distribution == 5)

        if self.photon_energy_distribution == 3:
            self.le_line_value_1.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_2.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_3.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_4.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_5.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_6.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_7.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_8.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_9.parentWidget().children()[1].setFixedWidth(100)
            self.le_line_value_10.parentWidget().children()[1].setFixedWidth(100)
        else:
            self.le_line_value_1.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_2.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_3.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_4.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_5.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_6.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_7.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_8.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_9.parentWidget().children()[1].setFixedWidth(260)
            self.le_line_value_10.parentWidget().children()[1].setFixedWidth(260)

        self.container_right.setVisible(self.photon_energy_distribution == 3)

        self.set_NumberOfLines()

    def set_NumberOfLines(self):
        self.le_line_value_2.parentWidget().setVisible(self.number_of_lines >= 1)
        self.le_line_int_2.parentWidget().setVisible(self.number_of_lines >= 1)
        self.le_line_value_3.parentWidget().setVisible(self.number_of_lines >= 2)
        self.le_line_int_3.parentWidget().setVisible(self.number_of_lines >= 2)
        self.le_line_value_4.parentWidget().setVisible(self.number_of_lines >= 3)
        self.le_line_int_4.parentWidget().setVisible(self.number_of_lines >= 3)
        self.le_line_value_5.parentWidget().setVisible(self.number_of_lines >= 4)
        self.le_line_int_5.parentWidget().setVisible(self.number_of_lines >= 4)
        self.le_line_value_6.parentWidget().setVisible(self.number_of_lines >= 5)
        self.le_line_int_6.parentWidget().setVisible(self.number_of_lines >= 5)
        self.le_line_value_7.parentWidget().setVisible(self.number_of_lines >= 6)
        self.le_line_int_7.parentWidget().setVisible(self.number_of_lines >= 6)
        self.le_line_value_8.parentWidget().setVisible(self.number_of_lines >= 7)
        self.le_line_int_8.parentWidget().setVisible(self.number_of_lines >= 7)
        self.le_line_value_9.parentWidget().setVisible(self.number_of_lines >= 8)
        self.le_line_int_9.parentWidget().setVisible(self.number_of_lines >= 8)
        self.le_line_value_10.parentWidget().setVisible(self.number_of_lines == 9)
        self.le_line_int_10.parentWidget().setVisible(self.number_of_lines == 9)

    def set_Polarization(self):
        self.ewp_box_8.setVisible(self.polarization==1)

    def selectFile(self):
        self.le_user_defined_file.setText(oasysgui.selectFileFromDialog(self, self.user_defined_file, "Open Spectrum File", file_extension_filter="Data Files (*.dat *.txt)"))

    def selectOptimizeFile(self):
        self.le_optimize_file_name.setText(oasysgui.selectFileFromDialog(self, self.optimize_file_name, "Open Optimize Source Parameters File"))

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

            shadow_src = ShadowSource.create_src()

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
                                                  write_end_file=write_end_file)

            if self.photon_energy_distribution == 4:
                self.generate_gaussian_spectrum(beam_out)
            elif self.photon_energy_distribution == 5:
                self.generate_user_defined_spectrum(beam_out)

            self.fix_Intensity(beam_out)

            if self.trace_shadow:
                grabber.stop()

                for row in grabber.ttyData:
                   self.writeStdOut(row)

            self.setStatusMessage("Plotting Results")

            self.progressBarSet(80)
            self.plot_results(beam_out)

            self.setStatusMessage("")

            beam_out.setScanningData(self.scanning_data)

            self.send("Beam", beam_out)

        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

        self.progressBarFinished()

    #########################################################################################
    #
    # GENERATION OF GAUSSIAN OR USER DEFINED SPECTRUM
    #
    #########################################################################################

    def generate_gaussian_spectrum(self, beam_out):
        a, b = (self.gaussian_minimum - self.gaussian_central_value) / self.gaussian_sigma, \
               (self.gaussian_maximum - self.gaussian_central_value) / self.gaussian_sigma

        distribution = stats.truncnorm(a, b, loc=self.gaussian_central_value, scale=self.gaussian_sigma)
        sampled_spectrum = distribution.rvs(len(beam_out._beam.rays))

        beam_out._beam.rays[:, 10] = ShadowPhysics.getShadowKFromEnergy(energy=sampled_spectrum[:]) if self.units == 0 else \
                                     ShadowPhysics.getShadowKFromWavelength(wavelength=sampled_spectrum[:])

    #########################################################################################

    def generate_user_defined_spectrum(self, beam_out):
        sampled_spectrum = self.sample_from_spectrum(numpy.loadtxt(self.user_defined_file),
                                                     len(beam_out._beam.rays),
                                                     self.user_defined_spectrum_binning)

        beam_out._beam.rays[:, 10] = ShadowPhysics.getShadowKFromEnergy(energy=sampled_spectrum[:]) if self.units == 0 else \
                                     ShadowPhysics.getShadowKFromWavelength(wavelength=sampled_spectrum[:])

    def sample_from_spectrum(self, spectrum, npoints, nbins=10000):
        y_values = spectrum[1 if spectrum[0, 0] == 0 else 0:, 1]
        x_values = spectrum[1 if spectrum[0, 0] == 0 else 0:, 0]

        if len(x_values) < nbins: x_values, y_values = self.resample_spectrum(x_values, y_values, nbins)

        # normalize distribution function
        y_values /= numpy.max(y_values)
        y_values /= y_values.sum()

        refining_factor = 10**(self.user_defined_refining_factor)

        if self.seed != 0: numpy.random.seed(seed=self.seed)
        random_generator = stats.rv_discrete(name='user_defined_distribution', values=(x_values*refining_factor, y_values))

        return random_generator.rvs(size=npoints)/refining_factor

    def resample_spectrum(self, x_values, y_values, new_dim):
        e_min = x_values[0]
        e_max = x_values[-1]

        new_x_values = e_min + numpy.arange(0, new_dim + 1) * (e_max - e_min) / new_dim

        return new_x_values, numpy.interp(new_x_values, x_values, y_values)

    #########################################################################################

    # WEIRD MEMORY INITIALIZATION BY FORTRAN. JUST A FIX.
    def fix_Intensity(self, beam_out):
        if self.polarization == 0:
            beam_out._beam.rays[:, 15] = 0
            beam_out._beam.rays[:, 16] = 0
            beam_out._beam.rays[:, 17] = 0

    def acceptExchangeData(self, exchangeData):
        try:
            if not exchangeData is None:
                if exchangeData.get_program_name() == "XOPPY":
                    no_bandwidth = False
                    if exchangeData.get_widget_name() =="UNDULATOR_FLUX" :
                        self.user_defined_file = "xoppy_undulator_flux"
                        index_flux = 1
                    elif exchangeData.get_widget_name() == "BM" :
                        if exchangeData.get_content("is_log_plot") == 1:
                            raise Exception("Logarithmic X scale of Xoppy Energy distribution not supported")
                        if exchangeData.get_content("calculation_type") == 0 and exchangeData.get_content("psi") == 0:
                            self.user_defined_file = "xoppy_bm_flux"
                            index_flux = 5
                        else:
                            raise Exception("Xoppy result is not an Flux vs Energy distribution integrated in Psi")
                    elif exchangeData.get_widget_name() =="XWIGGLER" :
                        if exchangeData.get_content("is_log_plot") == 1:
                            raise Exception("Logarithmic X scale of Xoppy Energy distribution not supported")
                        self.user_defined_file = "xoppy_xwiggler_flux"
                        index_flux = 1
                    elif exchangeData.get_widget_name() =="WS" :
                        if exchangeData.get_content("is_log_plot") == 1:
                            raise Exception("Logarithmic X scale of Xoppy Energy distribution not supported")
                        self.user_defined_file = "xoppy_xwiggler_flux"
                        index_flux = 1
                    elif exchangeData.get_widget_name() =="XTUBES" :
                        self.user_defined_file = "xoppy_xtubes_flux"
                        index_flux = 1
                        no_bandwidth = True
                    elif exchangeData.get_widget_name() =="XTUBE_W" :
                        self.user_defined_file = "xoppy_xtube_w_flux"
                        index_flux = 1
                        no_bandwidth = True
                    elif exchangeData.get_widget_name() =="BLACK_BODY" :
                        self.user_defined_file = "xoppy_black_body_flux"
                        index_flux = 2
                    else:
                        raise Exception("Xoppy Source not recognized")

                    self.user_defined_file += "_" + str(id(self)) + ".dat"

                    self.photon_energy_distribution = 5
                    self.units = 0 # eV

                    spectrum = exchangeData.get_content("xoppy_data")

                    if not no_bandwidth:
                        spectrum[:,index_flux] /= 0.001*spectrum[:,0]

                    file = open(self.user_defined_file, "w")
                    for index in range(0, spectrum.shape[0]):
                        file.write(str(spectrum[index, 0]) + " " + str(spectrum[index, index_flux]) + "\n")

                    file.close()

                    if not spectrum is None:
                        self.user_defined_minimum = numpy.min(spectrum[:, 0])
                        self.user_defined_maximum = numpy.max(spectrum[:, 0])


                    self.set_PhotonEnergyDistribution()
        except Exception as exception:
            QtWidgets.QMessageBox.critical(self, "Error",
                                       str(exception),
                QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def setupUI(self):
        self.set_OptimizeSource()
        self.set_SpatialType()
        self.set_AngularDistribution()
        self.set_Depth()
        self.set_PhotonEnergyDistribution()
        self.set_Polarization()

    def checkFields(self):
        self.number_of_rays = congruence.checkPositiveNumber(self.number_of_rays, "Number of Random rays")
        self.seed = congruence.checkPositiveNumber(self.seed, "Seed")

        if self.spatial_type == 1:
            self.rect_width = congruence.checkPositiveNumber(self.rect_width, "Width")
            self.rect_height = congruence.checkPositiveNumber(self.rect_height, "Height")
        elif self.spatial_type == 2:
            self.ell_semiaxis_x = congruence.checkPositiveNumber(self.ell_semiaxis_x, "Semi-Axis X")
            self.ell_semiaxis_z = congruence.checkPositiveNumber(self.ell_semiaxis_z, "Semi-Axis Z")
        elif self.spatial_type == 3:
            self.gauss_sigma_x = congruence.checkPositiveNumber(self.gauss_sigma_x, "Sigma X")
            self.gauss_sigma_z = congruence.checkPositiveNumber(self.gauss_sigma_z, "Sigma Z")

        if self.angular_distribution == 0 or self.angular_distribution == 1:
            self.horizontal_div_x_plus = congruence.checkPositiveNumber(self.horizontal_div_x_plus, "Horizontal Divergence X(+)")
            self.horizontal_div_x_minus = congruence.checkPositiveNumber(self.horizontal_div_x_minus, "Horizontal Divergence X(-)")
            self.vertical_div_z_plus = congruence.checkPositiveNumber(self.vertical_div_z_plus, "Vertical Divergence Z(+)")
            self.vertical_div_z_minus = congruence.checkPositiveNumber(self.vertical_div_z_minus, "Vertical Divergence Z(-)")
        elif self.angular_distribution == 2:
            if self.angular_distribution_limits != 0:
                if self.angular_distribution_limits != 2:
                    self.horizontal_lim_x_plus = congruence.checkPositiveNumber(self.horizontal_lim_x_plus, "Horizontal Limit X(+)")
                    self.horizontal_lim_x_minus = congruence.checkPositiveNumber(self.horizontal_lim_x_minus, "Horizontal Limit X(-)")
                if self.angular_distribution_limits != 1:
                    self.vertical_lim_z_plus = congruence.checkPositiveNumber(self.vertical_lim_z_plus, "Vertical Limit Z(+)")
                    self.vertical_lim_z_minus = congruence.checkPositiveNumber(self.vertical_lim_z_minus, "Vertical Limit Z(-)")

            self.horizontal_sigma_x = congruence.checkPositiveNumber(self.horizontal_sigma_x, "Horizontal Sigma (X)")
            self.vertical_sigma_z = congruence.checkPositiveNumber(self.vertical_sigma_z, "Vertical Sigma (Z)")
        elif self.angular_distribution == 3:
            self.cone_internal_half_aperture = congruence.checkPositiveNumber(self.cone_internal_half_aperture, "Cone Internal Half-Aperture")
            self.cone_external_half_aperture = congruence.checkPositiveNumber(self.cone_external_half_aperture, "Cone External Half-Aperture")

        if self.depth == 1:
            self.source_depth_y = congruence.checkPositiveNumber(self.source_depth_y, "Source Depth (Y)")
        elif self.depth == 2:
            self.sigma_y = congruence.checkPositiveNumber(self.sigma_y, "Sigma Y")

        if self.photon_energy_distribution == 0:
            self.single_line_value = congruence.checkPositiveNumber(self.single_line_value, "Single Line Value")
        elif self.photon_energy_distribution == 1:
            if self.number_of_lines >= 1:
                self.line_value_1 = congruence.checkPositiveNumber(self.line_value_1, "Line 1")
            if self.number_of_lines >= 2:
                self.line_value_2 = congruence.checkPositiveNumber(self.line_value_2, "Line 2")
            if self.number_of_lines >= 3:
                self.line_value_3 = congruence.checkPositiveNumber(self.line_value_3, "Line 3")
            if self.number_of_lines >= 4:
                self.line_value_4 = congruence.checkPositiveNumber(self.line_value_4, "Line 4")
            if self.number_of_lines >= 5:
                self.line_value_5 = congruence.checkPositiveNumber(self.line_value_5, "Line 5")
            if self.number_of_lines >= 6:
                self.line_value_6 = congruence.checkPositiveNumber(self.line_value_6, "Line 6")
            if self.number_of_lines >= 7:
                self.line_value_7 = congruence.checkPositiveNumber(self.line_value_7, "Line 7")
            if self.number_of_lines >= 8:
                self.line_value_8 = congruence.checkPositiveNumber(self.line_value_8, "Line 8")
            if self.number_of_lines >= 9:
                self.line_value_9 = congruence.checkPositiveNumber(self.line_value_9, "Line 9")
            if self.number_of_lines == 10:
                self.line_value_10 = congruence.checkPositiveNumber(self.line_value_10, "Line 10")
        elif self.photon_energy_distribution == 2:
            self.uniform_minimum = congruence.checkPositiveNumber(self.uniform_minimum, "Minimum Energy/Wavelength")
            self.uniform_maximum = congruence.checkStrictlyPositiveNumber(self.uniform_maximum, "Maximum Energy/Wavelength")

            congruence.checkLessThan(self.uniform_minimum, self.uniform_maximum, "Minimum Energy/Wavelength", "Maximum Energy/Wavelength")
        elif self.photon_energy_distribution == 3:
            if self.number_of_lines >= 1:
                self.line_value_1 = congruence.checkPositiveNumber(self.line_value_1, "Line 1")
                self.line_int_1 = congruence.checkPositiveNumber(self.line_int_1, "Int 1")
            if self.number_of_lines >= 2:
                self.line_value_2 = congruence.checkPositiveNumber(self.line_value_2, "Line 2")
                self.line_int_2 = congruence.checkPositiveNumber(self.line_int_1, "Int 2")
            if self.number_of_lines >= 3:
                self.line_value_3 = congruence.checkPositiveNumber(self.line_value_3, "Line 3")
                self.line_int_3 = congruence.checkPositiveNumber(self.line_int_1, "Int 3")
            if self.number_of_lines >= 4:
                self.line_value_4 = congruence.checkPositiveNumber(self.line_value_4, "Line 4")
                self.line_int_4 = congruence.checkPositiveNumber(self.line_int_1, "Int 4")
            if self.number_of_lines >= 5:
                self.line_value_5 = congruence.checkPositiveNumber(self.line_value_5, "Line 5")
                self.line_int_5 = congruence.checkPositiveNumber(self.line_int_1, "Int 5")
            if self.number_of_lines >= 6:
                self.line_value_6 = congruence.checkPositiveNumber(self.line_value_6, "Line 6")
                self.line_int_6 = congruence.checkPositiveNumber(self.line_int_1, "Int 6")
            if self.number_of_lines >= 7:
                self.line_value_7 = congruence.checkPositiveNumber(self.line_value_7, "Line 7")
                self.line_int_7 = congruence.checkPositiveNumber(self.line_int_1, "Int 7")
            if self.number_of_lines >= 8:
                self.line_value_8 = congruence.checkPositiveNumber(self.line_value_8, "Line 8")
                self.line_int_8 = congruence.checkPositiveNumber(self.line_int_1, "Int 8")
            if self.number_of_lines >= 9:
                self.line_value_9 = congruence.checkPositiveNumber(self.line_value_9, "Line 9")
                self.line_int_9 = congruence.checkPositiveNumber(self.line_int_1, "Int 9")
            if self.number_of_lines == 10:
                self.line_value_10 = congruence.checkPositiveNumber(self.line_value_10, "Line 10")
                self.line_int_10 = congruence.checkPositiveNumber(self.line_int_1, "Int 10")
        elif self.photon_energy_distribution == 4:
            self.gaussian_central_value = congruence.checkStrictlyPositiveNumber(self.gaussian_central_value, "Central Value")
            self.gaussian_sigma = congruence.checkStrictlyPositiveNumber(self.gaussian_sigma, "Sigma")
            self.gaussian_minimum = congruence.checkPositiveNumber(self.gaussian_minimum, "Minimum Energy/Wavelength")
            self.gaussian_maximum = congruence.checkStrictlyPositiveNumber(self.gaussian_maximum, "Maximum Energy/Wavelength")

            congruence.checkLessThan(self.gaussian_minimum, self.gaussian_maximum, "Minimum Energy/Wavelength", "Maximum Energy/Wavelength")

        elif self.photon_energy_distribution == 5:
            congruence.checkFile(self.user_defined_file)
            self.user_defined_minimum = congruence.checkPositiveNumber(self.user_defined_minimum, "Minimum Energy/Wavelength")
            self.user_defined_maximum = congruence.checkStrictlyPositiveNumber(self.user_defined_maximum, "Maximum Energy/Wavelength")

            congruence.checkLessThan(self.user_defined_minimum, self.user_defined_maximum, "Minimum Energy/Wavelength", "Maximum Energy/Wavelength")
            congruence.checkStrictlyPositiveNumber(self.user_defined_spectrum_binning, "Spectrum Binning")
            congruence.checkPositiveNumber(self.user_defined_refining_factor, "Refining Factor")

        if self.optimize_source > 0:
            self.max_number_of_rejected_rays = congruence.checkPositiveNumber(self.max_number_of_rejected_rays, "Max number of rejected rays")
            congruence.checkFile(self.optimize_file_name)

    def populateFields(self, shadow_src):
        shadow_src.src.NPOINT = self.number_of_rays
        shadow_src.src.ISTAR1 = self.seed

        shadow_src.src.FGRID = 0
        shadow_src.src.IDO_VX = 0
        shadow_src.src.IDO_VZ = 0
        shadow_src.src.IDO_X_S = 0
        shadow_src.src.IDO_Y_S = 0
        shadow_src.src.IDO_Z_S = 0

        shadow_src.src.FSOUR = self.spatial_type

        if self.spatial_type == 1:
            shadow_src.src.WXSOU = self.rect_width
            shadow_src.src.WZSOU = self.rect_height
        elif self.spatial_type == 2:
            shadow_src.src.WXSOU = self.ell_semiaxis_x
            shadow_src.src.WZSOU = self.ell_semiaxis_z
        elif self.spatial_type == 3:
            shadow_src.src.SIGMAX = self.gauss_sigma_x
            shadow_src.src.SIGMAZ = self.gauss_sigma_z

        if self.angular_distribution == 0 or self.angular_distribution == 1:
            shadow_src.src.FDISTR = self.angular_distribution + 1
            shadow_src.src.HDIV1 = self.horizontal_div_x_plus
            shadow_src.src.HDIV2 = self.horizontal_div_x_minus
            shadow_src.src.VDIV1 = self.vertical_div_z_plus
            shadow_src.src.VDIV2 = self.vertical_div_z_minus
        elif self.angular_distribution == 2:
            shadow_src.src.FDISTR = 3

            shadow_src.src.HDIV1 = 0
            shadow_src.src.HDIV2 = 0
            shadow_src.src.VDIV1 = 0
            shadow_src.src.VDIV2 = 0

            if self.angular_distribution_limits == 1 or self.angular_distribution_limits == 3:
                shadow_src.src.HDIV1 = self.horizontal_lim_x_plus
                shadow_src.src.HDIV2 = self.horizontal_lim_x_minus
            if self.angular_distribution_limits == 2 or self.angular_distribution_limits == 3:
                shadow_src.src.VDIV1 = self.vertical_lim_z_plus
                shadow_src.src.VDIV2 = self.vertical_lim_z_minus

            shadow_src.src.SIGDIX = self.horizontal_sigma_x
            shadow_src.src.SIGDIZ = self.vertical_sigma_z
        elif self.angular_distribution == 3:
            shadow_src.src.FDISTR = 5
            shadow_src.src.CONE_MIN = self.cone_internal_half_aperture
            shadow_src.src.CONE_MAX = self.cone_external_half_aperture

        shadow_src.src.FSOURCE_DEPTH = self.depth + 1

        if self.depth == 1:
            shadow_src.src.WYSOU = self.source_depth_y
        elif self.depth == 2:
            shadow_src.src.SIGMAY = self.sigma_y

        shadow_src.src.F_COLOR = self.photon_energy_distribution + 1
        shadow_src.src.F_PHOT = self.units

        if self.photon_energy_distribution == 0:
            shadow_src.src.PH1 = self.single_line_value
        elif self.photon_energy_distribution == 1:
            shadow_src.src.N_COLOR = self.number_of_lines+1
            shadow_src.src.PH1 = self.line_value_1
            shadow_src.src.PH2 = self.line_value_2
            shadow_src.src.PH3 = self.line_value_3
            shadow_src.src.PH4 = self.line_value_4
            shadow_src.src.PH5 = self.line_value_5
            shadow_src.src.PH6 = self.line_value_6
            shadow_src.src.PH7 = self.line_value_7
            shadow_src.src.PH8 = self.line_value_8
            shadow_src.src.PH9 = self.line_value_9
            shadow_src.src.PH10 = self.line_value_10
        elif self.photon_energy_distribution == 2:
            shadow_src.src.PH1 = self.uniform_minimum
            shadow_src.src.PH2 = self.uniform_maximum
        elif self.photon_energy_distribution == 3:
            shadow_src.src.N_COLOR = self.number_of_lines+1
            shadow_src.src.PH1 = self.line_value_1
            shadow_src.src.PH2 = self.line_value_2
            shadow_src.src.PH3 = self.line_value_3
            shadow_src.src.PH4 = self.line_value_4
            shadow_src.src.PH5 = self.line_value_5
            shadow_src.src.PH6 = self.line_value_6
            shadow_src.src.PH7 = self.line_value_7
            shadow_src.src.PH8 = self.line_value_8
            shadow_src.src.PH9 = self.line_value_9
            shadow_src.src.PH10 = self.line_value_10
            shadow_src.src.RL1 = self.line_int_1
            shadow_src.src.RL2 = self.line_int_2
            shadow_src.src.RL3 = self.line_int_3
            shadow_src.src.RL4 = self.line_int_4
            shadow_src.src.RL5 = self.line_int_5
            shadow_src.src.RL6 = self.line_int_6
            shadow_src.src.RL7 = self.line_int_7
            shadow_src.src.RL8 = self.line_int_8
            shadow_src.src.RL9 = self.line_int_9
            shadow_src.src.RL10 = self.line_int_10
        elif self.photon_energy_distribution == 4 or self.angular_distribution == 5:
            shadow_src.src.PH1 = 1000 # just a number, will be recomputed according to energy distribution

        shadow_src.src.F_POLAR = self.polarization

        if self.polarization == 1:
            shadow_src.src.F_COHER = self.coherent_beam
            shadow_src.src.POL_ANGLE = self.phase_diff
            shadow_src.src.POL_DEG = self.polarization_degree

        shadow_src.src.F_OPD = 1
        shadow_src.src.F_BOUND_SOUR = self.optimize_source
        if self.optimize_source > 0:
            shadow_src.src.FILE_BOUND = bytes(congruence.checkFileName(self.optimize_file_name), 'utf-8')
        shadow_src.src.NTOTALPOINT = self.max_number_of_rejected_rays

    def deserialize(self, shadow_file):
        if not shadow_file is None:
            try:
                self.number_of_rays=int(shadow_file.getProperty("NPOINT"))
                self.seed=int(shadow_file.getProperty("ISTAR1"))

                sampling = int(shadow_file.getProperty("FGRID"))

                if sampling > 0: raise Exception("Sampling different from Random/Random is no more supported")

                self.spatial_type = int(shadow_file.getProperty("FSOUR"))

                if self.spatial_type == 1:
                    self.rect_width = float(shadow_file.getProperty("WXSOU"))
                    self.rect_height = float(shadow_file.getProperty("WZSOU"))
                elif self.spatial_type == 2:
                    self.ell_semiaxis_x = float(shadow_file.getProperty("WXSOU"))
                    self.ell_semiaxis_z = float(shadow_file.getProperty("WZSOU"))
                elif self.spatial_type == 3:
                    self.gauss_sigma_x = float(shadow_file.getProperty("SIGMAX"))
                    self.gauss_sigma_z = float(shadow_file.getProperty("SIGMAZ"))

                fdistr = int(shadow_file.getProperty("FDISTR"))

                self.angular_distribution = 0

                if fdistr == 5:
                    self.angular_distribution = 3
                elif fdistr <= 3:
                    self.angular_distribution = fdistr-1

                if self.angular_distribution == 0 or \
                    self.angular_distribution == 1:
                    self.horizontal_div_x_plus = float(shadow_file.getProperty("HDIV1"))
                    self.horizontal_div_x_minus = float(shadow_file.getProperty("HDIV2"))
                    self.vertical_div_z_plus = float(shadow_file.getProperty("VDIV1"))
                    self.vertical_div_z_minus = float(shadow_file.getProperty("VDIV2"))
                elif self.angular_distribution == 2:
                    self.horizontal_lim_x_plus = float(shadow_file.getProperty("HDIV1"))
                    self.horizontal_lim_x_minus = float(shadow_file.getProperty("HDIV2"))
                    self.vertical_lim_z_plus = float(shadow_file.getProperty("VDIV1"))
                    self.vertical_lim_z_minus = float(shadow_file.getProperty("VDIV2"))

                    horiz = self.horizontal_lim_x_plus == 0.0 and self.horizontal_lim_x_minus == 0.0
                    verti = self.vertical_lim_z_plus == 0.0 and self.vertical_lim_z_minus == 0.0

                    if not horiz and verti:
                       self.angular_distribution_limits = 1
                    elif horiz and not verti:
                       self.angular_distribution_limits = 2
                    elif not horiz and not verti:
                        self.angular_distribution_limits = 3
                    else:
                        self.angular_distribution_limits = 0

                    self.horizontal_sigma_x = float(shadow_file.getProperty("SIGDIX"))
                    self.vertical_sigma_z = float(shadow_file.getProperty("SIGDIZ"))
                elif self.angular_distribution == 3:
                    self.cone_internal_half_aperture = float(shadow_file.getProperty("CONE_MIN"))
                    self.cone_external_half_aperture = float(shadow_file.getProperty("CONE_MAX"))


                self.depth = int(shadow_file.getProperty("FSOURCE_DEPTH")) - 1

                if self.depth == 1:
                    self.source_depth_y = float(shadow_file.getProperty("WYSOU"))
                elif self.depth == 2:
                    self.sigma_y = float(shadow_file.getProperty("SIGMAY"))

                self.photon_energy_distribution = int(shadow_file.getProperty("F_COLOR"))-1
                self.units = int(shadow_file.getProperty("F_PHOT"))

                if self.photon_energy_distribution == 0:
                    self.single_line_value = float(shadow_file.getProperty("PH1"))
                elif self.photon_energy_distribution == 1:
                    self.number_of_lines = int(shadow_file.getProperty("N_COLOR"))-1
                    self.line_value_1 = float(shadow_file.getProperty("PH1"))
                    self.line_value_2 = float(shadow_file.getProperty("PH2"))
                    self.line_value_3 = float(shadow_file.getProperty("PH3"))
                    self.line_value_4 = float(shadow_file.getProperty("PH4"))
                    self.line_value_5 = float(shadow_file.getProperty("PH5"))
                    self.line_value_6 = float(shadow_file.getProperty("PH6"))
                    self.line_value_7 = float(shadow_file.getProperty("PH7"))
                    self.line_value_8 = float(shadow_file.getProperty("PH8"))
                    self.line_value_9 = float(shadow_file.getProperty("PH9"))
                    self.line_value_10 = float(shadow_file.getProperty("PH10"))
                elif self.photon_energy_distribution == 2:
                    self.uniform_minimum = float(shadow_file.getProperty("PH1"))
                    self.uniform_maximum = float(shadow_file.getProperty("PH2"))
                elif self.photon_energy_distribution == 3:
                    self.number_of_lines = int(shadow_file.getProperty("N_COLOR"))-1
                    self.line_value_1 = float(shadow_file.getProperty("PH1"))
                    self.line_value_2 = float(shadow_file.getProperty("PH2"))
                    self.line_value_3 = float(shadow_file.getProperty("PH3"))
                    self.line_value_4 = float(shadow_file.getProperty("PH4"))
                    self.line_value_5 = float(shadow_file.getProperty("PH5"))
                    self.line_value_6 = float(shadow_file.getProperty("PH6"))
                    self.line_value_7 = float(shadow_file.getProperty("PH7"))
                    self.line_value_8 = float(shadow_file.getProperty("PH8"))
                    self.line_value_9 = float(shadow_file.getProperty("PH9"))
                    self.line_value_10 = float(shadow_file.getProperty("PH10"))
                    self.line_int_1 = float(shadow_file.getProperty("RL1"))
                    self.line_int_2 = float(shadow_file.getProperty("RL2"))
                    self.line_int_3 = float(shadow_file.getProperty("RL3"))
                    self.line_int_4 = float(shadow_file.getProperty("RL4"))
                    self.line_int_5 = float(shadow_file.getProperty("RL5"))
                    self.line_int_6 = float(shadow_file.getProperty("RL6"))
                    self.line_int_7 = float(shadow_file.getProperty("RL7"))
                    self.line_int_8 = float(shadow_file.getProperty("RL8"))
                    self.line_int_9 = float(shadow_file.getProperty("RL9"))
                    self.line_int_10 = float(shadow_file.getProperty("RL10"))

                self.polarization = int(shadow_file.getProperty("F_POLAR"))

                if self.polarization == 1:
                    self.coherent_beam = float(shadow_file.getProperty("F_COHER"))
                    self.phase_diff = float(shadow_file.getProperty("POL_ANGLE"))
                    self.polarization_degree = float(shadow_file.getProperty("POL_DEG"))

                self.optimize_source = int(shadow_file.getProperty("F_BOUND_SOUR"))
                self.optimize_file_name = str(shadow_file.getProperty("FILE_BOUND"))

                if not shadow_file.getProperty("NTOTALPOINT") is None:
                    self.max_number_of_rejected_rays = int(shadow_file.getProperty("NTOTALPOINT"))
                else:
                    self.max_number_of_rejected_rays = 10000000
            except Exception as exception:
                raise BlockingIOError("Geometrical source failed to load, bad file format: " + exception.args[0])

            self.setupUI()

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = GeometricalSource()
    ow.show()
    a.exec_()
    ow.saveSettings()
