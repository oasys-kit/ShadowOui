#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2018, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2018. UChicago Argonne, LLC. This software was produced       #
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
# #########################################################################

import os, numpy

from orangewidget import gui

from oasys.widgets import widget

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from oasys.util.oasys_objects import OasysPreProcessorData

from Shadow import ShadowTools as ST
from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData


class OWMultipleOasysDataConverter(widget.OWWidget):
    name = "Multiple Oasys Surface Data Converter"
    id = "oasysDataConverter"
    description = "Multiple Oasys Surface Data Converter"
    icon = "icons/multiple_oasys_data_converter.png"
    priority = 60
    category = ""
    keywords = ["wise", "gaussian"]

    inputs = [("Oasys PreProcessorData", OasysPreProcessorData, "set_input")]

    outputs = [{"name": "PreProcessor_Data",
                "type": ShadowPreProcessorData,
                "doc": "PreProcessor Data",
                "id": "PreProcessor_Data"},
               {"name":"Files",
                "type":list,
                "doc":"Files",
                "id":"Files"}]

    CONTROL_AREA_WIDTH = 605

    want_main_area = 0

    oasys_data = None

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 100))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)


        label = gui.label(self.controlArea, self, "From Multiple Oasys Surfaces To Shadow Surfaces")
        font = QFont(label.font())
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(14)
        label.setFont(font)
        palette = QPalette(label.palette()) # make a copy of the palette
        palette.setColor(QPalette.Foreground, QColor('Dark Blue'))
        label.setPalette(palette) # assign new palette

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_surfaces, height=45)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.oasys_data = input_data

            self.convert_surfaces()

    def convert_surfaces(self):
        if not self.oasys_data is None:
            try:
                if isinstance(self.oasys_data, OasysPreProcessorData):
                    error_profile_data = self.oasys_data.error_profile_data
                    surface_data = error_profile_data.surface_data

                    error_profile_data_files = []

                    for xx, yy, zz, error_profile_data_file in zip(surface_data.xx,
                                                                   surface_data.yy,
                                                                   surface_data.zz,
                                                                   surface_data.surface_data_file):

                        filename, file_extension = os.path.splitext(error_profile_data_file)

                        if (file_extension==".hd5" or file_extension==".hdf5" or file_extension==".hdf"):
                            error_profile_data_file = filename + "_shadow.dat"

                        ST.write_shadow_surface(zz/self.workspace_units_to_m,
                                                numpy.round(xx/self.workspace_units_to_m, 6),
                                                numpy.round(yy/self.workspace_units_to_m, 6),
                                                error_profile_data_file)

                        error_profile_data_files.append(error_profile_data_file)

                    self.send("PreProcessor_Data", ShadowPreProcessorData(error_profile_data_file=error_profile_data_files,
                                                                          error_profile_x_dim=error_profile_data.error_profile_x_dim/self.workspace_units_to_m,
                                                                          error_profile_y_dim=error_profile_data.error_profile_y_dim/self.workspace_units_to_m))
                    self.send("Files", error_profile_data_files)
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                if self.IS_DEVELOP: raise exception
