import copy
import os
import random
import sys
import numpy

from PyQt4.QtGui import QMessageBox

from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowSource, ShadowOpticalElement
from orangecontrib.shadow.util.shadow_util import ShadowPhysics, ShadowPreProcessor

from srxraylib.util.data_structures import ScaledArray, ScaledMatrix
from srxraylib.waveoptics.wavefront import Wavefront1D
from srxraylib.waveoptics import propagator

'''
Diffraction Plane
ghy_diff_plane = 1 : X
ghy_diff_plane = 2 : Z
ghy_diff_plane = 3 : 2D NOT USED

ghy_nf = 1 generate near-field profile

'''

class HybridInputParameters(object):
    widget=None

    shadow_beam = ShadowBeam()

    ghy_n_oe = -1 # not needed, oe number form beam
    ghy_n_screen = -1 # not needed, but kept for compatibility with old

    ghy_diff_plane = 2
    ghy_calcType = 1

    ghy_focallength = -1
    ghy_distance = -1

    ghy_usemirrorfile = 1
    ghy_mirrorfile = "mirror.dat"
    ghy_profile_dimension = 1

    ghy_nf = 1

    ghy_nbins_x = 200
    ghy_nbins_z = 200
    ghy_npeak = 20
    ghy_fftnpts = 1e6
    ghy_lengthunit = 1

    def __init__(self):
        super().__init__()

    def dump(self):
        return self.__dict__

class HybridCalculationParameters(object):
    shadow_oe_end = None

    original_beam_history = None

    image_plane_beam = None
    image_plane_cursor = None
    ff_beam = None
    nf_beam = None

    screen_plane_beam = None
    screen_plane_cursor = None

    # Star
    xx_star = None
    zz_star = None

    # Screen
    wenergy     = None
    wwavelength = None
    xp_screen   = None
    yp_screen   = None
    zp_screen   = None
    ref_screen  = None
    xx_screen = None
    ghy_x_min = 0.0
    ghy_x_max = 0.0
    zz_screen = None
    ghy_z_min = 0.0
    ghy_z_max = 0.0
    dx_ray = None
    dz_ray = None
    gwavelength = 0.0
    gknum = 0.0

    # Mirror
    xx_mirr = None
    zz_mirr = None
    angle_inc = None

    # Mirror Surface
    w_mirr_1D_values = None
    w_mirr_2D_values = None

    # Mirror Fitted Functions
    wangle_x = None
    wangle_z = None
    wl_x     = None
    wl_z     = None

    xx_focal_ray = None
    zz_focal_ray = None

    w_mirror_lx = None
    w_mirror_lz = None

    wIray_x = None
    wIray_z = None
    wIray_2d = None

    # Propagation output
    dif_xp = None
    dif_zp = None
    dif_x = None
    dif_z = None

    # Conversion Output
    dx_conv = None
    dz_conv = None
    xx_image_ff = None
    zz_image_ff = None
    xx_image_nf = None
    zz_image_nf = None

##########################################################################

def hy_run(input_parameters=HybridInputParameters()):
    try:
        calculation_parameters=HybridCalculationParameters()

        input_parameters.widget.status_message("Starting HYBRID calculation")
        input_parameters.widget.set_progress_bar(0)

        hy_readfiles(input_parameters, calculation_parameters)	#Read shadow output files needed by HYBRID

        input_parameters.widget.status_message("Analysis of Input Beam and OE completed")
        input_parameters.widget.set_progress_bar(10)

        hy_init(input_parameters, calculation_parameters)		#Calculate functions needed to construct exit pupil function

        input_parameters.widget.status_message("Initialization completed")
        input_parameters.widget.set_progress_bar(20)

        input_parameters.widget.status_message("Start Wavefront Propagation")
        hy_prop(input_parameters, calculation_parameters)	    #Perform wavefront propagation

        input_parameters.widget.status_message("Start Ray Resampling")
        input_parameters.widget.set_progress_bar(80)

        hy_conv(input_parameters, calculation_parameters)	    #Perform ray resampling

        input_parameters.widget.status_message("Creating Output Shadow Beam")

        hy_create_shadow_beam(input_parameters, calculation_parameters)

        return calculation_parameters
    except Exception as exception:
        raise exception

##########################################################################

def hy_readfiles(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):

    if input_parameters.ghy_n_oe < 0 and input_parameters.shadow_beam._oe_number == 0: # TODO!!!!!
        raise Exception("Source calculation not yet supported")

    if input_parameters.ghy_n_oe < 0:
        str_n_oe = str(input_parameters.shadow_beam._oe_number)

        if input_parameters.shadow_beam._oe_number < 10:
            str_n_oe = "0" + str_n_oe

        fileShadowScreen = "screen." + str_n_oe + "01"

        # Before ray-tracing save the original history:

        calculation_parameters.original_beam_history = input_parameters.shadow_beam.getOEHistory()

        shadow_oe_original = input_parameters.shadow_beam.getOEHistory(input_parameters.shadow_beam._oe_number)._shadow_oe_start
        input_beam = input_parameters.shadow_beam.getOEHistory(input_parameters.shadow_beam._oe_number)._input_beam
        shadow_oe = shadow_oe_original.duplicate() # no changes to the original object!


        if input_parameters.ghy_calcType == 3:
            if input_parameters.ghy_usemirrorfile == 0: # use EMBEDDED one in OE
                if shadow_oe._oe.F_RIPPLE == 1 and shadow_oe._oe.F_G_S == 2:
                    input_parameters.ghy_mirrorfile = shadow_oe._oe.FILE_RIP

                    # disable slope error calculation for OE, must be done by HYBRID!
                    shadow_oe._oe.F_RIPPLE = 0
                else:
                    raise Exception("O.E. has not Surface Error file (setup Advanced Option->Modified Surface:\n\nModification Type = Surface Error\nType of Defect: external spline)")
            else:
                if shadow_oe._oe.F_RIPPLE != 0:
                    if QMessageBox.No == showConfirmMessage("Possible incongruence", "Hybrid is going to make calculations using and externally inputed Heights Error Profile,\n" + \
                                                                "but the Shadow O.E. already has a Modified Surface option active:\n\n" + \
                                                                "Proceed anyway?"):
                        raise Exception("Procedure Interrupted")

        n_screen = 1
        i_screen = numpy.zeros(10)  # after
        i_abs = numpy.zeros(10)
        i_slit = numpy.zeros(10)
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

        shadow_oe._oe.set_screens(n_screen,
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

        if input_parameters.ghy_calcType == 3:
            if shadow_oe._oe.FWRITE > 1 or shadow_oe._oe.F_ANGLE == 0:
                shadow_oe._oe.FWRITE = 0 # all
                shadow_oe._oe.F_ANGLE = 1 # angles

        # need to rerun simulation

        input_parameters.widget.status_message("Creating HYBRID screen: redo simulation with modified O.E.")

        shadow_beam_at_image_plane = ShadowBeam.traceFromOE(input_beam, shadow_oe, history=False)

        input_parameters.shadow_beam = shadow_beam_at_image_plane

        image_beam, cursor = read_shadow_beam(shadow_beam_at_image_plane, 0) # all rays

        calculation_parameters.shadow_oe_end = shadow_oe

    else: # compatibility with old verion
        str_n_oe = str(input_parameters.ghy_n_oe)

        if input_parameters.ghy_n_oe < 10:
            str_n_oe = "0" + str_n_oe

        str_n_screen = str(input_parameters.ghy_n_screen)
        if input_parameters.ghy_n_screen < 10:
            str_n_screen = "0" + str_n_screen

        if (input_parameters.ghy_n_oe==0):
            fileShadowScreen = "begin.dat"
            fileShadowStar = "begin.dat"
        else:
            fileShadowStar = "star."+str_n_oe
            if(input_parameters.ghy_n_screen==0):
                fileShadowScreen = "star." + str_n_oe
            else:
                fileShadowScreen = "screen." + str_n_oe + str_n_screen

        image_beam, cursor = sh_readsh(fileShadowStar, 0)

        calculation_parameters.shadow_oe_end = sh_read_gfile("end." + str_n_oe)

    calculation_parameters.image_plane_beam = image_beam
    calculation_parameters.image_plane_cursor = cursor

    calculation_parameters.xx_star = image_beam._beam.rays[:, 0]
    calculation_parameters.zz_star = image_beam._beam.rays[:, 2]

    # read shadow screen file
    screen_beam, cursor = sh_readsh(fileShadowScreen, 0)

    calculation_parameters.screen_plane_beam = screen_beam
    calculation_parameters.screen_plane_cursor = cursor

    calculation_parameters.wenergy     = ShadowPhysics.getEnergyFromShadowK(screen_beam._beam.rays[:, 10])
    calculation_parameters.wwavelength = ShadowPhysics.getWavelengthfromShadowK(screen_beam._beam.rays[:, 10])
    calculation_parameters.xp_screen   = screen_beam._beam.rays[:, 3]
    calculation_parameters.yp_screen   = screen_beam._beam.rays[:, 4]
    calculation_parameters.zp_screen   = screen_beam._beam.rays[:, 5]

    genergy = numpy.average(calculation_parameters.wenergy) # average photon energy in eV

    input_parameters.widget.status_message("Using MEAN photon energy [eV]:" + str(genergy))

    calculation_parameters.xx_screen = screen_beam._beam.rays[:, 0]
    calculation_parameters.ghy_x_min = numpy.min(calculation_parameters.xx_screen)
    calculation_parameters.ghy_x_max = numpy.max(calculation_parameters.xx_screen)

    calculation_parameters.zz_screen = screen_beam._beam.rays[:, 2]
    calculation_parameters.ghy_z_min = numpy.min(calculation_parameters.zz_screen)
    calculation_parameters.ghy_z_max = numpy.max(calculation_parameters.zz_screen)

    calculation_parameters.dx_ray = numpy.arctan(calculation_parameters.xp_screen/calculation_parameters.yp_screen) # calculate divergence from direction cosines from SHADOW file  dx = atan(v_x/v_y)
    calculation_parameters.dz_ray = numpy.arctan(calculation_parameters.zp_screen/calculation_parameters.yp_screen) # calculate divergence from direction cosines from SHADOW file  dz = atan(v_z/v_y)

    # Process mirror
	# reads file with mirror height mesh
 	# calculates the function of the "incident angle" and the "mirror height" versus the Z coordinate in the screen.

    if input_parameters.ghy_calcType == 3:
        mirror_beam, cursor = sh_readsh("mirr." + str_n_oe, 0)

        calculation_parameters.xx_mirr = mirror_beam._beam.rays[:, 0]
        calculation_parameters.yy_mirr = mirror_beam._beam.rays[:, 1]
        calculation_parameters.zz_mirr = mirror_beam._beam.rays[:, 2]

        # read in angle files
        angle_flag, angle_index, angle_inc, angle_ref = sh_readangle("angle." + str_n_oe, 0, mirror_beam)

        calculation_parameters.angle_inc = (90.0 - angle_inc)/180.0*1e3*numpy.pi

        # read in mirror surface
        if input_parameters.ghy_usemirrorfile == 0 or input_parameters.ghy_profile_dimension == 1:
            calculation_parameters.w_mirr_2D_values = sh_readsurface(input_parameters.ghy_mirrorfile, dimension=2)
        else:
            calculation_parameters.w_mirr_1D_values = sh_readsurface(input_parameters.ghy_mirrorfile, dimension=1)

        # generate theta(z) and l(z) curve over a continuous grid

        hy_npoly_angle = 3
        hy_npoly_l = 6

        if numpy.amax(calculation_parameters.xx_screen) == numpy.amin(calculation_parameters.xx_screen):
            if input_parameters.ghy_diff_plane == 1: raise Exception("Unconsistend calculation: Diffraction plane is set on X, but the beam has no extention in that direction")
        else:
            calculation_parameters.wangle_x = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.angle_inc, hy_npoly_angle))
            calculation_parameters.wl_x     = numpy.poly1d(numpy.polyfit(calculation_parameters.xx_screen, calculation_parameters.xx_mirr, hy_npoly_l))

        if numpy.amax(calculation_parameters.zz_screen) == numpy.amin(calculation_parameters.zz_screen):
            if input_parameters.ghy_diff_plane == 2: raise Exception("Unconsistend calculation: Diffraction plane is set on Z, but the beam has no extention in that direction")
        else:
            calculation_parameters.wangle_z = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.angle_inc, hy_npoly_angle))
            calculation_parameters.wl_z     = numpy.poly1d(numpy.polyfit(calculation_parameters.zz_screen, calculation_parameters.yy_mirr, hy_npoly_l))

##########################################################################

def hy_init(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_n_oe < 0:
        oe_number = input_parameters.shadow_beam._oe_number
    else:
        oe_number = input_parameters.ghy_n_oe

    if input_parameters.ghy_calcType > 1:
        simag = calculation_parameters.shadow_oe_end._oe.SIMAG

        if input_parameters.ghy_focallength < 0:
            input_parameters.ghy_focallength = simag
            input_parameters.widget.status_message("Focal length not set (<-1), take from SIMAG" + str(input_parameters.ghy_focallength))

        if input_parameters.ghy_focallength != simag:
            input_parameters.widget.status_message("Defined focal length is different from SIMAG, used the defined focal length = " + str(input_parameters.ghy_focallength))
        else:
            input_parameters.widget.status_message("Focal length = " + str(input_parameters.ghy_focallength))

    if input_parameters.ghy_diff_plane == 1:
        calculation_parameters.xx_focal_ray = copy.deepcopy(calculation_parameters.xx_screen) + \
                                              input_parameters.ghy_focallength * numpy.tan(calculation_parameters.dx_ray)
    elif input_parameters.ghy_diff_plane == 2:
        calculation_parameters.zz_focal_ray = copy.deepcopy(calculation_parameters.zz_screen) + \
                                              input_parameters.ghy_focallength * numpy.tan(calculation_parameters.dz_ray)

    t_image = calculation_parameters.shadow_oe_end._oe.T_IMAGE

    if input_parameters.ghy_distance < 0:
        if oe_number != 0:
            input_parameters.ghy_distance = t_image
            input_parameters.widget.status_message("Distance not set (<-1), take from T_IMAGE" + str(input_parameters.ghy_distance))

    if oe_number != 0:
        if (input_parameters.ghy_distance == t_image):
            input_parameters.widget.status_message("Defined OE star plane distance is different from T_IMAGE, used the defined distance = " + str(input_parameters.ghy_distance))
        else:
            input_parameters.widget.status_message("Propagation distance = " + str(input_parameters.ghy_distance))

    if input_parameters.ghy_calcType == 3: #mirror with figure error
        if input_parameters.ghy_usemirrorfile == 0 or input_parameters.ghy_profile_dimension == 1:
            if input_parameters.ghy_diff_plane == 1: #X
                np_array = calculation_parameters.w_mirr_2D_values.z_values[:, round(len(calculation_parameters.w_mirr_2D_values.y_coord)/2)]

                calculation_parameters.w_mirror_lx = ScaledArray.initialize_from_steps(np_array,
                                                                                       calculation_parameters.w_mirr_2D_values.x_coord[0],
                                                                                       calculation_parameters.w_mirr_2D_values.x_coord[1] - calculation_parameters.w_mirr_2D_values.x_coord[0])
            elif input_parameters.ghy_diff_plane == 2: #Z
                np_array = calculation_parameters.w_mirr_2D_values.z_values[round(len(calculation_parameters.w_mirr_2D_values.x_coord)/2), :]

                calculation_parameters.w_mirror_lz = ScaledArray.initialize_from_steps(np_array,
                                                                                       calculation_parameters.w_mirr_2D_values.y_coord[0],
                                                                                       calculation_parameters.w_mirr_2D_values.y_coord[1] - calculation_parameters.w_mirr_2D_values.y_coord[0])
        else:
            if input_parameters.ghy_diff_plane == 1: #X
                calculation_parameters.w_mirror_lx = calculation_parameters.w_mirr_1D_values
            elif input_parameters.ghy_diff_plane == 2: #Z
                calculation_parameters.w_mirror_lz = calculation_parameters.w_mirr_1D_values

    # generate intensity profile (histogram): I_ray(z) curve

    if input_parameters.ghy_diff_plane == 1: # 1d in X
        if (input_parameters.ghy_nbins_x < 0):
            input_parameters.ghy_nbins_x = 200

        input_parameters.ghy_nbins_x = min(input_parameters.ghy_nbins_x, round(len(calculation_parameters.xx_screen) / 100))

        ticket = calculation_parameters.screen_plane_beam._beam.histo1(1,
                                                                       nbins=input_parameters.ghy_nbins_x,
                                                                       xrange=[numpy.min(calculation_parameters.xx_screen), numpy.max(calculation_parameters.xx_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins = ticket['bins']

        calculation_parameters.wIray_x = ScaledArray.initialize_from_range(ticket['histogram'], bins[0], bins[len(bins)-1])
    elif input_parameters.ghy_diff_plane == 2: # 1d in Z
        if (input_parameters.ghy_nbins_z < 0):
            input_parameters.ghy_nbins_z = 200

        input_parameters.ghy_nbins_z = min(input_parameters.ghy_nbins_z, round(len(calculation_parameters.zz_screen) / 100))

        ticket = calculation_parameters.screen_plane_beam._beam.histo1(3,
                                                                       nbins=input_parameters.ghy_nbins_z,
                                                                       xrange=[numpy.min(calculation_parameters.zz_screen), numpy.max(calculation_parameters.zz_screen)],
                                                                       nolost=1,
                                                                       ref=23)

        bins = ticket['bins']

        calculation_parameters.wIray_z = ScaledArray.initialize_from_range(ticket['histogram'], bins[0], bins[len(bins)-1])

    calculation_parameters.gwavelength = numpy.average(calculation_parameters.wwavelength)

    if input_parameters.ghy_lengthunit == 0:
        um = "m"
        calculation_parameters.gwavelength *= 1e-10
    if input_parameters.ghy_lengthunit == 1:
        um = "cm"
        calculation_parameters.gwavelength *= 1e-8
    elif input_parameters.ghy_lengthunit == 2:
        um = "mm"
        calculation_parameters.gwavelength *= 1e-7

    input_parameters.widget.status_message("Using MEAN photon wavelength (" + um + "): " + str(calculation_parameters.gwavelength))

    calculation_parameters.gknum = 2.0*numpy.pi/calculation_parameters.gwavelength #in [user-unit]^-1, wavenumber

##########################################################################

def hy_prop(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):

    # set distance and focal length for the aperture propagation.
    if input_parameters.ghy_calcType == 1: # simple aperture
        if input_parameters.ghy_diff_plane == 1: # X
            calculation_parameters.ghy_focallength = (calculation_parameters.ghy_x_max-calculation_parameters.ghy_x_min)**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak
        elif input_parameters.ghy_diff_plane == 2: # Z
            calculation_parameters.ghy_focallength = (calculation_parameters.ghy_z_max-calculation_parameters.ghy_z_min)**2/calculation_parameters.gwavelength/input_parameters.ghy_npeak

        input_parameters.widget.status_message("Focal length set to: " + str(calculation_parameters.ghy_focallength))

    # automatic control of number of peaks to avoid numerical overflow
    if input_parameters.ghy_npeak < 0: # number of bins control
        input_parameters.ghy_npeak = 50
    input_parameters.ghy_npeak = min(input_parameters.ghy_npeak, 50)

    input_parameters.ghy_npeak = max(input_parameters.ghy_npeak, 5)

    if input_parameters.ghy_fftnpts < 0:
        input_parameters.ghy_fftnpts = 4e6
    input_parameters.ghy_fftnpts = min(input_parameters.ghy_fftnpts, 4e6)

    input_parameters.widget.set_progress_bar(25)

    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        propagate_1D_x_direction(calculation_parameters, input_parameters)
    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        propagate_1D_z_direction(calculation_parameters, input_parameters)

def hy_conv(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        mDist = hy_CreateCDF1D(calculation_parameters.dif_xp)		#create cumulative distribution function from the angular diffraction profile
        pos_dif = hy_MakeDist1D(calculation_parameters.xp_screen, mDist)	#generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file

        dx_wave = numpy.arctan(pos_dif) # calculate dx from tan(dx)
        dx_conv = dx_wave + calculation_parameters.dx_ray # add the ray divergence kicks

        calculation_parameters.xx_image_ff = calculation_parameters.xx_screen + input_parameters.ghy_distance*numpy.tan(dx_conv) # ray tracing to the image plane
        calculation_parameters.dx_conv = dx_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            mDist = hy_CreateCDF1D(calculation_parameters.dif_x)
            pos_dif = hy_MakeDist1D(calculation_parameters.xx_focal_ray, mDist)

            calculation_parameters.xx_image_nf = pos_dif + calculation_parameters.xx_focal_ray
    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        mDist = hy_CreateCDF1D(calculation_parameters.dif_zp)		#create cumulative distribution function from the angular diffraction profile
        pos_dif = hy_MakeDist1D(calculation_parameters.zp_screen, mDist)	#generate random ray divergence kicks based on the CDF, the number of rays is the same as in the original shadow file

        dz_wave = numpy.arctan(pos_dif) # calculate dz from tan(dz)
        dz_conv = dz_wave + calculation_parameters.dz_ray # add the ray divergence kicks

        calculation_parameters.zz_image_ff = calculation_parameters.zz_screen + input_parameters.ghy_distance*numpy.tan(dz_conv) # ray tracing to the image plane
        calculation_parameters.dz_conv = dz_conv

        if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
            mDist = hy_CreateCDF1D(calculation_parameters.dif_z)
            pos_dif = hy_MakeDist1D(calculation_parameters.zz_focal_ray, mDist)

            calculation_parameters.zz_image_nf = pos_dif + calculation_parameters.zz_focal_ray

#########################################################################

def hy_create_shadow_beam(input_parameters=HybridInputParameters(), calculation_parameters=HybridCalculationParameters()):
    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    calculation_parameters.ff_beam = calculation_parameters.image_plane_beam.duplicate(history=False)
    if do_nf: calculation_parameters.nf_beam = calculation_parameters.screen_plane_beam.duplicate(history=False)

    if input_parameters.ghy_diff_plane == 1: #1d calculation in x direction
        angle_perpen = numpy.arctan(calculation_parameters.zp_screen/calculation_parameters.yp_screen)
        angle_num = numpy.sqrt(1+(numpy.tan(angle_perpen))**2+(numpy.tan(calculation_parameters.dx_conv))**2)

        calculation_parameters.ff_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_ff)
        calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(calculation_parameters.dx_conv)/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(angle_perpen)/angle_num

        if do_nf: calculation_parameters.nf_beam._beam.rays[:, 0] = copy.deepcopy(calculation_parameters.xx_image_nf)

    elif input_parameters.ghy_diff_plane == 2: #1d calculation in z direction
        angle_perpen = numpy.arctan(calculation_parameters.xp_screen/calculation_parameters.yp_screen)
        angle_num = numpy.sqrt(1+(numpy.tan(angle_perpen))**2+(numpy.tan(calculation_parameters.dz_conv))**2)

        calculation_parameters.ff_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_ff)
        calculation_parameters.ff_beam._beam.rays[:, 3] = numpy.tan(angle_perpen)/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 4] = 1/angle_num
        calculation_parameters.ff_beam._beam.rays[:, 5] = numpy.tan(calculation_parameters.dz_conv)/angle_num

        if do_nf: calculation_parameters.nf_beam._beam.rays[:, 2] = copy.deepcopy(calculation_parameters.zz_image_nf)

    calculation_parameters.ff_beam.history = calculation_parameters.original_beam_history

##########################################################################
# 1D PROPAGATION ALGORITHM - X DIRECTION
##########################################################################

def propagate_1D_x_direction(calculation_parameters, input_parameters):

    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    if input_parameters.ghy_calcType == 3:
        rms_slope = hy_findrmsslopefromheight(calculation_parameters.w_mirror_lx)

        input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

        avg_wangle_x = numpy.radians(calculate_function_average_value(calculation_parameters.wangle_x,
                                                                      calculation_parameters.ghy_x_min,
                                                                      calculation_parameters.ghy_x_max))
    # ------------------------------------------
    # far field calculation
    # ------------------------------------------
    focallength_ff = calculate_focal_length_ff(calculation_parameters.ghy_x_min,
                                               calculation_parameters.ghy_x_max,
                                               input_parameters.ghy_npeak,
                                               calculation_parameters.gwavelength)

    if input_parameters.ghy_calcType == 3:
        if rms_slope == 0.0 or avg_wangle_x == 0.0:
            focallength_ff = min(focallength_ff,
                                 abs(calculation_parameters.ghy_x_max))
        else:
            focallength_ff = min(focallength_ff,
                                 (min(abs(calculation_parameters.ghy_x_max),
                                      abs(calculation_parameters.ghy_x_min)) * 2) / 8 / rms_slope / numpy.sin(avg_wangle_x / 1e3))

    fftsize = calculate_fft_size(calculation_parameters.ghy_x_min,
                                 calculation_parameters.ghy_x_max,
                                 calculation_parameters.gwavelength,
                                 focallength_ff,
                                 input_parameters.ghy_fftnpts)

    if do_nf: input_parameters.widget.set_progress_bar(27)
    else: input_parameters.widget.set_progress_bar(30)
    input_parameters.widget.status_message("FF: creating plane wave begin, fftsize = " +  str(fftsize))


    wavefront = Wavefront1D.initialize_wavefront_from_range(wavelenght=calculation_parameters.gwavelength,
                                                            number_of_points=fftsize,
                                                            x_min=calculation_parameters.ghy_x_min,
                                                            x_max=calculation_parameters.ghy_x_max)

    wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_x.interpolate_values(wavefront.get_abscissas())))
    wavefront.apply_ideal_lens(focallength_ff)

    if input_parameters.ghy_calcType == 3:
       wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                      calculation_parameters.gwavelength,
                                                                      calculation_parameters.wangle_x,
                                                                      calculation_parameters.wl_x,
                                                                      calculation_parameters.w_mirror_lx))

    if do_nf: input_parameters.widget.set_progress_bar(35)
    else: input_parameters.widget.set_progress_bar(50)
    input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

    intensity = propagator.propagate_1D_fresnel(wavefront, focallength_ff)

    if do_nf: input_parameters.widget.set_progress_bar(50)
    else: input_parameters.widget.set_progress_bar(70)
    input_parameters.widget.status_message("dif_xp: begin calculation")

    imagesize = min(abs(calculation_parameters.ghy_x_max), abs(calculation_parameters.ghy_x_min)) * 2
    imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1


    dif_xp = ScaledArray.initialize_from_range(numpy.ones(intensity.size()),
                                               -(imagenpts - 1) / 2 * intensity.delta(),
                                               (imagenpts - 1) / 2 * intensity.delta())


    dif_xp.np_array = numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_xp.scale))**2

    dif_xp.set_scale_from_range(-(imagenpts - 1) / 2 * intensity.delta() / focallength_ff,
                                (imagenpts - 1) / 2 * intensity.delta() / focallength_ff)

    calculation_parameters.dif_xp = dif_xp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:  # near field calculation
        fftsize = calculate_fft_size(calculation_parameters.ghy_x_min,
                                     calculation_parameters.ghy_x_max,
                                     calculation_parameters.gwavelength,
                                     input_parameters.ghy_focallength,
                                     input_parameters.ghy_fftnpts)

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize = " +  str(fftsize))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelenght=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=calculation_parameters.ghy_x_min,
                                                                x_max=calculation_parameters.ghy_x_max)

        wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_x.interpolate_values(wavefront.get_abscissas())))
        wavefront.apply_ideal_lens(input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
           wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                          calculation_parameters.gwavelength,
                                                                          calculation_parameters.wangle_x,
                                                                          calculation_parameters.wl_x,
                                                                          calculation_parameters.w_mirror_lx))

        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " + str(input_parameters.ghy_distance) + ")")
        input_parameters.widget.set_progress_bar(60)

        intensity = propagator.propagate_1D_fresnel(wavefront, input_parameters.ghy_distance)

        # ghy_npeak in the wavefront propagation image
        imagesize = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * input_parameters.ghy_focallength / abs(calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min))
        imagesize = max(imagesize,
                        2 * abs((calculation_parameters.ghy_x_max - calculation_parameters.ghy_x_min) * (input_parameters.ghy_distance - input_parameters.ghy_focallength)) / input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
            imagesize = max(imagesize,
                            16 * rms_slope * input_parameters.ghy_focallength * numpy.sin(avg_wangle_x / 1e3))

        imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1

        input_parameters.widget.set_progress_bar(75)
        input_parameters.widget.status_message("dif_x: begin calculation")

        dif_x = ScaledArray.initialize_from_range(numpy.ones(imagenpts),
                                                  -(imagenpts - 1) / 2 * intensity.delta(),
                                                  (imagenpts - 1) / 2 * intensity.delta())

        dif_x.np_array *= numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_x.scale))**2

        calculation_parameters.dif_x = dif_x

        input_parameters.widget.set_progress_bar(80)

##########################################################################
# 1D PROPAGATION ALGORITHM - Z DIRECTION
##########################################################################

def propagate_1D_z_direction(calculation_parameters, input_parameters):

    do_nf = input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1

    if input_parameters.ghy_calcType == 3:
        rms_slope = hy_findrmsslopefromheight(calculation_parameters.w_mirror_lz)

        input_parameters.widget.status_message("Using RMS slope = " + str(rms_slope))

    # ------------------------------------------
    # far field calculation
    # ------------------------------------------
    focallength_ff = calculate_focal_length_ff(calculation_parameters.ghy_z_min,
                                               calculation_parameters.ghy_z_max,
                                               input_parameters.ghy_npeak,
                                               calculation_parameters.gwavelength)

    if input_parameters.ghy_calcType == 3:
        if rms_slope == 0:
            focallength_ff = min(focallength_ff,
                                 abs(calculation_parameters.ghy_z_max))
        else:
            focallength_ff = min(focallength_ff,
                                 (min(abs(calculation_parameters.ghy_z_max),
                                      abs(calculation_parameters.ghy_z_min)) * 2) / 16 / rms_slope)

    fftsize = calculate_fft_size(calculation_parameters.ghy_z_min,
                                 calculation_parameters.ghy_z_max,
                                 calculation_parameters.gwavelength,
                                 focallength_ff,
                                 input_parameters.ghy_fftnpts)

    if do_nf: input_parameters.widget.set_progress_bar(27)
    else: input_parameters.widget.set_progress_bar(30)
    input_parameters.widget.status_message("FF: creating plane wave begin, fftsize = " +  str(fftsize))

    wavefront = Wavefront1D.initialize_wavefront_from_range(wavelenght=calculation_parameters.gwavelength,
                                                            number_of_points=fftsize,
                                                            x_min=calculation_parameters.ghy_z_min,
                                                            x_max=calculation_parameters.ghy_z_max)

    wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_z.interpolate_values(wavefront.get_abscissas())))
    wavefront.apply_ideal_lens(focallength_ff)

    if input_parameters.ghy_calcType == 3:
       wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                      calculation_parameters.gwavelength,
                                                                      calculation_parameters.wangle_z,
                                                                      calculation_parameters.wl_z,
                                                                      calculation_parameters.w_mirror_lz))

    if do_nf: input_parameters.widget.set_progress_bar(35)
    else: input_parameters.widget.set_progress_bar(50)
    input_parameters.widget.status_message("calculated plane wave: begin FF propagation (distance = " +  str(focallength_ff) + ")")

    intensity = propagator.propagate_1D_fresnel(wavefront, focallength_ff)

    if do_nf: input_parameters.widget.set_progress_bar(50)
    else: input_parameters.widget.set_progress_bar(70)
    input_parameters.widget.status_message("dif_zp: begin calculation")

    imagesize = min(abs(calculation_parameters.ghy_z_max), abs(calculation_parameters.ghy_z_min)) * 2
    imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1

    dif_zp = ScaledArray.initialize_from_range(numpy.ones(intensity.size()),
                                               -(imagenpts - 1) / 2 * intensity.delta(),
                                               (imagenpts - 1) / 2 * intensity.delta())

    dif_zp.np_array *= numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_zp.scale))**2

    dif_zp.set_scale_from_range(-(imagenpts - 1) / 2 * intensity.delta() / focallength_ff,
                                (imagenpts - 1) / 2 * intensity.delta() / focallength_ff)

    calculation_parameters.dif_zp = dif_zp

    if not do_nf: input_parameters.widget.set_progress_bar(80)

    # ------------------------------------------
    # near field calculation
    # ------------------------------------------
    if input_parameters.ghy_nf == 1 and input_parameters.ghy_calcType > 1:
        fftsize = calculate_fft_size(calculation_parameters.ghy_z_min,
                                     calculation_parameters.ghy_z_max,
                                     calculation_parameters.gwavelength,
                                     input_parameters.ghy_focallength,
                                     input_parameters.ghy_fftnpts)

        input_parameters.widget.status_message("NF: creating plane wave begin, fftsize = " +  str(fftsize))
        input_parameters.widget.set_progress_bar(55)

        wavefront = Wavefront1D.initialize_wavefront_from_range(wavelenght=calculation_parameters.gwavelength,
                                                                number_of_points=fftsize,
                                                                x_min=calculation_parameters.ghy_z_min,
                                                                x_max=calculation_parameters.ghy_z_max)

        wavefront.set_plane_wave_from_complex_amplitude(numpy.sqrt(calculation_parameters.wIray_z.interpolate_values(wavefront.get_abscissas())))
        wavefront.apply_ideal_lens(input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
           wavefront.add_phase_shifts(get_mirror_figure_error_phase_shift(wavefront.get_abscissas(),
                                                                          calculation_parameters.gwavelength,
                                                                          calculation_parameters.wangle_z,
                                                                          calculation_parameters.wl_z,
                                                                          calculation_parameters.w_mirror_lz))


        input_parameters.widget.status_message("calculated plane wave: begin NF propagation (distance = " + str(input_parameters.ghy_distance) + ")")
        input_parameters.widget.set_progress_bar(60)

        intensity = propagator.propagate_1D_fresnel(wavefront, input_parameters.ghy_distance)

        # ghy_npeak in the wavefront propagation image
        imagesize = (input_parameters.ghy_npeak * 2 * 0.88 * calculation_parameters.gwavelength * input_parameters.ghy_focallength / abs(calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min))
        imagesize = max(imagesize,
                        2 * abs((calculation_parameters.ghy_z_max - calculation_parameters.ghy_z_min) * (input_parameters.ghy_distance - input_parameters.ghy_focallength)) / input_parameters.ghy_focallength)

        if input_parameters.ghy_calcType == 3:
            imagesize = max(imagesize, 16 * rms_slope * input_parameters.ghy_focallength)

        imagenpts = round(imagesize / intensity.delta() / 2) * 2 + 1

        input_parameters.widget.set_progress_bar(75)
        input_parameters.widget.status_message("dif_z: begin calculation")

        dif_z = ScaledArray.initialize_from_range(numpy.ones(imagenpts),
                                                  -(imagenpts - 1) / 2 * intensity.delta(),
                                                   (imagenpts - 1) / 2 * intensity.delta())

        dif_z.np_array *= numpy.absolute(intensity.get_complex_amplitude_from_abscissas(dif_z.scale)**2)

        calculation_parameters.dif_z = dif_z

        input_parameters.widget.set_progress_bar(80)

#########################################################
#
# UTILITIES
#
#########################################################

def sh_read_gfile(gfilename):
    return ShadowOpticalElement.create_oe_from_file(congruence.checkFile(gfilename))

#########################################################

def read_shadow_beam(shadow_beam, flag):
    go = numpy.where(shadow_beam._beam.rays[:, 9] == 1)
    lo = numpy.where(shadow_beam._beam.rays[:, 9] < 1)

    all = flag == 0
    good_only = flag == 1
    lost_only = flag == 2

    if all:
        cursor = None
        image_beam_rays = copy.deepcopy(shadow_beam._beam.rays)
    elif good_only:
        cursor = go
        image_beam_rays = copy.deepcopy(shadow_beam._beam.rays[go])
    elif lost_only:
        cursor = lo
        image_beam_rays = copy.deepcopy(shadow_beam._beam.rays[lo])
    else:
        raise Exception("Flag not recongnized")

    out_beam = ShadowBeam()
    out_beam._beam.rays = image_beam_rays

    return out_beam, cursor

#########################################################

def sh_readsh(shfilename, flag):
    image_beam = ShadowBeam()
    image_beam.loadFromFile(congruence.checkFile(shfilename))

    all = flag == 0
    good_only = flag == 1
    lost_only = flag == 2

    if all:
        cursor = None
        image_beam_rays = copy.deepcopy(image_beam._beam.rays)
    elif good_only:
        cursor = numpy.where(image_beam._beam.rays[:, 9] == 1)
        image_beam_rays = copy.deepcopy(image_beam._beam.rays[cursor])
    elif lost_only:
        cursor = numpy.where(image_beam._beam.rays[:, 9] < 1)
        image_beam_rays = copy.deepcopy(image_beam._beam.rays[cursor])
    else:
        raise Exception("Flag not recongnized")

    out_beam = ShadowBeam()
    out_beam._beam.rays = image_beam_rays

    return out_beam, cursor

#########################################################

def sh_readangle(filename, flag=0, mirror_beam=None):
    values = numpy.loadtxt(congruence.checkFile(filename))

    all = flag == 0
    good_only = flag == 1
    lost_only = flag == 2

    if all:
        angle_index = copy.deepcopy(values[:, 0])
        angle_inc = copy.deepcopy(values[:, 1])
        angle_ref = copy.deepcopy(values[:, 2])
        angle_flag = copy.deepcopy(values[:, 3])
    elif good_only or lost_only:
        dimension = len(mirror_beam._beam.rays)

        angle_index = numpy.zeros(dimension)
        angle_inc = numpy.zeros(dimension)
        angle_ref = numpy.zeros(dimension)
        angle_flag = numpy.zeros(dimension)

        index = 0
        for ray in mirror_beam._beam.rays:
            ray_index = ray[11]-1

            angle_index[index] = values[ray_index, 0]
            angle_inc[index] = values[ray_index, 1]
            angle_ref[index] = values[ray_index, 2]
            angle_flag[index] = values[ray_index, 3]

            print (index, dimension, ray_index, len(values[:, 0]))

            index+=1
    else:
        raise Exception("Flag not recongnized")

    return angle_flag, angle_index, angle_inc, angle_ref

#########################################################

def sh_readsurface(filename, dimension):
    if dimension == 1:
        values = numpy.loadtxt(congruence.checkFile(filename))

        return ScaledArray(values[:, 1], values[:, 0])
    elif dimension == 2:
        x_coords, y_coords, z_values = ShadowPreProcessor.read_surface_error_file(filename)

        return ScaledMatrix(x_coords, y_coords, z_values)

#########################################################

def calculate_function_average_value(function, x_min, x_max, sampling=100):
    sampled_function = ScaledArray.initialize_from_range(numpy.zeros(sampling), x_min, x_max)
    sampled_function.np_array = function(sampled_function.scale)

    return numpy.average(sampled_function.np_array)

#########################################################

def hy_findrmsslopefromheight(wmirror_l):
    array_first_derivative = numpy.gradient(wmirror_l.np_array, wmirror_l.delta())

    return hy_findrmserror(ScaledArray(array_first_derivative, wmirror_l.scale))

#########################################################

def hy_findrmserror(data):
    wfftcol = numpy.absolute(numpy.fft.fft(data.np_array))

    waPSD = 2 * data.delta() * wfftcol[0:int(len(wfftcol)/2)]**2/data.size() # uniformed with IGOR, FFT is not simmetric around 0
    waPSD[0] /= 2
    waPSD[len(waPSD)-1] /= 2

    waRMS = numpy.trapz(waPSD, numpy.arange(0.0, 1.0, 1.0/len(waPSD))) # uniformed with IGOR: Same kind of integration, with automatic range assignement

    return numpy.sqrt(waRMS)

#########################################################

# Create sampling from 2d wave
def hy_CreateCDF1D(data):
    mDist = ScaledArray(data.np_array, data.scale)

    for index in range(1, mDist.size()):
       mDist.np_array[index] += mDist.np_array[index-1] # mDist matrix contains the rows

    mDist.np_array /= mDist.np_array[mDist.size()-1] # Normalizing each row of the matrix

    return mDist

def hy_MakeDist1D(np_array, mDist):
    random_generator = random.Random()
    random_generator.seed(25)

    pos_dif = numpy.zeros(len(np_array))
    for index in range(0, len(np_array)):
        pos_dif[index] = hy_GetOnePoint1D(mDist, random_generator)

    return pos_dif

def hy_GetOnePoint1D(mDist, random_generator, reset=0):
    if reset==1 : random_generator.seed(1)
    return mDist.interpolate_scale_value(random_generator.random()) # Finding vertical x value

# 1D
def calculate_focal_length_ff(min_value, max_value, n_peaks, wavelength):
    return (min(abs(max_value), abs(min_value))*2)**2/n_peaks/2/0.88/wavelength

def calculate_fft_size(min_value, max_value, wavelength, propagation_distance, fft_npts):
    return int(min(100 * (max_value - min_value) ** 2 / wavelength / propagation_distance / 0.88, fft_npts))

def get_mirror_figure_error_phase_shift(abscissas,
                                        wavelength,
                                        w_angle_function,
                                        w_l_function,
                                        mirror_figure_error):
    return numpy.exp((-1.0) * 4 * numpy.pi / wavelength * numpy.sin(w_angle_function(abscissas)/1e3) * \
                     mirror_figure_error.interpolate_values(w_l_function(abscissas)))



def showConfirmMessage(title, message):
    msgBox = QMessageBox()
    msgBox.setFixedWidth(500)
    msgBox.setIcon(QMessageBox.Question)
    msgBox.setText(title)
    msgBox.setInformativeText(message)
    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msgBox.setDefaultButton(QMessageBox.No)
    return msgBox.exec_()


################################################################
################################################################
# TEST
################################################################
################################################################

import time
from PyQt4.QtGui import QApplication
import matplotlib.pyplot as plt

import PyMca5.PyMcaGui.plotting.PlotWindow as PlotWindow
from PyMca5.PyMcaGui.plotting.ImageView import ImageView


def do_histo(array, bins):
    plt.hist(array, bins)
    plt.show()

def do_1d_plot(scaled_array, title="PROVA"):
    plot_canvas = PlotWindow.PlotWindow(roi=False, control=False, position=False, plugins=False, logx=False, logy=False)
    plot_canvas.setDefaultPlotLines(True)
    plot_canvas.setActiveCurveColor(color='darkblue')
    plot_canvas.setMinimumWidth(800)
    plot_canvas.setMaximumWidth(800)

    plot_canvas.addCurve(scaled_array.scale, scaled_array.np_array, title, symbol='', color='blue', replace=True) #'+', '^', ','
    plot_canvas.setDrawModeEnabled(True, 'rectangle')
    plot_canvas.setZoomModeEnabled(True)

    plot_canvas.show()

def do_2d_plot(scaled_matrix, title="PROVA"):
    plot_canvas = ImageView()

    colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

    plot_canvas._imagePlot.setDefaultColormap(colormap)
    plot_canvas.setMinimumWidth(800)
    plot_canvas.setMaximumWidth(800)

    nbins_x =  scaled_matrix.shape()[0]
    nbins_y =  scaled_matrix.shape()[1]

    xmin, xmax = numpy.min(scaled_matrix.x_coord), numpy.max(scaled_matrix.x_coord)
    ymin, ymax = numpy.min(scaled_matrix.y_coord), numpy.max(scaled_matrix.y_coord)

    origin = (xmin, ymin)
    scale = (abs((xmax-xmin)/nbins_x), abs((ymax-ymin)/nbins_y))

    # PyMCA inverts axis!!!! histogram must be calculated reversed
    data_to_plot = []
    for y_index in range(0, nbins_y):
        x_values = []
        for x_index in range(0, nbins_x):
            x_values.append(scaled_matrix.get_z_value(x_index, y_index))

        data_to_plot.append(x_values)

    plot_canvas.setImage(numpy.array(data_to_plot), origin=origin, scale=scale)

    plot_canvas.show()

if __name__ == "__main__":
    a = QApplication(sys.argv)

    doXianbo = True

    if doXianbo:
        os.chdir("/Users/labx/Desktop/TEMP/XIANBO_IN/")

        input_parameters = HybridInputParameters()

        input_parameters.ghy_n_oe = 1
        input_parameters.ghy_n_screen = 2
        input_parameters.ghy_diff_plane = 2
        input_parameters.ghy_calcType = 3
        input_parameters.ghy_mirrorfile = "mirror.dat"
        input_parameters.ghy_nf = 0
        input_parameters.ghy_nbins_z = 39
        input_parameters.ghy_npeak = 10
        input_parameters.ghy_fftnpts = 1e6
    else:
        os.chdir("/Users/labx/Desktop/TEMP/")

        src = ShadowSource.create_src_from_file(dir + "start.00")

        shadow_beam = ShadowBeam.traceFromSource(src)
        shadow_oe = ShadowOpticalElement.create_oe_from_file(dir + "start.01")
        shadow_beam = ShadowBeam.traceFromOE(shadow_beam, shadow_oe)

        input_parameters = HybridInputParameters()
        input_parameters.shadow_beam = shadow_beam
        input_parameters.ghy_diff_plane = 1
        input_parameters.ghy_calcType = 3
        input_parameters.ghy_mirrorfile = "mirror.dat"
        input_parameters.ghy_nf = 1
        input_parameters.ghy_nbins_z = 39
        input_parameters.ghy_npeak = 10
        input_parameters.ghy_fftnpts = 1e5

    t0 = time.time()

    output_beam, calculation_parameters = hy_run(input_parameters)

    t1 = time.time()

    print("TIME", t1-t0)

    if input_parameters.ghy_calcType == 3:
        #do_2d_plot(calculation_parameters.w_mirr_2D_values, "Slope Error Distribution")
        pass

    if input_parameters.ghy_diff_plane != 3:
        nbins = input_parameters.ghy_npeak*20+1

        if input_parameters.ghy_diff_plane == 1:
            do_1d_plot(calculation_parameters.wIray_x, "Intensity Distribution")
            do_1d_plot(calculation_parameters.dif_xp, "DIF XP")
            do_1d_plot(calculation_parameters.dif_xp, "DIF X")
        elif input_parameters.ghy_diff_plane == 2:
            do_1d_plot(calculation_parameters.wIray_z, "Intensity Distribution")
            do_1d_plot(calculation_parameters.dif_zp, "DIF ZP")
            #do_1d_plot(calculation_parameters.dif_z, "DIF Z")
            #do_histo(calculation_parameters.zz_image_ff, nbins)
            #do_histo(calculation_parameters.zz_image_nf, nbins)


            pass
    else:
        do_2d_plot(calculation_parameters.wIray_2d, "Intensity Distribution")


    output_beam.writeToFile("star_hybrid_godo.01")

    '''
    widget = ShadowPlot.DetailedPlotWidget()
    widget.plot_xy(output_beam._beam,
                   1,
                   3,
                   title="X,Z",
                   xtitle=r'X [$\mu$m]',
                   ytitle=r'Z [$\mu$m]',
                   yrange=[-2000, 2000],
                   xum=("X [" + u"\u03BC" + "m]"),
                   yum=("Z [" + u"\u03BC" + "m]"))
    widget.show()
    '''

    a.exec_()