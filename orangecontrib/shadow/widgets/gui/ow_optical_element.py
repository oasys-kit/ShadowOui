import sys, math, os
import numpy
from orangewidget import gui, widget
from orangewidget.settings import Setting
from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_generic_element
from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowPreProcessorData, \
    ShadowOpticalElement, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowGui, ShadowPhysics, ConfirmDialog

class GraphicalOptions:
    is_empty = False
    is_curved = False
    is_mirror=False
    is_screen_slit=False
    is_crystal=False
    is_grating=False
    is_spheric= False
    is_ellipsoidal=False
    is_toroidal=False
    is_paraboloid=False
    is_hyperboloid=False
    is_cone=False
    is_codling_slit=False
    is_polynomial=False
    is_conic_coefficients=False

    def __init__(self,
                 is_empty = False,
                 is_curved=False,
                 is_mirror=False,
                 is_crystal=False,
                 is_grating=False,
                 is_screen_slit=False,
                 is_spheric=False,
                 is_ellipsoidal=False,
                 is_toroidal=False,
                 is_paraboloid=False,
                 is_hyperboloid=False,
                 is_cone=False,
                 is_codling_slit=False,
                 is_polynomial=False,
                 is_conic_coefficients=False):
        self.is_empty = is_empty
        self.is_curved = is_curved
        self.is_mirror=is_mirror
        self.is_crystal=is_crystal
        self.is_grating=is_grating
        self.is_screen_slit=is_screen_slit
        self.is_spheric=is_spheric
        self.is_ellipsoidal=is_ellipsoidal
        self.is_toroidal=is_toroidal
        self.is_paraboloid=is_paraboloid
        self.is_hyperboloid=is_hyperboloid
        self.is_cone=is_cone
        self.is_codling_slit=is_codling_slit
        self.is_polynomial=is_polynomial
        self.is_conic_coefficients=is_conic_coefficients


class OpticalElement(ow_generic_element.GenericElement):

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorData"),
              ("PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorData")]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"},
               {"name":"Trigger",
                "type": ShadowTriggerIn,
                "doc":"Feedback signal to start a new beam simulation",
                "id":"Trigger"}]

    input_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    ONE_ROW_HEIGHT = 65
    TWO_ROW_HEIGHT = 110
    THREE_ROW_HEIGHT = 170

    TABS_AREA_HEIGHT = 480
    CONTROL_AREA_HEIGHT = 440
    CONTROL_AREA_WIDTH = 470
    INNER_BOX_WIDTH_L3=387
    INNER_BOX_WIDTH_L2=400
    INNER_BOX_WIDTH_L1=418
    INNER_BOX_WIDTH_L0=442

    graphical_options=None

    source_plane_distance = Setting(10.0)
    image_plane_distance = Setting(20.0)
    incidence_angle_deg = Setting(88.0)
    incidence_angle_mrad = Setting(0.0)
    reflection_angle_deg = Setting(88.0)
    reflection_angle_mrad = Setting(0.0)
    mirror_orientation_angle = Setting(0)

    ##########################################
    # BASIC SETTING
    ##########################################

    conic_coefficient_0 = Setting(0.0)
    conic_coefficient_1 = Setting(0.0)
    conic_coefficient_2 = Setting(0.0)
    conic_coefficient_3 = Setting(0.0)
    conic_coefficient_4 = Setting(0.0)
    conic_coefficient_5 = Setting(0.0)
    conic_coefficient_6 = Setting(0.0)
    conic_coefficient_7 = Setting(0.0)
    conic_coefficient_8 = Setting(0.0)
    conic_coefficient_9 = Setting(0.0)

    surface_shape_parameters = Setting(0)
    spherical_radius = Setting(0.0)

    torus_major_radius = Setting(0.0)
    torus_minor_radius = Setting(0.0)
    toroidal_mirror_pole_location=Setting(0.0)

    ellipse_hyperbola_semi_major_axis=Setting(0.0)
    ellipse_hyperbola_semi_minor_axis=Setting(0.0)
    angle_of_majax_and_pole=Setting(0.0)

    paraboloid_parameter=Setting(0.0)
    focus_location=Setting(0.0)

    focii_and_continuation_plane = Setting(0)

    object_side_focal_distance = Setting(0.0)
    image_side_focal_distance = Setting(0.0)
    incidence_angle_respect_to_normal = Setting(0.0)

    surface_curvature = Setting(0)
    is_cylinder = Setting(1)
    cylinder_orientation = Setting(0.0)
    reflectivity_type = Setting(0)
    source_of_reflectivity = Setting(0)
    file_prerefl = Setting("reflec.dat")
    alpha = Setting(0.0)
    gamma = Setting(0.0)
    file_prerefl_m = Setting("reflec.dat")
    m_layer_tickness = Setting(0.0)

    is_infinite = Setting(0)
    mirror_shape = Setting(0)
    dim_x_plus = Setting(0.0)
    dim_x_minus = Setting(0.0)
    dim_y_plus = Setting(0.0)
    dim_y_minus = Setting(0.0)

    diffraction_geometry = Setting(0)
    diffraction_calculation = Setting(0)
    file_diffraction_profile = Setting("diffraction_profile.dat")
    file_crystal_parameters = Setting("reflec.dat")
    crystal_auto_setting = Setting(0)
    units_in_use = Setting(0)
    photon_energy = Setting(5.0)
    photon_wavelength = Setting(5000.0)

    mosaic_crystal = Setting(0)
    angle_spread_FWHM = Setting(0.0)
    thickness = Setting(0.0)
    seed_for_mosaic = Setting(1626261131)

    johansson_geometry = Setting(0)
    johansson_radius = Setting(0.0)

    asymmetric_cut = Setting(0)
    planes_angle = Setting(0.0)
    below_onto_bragg_planes = Setting(-1)

    grating_diffraction_order = Setting(-1.0)
    grating_auto_setting = Setting(0)
    grating_units_in_use = Setting(0)
    grating_photon_energy = Setting(5.0)
    grating_photon_wavelength = Setting(5000.0)

    grating_ruling_type = Setting(0)
    grating_ruling_density = Setting(12000.0)

    grating_holo_left_distance = Setting(300.0)
    grating_holo_left_incidence_angle = Setting(-20.0)
    grating_holo_left_azimuth_from_y = Setting(0.0)
    grating_holo_right_distance = Setting(300.0)
    grating_holo_right_incidence_angle = Setting(-20.0)
    grating_holo_right_azimuth_from_y = Setting(0.0)
    grating_holo_pattern_type = Setting(0)
    grating_holo_source_type = Setting(0)
    grating_holo_cylindrical_source = Setting(0)
    grating_holo_recording_wavelength = Setting(4879.86)

    grating_groove_pole_distance = Setting(0.0)
    grating_groove_pole_azimuth_from_y = Setting(0.0)
    grating_coma_correction_factor = Setting(0.0)

    grating_poly_coeff_1 = Setting(0.0)
    grating_poly_coeff_2 = Setting(0.0)
    grating_poly_coeff_3 = Setting(0.0)
    grating_poly_coeff_4 = Setting(0.0)
    grating_poly_signed_absolute = Setting(0)

    grating_mount_type = Setting(0)

    grating_hunter_blaze_angle = Setting(0.0)
    grating_hunter_grating_selected = Setting(0)
    grating_hunter_monochromator_length = Setting(0.0)
    grating_hunter_distance_between_beams = Setting(0.0)

    ##########################################
    # ADVANCED SETTING
    ##########################################

    modified_surface = Setting(0)

    # surface error
    ms_type_of_defect = Setting(0)
    ms_defect_file_name = Setting(NONE_SPECIFIED)
    ms_ripple_wavel_x = Setting(0.0)
    ms_ripple_wavel_y = Setting(0.0)
    ms_ripple_ampli_x = Setting(0.0)
    ms_ripple_ampli_y = Setting(0.0)
    ms_ripple_phase_x = Setting(0.0)
    ms_ripple_phase_y = Setting(0.0)

    # faceted surface
    ms_file_facet_descr = Setting(NONE_SPECIFIED)
    ms_lattice_type = Setting(0)
    ms_orientation = Setting(0)
    ms_intercept_to_use = Setting(0)
    ms_facet_width_x = Setting(10.0)
    ms_facet_phase_x = Setting(0.0)
    ms_dead_width_x_minus = Setting(0.0)
    ms_dead_width_x_plus = Setting(0.0)
    ms_facet_width_y = Setting(10.0)
    ms_facet_phase_y = Setting(0.0)
    ms_dead_width_y_minus = Setting(0.0)
    ms_dead_width_y_plus = Setting(0.0)

    # surface roughness
    ms_file_surf_roughness = Setting(NONE_SPECIFIED)
    ms_roughness_rms_x = Setting(0.0)
    ms_roughness_rms_y = Setting(0.0)

    # kumakhov lens
    ms_specify_rz2 = Setting(0)
    ms_file_with_parameters_rz = Setting(NONE_SPECIFIED)
    ms_file_with_parameters_rz2 = Setting(NONE_SPECIFIED)
    ms_save_intercept_bounces = Setting(0)

    # segmented mirror
    ms_number_of_segments_x = Setting(1)
    ms_number_of_segments_y = Setting(1)
    ms_length_of_segments_x = Setting(0.0)
    ms_length_of_segments_y = Setting(0.0)
    ms_file_orientations = Setting(NONE_SPECIFIED)
    ms_file_polynomial = Setting(NONE_SPECIFIED)

    #####

    mirror_movement = Setting(0)

    mm_mirror_offset_x = Setting(0.0)
    mm_mirror_rotation_x = Setting(0.0)
    mm_mirror_offset_y = Setting(0.0)
    mm_mirror_rotation_y = Setting(0.0)
    mm_mirror_offset_z = Setting(0.0)
    mm_mirror_rotation_z = Setting(0.0)

    #####

    source_movement = Setting(0)
    sm_angle_of_incidence = Setting(0.0)
    sm_distance_from_mirror = Setting(0.0)
    sm_z_rotation = Setting(0.0)
    sm_offset_x_mirr_ref_frame = Setting(0.0)
    sm_offset_y_mirr_ref_frame = Setting(0.0)
    sm_offset_z_mirr_ref_frame = Setting(0.0)
    sm_offset_x_source_ref_frame = Setting(0.0)
    sm_offset_y_source_ref_frame = Setting(0.0)
    sm_offset_z_source_ref_frame = Setting(0.0)
    sm_rotation_around_x = Setting(0.0)
    sm_rotation_around_y = Setting(0.0)
    sm_rotation_around_z = Setting(0.0)

    #####

    file_to_write_out = Setting(3)
    write_out_inc_ref_angles = Setting(0)

    ##########################################
    # SCREEN/SLIT SETTING
    ##########################################

    aperturing = Setting(0)
    open_slit_solid_stop = Setting(0)
    aperture_shape = Setting(0)
    slit_width_xaxis = Setting(0.0)
    slit_height_zaxis = Setting(0.0)
    slit_center_xaxis = Setting(0.0)
    slit_center_zaxis = Setting(0.0)
    external_file_with_coordinate=Setting(NONE_SPECIFIED)
    absorption = Setting(0)
    thickness = Setting(0.0)
    opt_const_file_name = Setting(NONE_SPECIFIED)

    want_main_area=1

    def __init__(self, graphical_options = GraphicalOptions()):
        super().__init__()

        self.runaction = widget.OWAction("Run Shadow/Trace", self)
        self.runaction.triggered.connect(self.traceOpticalElement)
        self.addAction(self.runaction)

        self.graphical_options = graphical_options

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        upper_box = ShadowGui.widgetBox(self.controlArea, "Optical Element Orientation", addSpace=True, orientation="vertical")

        ShadowGui.lineEdit(upper_box, self, "source_plane_distance", "Source Plane Distance [cm]", labelWidth=300, valueType=float, orientation="horizontal")
        ShadowGui.lineEdit(upper_box, self, "image_plane_distance", "Image Plane Distance [cm]", labelWidth=300, valueType=float, orientation="horizontal")

        if self.graphical_options.is_screen_slit:
            tabs_setting = ShadowGui.tabWidget(self.controlArea)

            # graph tab
            tab_bas = ShadowGui.createTabPage(tabs_setting, "Basic Setting")
            tab_adv = ShadowGui.createTabPage(tabs_setting, "Advanced Setting")

            box_aperturing = ShadowGui.widgetBox(tab_bas, "Screen/Slit Shape", addSpace=True, orientation="vertical", height=240)

            gui.comboBox(box_aperturing, self, "aperturing", label="Aperturing", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_Aperturing, sendSelectedValue=False, orientation="horizontal")

            gui.separator(box_aperturing, width=self.INNER_BOX_WIDTH_L0)

            self.box_aperturing_shape = ShadowGui.widgetBox(box_aperturing, "", addSpace=False, orientation="vertical")

            gui.comboBox(self.box_aperturing_shape, self, "open_slit_solid_stop", label="Open slit/Solid stop", labelWidth=260,
                         items=["aperture/slit", "obstruction/stop"],
                         sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(self.box_aperturing_shape, self, "aperture_shape", label="Aperture shape", labelWidth=260,
                         items=["Rectangular", "Ellipse", "External"],
                         callback=self.set_ApertureShape, sendSelectedValue=False, orientation="horizontal")


            self.box_aperturing_shape_1 = ShadowGui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="horizontal")


            self.le_external_file_with_coordinate = ShadowGui.lineEdit(self.box_aperturing_shape_1, self, "external_file_with_coordinate", "External file with coordinate", labelWidth=185, valueType=str, orientation="horizontal")

            pushButton = gui.button(self.box_aperturing_shape_1, self, "...")
            pushButton.clicked.connect(self.selectExternalFileWithCoordinate)

            self.box_aperturing_shape_2 = ShadowGui.widgetBox(self.box_aperturing_shape, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.box_aperturing_shape_2, self, "slit_width_xaxis", "Slit width/x-axis [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.box_aperturing_shape_2, self, "slit_height_zaxis", "Slit height/z-axis [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.box_aperturing_shape_2, self, "slit_center_xaxis", "Slit center/x-axis [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.box_aperturing_shape_2, self, "slit_center_zaxis", "Slit center/z-axis [cm]", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_Aperturing()

            box_absorption = ShadowGui.widgetBox(tab_bas, "Absorption Parameters", addSpace=True, orientation="vertical", height=130)

            gui.comboBox(box_absorption, self, "absorption", label="Absorption", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_Absorption, sendSelectedValue=False, orientation="horizontal")

            gui.separator(box_absorption, width=self.INNER_BOX_WIDTH_L0)

            self.box_absorption_1 = ShadowGui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")
            self.box_absorption_1_empty = ShadowGui.widgetBox(box_absorption, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.box_absorption_1, self, "thickness", "Thickness [cm]", labelWidth=340, valueType=float, orientation="horizontal")

            file_box = ShadowGui.widgetBox(self.box_absorption_1, "", addSpace=True, orientation="horizontal", height=25)

            self.le_opt_const_file_name = ShadowGui.lineEdit(file_box, self, "opt_const_file_name", "Opt. const. file name", labelWidth=150, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectOptConstFileName)

            self.set_Absorption()

            ##########################################
            # ADVANCED SETTINGS
            ##########################################

            tabs_advanced_setting = gui.tabWidget(tab_adv)

            tab_adv_mir_mov = ShadowGui.createTabPage(tabs_advanced_setting, "O.E. Movement")
            tab_adv_sou_mov = ShadowGui.createTabPage(tabs_advanced_setting, "Source Movement")

            ##########################################
            #
            # TAB 2.2 - Mirror Movement
            #
            ##########################################

            mir_mov_box = ShadowGui.widgetBox(tab_adv_mir_mov, "O.E. Movement Parameters", addSpace=False, orientation="vertical", height=230)

            gui.comboBox(mir_mov_box, self, "mirror_movement", label="O.E. Movement", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_MirrorMovement, sendSelectedValue=False, orientation="horizontal")

            gui.separator(mir_mov_box, width=self.INNER_BOX_WIDTH_L1, height=10)

            self.mir_mov_box_1 = ShadowGui.widgetBox(mir_mov_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_x", "O.E. Offset X  [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_x", "O.E. Rotation X [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_y", "O.E. Offset Y [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_y", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_z", "O.E. Offset Z [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_z", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_MirrorMovement()

            ##########################################
            #
            # TAB 2.3 - Source Movement
            #
            ##########################################

            sou_mov_box = ShadowGui.widgetBox(tab_adv_sou_mov, "Source Movement Parameters", addSpace=False, orientation="vertical", height=400)

            gui.comboBox(sou_mov_box, self, "source_movement", label="Source Movement", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_SourceMovement, sendSelectedValue=False, orientation="horizontal")

            gui.separator(sou_mov_box, width=self.INNER_BOX_WIDTH_L1, height=10)

            self.sou_mov_box_1 = ShadowGui.widgetBox(sou_mov_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_angle_of_incidence", "Angle of Incidence [deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_distance_from_mirror", "Distance from O.E. [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_z_rotation", "Z-rotation [deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_mirr_ref_frame", "offset X [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_mirr_ref_frame", "offset Y [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_mirr_ref_frame", "offset Z [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_source_ref_frame", "offset X [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_source_ref_frame", "offset Y [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_source_ref_frame", "offset Z [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_x", "rotation [CCW, deg] around X", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_y", "rotation [CCW, deg] around Y", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_z", "rotation [CCW, deg] around Z", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_SourceMovement()

            ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="vertical", height=125)

        elif self.graphical_options.is_empty:
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            self.incidence_angle_deg_le = ShadowGui.lineEdit(upper_box, self, "incidence_angle_deg", "Incident Angle respect to the normal [deg]", labelWidth=300, callback=self.calculate_incidence_angle_mrad, valueType=float, orientation="horizontal")
            self.incidence_angle_rad_le = ShadowGui.lineEdit(upper_box, self, "incidence_angle_mrad", "... or with respect to the surface [mrad]", labelWidth=300, callback=self.calculate_incidence_angle_deg, valueType=float, orientation="horizontal")
            self.reflection_angle_deg_le = ShadowGui.lineEdit(upper_box, self, "reflection_angle_deg", "Reflection Angle respect to the normal [deg]", labelWidth=300, callback=self.calculate_reflection_angle_mrad, valueType=float, orientation="horizontal")
            self.reflection_angle_rad_le = ShadowGui.lineEdit(upper_box, self, "reflection_angle_mrad", "... or with respect to the surface [mrad]", labelWidth=300, callback=self.calculate_reflection_angle_deg, valueType=float, orientation="horizontal")

            gui.comboBox(upper_box, self, "mirror_orientation_angle", label="O.E. Orientation Angle [deg]", labelWidth=390,
                         items=[0, 90, 180, 270],
                         valueType=float,
                         sendSelectedValue=False, orientation="horizontal")

            tabs_setting = ShadowGui.tabWidget(self.controlArea)

            tab_adv = ShadowGui.createTabPage(tabs_setting, "Advanced Setting")

            ##########################################
            # ADVANCED SETTINGS
            ##########################################

            tabs_advanced_setting = gui.tabWidget(tab_adv)

            tab_adv_mir_mov = ShadowGui.createTabPage(tabs_advanced_setting, "O.E. Movement")
            tab_adv_sou_mov = ShadowGui.createTabPage(tabs_advanced_setting, "Source Movement")

            ##########################################
            #
            # TAB 2.2 - Mirror Movement
            #
            ##########################################

            mir_mov_box = ShadowGui.widgetBox(tab_adv_mir_mov, "O.E. Movement Parameters", addSpace=False, orientation="vertical", height=230)

            gui.comboBox(mir_mov_box, self, "mirror_movement", label="O.E. Movement", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_MirrorMovement, sendSelectedValue=False, orientation="horizontal")

            gui.separator(mir_mov_box, width=self.INNER_BOX_WIDTH_L1, height=10)

            self.mir_mov_box_1 = ShadowGui.widgetBox(mir_mov_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_x", "O.E. Offset X  [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_x", "O.E. Rotation X [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_y", "O.E. Offset Y [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_y", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_z", "O.E. Offset Z [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_z", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_MirrorMovement()

            ##########################################
            #
            # TAB 2.3 - Source Movement
            #
            ##########################################

            sou_mov_box = ShadowGui.widgetBox(tab_adv_sou_mov, "Source Movement Parameters", addSpace=False, orientation="vertical", height=400)

            gui.comboBox(sou_mov_box, self, "source_movement", label="Source Movement", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_SourceMovement, sendSelectedValue=False, orientation="horizontal")

            gui.separator(sou_mov_box, width=self.INNER_BOX_WIDTH_L1, height=10)

            self.sou_mov_box_1 = ShadowGui.widgetBox(sou_mov_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_angle_of_incidence", "Angle of Incidence [deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_distance_from_mirror", "Distance from O.E. [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_z_rotation", "Z-rotation [deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_mirr_ref_frame", "offset X [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_mirr_ref_frame", "offset Y [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_mirr_ref_frame", "offset Z [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_source_ref_frame", "offset X [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_source_ref_frame", "offset Y [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_source_ref_frame", "offset Z [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_x", "rotation [CCW, deg] around X", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_y", "rotation [CCW, deg] around Y", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_z", "rotation [CCW, deg] around Z", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_SourceMovement()

            ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="vertical", height=125)
        else:
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            self.incidence_angle_deg_le = ShadowGui.lineEdit(upper_box, self, "incidence_angle_deg", "Incident Angle respect to the normal [deg]", labelWidth=300, callback=self.calculate_incidence_angle_mrad, valueType=float, orientation="horizontal")
            self.incidence_angle_rad_le = ShadowGui.lineEdit(upper_box, self, "incidence_angle_mrad", "... or with respect to the surface [mrad]", labelWidth=300, callback=self.calculate_incidence_angle_deg, valueType=float, orientation="horizontal")
            self.reflection_angle_deg_le = ShadowGui.lineEdit(upper_box, self, "reflection_angle_deg", "Reflection Angle respect to the normal [deg]", labelWidth=300, callback=self.calculate_reflection_angle_mrad, valueType=float, orientation="horizontal")
            self.reflection_angle_rad_le = ShadowGui.lineEdit(upper_box, self, "reflection_angle_mrad", "... or with respect to the surface [mrad]", labelWidth=300, callback=self.calculate_reflection_angle_deg, valueType=float, orientation="horizontal")

            gui.comboBox(upper_box, self, "mirror_orientation_angle", label="O.E. Orientation Angle [deg]", labelWidth=390,
                         items=[0, 90, 180, 270],
                         valueType=float,
                         sendSelectedValue=False, orientation="horizontal")

            tabs_setting = ShadowGui.tabWidget(self.controlArea, height=self.TABS_AREA_HEIGHT)

            # graph tab
            tab_bas = ShadowGui.createTabPage(tabs_setting, "Basic Setting")
            tab_adv = ShadowGui.createTabPage(tabs_setting, "Advanced Setting")

            tabs_basic_setting = gui.tabWidget(tab_bas)

            if self.graphical_options.is_curved: tab_bas_shape = ShadowGui.createTabPage(tabs_basic_setting, "Surface Shape")
            if self.graphical_options.is_mirror: tab_bas_refl = ShadowGui.createTabPage(tabs_basic_setting, "Reflectivity")
            elif self.graphical_options.is_crystal: tab_bas_crystal = ShadowGui.createTabPage(tabs_basic_setting, "Crystal")
            elif self.graphical_options.is_grating: tab_bas_grating = ShadowGui.createTabPage(tabs_basic_setting, "Grating")
            tab_bas_dim = ShadowGui.createTabPage(tabs_basic_setting, "Dimensions")

            ##########################################
            #
            # TAB 1.1 - SURFACE SHAPE
            #
            ##########################################


            if self.graphical_options.is_curved:
                surface_box = ShadowGui.widgetBox(tab_bas_shape, "Surface Shape Parameter", addSpace=False, orientation="vertical")

                if self.graphical_options.is_conic_coefficients:
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_0", "c[1]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_1", "c[2]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_2", "c[3]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_3", "c[4]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_4", "c[5]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_5", "c[6]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_6", "c[7]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_7", "c[8]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_8", "c[9]", labelWidth=260, valueType=float, orientation="horizontal")
                    ShadowGui.lineEdit(surface_box, self, "conic_coefficient_9", "c[10]", labelWidth=260, valueType=float, orientation="horizontal")
                else:
                    gui.comboBox(surface_box, self, "surface_shape_parameters", label="Type", items=["internal/calculated", "external/user_defined"], labelWidth=240,
                                 callback=self.set_IntExt_Parameters, sendSelectedValue=False, orientation="horizontal")

                    self.surface_box_ext = ShadowGui.widgetBox(surface_box, "", addSpace=True, orientation="vertical", height=150)
                    gui.separator(self.surface_box_ext)

                    if self.graphical_options.is_spheric:
                        ShadowGui.lineEdit(self.surface_box_ext, self, "spherical_radius", "Spherical Radius [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                    elif self.graphical_options.is_toroidal:
                        ShadowGui.lineEdit(self.surface_box_ext, self, "torus_major_radius", "Torus Major Radius [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                        ShadowGui.lineEdit(self.surface_box_ext, self, "torus_minor_radius", "Torus Minor Radius [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                    elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                        ShadowGui.lineEdit(self.surface_box_ext, self, "ellipse_hyperbola_semi_major_axis", "Ellipse/Hyperbola semi-major Axis [cm]",  labelWidth=260, valueType=float, orientation="horizontal")
                        ShadowGui.lineEdit(self.surface_box_ext, self, "ellipse_hyperbola_semi_minor_axis", "Ellipse/Hyperbola semi-minor Axis [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                        ShadowGui.lineEdit(self.surface_box_ext, self, "angle_of_majax_and_pole", "Angle of MajAx and Pole [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                    elif self.graphical_options.is_paraboloid:
                        ShadowGui.lineEdit(self.surface_box_ext, self, "paraboloid_parameter", "Paraboloid parameter", labelWidth=260, valueType=float, orientation="horizontal")

                    self.surface_box_int = ShadowGui.widgetBox(surface_box, "", addSpace=True, orientation="vertical", height=150)

                    gui.comboBox(self.surface_box_int, self, "focii_and_continuation_plane", label="Focii and Continuation Plane", labelWidth=280,
                                 items=["Coincident", "Different"], callback=self.set_FociiCont_Parameters, sendSelectedValue=False, orientation="horizontal")

                    self.surface_box_int_2 = ShadowGui.widgetBox(self.surface_box_int, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                    self.surface_box_int_2_empty = ShadowGui.widgetBox(self.surface_box_int, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                    self.w_object_side_focal_distance = ShadowGui.lineEdit(self.surface_box_int_2, self, "object_side_focal_distance", "Object Side_Focal Distance [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                    self.w_image_side_focal_distance = ShadowGui.lineEdit(self.surface_box_int_2, self, "image_side_focal_distance", "Image Side_Focal Distance [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                    self.w_incidence_angle_respect_to_normal = ShadowGui.lineEdit(self.surface_box_int_2, self, "incidence_angle_respect_to_normal", "Incidence Angle Respect to Normal [deg]", labelWidth=260, valueType=float, orientation="horizontal")

                    if self.graphical_options.is_paraboloid:
                        gui.comboBox(self.surface_box_int, self, "focus_location", label="Focus location", labelWidth=280, items=["Image", "Source"], sendSelectedValue=False, orientation="horizontal")

                    self.set_IntExt_Parameters()

                    if self.graphical_options.is_toroidal:
                        surface_box_thorus = ShadowGui.widgetBox(surface_box, "", addSpace=True, orientation="vertical")

                        gui.comboBox(surface_box_thorus, self, "toroidal_mirror_pole_location", label="Torus pole location", labelWidth=145,
                                     items=["lower/outer (concave/concave)",
                                            "lower/inner (concave/convex)",
                                            "upper/inner (convex/concave)",
                                            "upper/outer (convex/convex)"],
                                     sendSelectedValue=False, orientation="horizontal")

                    surface_box_2 = ShadowGui.widgetBox(tab_bas_shape, "Cylinder Parameter", addSpace=True, orientation="vertical", height=125)

                    gui.comboBox(surface_box_2, self, "surface_curvature", label="Surface Curvature", items=["Concave", "Convex"], labelWidth=280, sendSelectedValue=False, orientation="horizontal")
                    gui.comboBox(surface_box_2, self, "is_cylinder", label="Cylindrical", items=["No", "Yes"],  labelWidth=350, callback=self.set_isCyl_Parameters, sendSelectedValue=False, orientation="horizontal")

                    self.surface_box_cyl = ShadowGui.widgetBox(surface_box_2, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                    self.surface_box_cyl_empty = ShadowGui.widgetBox(surface_box_2, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                    gui.comboBox(self.surface_box_cyl, self, "cylinder_orientation", label="Cylinder Orientation (deg) [CCW from X axis]", labelWidth=350,
                                 items=[0, 90, 180, 270],
                                 valueType=float,
                                 sendSelectedValue=False, orientation="horizontal")

                    self.set_isCyl_Parameters()

            ##########################################
            #
            # TAB 1.2 - REFLECTIVITY/CRYSTAL
            #
            ##########################################

            if self.graphical_options.is_mirror:
                refl_box = ShadowGui.widgetBox(tab_bas_refl, "Reflectivity Parameter", addSpace=False, orientation="vertical", height=190)

                gui.comboBox(refl_box, self, "reflectivity_type", label="Reflectivity", labelWidth=150,
                             items=["Not considered", "Full Polarization dependence", "No Polarization dependence (scalar)"],
                             callback=self.set_Refl_Parameters, sendSelectedValue=False, orientation="horizontal")

                gui.separator(refl_box, width=self.INNER_BOX_WIDTH_L2, height=10)

                self.refl_box_pol = ShadowGui.widgetBox(refl_box, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)
                self.refl_box_pol_empty = ShadowGui.widgetBox(refl_box, "", addSpace=True, orientation="vertical", width=self.INNER_BOX_WIDTH_L1)

                gui.comboBox(self.refl_box_pol, self, "source_of_reflectivity", label="Source of Reflectivity", labelWidth=200,
                             items=["file generated by PREREFL", "electric susceptibility", "file generated by pre_mlayer"],
                             callback=self.set_ReflSource_Parameters, sendSelectedValue=False, orientation="horizontal")

                self.refl_box_pol_1 = ShadowGui.widgetBox(self.refl_box_pol, "", addSpace=True, orientation="vertical")

                gui.separator(self.refl_box_pol_1, width=self.INNER_BOX_WIDTH_L1)

                file_box = ShadowGui.widgetBox(self.refl_box_pol_1, "", addSpace=True, orientation="horizontal", height=25)

                self.le_file_prerefl = ShadowGui.lineEdit(file_box, self, "file_prerefl", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFilePrerefl)

                self.refl_box_pol_2 = gui.widgetBox(self.refl_box_pol, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.refl_box_pol_2, self, "alpha", "Alpha [epsilon=(1-alpha)+i gamma]", labelWidth=260, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.refl_box_pol_2, self, "gamma", "Gamma [epsilon=(1-alpha)+i gamma]", labelWidth=260, valueType=float, orientation="horizontal")

                self.refl_box_pol_3 = gui.widgetBox(self.refl_box_pol, "", addSpace=True, orientation="vertical")

                file_box = ShadowGui.widgetBox(self.refl_box_pol_3, "", addSpace=True, orientation="horizontal", height=25)

                self.le_file_prerefl_m = ShadowGui.lineEdit(file_box, self, "file_prerefl_m", "File Name", labelWidth=100, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFilePrereflM)

                gui.comboBox(self.refl_box_pol_3, self, "m_layer_tickness", label="Mlayer thickness vary as cosine", labelWidth=350,
                             items=["No", "Yes"],
                             sendSelectedValue=False, orientation="horizontal")

                self.set_Refl_Parameters()
            elif self.graphical_options.is_crystal:
                tabs_crystal_setting = gui.tabWidget(tab_bas_crystal)

                self.tab_cryst_1 = ShadowGui.createTabPage(tabs_crystal_setting, "Diffraction Settings")
                self.tab_cryst_2 = ShadowGui.createTabPage(tabs_crystal_setting, "Geometric Setting")

                crystal_box = ShadowGui.widgetBox(self.tab_cryst_1, "Diffraction Parameters", addSpace=True,
                                                  orientation="vertical", height=240)

                gui.comboBox(crystal_box, self, "diffraction_geometry", label="Diffraction Geometry", labelWidth=300,
                             items=["Bragg", "Laue"],
                             sendSelectedValue=False, orientation="horizontal")

                gui.comboBox(crystal_box, self, "diffraction_calculation", label="Diffraction Profile", labelWidth=300,
                             items=["Calculated", "User Defined"],
                             sendSelectedValue=False, orientation="horizontal",
                             callback=self.set_DiffractionCalculation)

                gui.separator(crystal_box, height=10)

                self.crystal_box_1 = ShadowGui.widgetBox(crystal_box, "", addSpace=True, orientation="vertical",
                                                         height=150)


                file_box = ShadowGui.widgetBox(self.crystal_box_1, "", addSpace=True, orientation="horizontal", height=30)

                self.le_file_crystal_parameters = ShadowGui.lineEdit(file_box, self, "file_crystal_parameters", "File with crystal\nparameters",
                                   labelWidth=150, valueType=str, orientation="horizontal")

                pushButton = gui.button(file_box, self, "...")
                pushButton.clicked.connect(self.selectFileCrystalParameters)

                gui.comboBox(self.crystal_box_1, self, "crystal_auto_setting", label="Auto setting", labelWidth=350,
                             items=["No", "Yes"],
                             callback=self.set_Autosetting, sendSelectedValue=False, orientation="horizontal")

                gui.separator(self.crystal_box_1, height=10)

                self.autosetting_box = ShadowGui.widgetBox(self.crystal_box_1, "", addSpace=True,
                                                           orientation="vertical")
                self.autosetting_box_empty = ShadowGui.widgetBox(self.crystal_box_1, "", addSpace=True,
                                                                 orientation="vertical")

                self.autosetting_box_units = ShadowGui.widgetBox(self.autosetting_box, "", addSpace=True, orientation="vertical")

                gui.comboBox(self.autosetting_box_units, self, "units_in_use", label="Units in use", labelWidth=260,
                             items=["eV", "Angstroms"],
                             callback=self.set_UnitsInUse, sendSelectedValue=False, orientation="horizontal")

                self.autosetting_box_units_1 = ShadowGui.widgetBox(self.autosetting_box_units, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.autosetting_box_units_1, self, "photon_energy", "Set photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

                self.autosetting_box_units_2 = ShadowGui.widgetBox(self.autosetting_box_units, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.autosetting_box_units_2, self, "photon_wavelength", "Set wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                self.crystal_box_2 = ShadowGui.widgetBox(crystal_box, "", addSpace=True, orientation="horizontal",
                                                         height=150)

                self.le_file_diffraction_profile = ShadowGui.lineEdit(self.crystal_box_2, self, "file_diffraction_profile",
                                   "File with Diffraction\nProfile (XOP format)", labelWidth=150, valueType=str,
                                   orientation="horizontal")

                pushButton = gui.button(self.crystal_box_2, self, "...")
                pushButton.clicked.connect(self.selectFileDiffractionProfile)

                self.set_DiffractionCalculation()

                mosaic_box = ShadowGui.widgetBox(self.tab_cryst_2, "Geometric Parameters", addSpace=True,
                                                 orientation="vertical", height=350)

                gui.comboBox(mosaic_box, self, "mosaic_crystal", label="Mosaic Crystal", labelWidth=355,
                             items=["No", "Yes"],
                             callback=self.set_Mosaic, sendSelectedValue=False, orientation="horizontal")

                gui.separator(mosaic_box, height=10)

                self.mosaic_box_1 = ShadowGui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

                self.asymmetric_cut_box = ShadowGui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=110)

                gui.comboBox(self.asymmetric_cut_box, self, "asymmetric_cut", label="Asymmetric cut", labelWidth=355,
                             items=["No", "Yes"],
                             callback=self.set_AsymmetricCut, sendSelectedValue=False, orientation="horizontal")

                self.asymmetric_cut_box_1 = ShadowGui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")
                self.asymmetric_cut_box_1_empty = ShadowGui.widgetBox(self.asymmetric_cut_box, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.asymmetric_cut_box_1, self, "planes_angle", "Planes angle [deg]", labelWidth=260, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.asymmetric_cut_box_1, self, "below_onto_bragg_planes", "Below[-1]/onto[1] bragg planes",  labelWidth=260, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.asymmetric_cut_box_1, self, "thickness", "Thickness [cm]", valueType=float, labelWidth=260, orientation="horizontal")

                gui.separator(self.mosaic_box_1)

                self.johansson_box = ShadowGui.widgetBox(self.mosaic_box_1, "", addSpace=False, orientation="vertical", height=100)

                gui.comboBox(self.johansson_box, self, "johansson_geometry", label="Johansson Geometry", labelWidth=355,
                             items=["No", "Yes"],
                             callback=self.set_JohanssonGeometry, sendSelectedValue=False, orientation="horizontal")

                self.johansson_box_1 = ShadowGui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")
                self.johansson_box_1_empty = ShadowGui.widgetBox(self.johansson_box, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.johansson_box_1, self, "johansson_radius", "Johansson radius", labelWidth=260, valueType=float, orientation="horizontal")

                self.mosaic_box_2 = ShadowGui.widgetBox(mosaic_box, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.mosaic_box_2, self, "angle_spread_FWHM", "Angle spread FWHM [deg]",  labelWidth=260, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.mosaic_box_2, self, "thickness", "Thickness [cm]", labelWidth=260, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.mosaic_box_2, self, "seed_for_mosaic", "Seed for mosaic [>10^5]", labelWidth=260, valueType=float, orientation="horizontal")

                self.set_Mosaic()
            elif self.graphical_options.is_grating:
                tabs_grating_setting = gui.tabWidget(tab_bas_grating)

                tab_grating_2 = ShadowGui.createTabPage(tabs_grating_setting, "Ruling Setting")
                tab_grating_1 = ShadowGui.createTabPage(tabs_grating_setting, "Diffraction Settings")

                grating_box = ShadowGui.widgetBox(tab_grating_1, "Diffraction Parameters", addSpace=True, orientation="vertical", height=380)

                ShadowGui.lineEdit(grating_box, self, "grating_diffraction_order", "Diffraction Order", labelWidth=260, valueType=float, orientation="horizontal")

                gui.comboBox(grating_box, self, "grating_auto_setting", label="Auto setting", labelWidth=350,
                             items=["No", "Yes"],
                             callback=self.set_GratingAutosetting, sendSelectedValue=False, orientation="horizontal")

                gui.separator(grating_box, height=10)

                self.grating_autosetting_box = ShadowGui.widgetBox(grating_box, "", addSpace=True, orientation="vertical")
                self.grating_autosetting_box_empty = ShadowGui.widgetBox(grating_box, "", addSpace=True, orientation="vertical")

                self.grating_autosetting_box_units = ShadowGui.widgetBox(self.grating_autosetting_box, "", addSpace=True, orientation="vertical")

                gui.comboBox(self.grating_autosetting_box_units, self, "grating_units_in_use", label="Units in use", labelWidth=260,
                             items=["eV", "Angstroms"],
                             callback=self.set_GratingUnitsInUse, sendSelectedValue=False, orientation="horizontal")

                self.grating_autosetting_box_units_1 = ShadowGui.widgetBox(self.grating_autosetting_box_units, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.grating_autosetting_box_units_1, self, "grating_photon_energy", "Set photon energy [eV]", labelWidth=260, valueType=float, orientation="horizontal")

                self.grating_autosetting_box_units_2 = ShadowGui.widgetBox(self.grating_autosetting_box_units, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.grating_autosetting_box_units_2, self, "grating_photon_wavelength", "Set wavelength [Å]", labelWidth=260, valueType=float, orientation="horizontal")

                self.grating_mount_box = ShadowGui.widgetBox(grating_box, "", addSpace=True, orientation="vertical")

                gui.comboBox(self.grating_mount_box, self, "grating_mount_type", label="Mount Type", labelWidth=300,
                             items=["TGM/Seya", "ERG", "Constant Incidence Angle", "Costant Diffraction Angle", "Hunter"],
                             callback=self.set_GratingMountType, sendSelectedValue=False, orientation="horizontal")

                gui.separator(self.grating_mount_box)

                self.grating_mount_box_1 = ShadowGui.widgetBox(self.grating_mount_box, "", addSpace=True, orientation="vertical")

                ShadowGui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_blaze_angle", "Blaze angle [deg]", labelWidth=300, valueType=float, orientation="horizontal")
                gui.comboBox(self.grating_mount_box_1, self, "grating_hunter_grating_selected", label="Grating selected", labelWidth=300,
                             items=["First", "Second"], sendSelectedValue=False, orientation="horizontal")
                ShadowGui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_monochromator_length", "Monochromator Length [cm]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.grating_mount_box_1, self, "grating_hunter_distance_between_beams", "Distance between beams [cm]", labelWidth=300, valueType=float, orientation="horizontal")

                self.set_GratingAutosetting()

                ################

                ruling_box = ShadowGui.widgetBox(tab_grating_2, "Ruling Parameters", addSpace=True, orientation="vertical", height=380)

                gui.comboBox(ruling_box, self, "grating_ruling_type", label="Ruling Type", labelWidth=200,
                             items=["Constant on X-Y Plane", "Constant on Mirror Surface", "Holographic", "Fan Type", "Polynomial Line Density"],
                             callback=self.set_GratingRulingType, sendSelectedValue=False, orientation="horizontal")

                gui.separator(ruling_box)

                self.ruling_box_1 = ShadowGui.widgetBox(ruling_box, "", addSpace=True, orientation="horizontal")

                self.ruling_density_label = gui.widgetLabel(self.ruling_box_1, "Ruling Density at origin [Lines/cm]", labelWidth=300)
                ShadowGui.lineEdit(self.ruling_box_1, self, "grating_ruling_density", "", labelWidth=1, valueType=float, orientation="horizontal")

                self.ruling_box_2 = ShadowGui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_left_distance", "\"Left\" distance [cm]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_left_incidence_angle", "\"Left\" incidence angle [deg]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_left_azimuth_from_y", "\"Left\" azimuth from +Y (CCW) [deg]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_right_distance", "\"Right\" distance [cm]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_right_incidence_angle", "\"Right\" incidence angle [deg]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_right_azimuth_from_y", "\"Right\" azimuth from +Y (CCW) [deg]", labelWidth=300, valueType=float, orientation="horizontal")
                gui.comboBox(self.ruling_box_2, self, "grating_holo_pattern_type", label="Pattern Type", labelWidth=250,
                             items=["Spherical/Spherical", "Plane/Spherical", "Spherical/Plane", "Plane/Plane"], sendSelectedValue=False, orientation="horizontal")
                gui.comboBox(self.ruling_box_2, self, "grating_holo_source_type", label="Source Type", labelWidth=250,
                             items=["Real/Real", "Real/Virtual", "Virtual/Real", "Real/Real"], sendSelectedValue=False, orientation="horizontal")
                gui.comboBox(self.ruling_box_2, self, "grating_holo_pattern_type", label="Pattern Type", labelWidth=250,
                             items=["Spherical/Spherical", "Cylindrical/Spherical", "Spherical/Cylindrical", "Cylindrical/Cylindrical"], sendSelectedValue=False, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_2, self, "grating_holo_recording_wavelength", "Recording wavelength [Å]", labelWidth=300, valueType=float, orientation="horizontal")

                self.ruling_box_3 = ShadowGui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.ruling_box_3, self, "grating_groove_pole_distance", "Groove pole distance [cm]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_3, self, "grating_groove_pole_azimuth_from_y", "Groove pole azimuth from +Y (CCW) [deg]", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_3, self, "grating_coma_correction_factor", "Coma correction factor", labelWidth=300, valueType=float, orientation="horizontal")

                self.ruling_box_4 = ShadowGui.widgetBox(ruling_box, "", addSpace=False, orientation="vertical")

                ShadowGui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_1", "Polynomial Line Density coeff.: linear", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_2", "Polynomial Line Density coeff.: quadratic", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_3", "Polynomial Line Density coeff.: third power", labelWidth=300, valueType=float, orientation="horizontal")
                ShadowGui.lineEdit(self.ruling_box_4, self, "grating_poly_coeff_4", "Polynomial Line Density coeff.: fourth power", labelWidth=300, valueType=float, orientation="horizontal")
                gui.comboBox(self.ruling_box_4, self, "grating_poly_signed_absolute", label="Line density absolute/signed from the origin", labelWidth=300,
                             items=["Absolute", "Signed"], sendSelectedValue=False, orientation="horizontal")

                self.set_GratingRulingType()

            ##########################################
            #
            # TAB 1.3 - DIMENSIONS
            #
            ##########################################

            dimension_box = ShadowGui.widgetBox(tab_bas_dim, "Dimensions", addSpace=False, orientation="vertical", height=210)

            gui.comboBox(dimension_box, self, "is_infinite", label="Limits Check",
                         items=["Infinite o.e. dimensions", "Finite o.e. dimensions"],
                         callback=self.set_Dim_Parameters, sendSelectedValue=False, orientation="horizontal")

            gui.separator(dimension_box, width=self.INNER_BOX_WIDTH_L2, height=10)

            self.dimdet_box = ShadowGui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")
            self.dimdet_box_empty = ShadowGui.widgetBox(dimension_box, "", addSpace=False, orientation="vertical")

            gui.comboBox(self.dimdet_box, self, "mirror_shape", label="Shape selected", labelWidth=260,
                         items=["Rectangular", "Full ellipse", "Ellipse with hole"],
                         sendSelectedValue=False, orientation="horizontal")

            ShadowGui.lineEdit(self.dimdet_box, self, "dim_x_plus", "X(+) Half Width / Int Maj Ax [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.dimdet_box, self, "dim_x_minus", "X(-) Half Width / Int Maj Ax [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.dimdet_box, self, "dim_y_plus", "Y(+) Half Width / Int Min Ax [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.dimdet_box, self, "dim_y_minus", "Y(-) Half Width / Int Min Ax [cm]", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_Dim_Parameters()

            ##########################################
            ##########################################
            # ADVANCED SETTINGS
            ##########################################
            ##########################################

            tabs_advanced_setting = gui.tabWidget(tab_adv)

            tab_adv_mod_surf = ShadowGui.createTabPage(tabs_advanced_setting, "Modified Surface")
            tab_adv_mir_mov = ShadowGui.createTabPage(tabs_advanced_setting, "O.E. Movement")
            tab_adv_sou_mov = ShadowGui.createTabPage(tabs_advanced_setting, "Source Movement")
            tab_adv_misc = ShadowGui.createTabPage(tabs_advanced_setting, "Output Files")

            ##########################################
            #
            # TAB 2.1 - Modified Surface
            #
            ##########################################

            mod_surf_box = ShadowGui.widgetBox(tab_adv_mod_surf, "Modified Surface Parameters", addSpace=False, orientation="vertical", height=390)

            gui.comboBox(mod_surf_box, self, "modified_surface", label="Modification Type", labelWidth=260,
                         items=["None", "Surface Error", "Faceted Surface", "Surface Roughness", "Kumakhov Lens", "Segmented Mirror"],
                         callback=self.set_ModifiedSurface, sendSelectedValue=False, orientation="horizontal")

            gui.separator(mod_surf_box, height=10)

            # SURFACE ERROR

            self.surface_error_box =  ShadowGui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

            type_of_defect_box = ShadowGui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="vertical")

            gui.comboBox(type_of_defect_box, self, "ms_type_of_defect", label="Type of Defect", labelWidth=260,
                         items=["sinusoidal", "gaussian", "external spline"],
                         callback=self.set_TypeOfDefect, sendSelectedValue=False, orientation="horizontal")

            self.mod_surf_err_box_1 = ShadowGui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="horizontal")

            self.le_ms_defect_file_name = ShadowGui.lineEdit(self.mod_surf_err_box_1, self, "ms_defect_file_name", "File name", labelWidth=125, valueType=str, orientation="horizontal")

            pushButton = gui.button(self.mod_surf_err_box_1, self, "...")
            pushButton.clicked.connect(self.selectDefectFileName)

            self.mod_surf_err_box_2 = ShadowGui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_wavel_x", "Ripple Wavel. X", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_wavel_y", "Ripple Wavel. Y", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_ampli_x", "Ripple Ampli. X", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_ampli_y", "Ripple Ampli. Y", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_phase_x", "Ripple Phase X", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mod_surf_err_box_2, self, "ms_ripple_phase_y", "Ripple Phase Y", labelWidth=260, valueType=float, orientation="horizontal")

            # FACETED SURFACE

            self.faceted_surface_box =  ShadowGui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

            file_box = ShadowGui.widgetBox(self.faceted_surface_box, "", addSpace=True, orientation="horizontal", height=25)

            self.le_ms_file_facet_descr = ShadowGui.lineEdit(file_box, self, "ms_file_facet_descr", "File w/ facet descr.", labelWidth=125, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectFileFacetDescr)

            gui.comboBox(self.faceted_surface_box, self, "ms_lattice_type", label="Lattice Type", labelWidth=260,
                         items=["rectangle", "hexagonal"], sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(self.faceted_surface_box, self, "ms_orientation", label="Orientation", labelWidth=260,
                         items=["y-axis", "other"], sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(self.faceted_surface_box, self, "ms_intercept_to_use", label="Intercept to use", labelWidth=260,
                         items=["2nd first", "2nd closest", "closest", "farthest"], sendSelectedValue=False, orientation="horizontal")


            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_facet_width_x", "Facet width (in X)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_facet_phase_x", "Facet phase in X (0-360)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_x_minus", "Dead width (abs, for -X)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_x_plus", "Dead width (abs, for +X)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_facet_width_y", "Facet width (in Y)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_facet_phase_y", "Facet phase in Y (0-360)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_y_minus", "Dead width (abs, for -Y)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.faceted_surface_box, self, "ms_dead_width_y_plus", "Dead width (abs, for +Y)", labelWidth=260, valueType=float, orientation="horizontal")

            # SURFACE ROUGHNESS

            self.surface_roughness_box =  ShadowGui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")


            file_box = ShadowGui.widgetBox(self.surface_roughness_box, "", addSpace=True, orientation="horizontal", height=25)

            self.le_ms_file_surf_roughness = ShadowGui.lineEdit(file_box, self, "ms_file_surf_roughness", "Surface Roughness File w/ PSD fn", valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectFileSurfRoughness)

            ShadowGui.lineEdit(self.surface_roughness_box, self, "ms_roughness_rms_y", "Roughness RMS in Y (Å)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.surface_roughness_box, self, "ms_roughness_rms_x", "Roughness RMS in X (Å)", labelWidth=260, valueType=float, orientation="horizontal")

            # KUMAKHOV LENS

            self.kumakhov_lens_box =  ShadowGui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

            gui.comboBox(self.kumakhov_lens_box, self, "ms_specify_rz2", label="Specify r(z)^2", labelWidth=350,
                         items=["No", "Yes"], callback=self.set_SpecifyRz2, sendSelectedValue=False, orientation="horizontal")

            self.kumakhov_lens_box_1 =  ShadowGui.widgetBox(self.kumakhov_lens_box, box="", addSpace=False, orientation="vertical")
            self.kumakhov_lens_box_2 =  ShadowGui.widgetBox(self.kumakhov_lens_box, box="", addSpace=False, orientation="vertical")

            file_box = ShadowGui.widgetBox(self.kumakhov_lens_box_1, "", addSpace=True, orientation="horizontal", height=25)

            self.le_ms_file_with_parameters_rz = ShadowGui.lineEdit(file_box, self, "ms_file_with_parameters_rz", "File with parameters (r(z))", labelWidth=185, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectFileWithParametersRz)

            file_box = ShadowGui.widgetBox(self.kumakhov_lens_box_2, "", addSpace=True, orientation="horizontal", height=25)

            self.le_ms_file_with_parameters_rz2 = ShadowGui.lineEdit(file_box, self, "ms_file_with_parameters_rz2", "File with parameters (r(z)^2)", labelWidth=185, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectFileWithParametersRz2)

            gui.comboBox(self.kumakhov_lens_box, self, "ms_save_intercept_bounces", label="Save intercept and bounces", labelWidth=350,
                         items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal")

            # SEGMENTED MIRROR

            self.segmented_mirror_box =  ShadowGui.widgetBox(mod_surf_box, box="", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.segmented_mirror_box, self, "ms_number_of_segments_x", "Number of segments (X)", labelWidth=260, valueType=int, orientation="horizontal")
            ShadowGui.lineEdit(self.segmented_mirror_box, self, "ms_length_of_segments_x", "Length of segments (X)", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.segmented_mirror_box, self, "ms_number_of_segments_y", "Number of segments (Y)", labelWidth=260, valueType=int, orientation="horizontal")
            ShadowGui.lineEdit(self.segmented_mirror_box, self, "ms_length_of_segments_y", "Length of segments (Y)", labelWidth=260, valueType=float, orientation="horizontal")


            file_box = ShadowGui.widgetBox(self.segmented_mirror_box, "", addSpace=True, orientation="horizontal", height=25)

            self.le_ms_file_orientations = ShadowGui.lineEdit(file_box, self, "ms_file_orientations", "File w/ orientations", labelWidth=155, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectFileOrientations)

            file_box = ShadowGui.widgetBox(self.segmented_mirror_box, "", addSpace=True, orientation="horizontal", height=25)

            self.le_ms_file_polynomial = ShadowGui.lineEdit(file_box, self, "ms_file_polynomial", "File w/ polynomial", labelWidth=155, valueType=str, orientation="horizontal")

            pushButton = gui.button(file_box, self, "...")
            pushButton.clicked.connect(self.selectFilePolynomial)


            self.set_ModifiedSurface()

            ##########################################
            #
            # TAB 2.2 - Mirror Movement
            #
            ##########################################

            mir_mov_box = ShadowGui.widgetBox(tab_adv_mir_mov, "O.E. Movement Parameters", addSpace=False, orientation="vertical", height=230)

            gui.comboBox(mir_mov_box, self, "mirror_movement", label="O.E. Movement", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_MirrorMovement, sendSelectedValue=False, orientation="horizontal")

            gui.separator(mir_mov_box, width=self.INNER_BOX_WIDTH_L1, height=10)

            self.mir_mov_box_1 = ShadowGui.widgetBox(mir_mov_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_x", "O.E. Offset X  [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_x", "O.E. Rotation X [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_y", "O.E. Offset Y [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_y", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_offset_z", "O.E. Offset Z [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.mir_mov_box_1, self, "mm_mirror_rotation_z", "O.E. Rotation Z [CCW, deg]", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_MirrorMovement()

           ##########################################
            #
            # TAB 2.3 - Source Movement
            #
            ##########################################

            sou_mov_box = ShadowGui.widgetBox(tab_adv_sou_mov, "Source Movement Parameters", addSpace=False, orientation="vertical", height=400)

            gui.comboBox(sou_mov_box, self, "source_movement", label="Source Movement", labelWidth=350,
                         items=["No", "Yes"],
                         callback=self.set_SourceMovement, sendSelectedValue=False, orientation="horizontal")

            gui.separator(sou_mov_box, width=self.INNER_BOX_WIDTH_L1, height=10)

            self.sou_mov_box_1 = ShadowGui.widgetBox(sou_mov_box, "", addSpace=False, orientation="vertical")

            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_angle_of_incidence", "Angle of Incidence [deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_distance_from_mirror", "Distance from o.e. [cm]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_z_rotation", "Z-rotation [deg]", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_mirr_ref_frame", "offset X [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_mirr_ref_frame", "offset Y [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_mirr_ref_frame", "offset Z [cm] in O.E. reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_x_source_ref_frame", "offset X [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_y_source_ref_frame", "offset Y [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_offset_z_source_ref_frame", "offset Z [cm] in SOURCE reference frame", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_x", "rotation [CCW, deg] around X", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_y", "rotation [CCW, deg] around Y", labelWidth=260, valueType=float, orientation="horizontal")
            ShadowGui.lineEdit(self.sou_mov_box_1, self, "sm_rotation_around_z", "rotation [CCW, deg] around Z", labelWidth=260, valueType=float, orientation="horizontal")

            self.set_SourceMovement()

            ##########################################
            #
            # TAB 2.4 - Other
            #
            ##########################################

            adv_other_box = ShadowGui.widgetBox(tab_adv_misc, "Optional file output", addSpace=False, orientation="vertical")

            gui.comboBox(adv_other_box, self, "file_to_write_out", label="Files to write out", labelWidth=310,
                         items=["All", "Mirror", "Image", "None"],
                         sendSelectedValue=False, orientation="horizontal")

            gui.comboBox(adv_other_box, self, "write_out_inc_ref_angles", label="Write out Incident/Reflected angles [angle.xx]", labelWidth=350,
                         items=["No", "Yes"],
                         sendSelectedValue=False, orientation="horizontal")

        button_box = ShadowGui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Run Shadow/Trace", callback=self.traceOpticalElement)
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

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    # TAB 1.1

    def set_IntExt_Parameters(self):
        self.surface_box_int.setVisible(self.surface_shape_parameters == 0)
        self.surface_box_ext.setVisible(self.surface_shape_parameters == 1)
        if self.surface_shape_parameters == 0: self.set_FociiCont_Parameters()

    def set_FociiCont_Parameters(self):
        self.surface_box_int_2.setVisible(self.focii_and_continuation_plane == 1)
        self.surface_box_int_2_empty.setVisible(self.focii_and_continuation_plane == 0)

    def set_isCyl_Parameters(self):
        self.surface_box_cyl.setVisible(self.is_cylinder == 1)
        self.surface_box_cyl_empty.setVisible(self.is_cylinder == 0)

    # TAB 1.2

    def set_Refl_Parameters(self):
        self.refl_box_pol.setVisible(self.reflectivity_type != 0)
        self.refl_box_pol_empty.setVisible(self.reflectivity_type == 0)
        if self.reflectivity_type != 0: self.set_ReflSource_Parameters()

    def set_ReflSource_Parameters(self):
        self.refl_box_pol_1.setVisible(self.source_of_reflectivity == 0)
        self.refl_box_pol_2.setVisible(self.source_of_reflectivity == 1)
        self.refl_box_pol_3.setVisible(self.source_of_reflectivity == 2)

    def set_Autosetting(self):
        self.autosetting_box_empty.setVisible(self.crystal_auto_setting == 0)
        self.autosetting_box.setVisible(self.crystal_auto_setting == 1)

        if self.crystal_auto_setting == 0:
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.incidence_angle_deg_le.setEnabled(False)
            self.incidence_angle_rad_le.setEnabled(False)
            self.reflection_angle_deg_le.setEnabled(False)
            self.reflection_angle_rad_le.setEnabled(False)
            self.set_UnitsInUse()

    def set_DiffractionCalculation(self):
        self.tab_cryst_2.setEnabled(self.diffraction_calculation == 0)

        self.crystal_box_1.setVisible(self.diffraction_calculation == 0)
        self.crystal_box_2.setVisible(self.diffraction_calculation == 1)

        if (self.diffraction_calculation == 1):
            self.incidence_angle_deg_le.setEnabled(True)
            self.incidence_angle_rad_le.setEnabled(True)
            self.reflection_angle_deg_le.setEnabled(True)
            self.reflection_angle_rad_le.setEnabled(True)
        else:
            self.set_Autosetting()


    def set_UnitsInUse(self):
        self.autosetting_box_units_1.setVisible(self.units_in_use == 0)
        self.autosetting_box_units_2.setVisible(self.units_in_use == 1)

    def set_Mosaic(self):
        self.mosaic_box_1.setVisible(self.mosaic_crystal == 0)
        self.mosaic_box_2.setVisible(self.mosaic_crystal == 1)

        if self.mosaic_crystal == 0:
            self.set_AsymmetricCut()
            self.set_JohanssonGeometry()

    def set_AsymmetricCut(self):
        self.asymmetric_cut_box_1.setVisible(self.asymmetric_cut == 1)
        self.asymmetric_cut_box_1_empty.setVisible(self.asymmetric_cut == 0)

    def set_JohanssonGeometry(self):
        self.johansson_box_1.setVisible(self.johansson_geometry == 1)
        self.johansson_box_1_empty.setVisible(self.johansson_geometry == 0)

    def set_GratingAutosetting(self):
        self.grating_autosetting_box_empty.setVisible(self.grating_auto_setting == 0)
        self.grating_autosetting_box.setVisible(self.grating_auto_setting == 1)
        self.grating_mount_box.setVisible(self.grating_auto_setting == 1)

        if self.grating_auto_setting == 1:
            self.set_GratingUnitsInUse()
            self.set_GratingMountType()

    def set_GratingUnitsInUse(self):
        self.grating_autosetting_box_units_1.setVisible(self.grating_units_in_use == 0)
        self.grating_autosetting_box_units_2.setVisible(self.grating_units_in_use == 1)

    def set_GratingRulingType(self):
        self.ruling_box_1.setVisible(self.grating_ruling_type != 2)
        self.ruling_box_2.setVisible(self.grating_ruling_type == 2)
        self.ruling_box_3.setVisible(self.grating_ruling_type == 3)
        self.ruling_box_4.setVisible(self.grating_ruling_type == 4)

        if (self.grating_ruling_type == 0 or self.grating_ruling_type == 1):
            self.ruling_density_label.setText("Ruling Density at origin [Lines/cm]")
        elif (self.grating_ruling_type == 3):
            self.ruling_density_label.setText("Ruling Density at center [Lines/cm]")
        elif (self.grating_ruling_type == 4):
            self.ruling_density_label.setText("Polynomial Line Density coeff.: constant")

    def set_GratingMountType(self):
        self.grating_mount_box_1.setVisible(self.grating_mount_type == 4)

    # TAB 1.3

    def set_Dim_Parameters(self):
        self.dimdet_box.setVisible(self.is_infinite == 1)
        self.dimdet_box_empty.setVisible(self.is_infinite == 0)

    # TAB 2

    def set_SourceMovement(self):
        self.sou_mov_box_1.setVisible(self.source_movement == 1)

    def set_MirrorMovement(self):
        self.mir_mov_box_1.setVisible(self.mirror_movement == 1)

    def set_TypeOfDefect(self):
        self.mod_surf_err_box_1.setVisible(self.ms_type_of_defect != 0)
        self.mod_surf_err_box_2.setVisible(self.ms_type_of_defect == 0)

    def set_ModifiedSurface(self):
        self.surface_error_box.setVisible(self.modified_surface == 1)
        self.faceted_surface_box.setVisible(self.modified_surface == 2)
        self.surface_roughness_box.setVisible(self.modified_surface == 3)
        self.kumakhov_lens_box.setVisible(self.modified_surface == 4)
        self.segmented_mirror_box.setVisible(self.modified_surface == 5)
        if self.modified_surface == 1: self.set_TypeOfDefect()
        if self.modified_surface == 4: self.set_SpecifyRz2()

    def set_SpecifyRz2(self):
        self.kumakhov_lens_box_1.setVisible(self.ms_specify_rz2 == 0)
        self.kumakhov_lens_box_2.setVisible(self.ms_specify_rz2 == 1)


    def set_ApertureShape(self):
        self.box_aperturing_shape_1.setVisible(self.aperture_shape == 2)
        self.box_aperturing_shape_2.setVisible(self.aperture_shape != 2)

    def set_Aperturing(self):
            self.box_aperturing_shape.setVisible(self.aperturing == 1)

            if self.aperturing == 1: self.set_ApertureShape()

    def set_Absorption(self):
        self.box_absorption_1_empty.setVisible(self.absorption == 0)
        self.box_absorption_1.setVisible(self.absorption == 1)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def selectExternalFileWithCoordinate(self):
        self.le_external_file_with_coordinate.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Open External File With Coordinate", ".", "*.*"))

    def selectOptConstFileName(self):
        self.le_opt_const_file_name.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Open Opt. Const. File", ".", "*.*"))

    def selectFilePrerefl(self):
        self.le_file_prerefl.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File Prerefl", ".", "*.dat"))

    def selectFilePrereflM(self):
        self.le_file_prerefl_m.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File Premlayer", ".", "*.dat"))

    def selectFileCrystalParameters(self):
        self.le_file_crystal_parameters.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File With Crystal Parameters", ".", "*.dat"))

    def selectFileDiffractionProfile(self):
        self.le_file_diffraction_profile.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File With User Defined Diffraction Profile", ".", "*.*"))

    def selectDefectFileName(self):
        self.le_ms_defect_file_name.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select Defect File Name", ".", "*.*"))

    def selectFileFacetDescr(self):
        self.le_ms_file_facet_descr.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File with Facet Description", ".", "*.*"))

    def selectFileSurfRoughness(self):
        self.le_ms_file_surf_roughness.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select Surface Roughness File with PSD fn", ".", "*.*"))

    def selectFileWithParametersRz(self):
        self.le_ms_file_with_parameters_rz.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File with parameters (r(z))", ".", "*.*"))

    def selectFileWithParametersRz2(self):
        self.le_ms_file_with_parameters_rz2.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File with parameters (r(z)^2)", ".", "*.*"))

    def selectFileOrientations(self):
        self.le_ms_file_orientations.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File with Orientations", ".", "*.*"))

    def selectFilePolynomial(self):
        self.le_ms_file_polynomial.setText(
            QtGui.QFileDialog.getOpenFileName(self, "Select File with Polynomial", ".", "*.*"))

    def calculate_incidence_angle_mrad(self):
        self.incidence_angle_mrad = round(math.radians(90-self.incidence_angle_deg)*1000, 2)

    def calculate_reflection_angle_mrad(self):
        self.reflection_angle_mrad = round(math.radians(90-self.reflection_angle_deg)*1000, 2)

    def calculate_incidence_angle_deg(self):
        self.incidence_angle_deg = round(math.degrees(0.5*math.pi-(self.incidence_angle_mrad/1000)), 3)

    def calculate_reflection_angle_deg(self):
        self.reflection_angle_deg = round(math.degrees(0.5*math.pi-(self.reflection_angle_mrad/1000)), 3)

    def populateFields(self, shadow_oe = ShadowOpticalElement.create_empty_oe()):
        if self.graphical_options.is_screen_slit:
            shadow_oe.oe.T_SOURCE     = self.source_plane_distance
            shadow_oe.oe.T_IMAGE      = self.image_plane_distance
            shadow_oe.oe.T_INCIDENCE  = 0.0
            shadow_oe.oe.T_REFLECTION = 180.0
            shadow_oe.oe.ALPHA        = 0.0

            if self.mirror_movement == 1:
                 shadow_oe.oe.F_MOVE=1
                 shadow_oe.oe.OFFX=self.mm_mirror_offset_x
                 shadow_oe.oe.OFFY=self.mm_mirror_offset_y
                 shadow_oe.oe.OFFZ=self.mm_mirror_offset_z
                 shadow_oe.oe.X_ROT=self.mm_mirror_rotation_x
                 shadow_oe.oe.Y_ROT=self.mm_mirror_rotation_y
                 shadow_oe.oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe.oe.FSTAT=1
                 shadow_oe.oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe.oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe.oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe.oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe.oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe.oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe.oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe.oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe.oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe.oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe.oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe.oe.Z_SOUR_ROT=self.sm_rotation_around_z
        elif self.graphical_options.is_empty:
            shadow_oe.oe.T_SOURCE     = self.source_plane_distance
            shadow_oe.oe.T_IMAGE      = self.image_plane_distance
            shadow_oe.oe.T_INCIDENCE  = self.incidence_angle_deg
            shadow_oe.oe.T_REFLECTION = self.reflection_angle_deg
            shadow_oe.oe.ALPHA        = 90*self.mirror_orientation_angle

            if self.mirror_movement == 1:
                 shadow_oe.oe.F_MOVE=1
                 shadow_oe.oe.OFFX=self.mm_mirror_offset_x
                 shadow_oe.oe.OFFY=self.mm_mirror_offset_y
                 shadow_oe.oe.OFFZ=self.mm_mirror_offset_z
                 shadow_oe.oe.X_ROT=self.mm_mirror_rotation_x
                 shadow_oe.oe.Y_ROT=self.mm_mirror_rotation_y
                 shadow_oe.oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe.oe.FSTAT=1
                 shadow_oe.oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe.oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe.oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe.oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe.oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe.oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe.oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe.oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe.oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe.oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe.oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe.oe.Z_SOUR_ROT=self.sm_rotation_around_z
        else:
            shadow_oe.oe.T_SOURCE     = self.source_plane_distance
            shadow_oe.oe.T_IMAGE      = self.image_plane_distance
            shadow_oe.oe.T_INCIDENCE  = self.incidence_angle_deg
            shadow_oe.oe.T_REFLECTION = self.reflection_angle_deg
            shadow_oe.oe.ALPHA        = 90*self.mirror_orientation_angle

            #####################################
            # BASIC SETTING
            #####################################

            if self.graphical_options.is_curved:
                if self.is_cylinder==1:
                   shadow_oe.oe.FCYL = 1
                   shadow_oe.oe.CIL_ANG=90*self.cylinder_orientation
                else:
                   shadow_oe.oe.FCYL = 0

                if self.graphical_options.is_conic_coefficients:
                    conic_coefficients = [self.conic_coefficient_0,
                                          self.conic_coefficient_1,
                                          self.conic_coefficient_2,
                                          self.conic_coefficient_3,
                                          self.conic_coefficient_4,
                                          self.conic_coefficient_5,
                                          self.conic_coefficient_6,
                                          self.conic_coefficient_7,
                                          self.conic_coefficient_8,
                                          self.conic_coefficient_9]

                    shadow_oe.oe.F_EXT = 1
                    shadow_oe.oe.CCC[:] = conic_coefficients[:]
                else:
                    if self.surface_shape_parameters == 0:
                       if (self.is_cylinder==1 and self.cylinder_orientation==1):
                           if self.graphical_options.is_spheric:
                               shadow_oe.oe.F_EXT=1

                               #IMPLEMENTATION OF THE AUTOMATIC CALCULATION OF THE SAGITTAL FOCUSING FOR SPHERICAL CYLINDERS
                               # RADIUS = (2 F1 F2 sin (theta)) /( F1+F2)
                               if self.focii_and_continuation_plane == 0:
                                  self.spherical_radius = ((2*self.source_plane_distance*self.image_plane_distance)/(self.source_plane_distance+self.image_plane_distance))*math.sin(self.reflection_angle_mrad)
                               else:
                                  self.spherical_radius = ((2*self.object_side_focal_distance*self.image_side_focal_distance)/(self.object_side_focal_distance+self.image_side_focal_distance))*math.sin(round(math.radians(90-self.incidence_angle_respect_to_normal), 2))

                               shadow_oe.oe.RMIRR = self.spherical_radius
                       else:
                           shadow_oe.oe.F_EXT = 0

                           if self.focii_and_continuation_plane == 0:
                              shadow_oe.oe.F_DEFAULT=1
                           else:
                              shadow_oe.oe.F_DEFAULT=0
                              shadow_oe.oe.SSOUR = self.object_side_focal_distance
                              shadow_oe.oe.SIMAG = self.image_side_focal_distance
                              shadow_oe.oe.THETA = self.incidence_angle_respect_to_normal

                           if self.graphical_options.is_paraboloid: shadow_oe.oe.F_SIDE=self.focus_location
                    else:
                       shadow_oe.oe.F_EXT=1
                       if self.graphical_options.is_spheric:
                           shadow_oe.oe.RMIRR = self.spherical_radius
                       elif self.graphical_options.is_toroidal:
                           shadow_oe.oe.R_MAJ=self.torus_major_radius
                           shadow_oe.oe.R_MIN=self.torus_minor_radius
                       elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                           shadow_oe.oe.AXMAJ=self.ellipse_hyperbola_semi_major_axis
                           shadow_oe.oe.AXMIN=self.ellipse_hyperbola_semi_minor_axis
                           shadow_oe.oe.ELL_THE=self.angle_of_majax_and_pole
                       elif self.graphical_options.is_paraboloid:
                           shadow_oe.oe.PARAM=self.paraboloid_parameter

                    if self.graphical_options.is_toroidal: shadow_oe.oe.F_TORUS=self.toroidal_mirror_pole_location

                    if self.surface_curvature == 0:
                       shadow_oe.oe.F_CONVEX=0
                    else:
                       shadow_oe.oe.F_CONVEX=1
            else:
               shadow_oe.oe.FCYL = 0

            if self.graphical_options.is_mirror:
                if self.reflectivity_type == 0:
                   shadow_oe.oe.F_REFLEC = 0
                elif self.reflectivity_type == 1:
                    if self.source_of_reflectivity == 0:
                        shadow_oe.oe.F_REFLEC = 1
                        shadow_oe.oe.F_REFL = 0
                        shadow_oe.oe.FILE_REFL = bytes(self.file_prerefl, 'utf-8')
                        shadow_oe.oe.ALFA = 0.0
                        shadow_oe.oe.GAMMA = 0.0
                        shadow_oe.oe.F_THICK = 0
                    elif self.source_of_reflectivity == 1:
                        shadow_oe.oe.F_REFLEC = 1
                        shadow_oe.oe.F_REFL = 1
                        shadow_oe.oe.FILE_REFL = 'GAAS.SHA'
                        shadow_oe.oe.ALFA = self.alpha
                        shadow_oe.oe.GAMMA = self.gamma
                        shadow_oe.oe.F_THICK = 0
                    elif self.source_of_reflectivity == 2:
                        shadow_oe.oe.F_REFLEC = 1
                        shadow_oe.oe.F_REFL = 2
                        shadow_oe.oe.FILE_REFL = bytes(self.file_prerefl_m, 'utf-8')
                        shadow_oe.oe.ALFA = 0.0
                        shadow_oe.oe.GAMMA = 0.0
                        shadow_oe.oe.F_THICK = self.m_layer_tickness
                elif self.reflectivity_type == 2:
                    if self.source_of_reflectivity == 0:
                        shadow_oe.oe.F_REFLEC = 2
                        shadow_oe.oe.F_REFL = 0
                        shadow_oe.oe.FILE_REFL = bytes(self.file_prerefl, 'utf-8')
                        shadow_oe.oe.ALFA = 0.0
                        shadow_oe.oe.GAMMA = 0.0
                        shadow_oe.oe.F_THICK = 0
                    elif self.source_of_reflectivity == 1:
                        shadow_oe.oe.F_REFLEC = 2
                        shadow_oe.oe.F_REFL = 1
                        shadow_oe.oe.FILE_REFL = 'GAAS.SHA'
                        shadow_oe.oe.ALFA = self.alpha
                        shadow_oe.oe.GAMMA = self.gamma
                        shadow_oe.oe.F_THICK = 0
                    elif self.source_of_reflectivity == 2:
                        shadow_oe.oe.F_REFLEC = 2
                        shadow_oe.oe.F_REFL = 2
                        shadow_oe.oe.FILE_REFL = bytes(self.file_prerefl_m, 'utf-8')
                        shadow_oe.oe.ALFA = 0.0
                        shadow_oe.oe.GAMMA = 0.0
                        shadow_oe.oe.F_THICK = self.m_layer_tickness
            elif self.graphical_options.is_crystal:
                shadow_oe.oe.F_REFLEC = 0

                if self.diffraction_calculation == 1:
                    shadow_oe.oe.F_CRYSTAL = 0  # user defined profile -> simulated as mirror with no reflectivity
                else:
                    shadow_oe.oe.F_CRYSTAL = 1
                    shadow_oe.oe.FILE_REFL = bytes(self.file_crystal_parameters, 'utf-8')
                    shadow_oe.oe.F_REFLECT = 0
                    shadow_oe.oe.F_BRAGG_A = 0
                    shadow_oe.oe.A_BRAGG = 0.0
                    shadow_oe.oe.F_REFRACT = 0

                    shadow_oe.oe.F_REFRAC = self.diffraction_geometry

                    if self.crystal_auto_setting == 0:
                        shadow_oe.oe.F_CENTRAL = 0
                    else:
                        shadow_oe.oe.F_CENTRAL = 1
                        shadow_oe.oe.F_PHOT_CENT = self.units_in_use
                        shadow_oe.oe.PHOT_CENT = self.photon_energy
                        shadow_oe.oe.R_LAMBDA = self.photon_wavelength

                    if self.mosaic_crystal == 1:
                        shadow_oe.oe.F_MOSAIC = 1
                        shadow_oe.oe.MOSAIC_SEED = self.seed_for_mosaic
                        shadow_oe.oe.SPREAD_MOS = self.angle_spread_FWHM
                        shadow_oe.oe.THICKNESS = self.thickness
                    else:
                        if self.asymmetric_cut == 1:
                            shadow_oe.oe.F_BRAGG_A = 1
                            shadow_oe.oe.A_BRAGG = self.planes_angle
                            shadow_oe.oe.ORDER = self.below_onto_bragg_planes
                            shadow_oe.oe.THICKNESS = self.thickness
                        if self.johansson_geometry == 1:
                            shadow_oe.oe.F_JOHANSSON = 1
                            shadow_oe.oe.F_EXT = 1
                            shadow_oe.oe.R_JOHANSSON = self.johansson_radius
            elif self.graphical_options.is_grating:
                shadow_oe.oe.F_REFLEC = 0

                if self.grating_ruling_type == 0 or self.grating_ruling_type == 1:
                    shadow_oe.oe.F_GRATING = 1
                    shadow_oe.oe.F_RULING = self.grating_ruling_type
                    shadow_oe.oe.RULING = self.grating_ruling_density
                elif self.grating_ruling_type == 2:
                    shadow_oe.oe.F_GRATING = 1
                    shadow_oe.oe.F_RULING = 2
                    shadow_oe.oe.HOLO_R1  = self.grating_holo_left_distance
                    shadow_oe.oe.HOLO_R2  = self.grating_holo_right_distance
                    shadow_oe.oe.HOLO_DEL = self.grating_holo_left_incidence_angle
                    shadow_oe.oe.HOLO_GAM = self.grating_holo_right_incidence_angle
                    shadow_oe.oe.HOLO_W   = self.grating_holo_recording_wavelength
                    shadow_oe.oe.HOLO_RT1 = self.grating_holo_left_azimuth_from_y
                    shadow_oe.oe.HOLO_RT2 = self.grating_holo_right_azimuth_from_y
                    shadow_oe.oe.F_PW = self.grating_holo_pattern_type
                    shadow_oe.oe.F_PW_C = self.grating_holo_cylindrical_source
                    shadow_oe.oe.F_VIRTUAL = self.grating_holo_source_type
                elif self.grating_ruling_type == 3:
                    shadow_oe.oe.F_GRATING = 1
                    shadow_oe.oe.F_RULING = 3
                    shadow_oe.oe.AZIM_FAN = self.grating_groove_pole_azimuth_from_y
                    shadow_oe.oe.DIST_FAN = self.grating_groove_pole_distance
                    shadow_oe.oe.COMA_FAC = self.grating_coma_correction_factor
                elif self.grating_ruling_type == 4:
                    shadow_oe.oe.F_GRATING = 1
                    shadow_oe.oe.F_RULING = 5
                    shadow_oe.oe.F_RUL_ABS = self.grating_poly_signed_absolute
                    shadow_oe.oe.RULING = self.grating_ruling_density
                    shadow_oe.oe.RUL_A1 = self.grating_poly_coeff_1
                    shadow_oe.oe.RUL_A2 = self.grating_poly_coeff_2
                    shadow_oe.oe.RUL_A3 = self.grating_poly_coeff_3
                    shadow_oe.oe.RUL_A4 = self.grating_poly_coeff_4
                if self.grating_auto_setting == 0:
                    shadow_oe.oe.F_CENTRAL=0
                else:
                    shadow_oe.oe.F_CENTRAL = 1
                    shadow_oe.oe.F_PHOT_CENT = self.grating_units_in_use
                    shadow_oe.oe.PHOT_CENT = self.grating_photon_energy
                    shadow_oe.oe.R_LAMBDA = self.grating_photon_wavelength
                    shadow_oe.oe.F_MONO = self.grating_mount_type

                    if self.grating_mount_type != 4:
                        shadow_oe.oe.F_HUNT = 1
                        shadow_oe.oe.HUNT_H = 0.0
                        shadow_oe.oe.HUNT_L = 0.0
                        shadow_oe.oe.BLAZE = 0.0
                    else:
                        shadow_oe.oe.F_HUNT = self.grating_hunter_grating_selected+1
                        shadow_oe.oe.HUNT_H = self.grating_hunter_distance_between_beams
                        shadow_oe.oe.HUNT_L = self.grating_hunter_monochromator_length
                        shadow_oe.oe.BLAZE = self.grating_hunter_blaze_angle

            if self.is_infinite == 0:
                shadow_oe.oe.FHIT_C = 0
            else:
                shadow_oe.oe.FHIT_C = 1
                shadow_oe.oe.FSHAPE = (self.mirror_shape+1)
                shadow_oe.oe.RLEN1  = self.dim_y_plus
                shadow_oe.oe.RLEN2  = self.dim_y_minus
                shadow_oe.oe.RWIDX1 = self.dim_x_plus
                shadow_oe.oe.RWIDX2 = self.dim_x_minus

            #####################################
            # ADVANCED SETTING
            #####################################

            if self.modified_surface == 1:
                 if self.ms_type_of_defect == 0:
                     shadow_oe.oe.F_RIPPLE = 1
                     shadow_oe.oe.F_G_S = 0
                     shadow_oe.oe.X_RIP_AMP = self.ms_ripple_ampli_x
                     shadow_oe.oe.X_RIP_WAV = self.ms_ripple_wavel_x
                     shadow_oe.oe.X_PHASE   = self.ms_ripple_phase_x
                     shadow_oe.oe.Y_RIP_AMP = self.ms_ripple_ampli_y
                     shadow_oe.oe.Y_RIP_WAV = self.ms_ripple_wavel_y
                     shadow_oe.oe.Y_PHASE   = self.ms_ripple_phase_y
                     shadow_oe.oe.FILE_RIP  = b''
                 else:
                     shadow_oe.oe.F_RIPPLE = 1
                     shadow_oe.oe.F_G_S = self.ms_type_of_defect
                     shadow_oe.oe.X_RIP_AMP = 0.0
                     shadow_oe.oe.X_RIP_WAV = 0.0
                     shadow_oe.oe.X_PHASE   = 0.0
                     shadow_oe.oe.Y_RIP_AMP = 0.0
                     shadow_oe.oe.Y_RIP_WAV = 0.0
                     shadow_oe.oe.Y_PHASE   = 0.0
                     shadow_oe.oe.FILE_RIP  = bytes(self.ms_defect_file_name, 'utf-8')

            elif self.modified_surface == 2:
                shadow_oe.oe.F_FACET = 1
                shadow_oe.oe.FILE_FAC=bytes(self.ms_file_facet_descr, 'utf-8')
                shadow_oe.oe.F_FAC_LATT=self.ms_lattice_type
                shadow_oe.oe.F_FAC_ORIENT=self.ms_orientation
                shadow_oe.oe.F_POLSEL=self.ms_lattice_type+1
                shadow_oe.oe.RFAC_LENX=self.ms_facet_width_x
                shadow_oe.oe.RFAC_PHAX=self.ms_facet_phase_x
                shadow_oe.oe.RFAC_DELX1=self.ms_dead_width_x_minus
                shadow_oe.oe.RFAC_DELX2=self.ms_dead_width_x_plus
                shadow_oe.oe.RFAC_LENY=self.ms_facet_width_y
                shadow_oe.oe.RFAC_PHAY=self.ms_facet_phase_y
                shadow_oe.oe.RFAC_DELY1=self.ms_dead_width_y_minus
                shadow_oe.oe.RFAC_DELY2=self.ms_dead_width_y_plus
            elif self.modified_surface == 3:
                shadow_oe.oe.F_ROUGHNESS = 1
                shadow_oe.oe.FILE_ROUGH=bytes(self.ms_file_surf_roughness, 'utf-8')
                shadow_oe.oe.ROUGH_X=self.ms_roughness_rms_x
                shadow_oe.oe.ROUGH_Y=self.ms_roughness_rms_y
            elif self.modified_surface == 4:
                shadow_oe.oe.F_KOMA = 1
                shadow_oe.oe.F_KOMA_CA=self.ms_specify_rz2
                shadow_oe.oe.FILE_KOMA=bytes(self.ms_file_with_parameters_rz, 'utf-8')
                shadow_oe.oe.FILE_KOMA_CA=bytes(self.ms_file_with_parameters_rz2, 'utf-8')
                shadow_oe.oe.F_KOMA_BOUNCE=self.ms_save_intercept_bounces
            elif self.modified_surface == 5:
                shadow_oe.oe.F_SEGMENT = 1
                shadow_oe.oe.ISEG_XNUM=self.ms_number_of_segments_x
                shadow_oe.oe.ISEG_YNUM=self.ms_number_of_segments_y
                shadow_oe.oe.SEG_LENX=self.ms_length_of_segments_x
                shadow_oe.oe.SEG_LENY=self.ms_length_of_segments_y
                shadow_oe.oe.FILE_SEGMENT=bytes(self.ms_file_orientations, 'utf-8')
                shadow_oe.oe.FILE_SEGP=bytes(self.ms_file_polynomial, 'utf-8')

            if self.mirror_movement == 1:
                 shadow_oe.oe.F_MOVE=1
                 shadow_oe.oe.OFFX=self.mm_mirror_offset_x
                 shadow_oe.oe.OFFY=self.mm_mirror_offset_y
                 shadow_oe.oe.OFFZ=self.mm_mirror_offset_z
                 shadow_oe.oe.X_ROT=self.mm_mirror_rotation_x
                 shadow_oe.oe.Y_ROT=self.mm_mirror_rotation_y
                 shadow_oe.oe.Z_ROT=self.mm_mirror_rotation_z

            if self.source_movement == 1:
                 shadow_oe.oe.FSTAT=1
                 shadow_oe.oe.RTHETA=self.sm_angle_of_incidence
                 shadow_oe.oe.RDSOUR=self.sm_distance_from_mirror
                 shadow_oe.oe.ALPHA_S=self.sm_z_rotation
                 shadow_oe.oe.OFF_SOUX=self.sm_offset_x_mirr_ref_frame
                 shadow_oe.oe.OFF_SOUY=self.sm_offset_y_mirr_ref_frame
                 shadow_oe.oe.OFF_SOUZ=self.sm_offset_z_mirr_ref_frame
                 shadow_oe.oe.X_SOUR=self.sm_offset_x_source_ref_frame
                 shadow_oe.oe.Y_SOUR=self.sm_offset_y_source_ref_frame
                 shadow_oe.oe.Z_SOUR=self.sm_offset_z_source_ref_frame
                 shadow_oe.oe.X_SOUR_ROT=self.sm_rotation_around_x
                 shadow_oe.oe.Y_SOUR_ROT=self.sm_rotation_around_y
                 shadow_oe.oe.Z_SOUR_ROT=self.sm_rotation_around_z

            shadow_oe.oe.FWRITE=self.file_to_write_out

            if self.graphical_options.is_crystal and self.diffraction_calculation == 1:
                shadow_oe.oe.F_ANGLE = 1
            else:
                shadow_oe.oe.F_ANGLE = self.write_out_inc_ref_angles

    def doSpecificSetting(self, shadow_oe):
        pass

    def checkFields(self):
        if self.graphical_options.is_screen_slit:
            self.source_plane_distance = ShadowGui.checkPositiveNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = ShadowGui.checkPositiveNumber(self.image_plane_distance, "Image plane distance")

            if self.source_movement == 1:
                self.sm_distance_from_mirror = ShadowGui.checkPositiveNumber(self.sm_distance_from_mirror, "Source Movement: Distance from O.E.")
        elif self.graphical_options.is_empty:
            self.source_plane_distance = ShadowGui.checkPositiveNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = ShadowGui.checkPositiveNumber(self.image_plane_distance, "Image plane distance")

            if self.source_movement == 1:
                self.sm_distance_from_mirror = ShadowGui.checkPositiveNumber(self.sm_distance_from_mirror, "Source Movement: Distance from O.E.")
        else:
            self.source_plane_distance = ShadowGui.checkPositiveNumber(self.source_plane_distance, "Source plane distance")
            self.image_plane_distance = ShadowGui.checkPositiveNumber(self.image_plane_distance, "Image plane distance")

            if self.surface_shape_parameters == 0:
                if (self.is_cylinder==1 and (self.cylinder_orientation==1 or self.cylinder_orientation==3)):
                   if not self.graphical_options.is_spheric:
                       raise Exception("Automatic calculation of the sagittal focus supported only for Spheric O.E.")
                else:
                   if not self.focii_and_continuation_plane == 0:
                        self.object_side_focal_distance = ShadowGui.checkPositiveNumber(self.object_side_focal_distance, "Object side focal distance")
                        self.image_side_focal_distance = ShadowGui.checkPositiveNumber(self.image_side_focal_distance, "Image side focal distance")

                   if self.graphical_options.is_paraboloid:
                        self.focus_location = ShadowGui.checkPositiveNumber(self.focus_location, "Focus location")
            else:
               if self.graphical_options.is_spheric:
                   self.spherical_radius = ShadowGui.checkPositiveNumber(self.spherical_radius, "Spherical radius")
               elif self.graphical_options.is_toroidal:
                   self.torus_major_radius = ShadowGui.checkPositiveNumber(self.torus_major_radius, "Torus major radius")
                   self.torus_minor_radius = ShadowGui.checkPositiveNumber(self.torus_minor_radius, "Torus minor radius")
               elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                   self.ellipse_hyperbola_semi_major_axis = ShadowGui.checkPositiveNumber(self.ellipse_hyperbola_semi_major_axis, "Semi major axis")
                   self.ellipse_hyperbola_semi_minor_axis = ShadowGui.checkPositiveNumber(self.ellipse_hyperbola_semi_minor_axis, "Semi minor axis")
                   self.angle_of_majax_and_pole = ShadowGui.checkPositiveNumber(self.angle_of_majax_and_pole, "Angle of MajAx and Pole")
               elif self.graphical_options.is_paraboloid:
                   self.paraboloid_parameter = ShadowGui.checkPositiveNumber(self.paraboloid_parameter, "Paraboloid parameter")

            if self.graphical_options.is_toroidal:
                self.toroidal_mirror_pole_location = ShadowGui.checkPositiveNumber(self.toroidal_mirror_pole_location, "Toroidal mirror pole location")

            if self.graphical_options.is_mirror:
                if not self.reflectivity_type == 0:
                    if self.source_of_reflectivity == 0:
                        ShadowGui.checkFile(self.file_prerefl)
                    elif self.source_of_reflectivity == 2:
                        ShadowGui.checkFile(self.file_prerefl_m)
            elif self.graphical_options.is_crystal:
                if self.diffraction_calculation == 1:
                    ShadowGui.checkFile(self.file_diffraction_profile)
                else:
                    ShadowGui.checkFile(self.file_crystal_parameters)

                    if not self.crystal_auto_setting == 0:
                        if self.units_in_use == 0:
                            self.photon_energy = ShadowGui.checkPositiveNumber(self.photon_energy, "Photon Energy")
                        elif self.units_in_use == 1:
                            self.photon_wavelength = ShadowGui.checkPositiveNumber(self.photon_wavelength,
                                                                                   "Photon Wavelength")

                    if self.mosaic_crystal == 1:
                        self.seed_for_mosaic = ShadowGui.checkPositiveNumber(self.seed_for_mosaic,
                                                                             "Crystal: Seed for mosaic")
                        self.angle_spread_FWHM = ShadowGui.checkPositiveNumber(self.angle_spread_FWHM,
                                                                               "Crystal: Angle spread FWHM")
                        self.thickness = ShadowGui.checkPositiveNumber(self.thickness, "Crystal: thickness")
                    else:
                        if self.asymmetric_cut == 1:
                            self.thickness = ShadowGui.checkPositiveNumber(self.thickness, "Crystal: thickness")
                        if self.johansson_geometry == 1:
                            self.johansson_radius = ShadowGui.checkPositiveNumber(self.johansson_radius,
                                                                                  "Crystal: Johansson radius")
            elif self.graphical_options.is_grating:
                if not self.grating_auto_setting == 0:
                    if self.grating_units_in_use == 0:
                        self.grating_photon_energy = ShadowGui.checkPositiveNumber(self.grating_photon_energy, "Photon Energy")
                    elif self.grating_units_in_use == 1:
                        self.grating_photon_wavelength = ShadowGui.checkPositiveNumber(self.grating_photon_wavelength, "Photon Wavelength")

                    if self.grating_mount_type == 4:
                        self.grating_hunter_monochromator_length = ShadowGui.checkPositiveNumber(self.grating_hunter_monochromator_length, "Monochromator length")
                        self.grating_hunter_distance_between_beams = ShadowGui.checkPositiveNumber(self.grating_hunter_distance_between_beams, "Distance between beams")

                if self.grating_ruling_type == 0 or self.grating_ruling_type == 1 or self.grating_ruling_type == 3:
                    self.grating_ruling_density = ShadowGui.checkPositiveNumber(self.grating_ruling_density, "Ruling Density")
                elif self.grating_ruling_type == 2:
                    self.grating_holo_recording_wavelength = ShadowGui.checkPositiveNumber(self.grating_holo_recording_wavelength, "Recording Wavelength")
                elif self.grating_ruling_type == 4:
                    self.grating_ruling_density = ShadowGui.checkPositiveNumber(self.grating_ruling_density, "Polynomial Line Density coeff.: constant")

            if not self.is_infinite == 0:
               self.dim_y_plus = ShadowGui.checkPositiveNumber(self.dim_y_plus, "Dimensions: y plus")
               self.dim_y_minus = ShadowGui.checkPositiveNumber(self.dim_y_minus, "Dimensions: y minus")
               self.dim_x_plus = ShadowGui.checkPositiveNumber(self.dim_x_plus, "Dimensions: x plus")
               self.dim_x_minus = ShadowGui.checkPositiveNumber(self.dim_x_minus, "Dimensions: x minus")


            #####################################
            # ADVANCED SETTING
            #####################################

            if self.modified_surface == 1:
                 if self.ms_type_of_defect == 0:
                     self.ms_ripple_ampli_x = ShadowGui.checkPositiveNumber(self.ms_ripple_ampli_x , "Modified Surface: Ripple Amplitude x")
                     self.ms_ripple_wavel_x = ShadowGui.checkPositiveNumber(self.ms_ripple_wavel_x , "Modified Surface: Ripple Wavelength x")
                     self.ms_ripple_ampli_y = ShadowGui.checkPositiveNumber(self.ms_ripple_ampli_y , "Modified Surface: Ripple Amplitude y")
                     self.ms_ripple_wavel_y = ShadowGui.checkPositiveNumber(self.ms_ripple_wavel_y , "Modified Surface: Ripple Wavelength y")
                 else:
                     ShadowGui.checkFile(self.ms_defect_file_name)
            elif self.modified_surface == 2:
                self.checkFile(self.ms_file_facet_descr)
                self.ms_facet_width_x = ShadowGui.checkPositiveNumber(self.ms_facet_width_x, "Modified Surface: Facet width x")
                self.ms_facet_phase_x = ShadowGui.checkPositiveAngle(self.ms_facet_phase_x, "Modified Surface: Facet phase x")
                self.ms_dead_width_x_minus = ShadowGui.checkPositiveNumber(self.ms_dead_width_x_minus, "Modified Surface: Dead width x minus")
                self.ms_dead_width_x_plus = ShadowGui.checkPositiveNumber(self.ms_dead_width_x_plus, "Modified Surface: Dead width x plus")
                self.ms_facet_width_y = ShadowGui.checkPositiveNumber(self.ms_facet_width_y, "Modified Surface: Facet width y")
                self.ms_facet_phase_y = ShadowGui.checkPositiveAngle(self.ms_facet_phase_y, "Modified Surface: Facet phase y")
                self.ms_dead_width_y_minus = ShadowGui.checkPositiveNumber(self.ms_dead_width_y_minus, "Modified Surface: Dead width y minus")
                self.ms_dead_width_y_plus = ShadowGui.checkPositiveNumber(self.ms_dead_width_y_plus, "Modified Surface: Dead width y plus")
            elif self.modified_surface == 3:
                ShadowGui.checkFile(self.ms_file_surf_roughness)
                self.ms_roughness_rms_x = ShadowGui.checkPositiveNumber(self.ms_roughness_rms_x, "Modified Surface: Roughness rms x")
                self.ms_roughness_rms_y = ShadowGui.checkPositiveNumber(self.ms_roughness_rms_y, "Modified Surface: Roughness rms y")
            elif self.modified_surface == 4:
                if self.ms_specify_rz2==0: ShadowGui.checkFile(self.ms_file_with_parameters_rz)
                if self.ms_specify_rz2==0: ShadowGui.checkFile(self.ms_file_with_parameters_rz2)
            elif self.modified_surface == 5:
                ShadowGui.checkFile(self.ms_file_orientations)
                ShadowGui.checkFile(self.ms_file_polynomial)
                self.ms_number_of_segments_x = ShadowGui.checkPositiveNumber(self.ms_number_of_segments_x, "Modified Surface: Number of segments x")
                self.ms_number_of_segments_y = ShadowGui.checkPositiveNumber(self.ms_number_of_segments_y, "Modified Surface: Number of segments y")
                self.ms_length_of_segments_x = ShadowGui.checkPositiveNumber(self.ms_length_of_segments_x, "Modified Surface: Length of segments x")
                self.ms_length_of_segments_y = ShadowGui.checkPositiveNumber(self.ms_length_of_segments_y, "Modified Surface: Length of segments y")

            if self.source_movement == 1:
                if self.sm_distance_from_mirror < 0: raise Exception("Source Movement: Distance from O.E.")

    def writeCalculatedFields(self, shadow_oe):
        if self.surface_shape_parameters == 0:
            if self.graphical_options.is_spheric:
                self.spherical_radius = shadow_oe.oe.RMIRR
            elif self.graphical_options.is_toroidal:
                self.torus_major_radius = shadow_oe.oe.R_MAJ
                self.torus_minor_radius = shadow_oe.oe.R_MIN
            elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                self.ellipse_hyperbola_semi_major_axis = shadow_oe.oe.AXMAJ
                self.ellipse_hyperbola_semi_minor_axis = shadow_oe.oe.AXMIN
                self.angle_of_majax_and_pole = shadow_oe.oe.ELL_THE
            elif self.graphical_options.is_paraboloid:
                self.paraboloid_parameter = shadow_oe.oe.PARAM

        if self.diffraction_calculation == 0 and self.crystal_auto_setting == 1:
            self.incidence_angle_mrad = round((math.pi*0.5-shadow_oe.oe.T_INCIDENCE)*1000, 2)
            self.reflection_angle_mrad = round((math.pi*0.5-shadow_oe.oe.T_REFLECTION)*1000, 2)
            self.calculate_incidence_angle_deg()
            self.calculate_reflection_angle_deg()

    def completeOperations(self, shadow_oe=None):
        self.setStatusMessage("Running SHADOW")

        sys.stdout = EmittingStream(textWritten=self.writeStdOut)

        if self.trace_shadow:
            grabber = TTYGrabber()
            grabber.start()

        self.progressBarSet(50)

        ###########################################
        # TODO: TO BE ADDED JUST IN CASE OF BROKEN
        #       ENVIRONMENT: MUST BE FOUND A PROPER WAY
        #       TO TEST SHADOW
        self.fixWeirdShadowBug()
        ###########################################

        beam_out = ShadowBeam.traceFromOE(self.input_beam, shadow_oe)

        if self.graphical_options.is_crystal and self.diffraction_calculation == 1:
            beam_out = self.apply_user_diffraction_profile(beam_out)

        self.writeCalculatedFields(shadow_oe)

        if self.trace_shadow:
            grabber.stop()

            for row in grabber.ttyData:
               self.writeStdOut(row)

        self.setStatusMessage("Plotting Results")

        self.plot_results(beam_out)

        self.setStatusMessage("")

        self.send("Beam", beam_out)
        self.send("Trigger", ShadowTriggerIn(new_beam=True))

    def apply_user_diffraction_profile(self, input_beam):
        str_oe_number = str(input_beam.oe_number)

        if (input_beam.oe_number < 10): str_oe_number = "0" + str_oe_number

        values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/angle." + str_oe_number))

        beam_incident_angles = values[:, 1]
        beam_flags = values[:, 3]
        bragg_angles = []

        for index in range(0, len(input_beam.beam.rays)):
            wavelength = ShadowPhysics.getWavelengthfromShadowK(input_beam.beam.rays[index, 10])
            bragg_angles.append(90 - math.degrees(ShadowPhysics.calculateBraggAngle(wavelength, 1, 1, 1, 5.43123)))
            if beam_flags[index] == -55000.0: input_beam.beam.rays[index, 9] = 1

        delta_thetas = beam_incident_angles - bragg_angles

        if self.file_diffraction_profile.startswith('/'):
            values = numpy.loadtxt(os.path.abspath(self.file_diffraction_profile))
        else:
            values = numpy.loadtxt(os.path.abspath(os.path.curdir + "/" + self.file_diffraction_profile))

        crystal_incident_angles = values[:, 0]
        crystal_reflectivities = values[:, 1]

        interpolated_weight = []

        for index in range(0, len(delta_thetas)):
            values_up = crystal_incident_angles[numpy.where(crystal_incident_angles >= delta_thetas[index])]
            values_down = crystal_incident_angles[numpy.where(crystal_incident_angles < delta_thetas[index])]

            if len(values_up) == 0:
                refl_up = []
                refl_up.append(crystal_reflectivities[0])
            else:
                refl_up = crystal_reflectivities[numpy.where(crystal_incident_angles == values_up[-1])]

            if len(values_down) == 0:
                refl_down = []
                refl_down.append(crystal_reflectivities[-1])
            else:
                refl_down = crystal_reflectivities[numpy.where(crystal_incident_angles == values_down[0])]

            interpolated_weight.append(numpy.sqrt((refl_up[0] + refl_down[0]) / 2))

        output_beam = input_beam.duplicate()

        for index in range(0, len(output_beam.beam.rays)):
            output_beam.beam.rays[index, 6] = output_beam.beam.rays[index, 6] * interpolated_weight[index]
            output_beam.beam.rays[index, 7] = output_beam.beam.rays[index, 7] * interpolated_weight[index]
            output_beam.beam.rays[index, 8] = output_beam.beam.rays[index, 8] * interpolated_weight[index]
            output_beam.beam.rays[index, 15] = output_beam.beam.rays[index, 15] * interpolated_weight[index]
            output_beam.beam.rays[index, 16] = output_beam.beam.rays[index, 16] * interpolated_weight[index]
            output_beam.beam.rays[index, 17] = output_beam.beam.rays[index, 17] * interpolated_weight[index]

        return output_beam

    def traceOpticalElement(self):
        try:
            self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowGui.checkEmptyBeam(self.input_beam):
                if ShadowGui.checkGoodBeam(self.input_beam):
                    self.checkFields()

                    shadow_oe = self.instantiateShadowOE()

                    self.populateFields(shadow_oe)
                    self.doSpecificSetting(shadow_oe)

                    self.progressBarSet(10)

                    self.completeOperations(shadow_oe)
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                       str(exception), QtGui.QMessageBox.Ok)

            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def setBeam(self, beam):
        self.onReceivingInput()

        if ShadowGui.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.traceOpticalElement()

    def setPreProcessorData(self, data):
        if data is not None:
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                self.file_crystal_parameters=data.bragg_data_file

            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.file_prerefl=data.prerefl_data_file

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                self.file_prerefl_m=data.m_layer_data_file_dat
                # TODO: file .sha!

            if data.waviness_data_file != ShadowPreProcessorData.NONE:
                self.ms_defect_file_name = data.waviness_data_file

    def deserialize(self, shadow_file):
        if self.graphical_options.is_screen_slit:
            raise Exception("Operation non supported for Screen/Slit Widget")
        else:
            try:
                self.source_plane_distance = float(shadow_file.getProperty("T_SOURCE"))
                self.image_plane_distance = float(shadow_file.getProperty("T_IMAGE"))
                self.incidence_angle_deg = float(shadow_file.getProperty("T_INCIDENCE"))
                self.reflection_angle_deg = float(shadow_file.getProperty("T_REFLECTION"))
                self.mirror_orientation_angle = int(float(shadow_file.getProperty("ALPHA"))/90)

                if self.graphical_options.is_curved:
                    self.is_cylinder = int(shadow_file.getProperty("FCYL"))

                    if self.is_cylinder == 1:
                        self.cylinder_orientation = int(float(shadow_file.getProperty("CIL_ANG"))/90)

                    if self.graphical_options.is_conic_coefficients:
                        self.conic_coefficient_0 = float(shadow_file.getProperty("CCC(1)"))
                        self.conic_coefficient_1 = float(shadow_file.getProperty("CCC(2)"))
                        self.conic_coefficient_2 = float(shadow_file.getProperty("CCC(3)"))
                        self.conic_coefficient_3 = float(shadow_file.getProperty("CCC(4)"))
                        self.conic_coefficient_4 = float(shadow_file.getProperty("CCC(5)"))
                        self.conic_coefficient_5 = float(shadow_file.getProperty("CCC(6)"))
                        self.conic_coefficient_6 = float(shadow_file.getProperty("CCC(7)"))
                        self.conic_coefficient_7 = float(shadow_file.getProperty("CCC(8)"))
                        self.conic_coefficient_8 = float(shadow_file.getProperty("CCC(9)"))
                        self.conic_coefficient_9 = float(shadow_file.getProperty("CCC(10)"))
                    else:
                        self.surface_shape_parameters = int(shadow_file.getProperty("F_EXT"))

                        if self.surface_shape_parameters == 0:

                            if int(shadow_file.getProperty("F_DEFAULT")) == 1:
                                self.focii_and_continuation_plane = 0
                            elif int(shadow_file.getProperty("F_DEFAULT")) == 0:
                                self.focii_and_continuation_plane = 1

                            if self.focii_and_continuation_plane == 1:
                                self.object_side_focal_distance =  float(shadow_file.getProperty("SSOUR"))
                                self.image_side_focal_distance = float(shadow_file.getProperty("SIMAG"))
                                self.incidence_angle_respect_to_normal = float(shadow_file.getProperty("THETA"))

                            if self.graphical_options.is_paraboloid: self.focus_location = float(shadow_file.getProperty("F_SIDE"))
                        else:
                           if self.graphical_options.is_spheric:
                               self.spherical_radius = float(shadow_file.getProperty("RMIRR"))
                           elif self.graphical_options.is_toroidal:
                               self.torus_major_radius = float(shadow_file.getProperty("R_MAJ"))
                               self.torus_minor_radius = float(shadow_file.getProperty("R_MIN"))
                           elif self.graphical_options.is_hyperboloid or self.graphical_options.is_ellipsoidal:
                               self.ellipse_hyperbola_semi_major_axis = float(shadow_file.getProperty("AXMAJ"))
                               self.ellipse_hyperbola_semi_minor_axis = float(shadow_file.getProperty("AXMIN"))
                               self.angle_of_majax_and_pole = float(shadow_file.getProperty("ELL_THE"))
                           elif self.graphical_options.is_paraboloid:
                               self.paraboloid_parameter = float(shadow_file.getProperty("PARAM"))

                    if self.graphical_options.is_toroidal: self.toroidal_mirror_pole_location = int(shadow_file.getProperty("F_TORUS"))

                    self.surface_curvature == int(shadow_file.getProperty("F_CONVEX"))

                if self.graphical_options.is_mirror:
                    self.reflectivity_type = int(shadow_file.getProperty("F_REFLEC"))

                    if self.reflectivity_type > 0:
                        self.source_of_reflectivity = int(shadow_file.getProperty("F_REFL"))

                        if self.source_of_reflectivity == 0:
                            self.file_prerefl = shadow_file.getProperty("FILE_REFL")
                        elif self.source_of_reflectivity == 1:
                            self.alpha = float(shadow_file.getProperty("ALFA"))
                            self.gamma = float(shadow_file.getProperty("GAMMA"))
                        elif self.source_of_reflectivity == 2:
                            self.file_prerefl_m = shadow_file.getProperty("FILE_REFL")
                            self.m_layer_tickness = float(shadow_file.getProperty("F_THICK"))
                elif self.graphical_options.is_crystal:
                    self.diffraction_calculation = 0
                    self.diffraction_geometry = int(shadow_file.getProperty("F_REFRAC"))
                    self.file_crystal_parameters = shadow_file.getProperty("FILE_REFL")

                    self.crystal_auto_setting = int(shadow_file.getProperty("F_CENTRAL"))
                    self.mosaic_crystal = int(shadow_file.getProperty("F_MOSAIC"))
                    self.asymmetric_cut = int(shadow_file.getProperty("F_BRAGG_A"))
                    self.johansson_geometry = int(shadow_file.getProperty("F_JOHANSSON"))

                    if self.crystal_auto_setting == 1:
                        self.units_in_use = int(shadow_file.getProperty("F_PHOT_CENT"))
                        self.photon_energy = float(shadow_file.getProperty("PHOT_CENT"))
                        self.photon_wavelength = float(shadow_file.getProperty("R_LAMBDA"))

                    if self.mosaic_crystal==1:
                        self.seed_for_mosaic = int(shadow_file.getProperty("MOSAIC_SEED"))
                        self.angle_spread_FWHM = float(shadow_file.getProperty("SPREAD_MOS"))
                        self.thickness = float(shadow_file.getProperty("THICKNESS"))
                    else:
                        if self.asymmetric_cut == 1:
                            self.planes_angle = float(shadow_file.getProperty("A_BRAGG"))
                            self.below_onto_bragg_planes = float(shadow_file.getProperty("ORDER"))
                            self.thickness = float(shadow_file.getProperty("THICKNESS"))
                        if self.johansson_geometry == 1:
                            self.johansson_radius = float(shadow_file.getProperty("R_JOHANSSON"))
                elif self.graphical_options.is_grating:
                    f_ruling = int(shadow_file.getProperty("F_RULING"))

                    if f_ruling == 4:
                        raise Exception("Grating with ruling type not supported: F_RULING=4")
                    else:
                        if f_ruling == 5:
                            self.grating_ruling_type = 4
                        else:
                            self.grating_ruling_type = f_ruling

                    if self.grating_ruling_type == 0 or self.grating_ruling_type == 1:
                        self.grating_ruling_density = float(shadow_file.getProperty("RULING"))
                    elif self.grating_ruling_type == 2:
                        self.grating_holo_left_distance         = float(shadow_file.getProperty("HOLO_R1"))
                        self.grating_holo_right_distance        = float(shadow_file.getProperty("HOLO_R2"))
                        self.grating_holo_left_incidence_angle  = float(shadow_file.getProperty("HOLO_DEL"))
                        self.grating_holo_right_incidence_angle = float(shadow_file.getProperty("HOLO_GAM"))
                        self.grating_holo_recording_wavelength  = float(shadow_file.getProperty("HOLO_W"))
                        self.grating_holo_left_azimuth_from_y   = float(shadow_file.getProperty("HOLO_RT1"))
                        self.grating_holo_right_azimuth_from_y  = float(shadow_file.getProperty("HOLO_RT2"))
                        self.grating_holo_pattern_type = int(shadow_file.getProperty("F_PW"))
                        self.grating_holo_cylindrical_source = int(shadow_file.getProperty("F_PW_C"))
                        self.grating_holo_source_type = int(shadow_file.getProperty("F_VIRTUAL"))
                    elif self.grating_ruling_type == 3:
                        self.grating_groove_pole_azimuth_from_y = float(shadow_file.getProperty("AZIM_FAN"))
                        self.grating_groove_pole_distance = float(shadow_file.getProperty("DIST_FAN"))
                        self.grating_coma_correction_factor = float(shadow_file.getProperty("COMA_FAC"))
                    elif self.grating_ruling_type == 4:
                        self.grating_ruling_density = float(shadow_file.getProperty("RULING"))
                        self.grating_poly_coeff_1   = float(shadow_file.getProperty("RUL_A1"))
                        self.grating_poly_coeff_2   = float(shadow_file.getProperty("RUL_A2"))
                        self.grating_poly_coeff_3   = float(shadow_file.getProperty("RUL_A3"))
                        self.grating_poly_coeff_4   = float(shadow_file.getProperty("RUL_A4"))
                        self.grating_poly_signed_absolute = int(shadow_file.getProperty("F_RUL_ABS"))

                    self.grating_auto_setting = int(shadow_file.getProperty("F_CENTRAL"))

                    if self.grating_auto_setting == 1:
                        self.grating_mount_type = int(shadow_file.getProperty("F_MONO"))
                        self.grating_units_in_use = int(shadow_file.getProperty("F_PHOT_CENT"))
                        self.grating_photon_energy = float(shadow_file.getProperty("PHOT_CENT"))
                        self.grating_photon_wavelength = float(shadow_file.getProperty("R_LAMBDA"))

                        if self.grating_mount_type == 4:
                            self.grating_hunter_grating_selected = int(shadow_file.getProperty("F_HUNT"))-1
                            self.grating_hunter_distance_between_beams = float(shadow_file.getProperty("HUNT_H"))
                            self.grating_hunter_monochromator_length   = float(shadow_file.getProperty("HUNT_L"))
                            self.grating_hunter_blaze_angle            = float(shadow_file.getProperty("BLAZE"))

                self.is_infinite = int(shadow_file.getProperty("FHIT_C"))

                if self.is_infinite == 1:
                    self.mirror_shape = int(shadow_file.getProperty("FSHAPE")) - 1
                    self.dim_y_plus  = float(shadow_file.getProperty("RLEN1"))
                    self.dim_y_minus = float(shadow_file.getProperty("RLEN2"))
                    self.dim_x_plus  = float(shadow_file.getProperty("RWIDX1"))
                    self.dim_x_minus = float(shadow_file.getProperty("RWIDX2"))

                #####################################
                # ADVANCED SETTING
                #####################################

                self.modified_surface = 0

                if int(shadow_file.getProperty("F_RIPPLE")) == 1: self.modified_surface = 1
                elif int(shadow_file.getProperty("F_FACET")) == 1: self.modified_surface = 2
                elif int(shadow_file.getProperty("F_ROUGHNESS")) == 1: self.modified_surface = 3
                elif int(shadow_file.getProperty("F_KOMA")) == 1: self.modified_surface = 4
                elif int(shadow_file.getProperty("F_SEGMENT")) == 1: self.modified_surface = 5

                if self.modified_surface == 1:
                     self.ms_type_of_defect = int(shadow_file.getProperty("F_G_S"))

                     if self.ms_type_of_defect == 0:
                         self.ms_ripple_ampli_x = float(shadow_file.getProperty("X_RIP_AMP"))
                         self.ms_ripple_wavel_x = float(shadow_file.getProperty("X_RIP_WAV"))
                         self.ms_ripple_phase_x = float(shadow_file.getProperty("X_PHASE"))
                         self.ms_ripple_ampli_y = float(shadow_file.getProperty("Y_RIP_AMP"))
                         self.ms_ripple_wavel_y = float(shadow_file.getProperty("Y_RIP_WAV"))
                         self.ms_ripple_phase_y = float(shadow_file.getProperty("Y_PHASE"))
                     else:
                         self.ms_defect_file_name = shadow_file.getProperty("FILE_RIP")
                elif self.modified_surface == 2:
                     self.ms_file_facet_descr = shadow_file.getProperty("FILE_FAC")
                     self.ms_lattice_type = int(shadow_file.getProperty("F_FAC_LATT"))
                     self.ms_orientation = int(shadow_file.getProperty("F_FAC_ORIENT"))
                     self.ms_lattice_type = int(shadow_file.getProperty("F_POLSEL"))-1
                     self.ms_facet_width_x = float(shadow_file.getProperty("RFAC_LENX"))
                     self.ms_facet_phase_x = float(shadow_file.getProperty("RFAC_PHAX"))
                     self.ms_dead_width_x_minus = float(shadow_file.getProperty("RFAC_DELX1"))
                     self.ms_dead_width_x_plus = float(shadow_file.getProperty("RFAC_DELX2"))
                     self.ms_facet_width_y = float(shadow_file.getProperty("RFAC_LENY"))
                     self.ms_facet_phase_y = float(shadow_file.getProperty("RFAC_PHAY"))
                     self.ms_dead_width_y_minus = float(shadow_file.getProperty("RFAC_DELY1"))
                     self.ms_dead_width_y_plus = float(shadow_file.getProperty("RFAC_DELY2"))
                elif self.modified_surface == 3:
                    self.ms_file_surf_roughness = shadow_file.getProperty("FILE_ROUGH")
                    self.ms_roughness_rms_x = float(shadow_file.getProperty("ROUGH_X"))
                    self.ms_roughness_rms_y = float(shadow_file.getProperty("ROUGH_Y"))
                elif self.modified_surface == 4:
                    self.ms_specify_rz2 = int(shadow_file.getProperty("F_KOMA_CA"))
                    self.ms_file_with_parameters_rz = shadow_file.getProperty("FILE_KOMA")
                    self.ms_file_with_parameters_rz2 = shadow_file.getProperty("FILE_KOMA_CA")
                    self.ms_save_intercept_bounces = int(shadow_file.getProperty("F_KOMA_BOUNCE"))
                elif self.modified_surface == 5:
                    self.ms_number_of_segments_x = int(shadow_file.getProperty("ISEG_XNUM"))
                    self.ms_number_of_segments_y = int(shadow_file.getProperty("ISEG_YNUM"))
                    self.ms_length_of_segments_x = float(shadow_file.getProperty("SEG_LENX"))
                    self.ms_length_of_segments_y = float(shadow_file.getProperty("SEG_LENY"))
                    self.ms_file_orientations = shadow_file.getProperty("FILE_SEGMENT")
                    self.ms_file_polynomial = shadow_file.getProperty("FILE_SEGP")

                self.mirror_movement = int(shadow_file.getProperty("F_MOVE"))

                if self.mirror_movement == 1:
                     self.mm_mirror_offset_x = float(shadow_file.getProperty("OFFX"))
                     self.mm_mirror_offset_y = float(shadow_file.getProperty("OFFY"))
                     self.mm_mirror_offset_z = float(shadow_file.getProperty("OFFZ"))
                     self.mm_mirror_rotation_x = float(shadow_file.getProperty("X_ROT"))
                     self.mm_mirror_rotation_y = float(shadow_file.getProperty("Y_ROT"))
                     self.mm_mirror_rotation_z = float(shadow_file.getProperty("Z_ROT"))

                self.source_movement = int(shadow_file.getProperty("FSTAT"))

                if self.source_movement == 1:
                     self.sm_angle_of_incidence = float(shadow_file.getProperty("RTHETA"))
                     self.sm_distance_from_mirror = float(shadow_file.getProperty("RDSOUR"))
                     self.sm_z_rotation = float(shadow_file.getProperty("ALPHA_S"))
                     self.sm_offset_x_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUX"))
                     self.sm_offset_y_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUY"))
                     self.sm_offset_z_mirr_ref_frame = float(shadow_file.getProperty("OFF_SOUZ"))
                     self.sm_offset_x_source_ref_frame = float(shadow_file.getProperty("X_SOUR"))
                     self.sm_offset_y_source_ref_frame = float(shadow_file.getProperty("Y_SOUR"))
                     self.sm_offset_z_source_ref_frame = float(shadow_file.getProperty("Z_SOUR"))
                     self.sm_rotation_around_x = float(shadow_file.getProperty("X_SOUR_ROT"))
                     self.sm_rotation_around_y = float(shadow_file.getProperty("Y_SOUR_ROT"))
                     self.sm_rotation_around_z = float(shadow_file.getProperty("Z_SOUR_ROT"))

                self.file_to_write_out = int(shadow_file.getProperty("FWRITE"))
                self.write_out_inc_ref_angles = int(shadow_file.getProperty("F_ANGLE"))
            except Exception as exception:
                raise BlockingIOError("O.E. failed to load, bad file format: " + exception.args[0])
                
            self.setupUI()


    def setupUI(self):
        if self.graphical_options.is_screen_slit:
            self.set_Aperturing()
            self.set_Absorption()
        else:
            self.calculate_incidence_angle_mrad()
            self.calculate_reflection_angle_mrad()

            if self.graphical_options.is_curved:
                if not self.graphical_options.is_conic_coefficients:
                    self.set_IntExt_Parameters()
                    self.set_isCyl_Parameters()

            if self.graphical_options.is_mirror:
                self.set_Refl_Parameters()
            elif self.graphical_options.is_crystal:
                self.set_Mosaic()
                self.set_DiffractionCalculation()
            elif self.graphical_options.is_grating:
                self.set_GratingAutosetting()
                self.set_GratingRulingType()

            self.set_Dim_Parameters()
            self.set_ModifiedSurface()

        self.set_MirrorMovement()
        self.set_SourceMovement()
