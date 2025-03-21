import sys, numpy
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFont

from orangewidget import widget, gui
from oasys.widgets import gui as oasysgui
from orangewidget.settings import Setting
from oasys.widgets.widget import OWWidget

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class MergeBeams(OWWidget):

    name = "Merge Shadow Beam"
    description = "Display Data: Merge Shadow Beam"
    icon = "icons/merge.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 4
    category = "Data Display Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam # 1" , ShadowBeam, "setBeam1" ),
              ("Input Beam # 2" , ShadowBeam, "setBeam2" ),
              ("Input Beam # 3" , ShadowBeam, "setBeam3" ),
              ("Input Beam # 4" , ShadowBeam, "setBeam4" ),
              ("Input Beam # 5" , ShadowBeam, "setBeam5" ),
              ("Input Beam # 6" , ShadowBeam, "setBeam6" ),
              ("Input Beam # 7" , ShadowBeam, "setBeam7" ),
              ("Input Beam # 8" , ShadowBeam, "setBeam8" ),
              ("Input Beam # 9" , ShadowBeam, "setBeam9" ),
              ("Input Beam # 10", ShadowBeam, "setBeam10"),]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Shadow Beam",
                "id":"beam"}]

    want_main_area=0
    want_control_area = 1

    input_beam1=None
    input_beam2=None
    input_beam3=None
    input_beam4=None
    input_beam5=None
    input_beam6=None
    input_beam7=None
    input_beam8=None
    input_beam9=None
    input_beam10=None

    use_weights = Setting(0)

    weight_input_beam1=Setting(0.0)
    weight_input_beam2=Setting(0.0)
    weight_input_beam3=Setting(0.0)
    weight_input_beam4=Setting(0.0)
    weight_input_beam5=Setting(0.0)
    weight_input_beam6=Setting(0.0)
    weight_input_beam7=Setting(0.0)
    weight_input_beam8=Setting(0.0)
    weight_input_beam9=Setting(0.0)
    weight_input_beam10=Setting(0.0)

    def __init__(self, show_automatic_box=True):
        super().__init__()

        self.runaction = widget.OWAction("Merge Beams", self)
        self.runaction.triggered.connect(self.merge_beams)
        self.addAction(self.runaction)

        self.setFixedWidth(470)
        self.setFixedHeight(470)

        gen_box = gui.widgetBox(self.controlArea, "Merge Shadow Beams", addSpace=True, orientation="vertical")

        button_box = oasysgui.widgetBox(gen_box, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Merge Beams and Send", callback=self.merge_beams)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        weight_box = oasysgui.widgetBox(gen_box, "Relative Weights", addSpace=False, orientation="vertical")

        gui.comboBox(weight_box, self, "use_weights", label="Use Relative Weights?", labelWidth=350,
                     items=["No", "Yes"],
                     callback=self.set_UseWeights, sendSelectedValue=False, orientation="horizontal")

        gui.separator(weight_box, height=10)

        self.le_weight_input_beam1 = oasysgui.lineEdit(weight_box, self, "weight_input_beam1", "Input Beam 1 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam2 = oasysgui.lineEdit(weight_box, self, "weight_input_beam2", "Input Beam 2 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam3 = oasysgui.lineEdit(weight_box, self, "weight_input_beam3", "Input Beam 3 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam4 = oasysgui.lineEdit(weight_box, self, "weight_input_beam4", "Input Beam 4 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam5 = oasysgui.lineEdit(weight_box, self, "weight_input_beam5", "Input Beam 5 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam6 = oasysgui.lineEdit(weight_box, self, "weight_input_beam6", "Input Beam 6 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam7 = oasysgui.lineEdit(weight_box, self, "weight_input_beam7", "Input Beam 7 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam8 = oasysgui.lineEdit(weight_box, self, "weight_input_beam8", "Input Beam 8 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam9 = oasysgui.lineEdit(weight_box, self, "weight_input_beam9", "Input Beam 9 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")

        self.le_weight_input_beam10 = oasysgui.lineEdit(weight_box, self, "weight_input_beam10", "Input Beam 10 weight",
                                                    labelWidth=300, valueType=float, orientation="horizontal")


        self.le_weight_input_beam1.setEnabled(False)
        self.le_weight_input_beam2.setEnabled(False)
        self.le_weight_input_beam3.setEnabled(False)
        self.le_weight_input_beam4.setEnabled(False)
        self.le_weight_input_beam5.setEnabled(False)
        self.le_weight_input_beam6.setEnabled(False)
        self.le_weight_input_beam7.setEnabled(False)
        self.le_weight_input_beam8.setEnabled(False)
        self.le_weight_input_beam9.setEnabled(False)
        self.le_weight_input_beam10.setEnabled(False)
        
    def setBeam1(self, beam):
        self.le_weight_input_beam1.setEnabled(False)
        self.input_beam1 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam1 = beam
                if self.use_weights==1: self.le_weight_input_beam1.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #1 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam2(self, beam):
        self.le_weight_input_beam2.setEnabled(False)
        self.input_beam2 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam2 = beam
                if self.use_weights==1: self.le_weight_input_beam2.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #2 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam3(self, beam):
        self.le_weight_input_beam3.setEnabled(False)
        self.input_beam3 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam3 = beam
                if self.use_weights==1: self.le_weight_input_beam3.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #3 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam4(self, beam):
        self.le_weight_input_beam4.setEnabled(False)
        self.input_beam4 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam4 = beam
                if self.use_weights==1: self.le_weight_input_beam4.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #4 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam5(self, beam):
        self.le_weight_input_beam5.setEnabled(False)
        self.input_beam5 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam5 = beam
                if self.use_weights==1: self.le_weight_input_beam5.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #5 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam6(self, beam):
        self.le_weight_input_beam6.setEnabled(False)
        self.input_beam6 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam6 = beam
                if self.use_weights==1: self.le_weight_input_beam6.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #6 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam7(self, beam):
        self.le_weight_input_beam7.setEnabled(False)
        self.input_beam7 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam7 = beam
                if self.use_weights==1: self.le_weight_input_beam7.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #7 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam8(self, beam):
        self.le_weight_input_beam8.setEnabled(False)
        self.input_beam8 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam8 = beam
                if self.use_weights==1: self.le_weight_input_beam8.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #8 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam9(self, beam):
        self.le_weight_input_beam9.setEnabled(False)
        self.input_beam9 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam9 = beam
                if self.use_weights==1: self.le_weight_input_beam9.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #9 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def setBeam10(self, beam):
        self.le_weight_input_beam10.setEnabled(False)
        self.input_beam10 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam10 = beam
                if self.use_weights==1: self.le_weight_input_beam10.setEnabled(True)
            else:
                QtWidgets.QMessageBox.critical(self, "Error",
                                           "Data #10 not displayable: No good rays or bad content",
                                           QtWidgets.QMessageBox.Ok)

    def merge_beams(self):
        try:
            merged_beam = None

            for index in range(1, 11):
                current_beam = getattr(self, "input_beam" + str(index))
                if not current_beam is None:
                    current_beam = current_beam.duplicate()

                    if self.use_weights == 1:
                        weight = getattr(self, "weight_input_beam" + str(index))
                        if not (0.0 <= weight <= 1): raise ValueError(f"Weight #{index} is not in [0, 1]")

                        electric_field_factor = numpy.sqrt(weight)

                        current_beam._beam.rays[:, 6]  *= electric_field_factor
                        current_beam._beam.rays[:, 7]  *= electric_field_factor
                        current_beam._beam.rays[:, 8]  *= electric_field_factor
                        current_beam._beam.rays[:, 15] *= electric_field_factor
                        current_beam._beam.rays[:, 16] *= electric_field_factor
                        current_beam._beam.rays[:, 17] *= electric_field_factor

                    if    merged_beam is None: merged_beam = current_beam
                    else: merged_beam = ShadowBeam.mergeBeams(merged_beam, current_beam, which_flux=3, merge_history=0)

            self.send("Beam", merged_beam)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e), QtWidgets.QMessageBox.Ok)

            if self.IS_DEVELOP: raise e

    def set_UseWeights(self):
        self.le_weight_input_beam1.setEnabled( self.use_weights == 1 and not  self.input_beam1 is None)
        self.le_weight_input_beam2.setEnabled( self.use_weights == 1 and not  self.input_beam2 is None)
        self.le_weight_input_beam3.setEnabled( self.use_weights == 1 and not  self.input_beam3 is None)
        self.le_weight_input_beam4.setEnabled( self.use_weights == 1 and not  self.input_beam4 is None)
        self.le_weight_input_beam5.setEnabled( self.use_weights == 1 and not  self.input_beam5 is None)
        self.le_weight_input_beam6.setEnabled( self.use_weights == 1 and not  self.input_beam6 is None)
        self.le_weight_input_beam7.setEnabled( self.use_weights == 1 and not  self.input_beam7 is None)
        self.le_weight_input_beam8.setEnabled( self.use_weights == 1 and not  self.input_beam8 is None)
        self.le_weight_input_beam9.setEnabled( self.use_weights == 1 and not  self.input_beam9 is None)
        self.le_weight_input_beam10.setEnabled(self.use_weights == 1 and not  self.input_beam10 is None)


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = MergeBeams()
    ow.show()
    a.exec_()
    ow.saveSettings()
