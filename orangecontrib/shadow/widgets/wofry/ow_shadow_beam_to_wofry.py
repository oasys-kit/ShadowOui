from orangewidget import gui
from oasys.widgets import gui as oasysgui

from oasys.widgets import widget

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

        main_box = oasysgui.widgetBox(self.controlArea, "Shadow to Wofry Wavefront Converter", orientation="vertical", width=self.CONTROL_AREA_WIDTH-5, height=50)

        gui.label(main_box, self, "--------------- from Shadow Beam to Wofry GenericWavefront2D ---------------")

    def set_input(self, input_data):
        self.setStatusMessage("")

        if not input_data is None:
            try:
                self.send("GenericWavefront2D",  SHADOW3Wavefront.initialize_from_shadow3_beam(input_data._beam).toGenericWavefront())
            except Exception as exception:
                QMessageBox.critical(self, "Error", str(exception), QMessageBox.Ok)

                #raise exception
