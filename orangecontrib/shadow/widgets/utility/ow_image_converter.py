import numpy
from oasys.widgets import widget
from oasys.widgets import gui as oasysgui

from orangewidget import gui
from orangewidget.settings import Setting

from PIL import Image
import requests
from io import BytesIO

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

from PyQt5.QtWidgets import QApplication, QMessageBox

from srxraylib.util.inverse_method_sampler import Sampler2D

from silx.gui.plot import Plot2D
from silx.gui.colors import Colormap

class ImageToBeamConverter(widget.OWWidget):

    name = "Image To Beam"
    description = "Utility: ImageToBeamConverter"
    icon = "icons/image_converter.png"
    maintainer = "Luca Rebuffi and Manuel Sanchez del Rio"
    maintainer_email = "lrebuffi(@at@)anl.gov"
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

    image_file_name=Setting("https://www.lbl.gov/wp-content/uploads/2013/06/Lawrence-tb.jpg")
    pixel_size = Setting(14.0)
    number_of_rays = Setting(50000)
    number_of_x_bins = Setting(10)
    number_of_z_bins = Setting(5)

    image_nparray = None

    def __init__(self):
        self.setFixedWidth(700)
        self.setFixedHeight(600)


        left_box_1 = oasysgui.widgetBox(self.controlArea, "CCD Image", addSpace=True, orientation="vertical")

        ########################################  Image File
        self.select_file_box_1 = oasysgui.widgetBox(left_box_1, orientation="horizontal") #"", addSpace=False, orientation="horizontal", height=50)
        self.le_image_txt_file_name = oasysgui.lineEdit(self.select_file_box_1, self, "image_file_name", "Image File or URL",
                                                        labelWidth=150, valueType=str, orientation="horizontal")
        gui.button(self.select_file_box_1, self, "...", callback=self.selectFile)
        gui.button(self.select_file_box_1, self, "Reload", callback=self.loadFileToNumpyArray)

        # ##################   Preview
        select_file_box_2_figure = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="vertical")

        figure_box = oasysgui.widgetBox(select_file_box_2_figure, "Preview", addSpace=True, orientation="vertical", width=650, height=325)
        self.preview_box = Plot2D()

        figure_box.layout().addWidget(self.preview_box)

        self.preview_box.setKeepDataAspectRatio(True)

        #########################################  image operations
        operations_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal")
        gui.button(operations_box, self, "Flip Vertically",callback=self.flip_v)
        gui.button(operations_box, self, "Flip Horizontally",callback=self.flip_h)
        gui.button(operations_box, self, "90 deg rotation (CCW)", callback=self.rot_ccw)
        gui.button(operations_box, self, "90 deg rotation (CW)", callback=self.rot_cw)


        ################################# beam parameters
        beam_parameters_box = oasysgui.widgetBox(left_box_1, "", addSpace=True, orientation="horizontal")
        oasysgui.lineEdit(beam_parameters_box, self, "pixel_size", "Pixel Size [um]", labelWidth=200, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(beam_parameters_box, self, "number_of_rays", "Number of sampled rays", labelWidth=200, valueType=int, orientation="horizontal")

        gui.separator(self.controlArea)

        button = gui.button(self.controlArea, self, "Convert To Beam", callback=self.convertToBeam)
        button.setFixedHeight(45)

        gui.rubber(self.controlArea)

        if self.image_file_name != "":
            self.loadFileToNumpyArray()


    def selectFile(self):
        self.image_file_name = oasysgui.selectFileFromDialog(self, self.image_file_name, "Open Image",
                                file_extension_filter="(*.png *.jpg *.jpeg *csv)")
        self.loadFileToNumpyArray()

    def preview(self):
        self.preview_box.addImage(self.image_nparray.T,colormap=Colormap(name="reversed gray"))

    def setTextual(self):
        self.select_file_box_2.setVisible(self.is_textual==0)
        self.select_file_box_1.setVisible(self.is_textual==1)

    def is_remote(self):
        if self.image_file_name[0:4] == "http" or self.image_file_name[0:3] == "ftp":
            return True
        else:
            return False

    def loadFileToNumpyArray(self):

        if self.is_remote():
            try:
                response = requests.get(self.image_file_name)
                img = Image.open(BytesIO(response.content))
                img = numpy.array(img).sum(2) * 1.0
                img = numpy.rot90(img, axes=(1, 0))
                self.image_nparray = img.max() - img
            except:
                QMessageBox.information(self, "QMessageBox.information()",
                        "Impossible to load remote file:\n %s.\nUse jpg or png files"%self.image_file_name, QMessageBox.Ok)
        else:
            try:
                img = Image.open(self.image_file_name)
                img = numpy.array(img).sum(2) * 1.0
                img = numpy.rot90(img, axes=(1, 0))
                self.image_nparray = img.max() - img
            except:
                try:
                    self.image_nparray = numpy.loadtxt(self.image_file_name,delimiter=",")
                except:
                    QMessageBox.information(self, "QMessageBox.information()",
                            "Impossible to load file %s. Use jpg, png or csv file"%self.image_file_name,QMessageBox.Ok)

        self.preview()

    def flip_h(self):
        self.image_nparray = numpy.flip(self.image_nparray,axis=1)
        self.preview()

    def flip_v(self):
        self.image_nparray = numpy.flip(self.image_nparray,axis=0)
        self.preview()

    def rot_cw(self):
        self.image_nparray = numpy.rot90(self.image_nparray,axes=(1,0))
        self.preview()

    def rot_ccw(self):
        self.image_nparray = numpy.rot90(self.image_nparray,axes=(0,1))
        self.preview()


    def sample_points(self):
        try:
            x0 = numpy.arange(self.image_nparray.shape[0])
            x1 = numpy.arange(self.image_nparray.shape[1])

            s2d = Sampler2D(self.image_nparray, x0, x1)
            x0s, x1s = s2d.get_n_sampled_points(self.number_of_rays)

            return x0s, x1s

        except:
            QMessageBox.information(self, "QMessageBox.information()",
                        "Cannot sample points from data type: %s"%type(self.image_nparray))

    def convertToBeam(self):

        x0s, x1s = self.sample_points()

        self.progressBarInit()
        self.progressBarSet(10)
        self.setStatusMessage("Converting Image Map")

        self.progressBarSet(50)

        beam_out = self.convertMapToBeam(x0s,x1s)

        self.setStatusMessage("Plotting Results")

        self.progressBarSet(80)

        self.setStatusMessage("")

        self.progressBarFinished()

        self.send("Beam", beam_out)


    def convertMapToBeam(self, x0s, x1s):

        number_of_rays = x0s.size

        if number_of_rays == 0: return None

        beam_out = ShadowBeam(number_of_rays=number_of_rays)

        x = x0s - self.image_nparray.shape[0] / 2
        z = x1s - self.image_nparray.shape[1] / 2

        x *= self.pixel_size*1e-6 / self.workspace_units_to_m
        z *= self.pixel_size*1e-6 / self.workspace_units_to_m

        for index in range(0, number_of_rays):

            ray = beam_out._beam.rays[index]

            ray[0]  = x[index]                         # X
            ray[1]  = 0.0                              # Y
            ray[2]  = z[index]                         # Z
            ray[3]  = 0                                # director cos x
            ray[4]  = 1                                # director cos y
            ray[5]  = 0                                # director cos z
            ray[6]  = 1.0/numpy.sqrt(2)                # Es_x
            ray[7]  = 0.0                              # Es_y
            ray[8]  = 0.0                              # Es_z
            ray[9]  = 1                                # good/lost
            ray[10] = 2*numpy.pi/1e-8                  # wavenumber
            ray[11] = index                            # ray index
            ray[12] = 1                                # good only
            ray[13] = 0.0                              # Es_phi
            ray[14] = 0.0                              # Ep_phi
            ray[15] = 0.0                              # Ep_x
            ray[16] = 0.0                              # Ep_y
            ray[17] = 1.0/numpy.sqrt(2)                # Ep_z

        return beam_out


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    w = ImageToBeamConverter()
    w.workspace_units_to_m = 1.0
    w.show()
    app.exec()
    w.saveSettings()