from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets import widget
from orangewidget.settings import Setting

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

from wofryshadow.propagator.wavefront2D.shadow3_wavefront import SHADOW3Wavefront

class OWToWofryWavefront2d(widget.OWWidget):
    name = "To Wofry Wavefront 2D"
    id = "toWofryWavefront2D"
    description = "To Wofry Wavefront 2D"
    icon = "icons/to_wofry_wavefront_2d.png"
    priority = 2
    category = ""
    keywords = ["shadow", "gaussian"]

    inputs = [("Beam", ShadowBeam, "set_input")]

    outputs = [{"name":"GenericWavefront2D",
                "type":GenericWavefront2D,
                "doc":"GenericWavefront2D",
                "id":"GenericWavefront2D"}]

    CONTROL_AREA_WIDTH = 605

    want_main_area = 0

    pixels_h = Setting(100)
    pixels_v = Setting(100)

    shadow_beam = None

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.CONTROL_AREA_WIDTH+10)),
                               round(min(geom.height()*0.95, 220))))

        self.setFixedHeight(self.geometry().height())
        self.setFixedWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.CONTROL_AREA_WIDTH)

        label = gui.label(self.controlArea, self, "From Shadow Beam To Wofry Wavefront")
        font = QFont(label.font())
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(14)
        label.setFont(font)
        palette = QPalette(label.palette()) # make a copy of the palette
        palette.setColor(QPalette.Foreground, QColor('Dark Blue'))
        label.setPalette(palette) # assign new palette

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_beam, height=45)

        gui.separator(self.controlArea, 10)

        main_box = oasysgui.widgetBox(self.controlArea, "Converter Settings", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=100)

        oasysgui.lineEdit(main_box, self, "pixels_h", "Number of Pixels (H)", labelWidth=280, valueType=int, orientation="horizontal")
        oasysgui.lineEdit(main_box, self, "pixels_v", "Number of Pixels (V)", labelWidth=280, valueType=int, orientation="horizontal")

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.shadow_beam = input_data

            self.convert_beam()


    def convert_beam(self):
        try:
            if not self.shadow_beam is None:
                if self.pixels_h <= 1: self.pixels_h = 100
                if self.pixels_v <= 1: self.pixels_v = 100

                self.send("GenericWavefront2D",
                          SHADOW3Wavefront.initialize_from_shadow3_beam(self.shadow_beam._beam).toGenericWavefront(
                              pixels_h=self.pixels_h,
                              pixels_v=self.pixels_v,
                              shadow_to_meters=self.workspace_units_to_m))
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            raise exception
