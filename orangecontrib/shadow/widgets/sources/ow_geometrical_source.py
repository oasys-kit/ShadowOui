import sys, numpy
import scipy.stats as stats

from orangewidget import gui
from orangewidget.settings import Setting
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication, QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_source
from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerOut, ShadowBeam, \
    ShadowSource
from orangecontrib.shadow.util.shadow_util import ShadowGui, ShadowPhysics

class GeometricalSource(ow_source.Source):

    name = "Geometrical Source"
    description = "Shadow Source: Geometrical Source"
    icon = "icons/geometrical.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "Sources"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Trigger", ShadowTriggerOut, "sendNewBeam")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    want_main_area=1

    sampling = Setting(0)

    number_of_rays=Setting(5000)
    seed=Setting(6775431)

    grid_points_in_xfirst = Setting(1)
    grid_points_in_zfirst = Setting(1)
    grid_points_in_x = Setting(1)
    grid_points_in_y = Setting(1)
    grid_points_in_z = Setting(1)
    radial_grid_points = Setting(0)
    concentrical_grid_points = Setting(0)

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

    horizontal_lim_x_plus = Setting(5.0e-7)
    horizontal_lim_x_minus = Setting(5.0e-7)
    vertical_lim_z_plus = Setting(5.0e-6)
    vertical_lim_z_minus = Setting(5.0e-6)
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

    polarization = Setting(1)
    coherent_beam = Setting(0)
    phase_diff = Setting(0.0)
    polarization_degree = Setting(1.0)

    store_optical_paths=Setting(1) # REMOVED FROM GUI: 1 AS DEFAULT

    optimize_source=Setting(0)
    optimize_file_name = Setting("NONESPECIFIED")
    max_number_of_rejected_rays = Setting(10000000)

    def __init__(self):
        super().__init__()

        tabs = ShadowGui.tabWidget(self.controlArea, width=480,  height=620)

        tab_montecarlo = ShadowGui.createTabPage(tabs, "Monte Carlo and Sampling")
        tab_geometry = ShadowGui.createTabPage(tabs, "Geometry")
        tab_energy = ShadowGui.createTabPage(tabs, "Energy and Polarization")

        ##############################
        # MONTECARLO

        left_box_1 = ShadowGui.widgetBox(tab_montecarlo, "Options", addSpace=True, orientation="vertical", height=280)

        gui.separator(left_box_1)

        ##################################################################
        #
        # OTHER THAN RANDOM/RANDOM NOT PROPERLY WORKING, DISABLED UNTIL FIXED
        #
        #gui.comboBox(left_box_1, self, "sampling", label="Sampling (space/divergence)", labelWidth=300,
        #             items=["Random/Random", "Grid/Grid", "Grid/Random", "Random/Grid"], orientation="horizontal", callback=self.set_Sampling)

        gui.comboBox(left_box_1, self, "sampling", label="Sampling (space/divergence)", labelWidth=300,
                     items=["Random/Random"], orientation="horizontal", callback=self.set_Sampling)

        gui.separator(left_box_1)

        self.sample_box_1 = ShadowGui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.sample_box_1, self, "number_of_rays", "Number of Random Rays", labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(self.sample_box_1, self, "seed", "Seed", labelWidth=300, valueType=int, orientation="horizontal")

        self.sample_box_2 = ShadowGui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.sample_box_2, self, "grid_points_in_xfirst", "Grid Points in X'", labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(self.sample_box_2, self, "grid_points_in_zfirst", "Grid Points in Z'",  labelWidth=300, valueType=int, orientation="horizontal")

        self.sample_box_3 = ShadowGui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.sample_box_3, self, "grid_points_in_x", "Grid Points in X", labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(self.sample_box_3, self, "grid_points_in_y", "Grid Points in Y", labelWidth=300, valueType=int, orientation="horizontal")
        ShadowGui.lineEdit(self.sample_box_3, self, "grid_points_in_z", "Grid Points in Z",  labelWidth=300, valueType=int, orientation="horizontal")

        #self.sample_box_4 = ShadowGui.widgetBox(left_box_1, "", addSpace=False, orientation="vertical")

        #ShadowGui.lineEdit(self.sample_box_4, self, "radial_grid_points", "Radial Grid Points", labelWidth=300, valueType=int, orientation="horizontal")
        #ShadowGui.lineEdit(self.sample_box_4, self, "concentrical_grid_points", "Concentrical Grid Points",  labelWidth=300, valueType=int, orientation="horizontal")

        self.set_Sampling()

        ##############################
        # GEOMETRY

        left_box_2 = ShadowGui.widgetBox(tab_geometry, "", addSpace=True, orientation="vertical", height=550)

        gui.separator(left_box_2)

        ######

        spatial_type_box = ShadowGui.widgetBox(left_box_2, "Spatial Type", addSpace=True, orientation="vertical", height=120)

        gui.comboBox(spatial_type_box, self, "spatial_type", label="Spatial Type", labelWidth=355,
                     items=["Point", "Rectangle", "Ellipse", "Gaussian"], orientation="horizontal", callback=self.set_SpatialType)

        gui.separator(spatial_type_box)

        self.spatial_type_box_1 = ShadowGui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.spatial_type_box_1, self, "rect_width", "Width [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.spatial_type_box_1, self, "rect_height", "Height [cm]", labelWidth=300, valueType=float, orientation="horizontal")

        self.spatial_type_box_2 = ShadowGui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.spatial_type_box_2, self, "ell_semiaxis_x", "Semi-Axis X [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.spatial_type_box_2, self, "ell_semiaxis_z", "Semi-Axis Z [cm]", labelWidth=300, valueType=float, orientation="horizontal")

        self.spatial_type_box_3 = ShadowGui.widgetBox(spatial_type_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.spatial_type_box_3, self, "gauss_sigma_x", "Sigma X [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.spatial_type_box_3, self, "gauss_sigma_z", "Sigma Z [cm]", labelWidth=300, valueType=float, orientation="horizontal")

        self.set_SpatialType()

        angular_distribution_box = ShadowGui.widgetBox(left_box_2, "Angular Distribution", addSpace=True, orientation="vertical", height=230)

        gui.comboBox(angular_distribution_box, self, "angular_distribution", label="Angular Distribution", labelWidth=355,
                     items=["Flat", "Uniform", "Gaussian", "Conical"], orientation="horizontal", callback=self.set_AngularDistribution)

        gui.separator(angular_distribution_box)

        self.angular_distribution_box_1 = ShadowGui.widgetBox(angular_distribution_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.angular_distribution_box_1, self, "horizontal_div_x_plus", "Horizontal Divergence X(+) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_1, self, "horizontal_div_x_minus", "Horizontal Divergence X(-) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_1, self, "vertical_div_z_plus", "Vertical Divergence Z(+) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_1, self, "vertical_div_z_minus", "Vertical Divergence Z(-) [rad]", labelWidth=300, valueType=float, orientation="horizontal")

        self.angular_distribution_box_2 = ShadowGui.widgetBox(angular_distribution_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.angular_distribution_box_2, self, "horizontal_lim_x_plus", "Horizontal Limit X(+) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_2, self, "horizontal_lim_x_minus", "Horizontal Limit X(-) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_2, self, "vertical_lim_z_plus", "Vertical Limit Z(+) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_2, self, "vertical_lim_z_minus", "Vertical Limit Z(-) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_2, self, "horizontal_sigma_x", "Horizontal Sigma (X) [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_2, self, "vertical_sigma_z", "Vertical Sigma (Z) [rad]", labelWidth=300, valueType=float, orientation="horizontal")

        self.angular_distribution_box_3 = ShadowGui.widgetBox(angular_distribution_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.angular_distribution_box_3, self, "cone_internal_half_aperture", "Cone Internal Half-Aperture [rad]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.angular_distribution_box_3, self, "cone_external_half_aperture", "Cone External Half-Aperture [rad]", labelWidth=300, valueType=float, orientation="horizontal")

        self.set_AngularDistribution()

        depth_box = ShadowGui.widgetBox(left_box_2, "Depth", addSpace=True, orientation="vertical", height=100)

        gui.comboBox(depth_box, self, "depth", label="Depth", labelWidth=355,
                     items=["Off", "Uniform", "Gaussian"], orientation="horizontal", callback=self.set_Depth)

        gui.separator(depth_box, 1)

        self.depth_box_1 = ShadowGui.widgetBox(depth_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.depth_box_1, self, "source_depth_y", "Source Depth (Y) [cm]", labelWidth=300, valueType=float, orientation="horizontal")

        self.depth_box_2 = ShadowGui.widgetBox(depth_box, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.depth_box_2, self, "sigma_y", "Sigma Y [cm]", labelWidth=300, valueType=float, orientation="horizontal")

        self.set_Depth()

        ##############################
        # ENERGY

        left_box_3 = ShadowGui.widgetBox(tab_energy, "", addSpace=True, orientation="vertical", height=640)

        gui.separator(left_box_3)

        ######

        energy_wavelength_box = ShadowGui.widgetBox(left_box_3, "Energy/Wavelength", addSpace=True, orientation="vertical", height=420)

        gui.comboBox(energy_wavelength_box, self, "photon_energy_distribution", label="Photon Energy Distribution", labelWidth=300,
                     items=["Single Line", "Several Lines", "Uniform", "Relative Intensities", "Gaussian", "User Defined"], orientation="horizontal", callback=self.set_PhotonEnergyDistribution)

        gui.separator(energy_wavelength_box)

        gui.comboBox(energy_wavelength_box, self, "units", label="Units", labelWidth=300,
                     items=["Energy/eV", "Wavelength/Å"], orientation="horizontal", callback=self.set_PhotonEnergyDistribution)

        gui.separator(energy_wavelength_box)

        self.ewp_box_5 = ShadowGui.widgetBox(energy_wavelength_box, "", addSpace=False, orientation="vertical")

        gui.comboBox(self.ewp_box_5, self, "number_of_lines", label="Number of Lines", labelWidth=350,
                     items=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], orientation="horizontal", callback=self.set_NumberOfLines)

        container =  ShadowGui.widgetBox(energy_wavelength_box, "", addSpace=False, orientation="horizontal")
        self.container_left =  ShadowGui.widgetBox(container, "", addSpace=False, orientation="vertical")
        self.container_right =  ShadowGui.widgetBox(container, "", addSpace=False, orientation="vertical")

        self.ewp_box_1 = ShadowGui.widgetBox(self.container_left, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.ewp_box_1, self, "single_line_value", "Value", labelWidth=300, valueType=float, orientation="horizontal")

        self.ewp_box_2 = ShadowGui.widgetBox(self.container_left, "Values", addSpace=True, orientation="vertical")

        self.le_line_value_1 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_1", "Line 1", valueType=float, orientation="horizontal")
        self.le_line_value_2 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_2", "Line 2", valueType=float, orientation="horizontal")
        self.le_line_value_3 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_3", "Line 3", valueType=float, orientation="horizontal")
        self.le_line_value_4 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_4", "Line 4", valueType=float, orientation="horizontal")
        self.le_line_value_5 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_5", "Line 5", valueType=float, orientation="horizontal")
        self.le_line_value_6 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_6", "Line 6", valueType=float, orientation="horizontal")
        self.le_line_value_7 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_7", "Line 7", valueType=float, orientation="horizontal")
        self.le_line_value_8 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_8", "Line 8", valueType=float, orientation="horizontal")
        self.le_line_value_9 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_9", "Line 9", valueType=float, orientation="horizontal")
        self.le_line_value_10 = ShadowGui.lineEdit(self.ewp_box_2, self, "line_value_10", "Line 10", valueType=float, orientation="horizontal")

        self.ewp_box_3 = ShadowGui.widgetBox(self.container_left, "", addSpace=False, orientation="vertical")

        ShadowGui.lineEdit(self.ewp_box_3, self, "uniform_minimum", "Minimum Energy/Wavelength", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.ewp_box_3, self, "uniform_maximum", "Maximum Energy/Wavelength", labelWidth=300, valueType=float, orientation="horizontal")

        self.ewp_box_4 = ShadowGui.widgetBox(self.container_right, "Relative Intensities", addSpace=True, orientation="vertical")
        
        self.le_line_int_1 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_1", "Int 1", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_2 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_2", "Int 2", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_3 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_3", "Int 3", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_4 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_4", "Int 4", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_5 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_5", "Int 5", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_6 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_6", "Int 6", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_7 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_7", "Int 7", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_8 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_8", "Int 8", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_9 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_9", "Int 9", labelWidth=100, valueType=float, orientation="horizontal")
        self.le_line_int_10 = ShadowGui.lineEdit(self.ewp_box_4, self, "line_int_10", "Int 10", labelWidth=100, valueType=float, orientation="horizontal")


        self.ewp_box_6 = ShadowGui.widgetBox(energy_wavelength_box, "Gaussian", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(self.ewp_box_6, self, "gaussian_central_value", "Central Value", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.ewp_box_6, self, "gaussian_sigma", "Sigma", labelWidth=300, valueType=float, orientation="horizontal")

        gui.separator(self.ewp_box_6)

        ShadowGui.lineEdit(self.ewp_box_6, self, "gaussian_minimum", "Minimum Energy/Wavelength", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.ewp_box_6, self, "gaussian_maximum", "Maximum Energy/Wavelength", labelWidth=300, valueType=float, orientation="horizontal")

        self.ewp_box_7 = ShadowGui.widgetBox(energy_wavelength_box, "User Defined", addSpace=True, orientation="vertical")

        file_box = ShadowGui.widgetBox(self.ewp_box_7, "", addSpace=True, orientation="horizontal", width=510, height=25)

        self.le_user_defined_file = ShadowGui.lineEdit(file_box, self, "user_defined_file", "Spectrum File",
                                                    labelWidth=100, valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectFile)

        gui.separator(self.ewp_box_7)

        ShadowGui.lineEdit(self.ewp_box_7, self, "user_defined_minimum", "Minimum Energy/Wavelength", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.ewp_box_7, self, "user_defined_maximum", "Maximum Energy/Wavelength", labelWidth=300, valueType=float, orientation="horizontal")

        self.set_PhotonEnergyDistribution()

        polarization_box = ShadowGui.widgetBox(left_box_3, "Polarization", addSpace=True, orientation="vertical", height=145)

        gui.comboBox(polarization_box, self, "polarization", label="Polarization", labelWidth=475,
                     items=["No", "Yes"], orientation="horizontal", callback=self.set_Polarization)

        self.ewp_box_8 = ShadowGui.widgetBox(polarization_box, "", addSpace=True, orientation="vertical")

        gui.comboBox(self.ewp_box_8, self, "coherent_beam", label="Coherent Beam", labelWidth=475,
                     items=["No", "Yes"], orientation="horizontal")

        ShadowGui.lineEdit(self.ewp_box_8, self, "phase_diff", "Phase Difference [deg,0=linear,+90=ell/right]", labelWidth=330, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(self.ewp_box_8, self, "polarization_degree", "Polarization Degree [cos_s/(cos_s+sin_s)]", labelWidth=330, valueType=float, orientation="horizontal")

        self.set_Polarization()

        ##############################

        left_box_4 = ShadowGui.widgetBox(self.controlArea, "Reject Rays", addSpace=True, orientation="vertical")
        left_box_4.setFixedHeight(110)

        gui.comboBox(left_box_4, self, "optimize_source", label="Optimize Source", items=["No", "Using file with phase/space volume)", "Using file with slit/acceptance"], labelWidth=200,
                     callback=self.set_OptimizeSource, orientation="horizontal")
        self.optimize_file_name_box = ShadowGui.widgetBox(left_box_4, "", addSpace=False, orientation="vertical")

        file_box = ShadowGui.widgetBox(self.optimize_file_name_box, "", addSpace=True, orientation="horizontal", height=25)

        self.le_optimize_file_name = ShadowGui.lineEdit(file_box, self, "optimize_file_name", "File Name", labelWidth=150,  valueType=str, orientation="horizontal")

        pushButton = gui.button(file_box, self, "...")
        pushButton.clicked.connect(self.selectOptimizeFile)

        ShadowGui.lineEdit(self.optimize_file_name_box, self, "max_number_of_rejected_rays", "Max number of rejected rays (set 0 for infinity)", labelWidth=300,  valueType=int, orientation="horizontal")

        self.set_OptimizeSource()

        button_box = ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

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

    def set_Sampling(self):
        self.sample_box_1.setVisible(self.sampling != 1)
        self.sample_box_2.setVisible(self.sampling == 1 or self.sampling == 3)
        self.sample_box_3.setVisible(self.sampling == 1 or self.sampling == 2)
        #self.sample_box_4.setVisible(self.sampling == 1 or self.sampling == 3)

    def set_SpatialType(self):
        self.spatial_type_box_1.setVisible(self.spatial_type == 1)
        self.spatial_type_box_2.setVisible(self.spatial_type == 2)
        self.spatial_type_box_3.setVisible(self.spatial_type == 3)

    def set_AngularDistribution(self):
        self.angular_distribution_box_1.setVisible(self.angular_distribution == 0 or self.angular_distribution == 1)
        self.angular_distribution_box_2.setVisible(self.angular_distribution == 2)
        self.angular_distribution_box_3.setVisible(self.angular_distribution == 3)

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
            self.le_line_value_1.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_2.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_3.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_4.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_5.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_6.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_7.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_8.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_9.parentWidget().children()[1].setFixedWidth(300)
            self.le_line_value_10.parentWidget().children()[1].setFixedWidth(300)

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
        self.le_user_defined_file.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Open Spectrum File", ".", "*.dat; *.txt"))

    def selectOptimizeFile(self):
        self.le_optimize_file_name.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Open Optimize Source Parameters File", ".", "*.*"))

    def runShadowSource(self):
        #self.error(self.error_id)
        self.setStatusMessage("")
        self.progressBarInit()

        try:
            self.checkFields()

            shadow_src = ShadowSource.create_src()

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

            if self.photon_energy_distribution == 4:
                self.generate_gaussian_spectrum(beam_out)
            elif self.photon_energy_distribution == 5:
                self.generate_user_defined_spectrum(beam_out)

            self.fix_Intensity(beam_out)

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

            #self.error_id = self.error_id + 1
            #self.error(self.error_id, "Exception occurred: " + str(exception))

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

        #sampled_spectrum = numpy.random.normal(loc=self.gaussian_central_value, scale=self.gaussian_sigma, size=len(beam_out._beam.rays))

        for index in range(0, len(beam_out._beam.rays)):
            if self.units == 0:
                beam_out._beam.rays[index, 10] = ShadowPhysics.getShadowKFromEnergy(energy=sampled_spectrum[index])
            else:
                beam_out._beam.rays[index, 10] = ShadowPhysics.getShadowKFromWavelength(wavelength=sampled_spectrum[index])

    #########################################################################################

    def generate_user_defined_spectrum(self, beam_out):
        spectrum = self.extract_spectrum_from_file(self.user_defined_file)

        sampled_spectrum = self.sample_from_spectrum(spectrum, len(beam_out._beam.rays))

        for index in range(0, len(beam_out._beam.rays)):
            if self.units == 0:
                beam_out._beam.rays[index, 10] = ShadowPhysics.getShadowKFromEnergy(energy=sampled_spectrum[index])
            else:
                beam_out._beam.rays[index, 10] = ShadowPhysics.getShadowKFromWavelength(wavelength=sampled_spectrum[index])

    def extract_spectrum_from_file(self, spectrum_file_name):
        spectrum = []

        try:
            spectrum_file = open(spectrum_file_name, "r")

            rows = spectrum_file.readlines()

            for row in rows:

                if not row.strip() == "":
                    values = row.split()

                    if not len(values) == 2: raise Exception("Malformed file, must be: <energy> <spaces> <intensity>")

                    energy = float(values[0].strip())
                    intensity = float(values[1].strip())

                    if energy > self.user_defined_minimum and energy <= self.user_defined_maximum:
                        spectrum.append([energy, intensity])

        except Exception as err:
            raise Exception("Problems reading spectrum file: {0}".format(err))
        except:
            raise Exception("Unexpected error reading spectrum file: ", sys.exc_info()[0])

        spectrum.insert(0, [self.user_defined_minimum, 0.0])

        return numpy.array(spectrum)

    def sample_from_spectrum(self, spectrum, npoints):
        # normalize distribution function
        spectrum[:, 1] /= spectrum[:, 1].sum()
        #calculate the cumulative distribution function
        a_cdf = numpy.cumsum(spectrum[:, 1])
        # create randomly distributed npoints
        rd = numpy.random.rand(npoints)
        # evaluate rd following the inverse of cdf
        return numpy.interp(rd, a_cdf, spectrum[:, 0])

    #########################################################################################

    # WEIRD MEMORY INITIALIZATION BY FORTRAN. JUST A FIX.
    def fix_Intensity(self, beam_out):
        if self.polarization == 0:
            for index in range(0, len(beam_out._beam.rays)):
                beam_out._beam.rays[index, 15] = 0
                beam_out._beam.rays[index, 16] = 0
                beam_out._beam.rays[index, 17] = 0

    def sendNewBeam(self, trigger):
        if trigger and trigger.new_beam == True:
            self.runShadowSource()

    def setupUI(self):
        self.set_OptimizeSource()
        self.set_Sampling()
        self.set_SpatialType()
        self.set_AngularDistribution()
        self.set_Depth()
        self.set_PhotonEnergyDistribution()
        self.set_Polarization()

    def checkFields(self):

        if self.sampling != 1:
            self.number_of_rays = ShadowGui.checkPositiveNumber(self.number_of_rays, "Number of Random rays")
            self.seed = ShadowGui.checkPositiveNumber(self.seed, "Seed")

        if self.sampling == 1:
            self.grid_points_in_xfirst = ShadowGui.checkPositiveNumber(self.grid_points_in_xfirst, "Grid Points in X'")
            self.grid_points_in_zfirst = ShadowGui.checkPositiveNumber(self.grid_points_in_zfirst, "Grid Points in Z'")
            self.grid_points_in_x = ShadowGui.checkPositiveNumber(self.grid_points_in_x, "Grid Points in X")
            self.grid_points_in_y = ShadowGui.checkPositiveNumber(self.grid_points_in_y, "Grid Points in Y")
            self.grid_points_in_z = ShadowGui.checkPositiveNumber(self.grid_points_in_z, "Grid Points in Z")
        elif self.sampling == 2:
            self.grid_points_in_x = ShadowGui.checkPositiveNumber(self.grid_points_in_x, "Grid Points in X")
            self.grid_points_in_y = ShadowGui.checkPositiveNumber(self.grid_points_in_y, "Grid Points in Y")
            self.grid_points_in_z = ShadowGui.checkPositiveNumber(self.grid_points_in_z, "Grid Points in Z")
        elif self.sampling == 3:
            self.grid_points_in_xfirst = ShadowGui.checkPositiveNumber(self.grid_points_in_xfirst, "Grid Points in X'")
            self.grid_points_in_zfirst = ShadowGui.checkPositiveNumber(self.grid_points_in_zfirst, "Grid Points in Z'")

        if self.spatial_type == 1:
            self.rect_width = ShadowGui.checkPositiveNumber(self.rect_width, "Width")
            self.rect_height = ShadowGui.checkPositiveNumber(self.rect_height, "Height")
        elif self.spatial_type == 2:
            self.ell_semiaxis_x = ShadowGui.checkPositiveNumber(self.ell_semiaxis_x, "Semi-Axis X")
            self.ell_semiaxis_z = ShadowGui.checkPositiveNumber(self.ell_semiaxis_z, "Semi-Axis Z")
        elif self.spatial_type == 3:
            self.gauss_sigma_x = ShadowGui.checkPositiveNumber(self.gauss_sigma_x, "Sigma X")
            self.gauss_sigma_z = ShadowGui.checkPositiveNumber(self.gauss_sigma_z, "Sigma Z")

        if self.angular_distribution == 0 or self.angular_distribution == 1:
            self.horizontal_div_x_plus = ShadowGui.checkPositiveNumber(self.horizontal_div_x_plus, "Horizontal Divergence X(+)")
            self.horizontal_div_x_minus = ShadowGui.checkPositiveNumber(self.horizontal_div_x_minus, "Horizontal Divergence X(-)")
            self.vertical_div_z_plus = ShadowGui.checkPositiveNumber(self.vertical_div_z_plus, "Vertical Divergence Z(+)")
            self.vertical_div_z_minus = ShadowGui.checkPositiveNumber(self.vertical_div_z_minus, "Vertical Divergence Z(-)")
        elif self.angular_distribution == 2:
            self.horizontal_lim_x_plus = ShadowGui.checkPositiveNumber(self.horizontal_lim_x_plus, "Horizontal Limit X(+)")
            self.horizontal_lim_x_minus = ShadowGui.checkPositiveNumber(self.horizontal_lim_x_minus, "Horizontal Limit X(-)")
            self.vertical_lim_z_plus = ShadowGui.checkPositiveNumber(self.vertical_lim_z_plus, "Vertical Limit Z(+)")
            self.vertical_lim_z_minus = ShadowGui.checkPositiveNumber(self.vertical_lim_z_minus, "Vertical Limit Z(-)")
            self.horizontal_sigma_x = ShadowGui.checkPositiveNumber(self.horizontal_sigma_x, "Horizontal Sigma (X)")
            self.vertical_sigma_z = ShadowGui.checkPositiveNumber(self.vertical_sigma_z, "Vertical Sigma (Z)")
        elif self.angular_distribution == 3:
            self.cone_internal_half_aperture = ShadowGui.checkPositiveNumber(self.cone_internal_half_aperture, "Cone Internal Half-Aperture")
            self.cone_external_half_aperture = ShadowGui.checkPositiveNumber(self.cone_external_half_aperture, "Cone External Half-Aperture")

        if self.depth == 1:
            self.source_depth_y = ShadowGui.checkPositiveNumber(self.source_depth_y, "Source Depth (Y)")
        elif self.depth == 2:
            self.sigma_y = ShadowGui.checkPositiveNumber(self.sigma_y, "Sigma Y")

        if self.photon_energy_distribution == 0:
            self.single_line_value = ShadowGui.checkPositiveNumber(self.single_line_value, "Single Line Value")
        elif self.photon_energy_distribution == 1:
            if self.number_of_lines >= 1:
                self.line_value_1 = ShadowGui.checkPositiveNumber(self.line_value_1, "Line 1")
            if self.number_of_lines >= 2:
                self.line_value_2 = ShadowGui.checkPositiveNumber(self.line_value_2, "Line 2")
            if self.number_of_lines >= 3:
                self.line_value_3 = ShadowGui.checkPositiveNumber(self.line_value_3, "Line 3")
            if self.number_of_lines >= 4:
                self.line_value_4 = ShadowGui.checkPositiveNumber(self.line_value_4, "Line 4")
            if self.number_of_lines >= 5:
                self.line_value_5 = ShadowGui.checkPositiveNumber(self.line_value_5, "Line 5")
            if self.number_of_lines >= 6:
                self.line_value_6 = ShadowGui.checkPositiveNumber(self.line_value_6, "Line 6")
            if self.number_of_lines >= 7:
                self.line_value_7 = ShadowGui.checkPositiveNumber(self.line_value_7, "Line 7")
            if self.number_of_lines >= 8:
                self.line_value_8 = ShadowGui.checkPositiveNumber(self.line_value_8, "Line 8")
            if self.number_of_lines >= 9:
                self.line_value_9 = ShadowGui.checkPositiveNumber(self.line_value_9, "Line 9")
            if self.number_of_lines == 10:
                self.line_value_10 = ShadowGui.checkPositiveNumber(self.line_value_10, "Line 10")
        elif self.photon_energy_distribution == 2:
            self.uniform_minimum = ShadowGui.checkPositiveNumber(self.uniform_minimum, "Minimum Energy/Wavelength")
            self.uniform_maximum = ShadowGui.checkStrictlyPositiveNumber(self.uniform_maximum, "Maximum Energy/Wavelength")

            if self.uniform_minimum >= self.uniform_maximum: raise Exception("Minimum Energy/Wavelength should be less than Maximum Energy/Wavelength")
        elif self.photon_energy_distribution == 3:
            if self.number_of_lines >= 1:
                self.line_value_1 = ShadowGui.checkPositiveNumber(self.line_value_1, "Line 1")
                self.line_int_1 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 1")
            if self.number_of_lines >= 2:
                self.line_value_2 = ShadowGui.checkPositiveNumber(self.line_value_2, "Line 2")
                self.line_int_2 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 2")
            if self.number_of_lines >= 3:
                self.line_value_3 = ShadowGui.checkPositiveNumber(self.line_value_3, "Line 3")
                self.line_int_3 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 3")
            if self.number_of_lines >= 4:
                self.line_value_4 = ShadowGui.checkPositiveNumber(self.line_value_4, "Line 4")
                self.line_int_4 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 4")
            if self.number_of_lines >= 5:
                self.line_value_5 = ShadowGui.checkPositiveNumber(self.line_value_5, "Line 5")
                self.line_int_5 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 5")
            if self.number_of_lines >= 6:
                self.line_value_6 = ShadowGui.checkPositiveNumber(self.line_value_6, "Line 6")
                self.line_int_6 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 6")
            if self.number_of_lines >= 7:
                self.line_value_7 = ShadowGui.checkPositiveNumber(self.line_value_7, "Line 7")
                self.line_int_7 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 7")
            if self.number_of_lines >= 8:
                self.line_value_8 = ShadowGui.checkPositiveNumber(self.line_value_8, "Line 8")
                self.line_int_8 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 8")
            if self.number_of_lines >= 9:
                self.line_value_9 = ShadowGui.checkPositiveNumber(self.line_value_9, "Line 9")
                self.line_int_9 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 9")
            if self.number_of_lines == 10:
                self.line_value_10 = ShadowGui.checkPositiveNumber(self.line_value_10, "Line 10")
                self.line_int_10 = ShadowGui.checkPositiveNumber(self.line_int_1, "Int 10")
        elif self.photon_energy_distribution == 4:
            self.gaussian_central_value = ShadowGui.checkStrictlyPositiveNumber(self.gaussian_central_value, "Central Value")
            self.gaussian_sigma = ShadowGui.checkStrictlyPositiveNumber(self.gaussian_sigma, "Sigma")
            self.gaussian_minimum = ShadowGui.checkPositiveNumber(self.gaussian_minimum, "Minimum Energy/Wavelength")
            self.gaussian_maximum = ShadowGui.checkStrictlyPositiveNumber(self.gaussian_maximum, "Maximum Energy/Wavelength")

            if self.gaussian_minimum >= self.gaussian_maximum: raise Exception("Minimum Energy/Wavelength should be less than Maximum Energy/Wavelength")

        elif self.photon_energy_distribution == 5:
            self.user_defined_file = ShadowGui.checkFile(self.user_defined_file)
            self.user_defined_minimum = ShadowGui.checkPositiveNumber(self.user_defined_minimum, "Minimum Energy/Wavelength")
            self.user_defined_maximum = ShadowGui.checkStrictlyPositiveNumber(self.user_defined_maximum, "Maximum Energy/Wavelength")

        if self.optimize_source > 0:
            self.max_number_of_rejected_rays = ShadowGui.checkPositiveNumber(self.max_number_of_rejected_rays,
                                                                             "Max number of rejected rays")
            self.optimize_file_name = ShadowGui.checkFile(self.optimize_file_name)

    def populateFields(self, shadow_src):
        if self.sampling != 1:
            shadow_src.src.NPOINT = self.number_of_rays
            shadow_src.src.ISTAR1 = self.seed

        shadow_src.src.FGRID = self.sampling

        if self.sampling > 0:
            shadow_src.src.IDO_VX = self.grid_points_in_xfirst
            shadow_src.src.IDO_VZ = self.grid_points_in_zfirst
            shadow_src.src.IDO_X_S = self.grid_points_in_x
            shadow_src.src.IDO_Y_S = self.grid_points_in_y
            shadow_src.src.IDO_Z_S = self.grid_points_in_z
            #shadow_src.src.N_CIRCLE = self.radial_grid_points
            #shadow_src.src.N_CONE = self.concentrical_grid_points

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
            shadow_src.src.HDIV1 = self.horizontal_lim_x_plus
            shadow_src.src.HDIV2 = self.horizontal_lim_x_minus
            shadow_src.src.VDIV1 = self.vertical_lim_z_plus
            shadow_src.src.VDIV2 = self.vertical_lim_z_minus
            shadow_src.src.SIGDIX = self.horizontal_sigma_x
            shadow_src.src.SIGDIZ = self.vertical_sigma_z
        elif self.angular_distribution == 3:
            shadow_src.src.FDISTR = 5
            shadow_src.src.CONE_MIN = self.cone_internal_half_aperture
            shadow_src.src.CONE_MAX = self.cone_external_half_aperture

        shadow_src.src.FSOURCE_DEPTH = self.depth

        if self.depth == 1:
            shadow_src.src.WYSOU = self.source_depth_y
        elif self.depth == 2:
            shadow_src.src.SIGMAY = self.sigma_y

        shadow_src.src.F_COLOR = self.photon_energy_distribution + 1
        shadow_src.src.F_PHOT = self.units

        if self.photon_energy_distribution == 0:
            shadow_src.src.PH1 = self.single_line_value
        elif self.photon_energy_distribution == 1:
            shadow_src.src.N_COLOR = self.number_of_lines
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
            shadow_src.src.N_COLOR = self.number_of_lines
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

        shadow_src.src.F_OPD = self.store_optical_paths
        shadow_src.src.F_BOUND_SOUR = self.optimize_source
        shadow_src.src.FILE_BOUND = bytes(self.optimize_file_name, 'utf-8')
        shadow_src.src.NTOTALPOINT = self.max_number_of_rejected_rays

    def deserialize(self, shadow_file):
        if not shadow_file is None:
            try:
                self.number_of_rays=int(shadow_file.getProperty("NPOINT"))
                self.seed=int(shadow_file.getProperty("ISTAR1"))

                self.sampling = int(shadow_file.getProperty("FGRID"))

                if self.sampling>0:
                    self.grid_points_in_xfirst = int(shadow_file.getProperty("IDO_VX") )
                    self.grid_points_in_zfirst = int(shadow_file.getProperty("IDO_VZ"))
                    self.grid_points_in_x = int(shadow_file.getProperty("IDO_X_S"))
                    self.grid_points_in_y = int(shadow_file.getProperty("IDO_Y_S"))
                    self.grid_points_in_z = int(shadow_file.getProperty("IDO_Z_S"))
                    self.radial_grid_points = int(shadow_file.getProperty("N_CIRCLE"))
                    self.concentrical_grid_points = int(shadow_file.getProperty("N_CONE"))

                    self.sampling = 0 # NO MORE SUPPORTED OTHER THAN RANDOM/RANDOM

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
                    self.number_of_lines = int(shadow_file.getProperty("N_COLOR"))
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
                    self.number_of_lines = int(shadow_file.getProperty("N_COLOR"))
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

                self.store_optical_paths = int(shadow_file.getProperty("F_OPD"))

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
