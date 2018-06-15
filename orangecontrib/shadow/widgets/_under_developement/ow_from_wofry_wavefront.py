from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QRect

from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets.widget import AutomaticWidget
from orangewidget.settings import Setting

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D
from wofryshadow.propagator.wavefront2D.shadow3_wavefront import SHADOW3Wavefront

from orangecontrib.shadow.util.shadow_objects import ShadowBeam

class OWFromWofryWavefront2d(AutomaticWidget):
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

    MAX_WIDTH = 420
    MAX_HEIGHT = 170
    CONTROL_AREA_WIDTH = 410

    want_main_area = 0

    wavefront = None

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width()*0.05),
                               round(geom.height()*0.05),
                               round(min(geom.width()*0.98, self.MAX_WIDTH)),
                               round(min(geom.height()*0.95, self.MAX_HEIGHT))))

        self.setMinimumHeight(self.geometry().height())
        self.setMinimumWidth(self.geometry().width())
        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        self.controlArea.setFixedWidth(self.MAX_WIDTH-10)
        self.controlArea.setFixedHeight(self.MAX_HEIGHT-10)

        main_box = oasysgui.widgetBox(self.controlArea, "From Shadow Beam To Wofry Wavefront", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=80)

        gui.button(main_box, self, "Compute", callback=self.convert_wavefront, height=45)

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            self.wavefront = input_data

            if not self.is_automatic_execution:
                self.convert_wavefront()

    def convert_wavefront(self):
        try:
            if not self.wavefront is None:
                self.send("ShadowBeam", ShadowBeam(beam=SHADOW3Wavefront.fromGenericWavefront(wavefront=self.wavefront,
                                                                                              shadow_to_meters=self.workspace_units_to_m)))
        except Exception as exception:
            QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

            # if self.IS_DEVELOP: raise exception
