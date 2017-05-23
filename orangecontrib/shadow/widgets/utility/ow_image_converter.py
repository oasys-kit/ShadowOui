import os

import numpy
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui

from orangewidget import gui
from orangewidget.settings import Setting

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtGui import QColor

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

class ImageToBeamConverter(widget.OWWidget):

    name = "Image To Beam"
    description = "Utility: ImageToBeamConverter"
    icon = "icons/image_converter.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 6
    category = "Utility"
    keywords = ["data", "file", "load", "read"]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    want_main_area = 0

    is_textual = Setting(False)
    number_of_x_pixels = Setting(0)
    number_of_z_pixels = Setting(0)

    image_file_name=Setting("")
    pixel_size = Setting(14.0)
    number_of_x_bins = Setting(10)
    number_of_z_bins = Setting(5)
    flip_vertically = Setting(1)
    flip_horizontally = Setting(0)

    def __init__(self):
        self.setFixedWidth(590)
        self.setFixedHeight(550)

        left_box_1 = oasysgui.widgetBox(self.controlArea, "CCD Image", addSpace=True, orientation="vertical")

        gui.comboBox(left_box_1, self, "is_textual", label="Image Type", labelWidth=250, items=["JPEG/PNG", "Textual"], sendSelectedValue=False, orientation="horizontal", callback=self.setTextual)

        ########################################

        self.select_file_box_1 = oasysgui.widgetBox(left_box_1, "Textual Image Parameters", addSpace=True, orientation="horizontal", height=250)

        self.le_image_txt_file_name = oasysgui.lineEdit(self.select_file_box_1, self, "image_file_name", "Image File Name", labelWidth=120, valueType=str, orientation="horizontal")
        self.le_image_txt_file_name.setFixedWidth(300)

        gui.button(self.select_file_box_1, self, "...", callback=self.selectTxtFile)


        self.select_file_box_2 = oasysgui.widgetBox(left_box_1, "Image Parameters", addSpace=True, orientation="vertical", height=250)

        select_file_box_2_int = oasysgui.widgetBox(self.select_file_box_2, "", addSpace=True, orientation="horizontal")

        self.le_image_file_name = oasysgui.lineEdit(select_file_box_2_int, self, "image_file_name", "Image File Name", labelWidth=120, valueType=str, orientation="horizontal")
        self.le_image_file_name.setFixedWidth(300)

        gui.button(select_file_box_2_int, self, "...", callback=self.selectFile)

        figure_box = oasysgui.widgetBox(self.select_file_box_2, "Preview", addSpace=True, orientation="vertical", width=350, height=180)

        self.preview_box = QtGui.QLabel("")
        self.preview_box.setFixedHeight(100)

        figure_box.layout().addWidget(self.preview_box)

        le = oasysgui.lineEdit(figure_box, self, "number_of_x_pixels", "Number of x Pixels", labelWidth=200, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        font = QtGui.QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QtGui.QPalette(le.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        le.setPalette(palette)
        le = oasysgui.lineEdit(figure_box, self, "number_of_z_pixels", "Number of z Pixels", labelWidth=200, valueType=int, orientation="horizontal")
        le.setReadOnly(True)
        font = QtGui.QFont(le.font())
        font.setBold(True)
        le.setFont(font)
        palette = QtGui.QPalette(le.palette()) # make a copy of the palette
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor('dark blue'))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(243, 240, 160))
        le.setPalette(palette)

        ########################################

        self.setTextual()
        self.loadImage()

        oasysgui.lineEdit(left_box_1, self, "pixel_size", "Pixel Size [um]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "number_of_x_bins", "Number of Bin per Pixel [x]", labelWidth=200, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "number_of_z_bins", "Number of Bin per Pixel [z]", labelWidth=200, valueType=int, orientation="horizontal")
        gui.checkBox(left_box_1, self, "flip_vertically", "Flip Vertically")
        gui.checkBox(left_box_1, self, "flip_horizontally", "Flip Horizontally")

        gui.separator(self.controlArea)

        button = gui.button(self.controlArea, self, "Convert To Beam", callback=self.convertToBeam)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

    def selectTxtFile(self):
        self.le_image_txt_file_name.setText(oasysgui.selectFileFromDialog(self, self.image_txt_file_name, "Open Textual Image", file_extension_filter="Text Files (*.txt)"))

    def selectFile(self):
        self.le_image_file_name.setText(oasysgui.selectFileFromDialog(self, self.image_file_name, "Open Image", file_extension_filter="Image Files (*.png *.jpg)"))
        self.loadImage()

    def loadImage(self):
        if self.is_textual == 0:
            pixmap = QtGui.QPixmap(self.image_file_name)

            self.preview_box.setPixmap(pixmap)
            self.number_of_x_pixels = pixmap.width()
            self.number_of_z_pixels = pixmap.height()

    def setTextual(self):
        self.select_file_box_2.setVisible(self.is_textual==0)
        self.select_file_box_1.setVisible(self.is_textual==1)


    def convertToBeam(self):

        self.progressBarInit()
        self.progressBarSet(10)

        #self.information(0, "Converting Image Map")
        self.setStatusMessage("Converting Image Map")

        text_image = self.image_file_name

        if not self.is_textual:
            text_image = self.convertImagetoText()

        map = self.convertTextImageToXYMap(text_image)

        self.progressBarSet(50)

        beam_out = self.convertMapToBeam(map)

        #self.information(0, "Plotting Results")
        self.setStatusMessage("Plotting Results")

        self.progressBarSet(80)

        #self.information()
        self.setStatusMessage("")

        self.progressBarFinished()

        self.send("Beam", beam_out)

    def convertImagetoText(self):
        if str(self.image_file_name).endswith("txt") or str(self.image_file_name).endswith("TXT"):
          return self.image_file_name

        else:
            out_file_name = os.getcwd() + "/Output/temp_image.txt"
            out_file = open(out_file_name, "w")

            separator = '	'

            image = QtGui.QImage(self.image_file_name)

            x_pixels = image.width()
            z_pixels = image.height()

            for z_index in range (0, z_pixels):

                row = ""

                for x_index in range (0, x_pixels):
                    color = QColor(image.pixel(x_index, z_index))

                    red = color.red()
                    blue = color.blue()
                    green = color.green()

                    grey = (red*11+green*16+blue*5)/32

                    if x_index == x_pixels - 1:
                        row += str(int(grey))
                    else:
                        row += str(int(grey)) + separator

                out_file.write(row + "\r")

            out_file.flush()
            out_file.close()

        return out_file_name

    def convertTextImageToXYMap(self, text_image_file_name):
        input_file = open(text_image_file_name, "r")

        map = []
        rows = input_file.readlines()

        if (len(rows) > 0):
            p0 = self.pixel_size*0.5*1e-4
            p0_bin_z = p0/self.number_of_z_bins
            p0_bin_x = p0/self.number_of_x_bins

            number_of_x_pixels = len(rows[0].split('	'))
            number_of_z_pixels = len(rows)

            if (number_of_x_pixels*number_of_z_pixels*self.number_of_x_bins*self.number_of_z_bins) > 500000: raise Exception("Number of Pixels too high (>500000)")

            x0 = -p0*number_of_x_pixels*0.5
            z0 = -p0*number_of_z_pixels*0.5

            for z_index in range (0, len(rows)):
                values = rows[z_index].split('	')

                for z_pixel_bin_index in range(0, self.number_of_z_bins):
                    if (self.flip_vertically):
                        z = z0 + (p0*z_index + p0_bin_z*z_pixel_bin_index)
                    else:
                        z = z0 - (p0*z_index + p0_bin_z*z_pixel_bin_index)

                    for x_index in range(0, len(values)):
                        for x_pixel_bin_index in range(0, self.number_of_x_bins):
                            if (self.flip_horizontally):
                                x = x0 - (p0*x_index + p0_bin_x*x_pixel_bin_index)
                            else:
                                x = x0 + (p0*x_index + p0_bin_x*x_pixel_bin_index)

                            point = ImagePoint(x, 0, z, int(values[x_index]))
                            map.append(point)

        return map

    def convertMapToBeam(self, map):

        number_of_rays = len(map)

        if number_of_rays == 0: return None

        beam_out = ShadowBeam(number_of_rays=number_of_rays)

        for index in range(0, number_of_rays):
            point = map[index]

            ray = beam_out._beam.rays[index]

            E_value = numpy.sqrt(point.value*0.5)

            ray[0]  = point.x                       # X
            ray[1]  = point.y                        # Y
            ray[2]  = point.z                        # Z
            ray[3]  = 0                             # director cos x
            ray[4]  = 1                              # director cos y
            ray[5]  = 0                             # director cos z
            ray[6]  = 0  # Es_x
            ray[7]  = E_value  # Es_y
            ray[8]  = 0  # Es_z
            ray[9]  = 1  # good/lost
            ray[10] = 2*numpy.pi/1.5e-8
            ray[11] = index # ray index
            ray[12] = 1                                     # good only
            ray[13] = numpy.pi*0.5 # Es_phi
            ray[14] = numpy.pi*0.5 # Ep_phi
            ray[15] = 0 # Ep_x
            ray[16] = E_value # Ep_y
            ray[17] = 0 # Ep_z

        return beam_out

class ImagePoint:

    x = 0.0
    y = 0.0
    z = 0.0
    value = 0.0

    def __init__(self, x=0.0, y=0.0, z=0.0, value=0.0):
       self.x = x
       self.y = y
       self.z = z
       self.value = value
