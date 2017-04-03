"""
Example of how to trace a Fresnel Zone Plate
by Lucia Alianelli and Manuel Sanchez del Rio.
1) The source is from get_beam(), is a collimated source of squared cross section (800 microns),
    monochromatic (1.54 A)
2) fresnel_zone_plane() calculates a fzp, centered at (0,0). It returns a new shadow3 beam
    containing the beam after the fzp at the same plane of fzp.
   The fzp parameters are: inner zone radius: 12.4 microns, diameter:
                           619 microns
                           focal distance (at nominal wavelength 1.54 A): 100 cm
3) main() does:
    i) create the source with get_beam()
    ii) Traces a FZP placed at the same source plane
    iii) retraces noth the source and the focused source and displays both results.
        One can see hoe the FWZ focuses well the beam
    srio@esrf.eu - Written. Translated from macro_fresnelzonplate example in ShadowVUI
"""

import Shadow
import numpy

def get_beam():

    #
    # Python script to run shadow3. Created automatically with ShadowTools.make_python_script_from_list().
    #


    # write (1) or not (0) SHADOW files start.xx end.xx star.xx
    iwrite = 0

    #
    # initialize shadow3 source (oe0) and beam
    #
    beam = Shadow.Beam()
    oe0 = Shadow.Source()
    oe1 = Shadow.OE()

    #
    # Define variables. See meaning of variables in:
    #  https://raw.githubusercontent.com/srio/shadow3/master/docs/source.nml
    #  https://raw.githubusercontent.com/srio/shadow3/master/docs/oe.nml
    #

    oe0.FSOUR = 1
    oe0.HDIV1 = 1e-08
    oe0.HDIV2 = 1e-08
    oe0.IDO_VX = 0
    oe0.IDO_VZ = 0
    oe0.IDO_X_S = 0
    oe0.IDO_Y_S = 0
    oe0.IDO_Z_S = 0
    oe0.PH1 = 1.54
    oe0.VDIV1 = 1e-08
    oe0.VDIV2 = 1e-08
    oe0.WXSOU = 0.08
    oe0.WZSOU = 0.08



    #Run SHADOW to create the source

    if iwrite:
        oe0.write("start.00")

    beam.genSource(oe0)

    if iwrite:
        oe0.write("end.00")
        beam.write("begin.dat")

    return beam

def fresnel_zone_plane(beam_in,
        DDm = 618.           , # FZP diameter in microns
        nomlambdaA = 1.54    , # nominal wavelength in Angstrom
        focal = 100.         , #  focal distance (cm)
        R0m = 12.4           , #  inner zone radius (microns)
        ):
    """
    Fresnel zone plate. Simple calculation
    Coded by Lucia Alianelli (alianell@ill.fr) and
    Manuel Sanchez del Rio (srio@esrf.fr)
    This shadow3 script calculates the effect of a Fresnel Zone Plate
    It supposes the fzp is on top of a screen plane
    centered on the optical axis.
    :param beam: FZP diameter in microns
    :param DDm: nominal wavelength in Angstrom
    :param nomlambdaA:
    :param focal: focal distance (cm)
    :param R0m: inner zone radius (microns)
    :return:
    """

    #
    # Widget_Control,/HourGlass ; create an horglass icon during calculation
    # change units to cm
    #
    DD = DDm*1.e-4			        # cm
    R0 = R0m*1.e-4			        # cm
    nomlambda = nomlambdaA*1.e-8	# cm

    beam = beam_in.duplicate()

    #
    # reading Shadow file variables
    #

    #
    lambda1 = beam.getshonecol(19) # lambda in Angstroms
    x =       beam.getshonecol(1)
    z =       beam.getshonecol(3)
    xpin =    beam.getshonecol(4)
    zpin =    beam.getshonecol(6)

    #
    #
    # ;
    #
    Kmod = 2 * numpy.pi / lambda1       # wavevector modulus in Angstrom-1
    r = numpy.sqrt(x**2. + z**2.)       # distance to center
    Kxin = Kmod * xpin
    Kzin = Kmod * zpin

    nrays = x.size

    n =     numpy.zeros(nrays)
    d =     numpy.zeros(nrays)

    #
    # calculate n (index of n-th zone) and d (radius if the nth zone minus
    # radius of the n-a zone)
    #
    # Rays that arrive onto the inner zone
    # IN are the indices of rays that arrive inside the inner zone

    IN = numpy.where(r <= R0)
    IN = numpy.array(IN)
    if IN.size > 0:
        n[IN] = 0.0
        d[IN] = 0.0

    # Rays that arrive outside the inner zone
    # (see formulas in A.G. Michette, "X-ray science and technology"
    #  Institute of Physics Publishing (1993))

    OUT = numpy.where(r >= R0)
    OUT = numpy.array(OUT)
    if OUT.size > 0:
        n[OUT] = (r[OUT]**2 - R0**2) / (nomlambda * focal)
        d[OUT] = numpy.sqrt((n[OUT]+.5) * nomlambda * focal + R0**2) - \
                 numpy.sqrt((n[OUT]-.5) * nomlambda * focal + R0**2)


    # computing G (the "grating" wavevector in Angstrom^-1)

    dA = d * 1.e8				# Angstrom
    Gx = -numpy.pi / dA * (x/r)
    Gz = -numpy.pi / dA * (z/r)

    # computing kout

    Kxout = Kxin + Gx
    Kzout = Kzin + Gz
    xpout = Kxout / Kmod
    zpout = Kzout / Kmod


    # Handle rays that arrive outside the FZP
    # flag for lost rays

    LOST = numpy.where(r > DD/2)
    LOST = numpy.array(LOST)
    if LOST.size > 0:
        beam.rays[LOST,9] = -100.0


    beam.rays[:,3] = xpout
    beam.rays[:,4] = numpy.sqrt(1 - xpout**2 - zpout**2)
    beam.rays[:,5] = zpout

    return beam



if __name__ == "__main__":

    # get source
    beam = get_beam()
    # apply FZP ay the spurce position
    beam_out = fresnel_zone_plane(beam)
    # propagate both source and beam after FZP until focal plane at 1m
    beam.retrace(100)
    beam_out.retrace(100.0)

    # make plots
    Shadow.ShadowTools.plotxy(beam,1,3,nbins=101,nolost=1,title="Without FZP - Propagated source - Real space")
    Shadow.ShadowTools.plotxy(beam_out,1,3,nbins=101,nolost=1,title="With FZP - Focused - Real space")