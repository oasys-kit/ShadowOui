#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------- #
# Copyright (c) 2021, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2021. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# ----------------------------------------------------------------------- #

import numpy
from Shadow import OE, IdealLensOE, CompoundOE

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

from oasys.widgets.abstract.beamline_rendering.ow_abstract_beamline_renderer import AbstractBeamlineRenderer, AspectRatioModifier, Orientations, OpticalElementsColors, initialize_arrays

class ShadowBeamlineRenderer(AbstractBeamlineRenderer):
    name = "Beamline Renderer"
    description = "Beamline Renderer"
    icon = "icons/renderer.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 1000
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    input_beam=None

    def setBeam(self, beam):
        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam

                self.render()

    def render_beamline(self, reset_rotation=True):
        if not self.input_beam is None:
            self.axis.clear()
            self.axis.text2D(0.05, 0.95,
                            "Mouse Left Button (Hold and Drag): Rotate\nMouse Right Button (Hold and Drag): Zoom\nMouse Left & Right Buttons or Central Buttons (Hold and Drag): Shift",
                            transform=self.axis.transAxes,
                            color='blue')


            number_of_elements=self.input_beam.historySize() + 1

            centers, limits = initialize_arrays(number_of_elements=number_of_elements)

            aspect_ratio_modifier = AspectRatioModifier(element_expansion_factor=[self.element_expansion_factor,
                                                                                  self.element_expansion_factor,
                                                                                  self.element_expansion_factor],
                                                        layout_reduction_factor=[1/self.distance_compression_factor,
                                                                                 1.0,
                                                                                 1,0])
            previous_oe_distance    = 0.0
            previous_image_distance = 0.0
            previous_height = self.initial_height # for better visibility
            previous_shift  = 0.0
            previous_orientation = Orientations.UP
            beam_horizontal_inclination = 0.0
            beam_vertical_inclination = 0.0

            TODEG = 180.0 / numpy.pi

            for history_element in self.input_beam.getOEHistory():
                if not history_element._shadow_source_end is None:
                    #source = history_element._shadow_source_end.src
                    self.add_source(centers, limits, length=0.0, height=self.initial_height, canting=0.0, aspect_ration_modifier=aspect_ratio_modifier)
                elif not history_element._shadow_oe_end is None:
                    oe_number = history_element._oe_number
                    oe_end   = history_element._shadow_oe_end._oe
                    oe_start = history_element._shadow_oe_start._oe

                    source_distance = oe_end.T_SOURCE
                    image_distance  = oe_end.T_IMAGE

                    oe_distance = previous_oe_distance + previous_image_distance + source_distance

                    def get_height_shift():
                        if previous_orientation == Orientations.UP:
                            height = previous_height + (source_distance + previous_image_distance)*numpy.sin(2*beam_vertical_inclination)
                            shift  = previous_shift
                        elif previous_orientation == Orientations.DOWN:
                            height = previous_height - (source_distance + previous_image_distance)*numpy.sin(2*beam_vertical_inclination)
                            shift  = previous_shift
                        if previous_orientation == Orientations.LEFT:
                            height = previous_height
                            shift  = previous_shift - (source_distance + previous_image_distance)*numpy.sin(2*beam_horizontal_inclination)
                        elif previous_orientation == Orientations.RIGHT:
                            height = previous_height
                            shift  = previous_shift + (source_distance + previous_image_distance)*numpy.sin(2*beam_horizontal_inclination)

                        return height, shift

                    if isinstance(oe_end, OE):
                        if oe_end.F_REFRAC == 2: # empty element
                            height, shift = get_height_shift()
                            self.add_point(centers, limits,
                                           oe_index=oe_number, distance=oe_distance, height=height, shift=shift,
                                           label="Empty Element", aspect_ratio_modifier=aspect_ratio_modifier)
                        else:
                            if oe_end.F_REFRAC == 0:
                                if oe_end.IDUMMY == 0:  # oe not changed by shadow, angles in deg changed to rad
                                    inclination = (90 - oe_end.T_INCIDENCE) / TODEG
                                    alpha       = int(oe_end.ALPHA)
                                else:
                                    inclination  = (numpy.pi/2) - oe_end.T_INCIDENCE
                                    alpha        = int(oe_end.ALPHA * TODEG)

                                height, shift = get_height_shift()

                                print()

                                if previous_orientation == Orientations.UP:
                                    if alpha == 0:     orientation = Orientations.UP
                                    elif alpha == 90:  orientation = Orientations.LEFT
                                    elif alpha == 180: orientation = Orientations.DOWN
                                    elif alpha == 270: orientation = Orientations.RIGHT
                                elif previous_orientation == Orientations.DOWN:
                                    if alpha == 0:     orientation = Orientations.DOWN
                                    elif alpha == 90:  orientation = Orientations.RIGHT
                                    elif alpha == 180: orientation = Orientations.UP
                                    elif alpha == 270: orientation = Orientations.LEFT
                                elif previous_orientation == Orientations.LEFT:
                                    if alpha == 0:     orientation = Orientations.LEFT
                                    elif alpha == 90:  orientation = Orientations.DOWN
                                    elif alpha == 180: orientation = Orientations.RIGHT
                                    elif alpha == 270: orientation = Orientations.UP
                                elif previous_orientation == Orientations.RIGHT:
                                    if alpha == 0:     orientation = Orientations.RIGHT
                                    elif alpha == 90:  orientation = Orientations.UP
                                    elif alpha == 180: orientation = Orientations.LEFT
                                    elif alpha == 270: orientation = Orientations.DOWN

                                if oe_end.FHIT_C == 1:
                                    width = oe_start.RWIDX1 + oe_start.RWIDX2
                                    length = oe_start.RLEN1 + oe_start.RLEN2
                                else:
                                    width = 100 / self.workspace_units_to_mm
                                    length = 100 / self.workspace_units_to_mm

                                if oe_end.F_CRYSTAL == 1:
                                    color = OpticalElementsColors.CRYSTAL
                                    label = "Crystal"
                                elif oe_end.F_GRATING == 1:
                                    color = OpticalElementsColors.GRATING
                                    label = "Grating"
                                else:
                                    color = OpticalElementsColors.MIRROR
                                    label = "Mirror"

                                self.add_optical_element(centers, limits,
                                                         oe_index=oe_number, distance=oe_distance, height=height, shift=shift,
                                                         length=length, width=width, thickness=10/self.workspace_units_to_mm, inclination=inclination, orientation=orientation,
                                                         color=color, aspect_ration_modifier=aspect_ratio_modifier, label=label)

                                if orientation == Orientations.UP:      beam_vertical_inclination += inclination
                                elif orientation == Orientations.DOWN:  beam_vertical_inclination -= inclination
                                elif orientation == Orientations.LEFT:  beam_horizontal_inclination -= inclination
                                elif orientation == Orientations.RIGHT: beam_horizontal_inclination += inclination

                                previous_orientation = orientation
                            else:
                                height, shift = get_height_shift()
                                self.add_point(centers, limits,
                                               oe_index=oe_number, distance=oe_distance, height=height, shift=shift,
                                               label="Refractor (not implemented)", aspect_ratio_modifier=aspect_ratio_modifier)
                    elif isinstance(oe_end, IdealLensOE):
                        height, shift = get_height_shift()
                        self.add_point(centers, limits,
                                       oe_index=oe_number, distance=oe_distance, height=height, shift=shift,
                                       label="Ideal Lens (not implemented)", aspect_ratio_modifier=aspect_ratio_modifier)
                    elif isinstance(oe_end, CompoundOE):
                        height, shift = get_height_shift()
                        self.add_point(centers, limits,
                                       oe_index=oe_number, distance=oe_distance, height=height, shift=shift,
                                       label="Compound OE (not implemented)", aspect_ratio_modifier=aspect_ratio_modifier)

                    previous_height         = height
                    previous_shift          = shift
                    previous_oe_distance    = oe_distance
                    previous_image_distance = image_distance

            height, shift = get_height_shift()
            self.add_point(centers, limits, oe_index=self.input_beam.historySize(), distance=previous_oe_distance + previous_image_distance,
                           height=height, shift=shift, label="End Point",
                           aspect_ratio_modifier=aspect_ratio_modifier)

            limits[:, 0, :] *= 10 # X axis

            if self.use_range == 1:
                for i in range(number_of_elements): limits[i, 1, :] = numpy.array([self.range_min, self.range_max])
                self.draw_central_radiation_line(centers=centers, rng=numpy.array([self.range_min, self.range_max]))
            else:
                self.draw_central_radiation_line(centers=centers)

            self.axis.set_xlim([numpy.min(limits[:, 0, :]), numpy.max(limits[:, 0, :])])
            self.axis.set_ylim([numpy.min(limits[:, 1, :]), numpy.max(limits[:, 1, :])])
            self.axis.set_zlim([numpy.min([0.0, numpy.min(limits[:, 2, :])]), numpy.max(limits[:, 2, :])])

            length_x = numpy.max(limits[:, 0, :]) - numpy.min(limits[:, 0, :])
            length_y = numpy.max(limits[:, 1, :]) - numpy.min(limits[:, 1, :])
            length_z = numpy.max(limits[:, 2, :])

            factor = numpy.max([length_x, length_y, length_z])

            self.axis.set_box_aspect(((length_x/factor), (length_y/factor), (length_z/factor)))

            self.axis.set_xlabel("Width")
            self.axis.set_ylabel("Length")
            self.axis.set_zlabel("Height")

            if reset_rotation: self.reset_rotation()

