from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets import widget

from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

from wofryshadow.propagator.wavefront2D.shadow3_wavefront import SHADOW3Wavefront

class OWFromWofryWavefront2d(widget.OWWidget):
    name = "From Wofry Wavefront 2D"
    id = "fromWofryWavefront2D"
    description = "from Wofry Wavefront 2D"
    icon = "icons/from_wofry_wavefront_2d.png"
    priority = 1
    category = ""
    keywords = ["shadow", "gaussian"]

    inputs = [("GenericWavefront2D", GenericWavefront2D, "set_input")]

    outputs = [{"name":"ShadowBeam",
                "type":ShadowBeam,
                "doc":"ShadowBeam",
                "id":"ShadowBeam"}]

    CONTROL_AREA_WIDTH = 605

    want_main_area = 0

    wavefront = None

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


        label = gui.label(self.controlArea, self, "From Wofry Wavefront To Shadow Beam")
        font = QFont(label.font())
        font.setBold(True)
        font.setItalic(True)
        font.setPixelSize(14)
        label.setFont(font)
        palette = QPalette(label.palette()) # make a copy of the palette
        palette.setColor(QPalette.Foreground, QColor('Dark Blue'))
        label.setPalette(palette) # assign new palette

        gui.separator(self.controlArea, 10)

        gui.button(self.controlArea, self, "Convert", callback=self.convert_wavefront, height=45)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.wavefront = input_data

            self.convert_wavefront()

    def convert_wavefront(self):
        try:
            if not self.wavefront is None:
                self.send("ShadowBeam", ShadowBeam(beam=SHADOW3Wavefront.fromGenericWavefront(self.wavefront)))
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            # raise exception
