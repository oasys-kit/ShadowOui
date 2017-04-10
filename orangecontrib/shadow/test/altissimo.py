import xraylib
import numpy, copy, re

from oasys.util.oasys_util import ChemicalFormulaParser

from orangecontrib.shadow.util.shadow_util import ShadowPhysics, ShadowMath
from orangecontrib.shadow.util.shadow_objects import ShadowBeam, ShadowOpticalElement

AMPLITUDE_ZP = 0
PHASE_ZP = 1

# INPUT 

#type_of_zp = PHASE_ZP
type_of_zp = AMPLITUDE_ZP

source_plane_distance = 100
image_plane_distance = 2000

input_beam = in_object_1.duplicate(history=False)

delta_rn = 25 # nm
diameter = 618 # micron
zone_plate_material = "Au"
zone_plate_thickness = 200 # nm
substrate_material = "Si3N4"
substrate_thickness = 50 # nm

source_distance = 100

#################################


def get_material_density(material):
    elements = ChemicalFormulaParser.parse_formula(material)
    
    mass = 0.0
    volume = 0.0
    
    for element in elements:
        mass += element._molecular_weight*element._n_atoms
        volume += 10.*element._n_atoms
                
    rho = mass/(0.602*volume) 

    return rho
    
def get_material_weight_factor(shadow_beam, material, thickness):
    mu = numpy.zeros(len(shadow_beam._beam.rays))
    
    for i in range(0, len(mu)):
        mu[i] = xraylib.CS_Total_CP(material, ShadowPhysics.getEnergyFromShadowK(shadow_beam._beam.rays[i, 10])/1000) # energy in KeV
    
    rho = get_material_density(material)
                
    return numpy.sqrt(numpy.exp(-mu*rho*thickness*1e-7))
    

def get_delta_beta(shadow_rays, material):
    beta = numpy.zeros(len(shadow_rays))
    delta = numpy.zeros(len(shadow_rays))
    density = xraylib.ElementDensity(xraylib.SymbolToAtomicNumber(material))

    for i in range(0, len(shadow_rays)):
        energy_in_KeV = ShadowPhysics.getEnergyFromShadowK(shadow_rays[i, 10])/1000
        delta[i] = (1-xraylib.Refractive_Index_Re(material, energy_in_KeV, density))
        beta[i]  = xraylib.Refractive_Index_Im(material, energy_in_KeV, density)

    return delta, beta 

def apply_fresnel_zone_plate(input_beam, 
                             type_of_zp, 
                             diameter, 
                             delta_rn,                              
                             image_position, 
                             substrate_material, 
                             substrate_thickness,
                             zone_plate_material,
                             zone_plate_thickness):
    
    max_zones_number = int(diameter*1000/(4*delta_rn))

    print ("MZN", max_zones_number)

    focused_beam = input_beam.duplicate(history=False)
   
    if type_of_zp == PHASE_ZP: 
        substrate_weight_factor = get_material_weight_factor(focused_beam, substrate_material, substrate_thickness) 
    
        focused_beam._beam.rays[:, 6] = focused_beam._beam.rays[:, 6]*substrate_weight_factor[:]
        focused_beam._beam.rays[:, 7] = focused_beam._beam.rays[:, 7]*substrate_weight_factor[:]
        focused_beam._beam.rays[:, 8] = focused_beam._beam.rays[:, 8]*substrate_weight_factor[:]
        focused_beam._beam.rays[:, 15] = focused_beam._beam.rays[:, 15]*substrate_weight_factor[:]
        focused_beam._beam.rays[:, 16] = focused_beam._beam.rays[:, 16]*substrate_weight_factor[:]
        focused_beam._beam.rays[:, 17] = focused_beam._beam.rays[:, 17]*substrate_weight_factor[:]
    
    good_zones = []
    dark_zones = []
    r_zone_i_previous = 0.0
    for i in range(1, max_zones_number+1):
        r_zone_i = numpy.sqrt(i*diameter*1000*delta_rn)*1e-7
        if i % 2 == 0: good_zones.append([r_zone_i_previous, r_zone_i])
        else: dark_zones.append([r_zone_i_previous, r_zone_i])
        r_zone_i_previous = r_zone_i

    x = input_beam._beam.rays[:, 0]
    z = input_beam._beam.rays[:, 2]
    r = numpy.sqrt(x**2 + z**2) 
        
    focused_beam._beam.rays[:, 9] = -100
    
    for zone in good_zones:
        t = numpy.where(numpy.logical_and(r >= zone[0], r <= zone[1]))

        intercepted_rays = focused_beam._beam.rays[t]
                
        # (see formulas in A.G. Michette, "X-ray science and technology"
        #  Institute of Physics Publishing (1993))

        x_int = intercepted_rays[:, 0]
        z_int = intercepted_rays[:, 2]
        xp_int = intercepted_rays[:, 3]
        zp_int = intercepted_rays[:, 5]
        k_mod_int = intercepted_rays[:, 10]

        r_int = numpy.sqrt(x_int**2 + z_int**2) 
      
        k_x_int = k_mod_int*xp_int
        k_z_int = k_mod_int*zp_int
        d = zone[1] - zone[0]
        
        # computing G (the "grating" wavevector in Angstrom^-1)
        gx = -numpy.pi / d * (x_int/r_int)
        gz = -numpy.pi / d * (z_int/r_int)
       
        k_x_out = k_x_int + gx
        k_z_out = k_z_int + gz
        xp_out = k_x_out / k_mod_int
        zp_out = k_z_out / k_mod_int
   
        intercepted_rays[:, 3] = xp_out # XP
        intercepted_rays[:, 5] = zp_out # ZP
        intercepted_rays[:, 9] = 1 
                    
        focused_beam._beam.rays[t, 3] = intercepted_rays[:, 3]       
        focused_beam._beam.rays[t, 4] = intercepted_rays[:, 4]       
        focused_beam._beam.rays[t, 5] = intercepted_rays[:, 5]       
        focused_beam._beam.rays[t, 9] = intercepted_rays[:, 9]    

    if type_of_zp == PHASE_ZP: 
        for zone in dark_zones:
            t = numpy.where(numpy.logical_and(r >= zone[0], r <= zone[1]))

            intercepted_rays = focused_beam._beam.rays[t]
                
            # (see formulas in A.G. Michette, "X-ray science and technology"
            #  Institute of Physics Publishing (1993))

            x_int = intercepted_rays[:, 0]
            z_int = intercepted_rays[:, 2]
            xp_int = intercepted_rays[:, 3]
            zp_int = intercepted_rays[:, 5]
            k_mod_int = intercepted_rays[:, 10]

            r_int = numpy.sqrt(x_int**2 + z_int**2) 
      
            k_x_int = k_mod_int*xp_int
            k_z_int = k_mod_int*zp_int
            d = zone[1] - zone[0]
        
            # computing G (the "grating" wavevector in Angstrom^-1)
            gx = -numpy.pi / d * (x_int/r_int)
            gz = -numpy.pi / d * (z_int/r_int)
       
            k_x_out = k_x_int + gx
            k_z_out = k_z_int + gz
            xp_out = k_x_out / k_mod_int
            zp_out = k_z_out / k_mod_int
   
            intercepted_rays[:, 3] = xp_out # XP
            intercepted_rays[:, 5] = zp_out # ZP
            intercepted_rays[:, 9] = 1 
                    
            focused_beam._beam.rays[t, 3] = intercepted_rays[:, 3]       
            focused_beam._beam.rays[t, 4] = intercepted_rays[:, 4]       
            focused_beam._beam.rays[t, 5] = intercepted_rays[:, 5]       
            focused_beam._beam.rays[t, 9] = intercepted_rays[:, 9]    

    go = numpy.where(focused_beam._beam.rays[:, 9] == 1)
    lo = numpy.where(focused_beam._beam.rays[:, 9] != 1)

    intensity_go = numpy.sum(focused_beam._beam.rays[go, 6] ** 2 + focused_beam._beam.rays[go, 7] ** 2 + focused_beam._beam.rays[go, 8] ** 2 + \
                             focused_beam._beam.rays[go, 15] ** 2 + focused_beam._beam.rays[go, 16] ** 2 + focused_beam._beam.rays[go, 17] ** 2)

    intensity_lo = numpy.sum(focused_beam._beam.rays[lo, 6] ** 2 + focused_beam._beam.rays[lo, 7] ** 2 + focused_beam._beam.rays[lo, 8] ** 2 + \
                             focused_beam._beam.rays[lo, 15] ** 2 + focused_beam._beam.rays[lo, 16] ** 2 + focused_beam._beam.rays[lo, 17] ** 2)


    if type_of_zp == PHASE_ZP:
        wavelength = ShadowPhysics.getWavelengthFromShadowK(focused_beam._beam.rays[go, 10])*1e-8 #cm
        delta, beta = get_delta_beta(focused_beam._beam.rays[go], zone_plate_material)
        
        phi = 2*numpy.pi*(zone_plate_thickness*1e-7)*delta/wavelength
        r = beta/delta
           
        efficiency_zp = ((1 + numpy.exp(-2*r*phi) - (2*numpy.exp(-r*phi)*numpy.cos(phi)))/numpy.pi)**2

        efficiency_weight_factor = numpy.sqrt(efficiency_zp)
    elif type_of_zp == AMPLITUDE_ZP:
        efficiency_zp = numpy.ones(len(focused_beam._beam.rays[go]))/(numpy.pi**2)
        efficiency_weight_factor = numpy.sqrt(efficiency_zp*(1 + (intensity_lo/intensity_go)))
    
    print ("EFF", efficiency_weight_factor**2, numpy.max(efficiency_weight_factor**2), numpy.min(efficiency_weight_factor**2))
    
    focused_beam._beam.rays[go, 6] = focused_beam._beam.rays[go, 6]*efficiency_weight_factor[:]
    focused_beam._beam.rays[go, 7] = focused_beam._beam.rays[go, 7]*efficiency_weight_factor[:]
    focused_beam._beam.rays[go, 8] = focused_beam._beam.rays[go, 8]*efficiency_weight_factor[:]
    focused_beam._beam.rays[go, 15] = focused_beam._beam.rays[go, 15]*efficiency_weight_factor[:]
    focused_beam._beam.rays[go, 16] = focused_beam._beam.rays[go, 16]*efficiency_weight_factor[:]
    focused_beam._beam.rays[go, 17] = focused_beam._beam.rays[go, 17]*efficiency_weight_factor[:]
    
    return focused_beam
    

#################################


empty_element = ShadowOpticalElement.create_empty_oe()

empty_element._oe.DUMMY = 1.0 # self.workspace_units_to_cm

empty_element._oe.T_SOURCE     = source_plane_distance
empty_element._oe.T_IMAGE      = 0.0
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
k_slit = numpy.array([1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
thick = numpy.zeros(10)
file_abs = numpy.array(['', '', '', '', '', '', '', '', '', ''])
rx_slit = numpy.zeros(10)
rz_slit = numpy.zeros(10)
sl_dis = numpy.zeros(10)
file_scr_ext = numpy.array(['', '', '', '', '', '', '', '', '', ''])
cx_slit = numpy.zeros(10)
cz_slit = numpy.zeros(10)

sl_dis[0] = 0.0
rx_slit[0] = diameter*1e-4
rz_slit[0] = diameter*1e-4
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


zone_plate_beam = ShadowBeam.traceFromOE(input_beam, empty_element, history=False)

go = numpy.where(zone_plate_beam._beam.rays[:, 9] == 1)

go_input_beam = ShadowBeam()
go_input_beam._beam.rays = copy.deepcopy(zone_plate_beam._beam.rays[go])

###################################################

avg_wavelength = ShadowPhysics.getWavelengthFromShadowK(numpy.average(go_input_beam._beam.rays[:, 10]))*1e-1 #ANGSTROM->nm

print ("W", avg_wavelength, "nm")

focal_distance = (delta_rn*(1000*diameter)/avg_wavelength)*1e-7 # cm
image_position = focal_distance*source_distance/(source_distance-focal_distance)
magnification = numpy.abs(image_position/source_distance)

print ("FD", focal_distance, "cm")
print ("Q", image_position, "cm")
print ("M", magnification)

out_beam = apply_fresnel_zone_plate(go_input_beam, type_of_zp, diameter, delta_rn, image_position, substrate_material, substrate_thickness, zone_plate_material, zone_plate_thickness)
#out_beam._beam.retrace(image_position)

print("BBONI", len(out_beam._beam.rays[numpy.where(out_beam._beam.rays[:, 9] == 1)]))
print("CASSATI", len(out_beam._beam.rays[numpy.where(out_beam._beam.rays[:, 9] != 1)]))

#go_input_beam._beam.retrace(image_position)

out_object = [go_input_beam, out_beam]
