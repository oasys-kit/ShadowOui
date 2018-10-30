import copy

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence
from oasys.widgets.gui import ConfirmDialog

from orangecontrib.shadow.util.shadow_objects import ShadowPreProcessorData, ShadowBeam
from orangecontrib.shadow.widgets.gui import ow_compound_optical_element

class KB(ow_compound_optical_element.CompoundOpticalElement):
    name = "Kirkpatrick-Baez Mirror"
    description = "Shadow Compound OE: Kirkpatrick-Baez Mirror"
    icon = "icons/kb.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "lrebuffi(@at@)anl.gov"
    priority = 4
    category = "Compound Optical Elements"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam"),
              ("Vertical Focusing PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorDataV"),
              ("Vertical Focusing PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorDataV"),
              ("Horizontal Focusing PreProcessor Data #1", ShadowPreProcessorData, "setPreProcessorDataH"),
              ("Horizontal Focusing PreProcessor Data #2", ShadowPreProcessorData, "setPreProcessorDataH")]


    NONE_SPECIFIED = "NONE SPECIFIED"

    p = Setting(0.0)
    q = Setting(0.0)
    separation = Setting(100.0)
    mirror_orientation_angle = Setting(0)
    use_different_focal_positions = Setting(0)
    focal_positions_p = Setting(0.0)
    focal_positions_q = Setting(0.0)

    grazing_angles_mrad = Setting([3.0, 3.0])
    shape = Setting([1, 1])
    has_finite_dimensions = Setting([0, 0])
    dimensions = Setting([[0.0, 0.0], [0.0, 0.0]])
    reflectivity_kind = Setting([0, 0])
    reflectivity_files = Setting([NONE_SPECIFIED, NONE_SPECIFIED])
    has_surface_error = Setting([0, 0])
    surface_error_files = Setting([NONE_SPECIFIED, NONE_SPECIFIED])


    def __init__(self):
        super().__init__()

        self.le_p = oasysgui.lineEdit(self.tab_bas, self, "p", "Distance Source - KB center (P)", labelWidth=280, valueType=float, orientation="horizontal")
        self.le_q = oasysgui.lineEdit(self.tab_bas, self, "q", "Distance KB center - Image plane (Q)", labelWidth=280, valueType=float, orientation="horizontal")

        self.le_separation = oasysgui.lineEdit(self.tab_bas, self, "separation", "Separation between the Mirrors\n(from center of V.F.M. to center of H.F.M.) ", labelWidth=280, valueType=float,
                           orientation="horizontal")
        oasysgui.lineEdit(self.tab_bas, self, "mirror_orientation_angle", "Mirror orientation angle [deg]\n(with respect to the previous o.e. for the first mirror)", labelWidth=280,
                           valueType=float, orientation="horizontal")

        gui.comboBox(self.tab_bas, self, "use_different_focal_positions", label="Different Focal Positions", labelWidth=280,
                     items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal", callback=self.set_use_different_focal_positions)

        self.focal_positions_box = oasysgui.widgetBox(self.tab_bas, "", addSpace=False, orientation="vertical", height=50)
        self.focal_positions_empty = oasysgui.widgetBox(self.tab_bas, "", addSpace=False, orientation="vertical", height=50)

        self.le_focal_positions_p = oasysgui.lineEdit(self.focal_positions_box, self, "focal_positions_p", "Focal Position P", labelWidth=280, valueType=float, orientation="horizontal")
        self.le_focal_positions_q = oasysgui.lineEdit(self.focal_positions_box, self, "focal_positions_q", "Focal Position Q", labelWidth=280, valueType=float, orientation="horizontal")

        self.set_use_different_focal_positions()

        self.tab_mirrors = oasysgui.tabWidget(self.tab_bas)

        tab_vertical = oasysgui.createTabPage(self.tab_mirrors, "Vertical Focusing Mirror")
        tab_horizontal = oasysgui.createTabPage(self.tab_mirrors, "Horizontal Focusing Mirror")

        self.v_box = MirrorBox(kb=self,
                               parent=tab_vertical,
                               grazing_angles_mrad=self.grazing_angles_mrad[0],
                               shape=self.shape[0],
                               has_finite_dimensions=self.has_finite_dimensions[0],
                               dimensions=self.dimensions[0],
                               reflectivity_kind=self.reflectivity_kind[0],
                               reflectivity_files=self.reflectivity_files[0],
                               has_surface_error=self.has_surface_error[0],
                               surface_error_files= self.surface_error_files[0])

        self.h_box = MirrorBox(kb=self,
                               parent=tab_horizontal,
                               grazing_angles_mrad=self.grazing_angles_mrad[1],
                               shape=self.shape[1],
                               has_finite_dimensions=self.has_finite_dimensions[1],
                               dimensions=self.dimensions[1],
                               reflectivity_kind=self.reflectivity_kind[1],
                               reflectivity_files=self.reflectivity_files[1],
                               has_surface_error=self.has_surface_error[1],
                               surface_error_files= self.surface_error_files[1])

    def after_change_workspace_units(self):
        label = self.le_p.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_q.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_separation.parent().layout().itemAt(0).widget()
        label.setText("Separation between the Mirrors [" + self.workspace_units_label + "]\n(from center of V.F.M. to center of H.F.M.)")
        label = self.le_focal_positions_p.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")
        label = self.le_focal_positions_q.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.workspace_units_label + "]")

        self.v_box.after_change_workspace_units()
        self.h_box.after_change_workspace_units()

    def callResetSettings(self):
        if ConfirmDialog.confirmed(parent=self, message="Confirm Reset of the Fields?"):
            self.resetSettings()

            while self.tab_mirrors.count() > 0:
                self.tab_mirrors.removeTab(0)

            tab_vertical = oasysgui.widgetBox(self.tab_mirrors, addToLayout=0, margin=4)
            tab_horizontal = oasysgui.widgetBox(self.tab_mirrors, addToLayout=0, margin=4)

            self.v_box = MirrorBox(kb=self,
                                   parent=tab_vertical,
                                   grazing_angles_mrad=self.grazing_angles_mrad[0],
                                   shape=self.shape[0],
                                   has_finite_dimensions=self.has_finite_dimensions[0],
                                   dimensions=self.dimensions[0],
                                   reflectivity_kind=self.reflectivity_kind[0],
                                   reflectivity_files=self.reflectivity_files[0],
                                   has_surface_error=self.has_surface_error[0],
                                   surface_error_files=self.surface_error_files[0])

            self.h_box = MirrorBox(kb=self,
                                   parent=tab_horizontal,
                                   grazing_angles_mrad=self.grazing_angles_mrad[1],
                                   shape=self.shape[1],
                                   has_finite_dimensions=self.has_finite_dimensions[1],
                                   dimensions=self.dimensions[1],
                                   reflectivity_kind=self.reflectivity_kind[1],
                                   reflectivity_files=self.reflectivity_files[1],
                                   has_surface_error=self.has_surface_error[1],
                                   surface_error_files=self.surface_error_files[1])

            self.tab_mirrors.addTab(tab_vertical, "Vertical Focusing Mirror")
            self.tab_mirrors.addTab(tab_horizontal, "Horizontal Focusing Mirror")

            self.setupUI()

    def set_use_different_focal_positions(self):
        self.focal_positions_box.setVisible(self.use_different_focal_positions == 1)
        self.focal_positions_empty.setVisible(self.use_different_focal_positions == 0)

    def get_focal_positions(self):
        if self.use_different_focal_positions == 0:
            return [0.0, 0.0]
        else:
            return [self.focal_positions_p, self.focal_positions_q]

    def dumpSettings(self):
        bkp_grazing_angles_mrad = copy.deepcopy(self.grazing_angles_mrad)
        bkp_shape = copy.deepcopy(self.shape)
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)
        bkp_dimensions = copy.deepcopy(self.dimensions)
        bkp_reflectivity_kind = copy.deepcopy(self.reflectivity_kind)
        bkp_reflectivity_files = copy.deepcopy(self.reflectivity_files)
        bkp_has_surface_error = copy.deepcopy(self.has_surface_error)
        bkp_surface_error_files = copy.deepcopy(self.surface_error_files)

        try:
            self.grazing_angles_mrad = []
            self.shape = []
            self.has_finite_dimensions = []
            self.dimensions = []
            self.reflectivity_kind = []
            self.reflectivity_files = []
            self.has_surface_error = []
            self.surface_error_files = []

            self.grazing_angles_mrad.append(self.v_box.grazing_angles_mrad)
            self.shape.append(self.v_box.shape)
            self.has_finite_dimensions.append(self.v_box.has_finite_dimensions)
            self.dimensions.append([self.v_box.mirror_width, self.v_box.mirror_length])
            self.reflectivity_kind.append(self.v_box.reflectivity_kind)
            self.reflectivity_files.append(self.v_box.reflectivity_files)
            self.has_surface_error.append(self.v_box.has_surface_error)
            self.surface_error_files.append(self.v_box.surface_error_files)

            self.grazing_angles_mrad.append(self.h_box.grazing_angles_mrad)
            self.shape.append(self.h_box.shape)
            self.has_finite_dimensions.append(self.h_box.has_finite_dimensions)
            self.dimensions.append([self.h_box.mirror_width, self.h_box.mirror_length])
            self.reflectivity_kind.append(self.h_box.reflectivity_kind)
            self.reflectivity_files.append(self.h_box.reflectivity_files)
            self.has_surface_error.append(self.h_box.has_surface_error)
            self.surface_error_files.append(self.h_box.surface_error_files)

        except:
            self.grazing_angles_mrad = copy.deepcopy(bkp_grazing_angles_mrad)
            self.shape = copy.deepcopy(bkp_shape)
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)
            self.dimensions = copy.deepcopy(bkp_dimensions)
            self.reflectivity_kind = copy.deepcopy(bkp_reflectivity_kind)
            self.reflectivity_files = copy.deepcopy(bkp_reflectivity_files)
            self.has_surface_error = copy.deepcopy(bkp_has_surface_error)
            self.surface_error_files = copy.deepcopy(bkp_surface_error_files)

    ##############################
    # SINGLE FIELDS SIGNALS
    ##############################

    def dump_grazing_angles_mrad(self):
        bkp_grazing_angles_mrad = copy.deepcopy(self.grazing_angles_mrad)

        try:
            self.grazing_angles_mrad = []

            self.grazing_angles_mrad.append(self.v_box.grazing_angles_mrad)
            self.grazing_angles_mrad.append(self.h_box.grazing_angles_mrad)
        except:
            self.grazing_angles_mrad = copy.deepcopy(bkp_grazing_angles_mrad)

    def dump_shape(self):
        bkp_shape = copy.deepcopy(self.shape)

        try:
            self.shape = []

            self.shape.append(self.v_box.shape)
            self.shape.append(self.h_box.shape)
        except:
            self.shape = copy.deepcopy(bkp_shape)

    def dump_has_finite_dimensions(self):
        bkp_has_finite_dimensions = copy.deepcopy(self.has_finite_dimensions)

        try:
            self.has_finite_dimensions = []

            self.has_finite_dimensions.append(self.v_box.has_finite_dimensions)
            self.has_finite_dimensions.append(self.h_box.has_finite_dimensions)
        except:
            self.has_finite_dimensions = copy.deepcopy(bkp_has_finite_dimensions)

    def dump_dimensions_0(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[0] = [self.v_box.mirror_width, self.v_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    def dump_dimensions_1(self):
        bkp_dimensions = copy.deepcopy(self.dimensions)

        try:
            self.dimensions[1] = [self.h_box.mirror_width, self.h_box.mirror_length]
        except:
            self.dimensions = copy.deepcopy(bkp_dimensions)

    def dump_reflectivity_kind(self):
        bkp_reflectivity_kind = copy.deepcopy(self.reflectivity_kind)

        try:
            self.reflectivity_kind = []

            self.reflectivity_kind.append(self.v_box.reflectivity_kind)
            self.reflectivity_kind.append(self.h_box.reflectivity_kind)
        except:
            self.reflectivity_kind = copy.deepcopy(bkp_reflectivity_kind)

    def dump_reflectivity_files(self):
        bkp_reflectivity_files = copy.deepcopy(self.reflectivity_files)

        try:
            self.reflectivity_files = []

            self.reflectivity_files.append(self.v_box.reflectivity_files)
            self.reflectivity_files.append(self.h_box.reflectivity_files)
        except:
            self.reflectivity_files = copy.deepcopy(bkp_reflectivity_files)

    def dump_has_surface_error(self):
        bkp_has_surface_error = copy.deepcopy(self.has_surface_error)

        try:
            self.has_surface_error = []

            self.has_surface_error.append(self.v_box.has_surface_error)
            self.has_surface_error.append(self.h_box.has_surface_error)
        except:
            self.has_surface_error = copy.deepcopy(bkp_has_surface_error)

    def dump_surface_error_files(self):
        bkp_surface_error_files = copy.deepcopy(self.surface_error_files)

        try:
            self.surface_error_files = []

            self.surface_error_files.append(self.v_box.surface_error_files)
            self.surface_error_files.append(self.h_box.surface_error_files)
        except:
            self.surface_error_files = copy.deepcopy(bkp_surface_error_files)

    ############################################################
    #
    # USER INPUT MANAGEMENT
    #
    ############################################################

    def populateFields(self, shadow_oe):
        self.dumpSettings()

        shape_out = []
        shape_out.append(self.v_box.get_shape())
        shape_out.append(self.h_box.get_shape())

        dimension1_out = self.v_box.get_dimensions()
        dimension2_out = self.h_box.get_dimensions()

        reflectivity_files_out = []
        reflectivity_files_out.append(self.v_box.get_reflectivity_files())
        reflectivity_files_out.append(self.h_box.get_reflectivity_files())

        surface_error_files_out = []
        surface_error_files_out.append(self.v_box.get_surface_error_files())
        surface_error_files_out.append(self.h_box.get_surface_error_files())

        shadow_oe._oe.append_kb(p0=self.p,
                               q0=self.q,
                               grazing_angles_mrad=self.grazing_angles_mrad,
                               separation=self.separation,
                               mirror_orientation_angle=self.mirror_orientation_angle,
                               focal_positions=self.get_focal_positions(),
                               shape=shape_out,
                               dimensions1=dimension1_out,
                               dimensions2=dimension2_out,
                               reflectivity_kind=self.reflectivity_kind,
                               reflectivity_files=reflectivity_files_out,
                               surface_error_files=surface_error_files_out)

    def checkFields(self):
        congruence.checkPositiveNumber(self.p, "Distance Source - KB center")
        congruence.checkPositiveNumber(self.q, "Distance KB center - Image plane")

        congruence.checkPositiveNumber(self.separation, "Separation between the Mirrors")
        congruence.checkPositiveAngle(self.mirror_orientation_angle, "Mirror orientation angle")

        if self.use_different_focal_positions == 1:
            congruence.checkPositiveNumber(self.focal_positions_p, "Focal Position P")
            congruence.checkPositiveNumber(self.focal_positions_q, "Focal Position Q")

        self.v_box.checkFields()
        self.h_box.checkFields()

    def setPreProcessorDataV(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.v_box.reflectivity_files = data.prerefl_data_file
                self.v_box.le_reflectivity_files.setText(data.prerefl_data_file)
                self.v_box.reflectivity_kind = 1
                self.v_box.reflectivity_kind_combo.setCurrentIndex(1)

                self.v_box.set_reflectivity_kind()

                self.dump_reflectivity_files()

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                self.v_box.reflectivity_files = data.m_layer_data_file_dat
                self.v_box.le_reflectivity_files.setText(data.m_layer_data_file_dat)
                self.v_box.reflectivity_kind = 2
                self.v_box.reflectivity_kind_combo.setCurrentIndex(2)

                self.v_box.set_reflectivity_kind()

                self.dump_reflectivity_files()

            if data.error_profile_data_file != ShadowPreProcessorData.NONE:
                self.v_box.surface_error_files = data.error_profile_data_file
                self.v_box.le_surface_error_files.setText(data.error_profile_data_file)
                self.v_box.has_surface_error = 1
                self.v_box.has_surface_error_combo.setCurrentIndex(1)

                if self.v_box.has_finite_dimensions == 0: # Finite
                    changed = False

                    if self.v_box.mirror_width > data.error_profile_x_dim or \
                       self.v_box.mirror_length > data.error_profile_y_dim:
                        changed = True

                    if changed:
                        if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                      "Dimensions of this mirror must be changed in order to ensure congruence with the error profile surface, accept?",
                                                      QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                            if self.v_box.mirror_width > data.error_profile_x_dim:
                                self.v_box.mirror_width = data.error_profile_x_dim
                                self.v_box.le_mirror_width.setText(str(data.error_profile_x_dim))
                            if self.v_box.mirror_length > data.error_profile_y_dim:
                                self.v_box.mirror_length = data.error_profile_y_dim
                                self.v_box.le_mirror_length.setText(str(data.error_profile_y_dim))

                            QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                                          "Dimensions of this mirror were changed",
                                                          QtWidgets.QMessageBox.Ok)
                else:
                    if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                  "This mirror must become with finite dimensions in order to ensure congruence with the error surface, accept?",
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                        self.v_box.has_finite_dimensions = 0
                        self.v_box.has_finite_dimensions_combo.setCurrentIndex(0)
                        self.v_box.mirror_width = data.error_profile_x_dim
                        self.v_box.le_mirror_width.setText(str(data.error_profile_x_dim))
                        self.v_box.mirror_length = data.error_profile_y_dim
                        self.v_box.le_mirror_length.setText(str(data.error_profile_y_dim))

                        QtWidgets.QMessageBox.warning(self, "Warning",
                                                      "Dimensions of this mirror were changed",
                                                      QtWidgets.QMessageBox.Ok)


                self.v_box.set_dimensions()
                self.v_box.set_has_surface_error()
                self.dump_dimensions_0()
                self.dump_dimensions_1()
                self.dump_surface_error_files()
                
            if data.bragg_data_file != ShadowPreProcessorData.NONE:
                QtWidgets.QMessageBox.warning(self, "Warning",
                          "This O.E. is not a crystal: bragg parameter will be ignored",
                          QtWidgets.QMessageBox.Ok)

    def setPreProcessorDataH(self, data):
        if data is not None:
            if data.prerefl_data_file != ShadowPreProcessorData.NONE:
                self.h_box.reflectivity_files = data.prerefl_data_file
                self.h_box.le_reflectivity_files.setText(data.prerefl_data_file)
                self.h_box.reflectivity_kind = 1
                self.h_box.reflectivity_kind_combo.setCurrentIndex(1)

                self.h_box.set_reflectivity_kind()

                self.dump_reflectivity_files()

            if data.m_layer_data_file_dat != ShadowPreProcessorData.NONE:
                self.h_box.reflectivity_files = data.m_layer_data_file_dat
                self.h_box.le_reflectivity_files.setText(data.m_layer_data_file_dat)
                self.h_box.reflectivity_kind = 2
                self.h_box.reflectivity_kind_combo.setCurrentIndex(2)

                self.h_box.set_reflectivity_kind()

            if data.error_profile_data_file != ShadowPreProcessorData.NONE:
                self.h_box.surface_error_files = data.error_profile_data_file
                self.h_box.le_surface_error_files.setText(data.error_profile_data_file)
                self.h_box.has_surface_error = 1
                self.h_box.has_surface_error_combo.setCurrentIndex(1)

                if self.h_box.has_finite_dimensions == 0: # Finite
                    changed = False

                    if self.h_box.mirror_width > data.error_profile_x_dim or \
                       self.h_box.mirror_length > data.error_profile_y_dim:
                        changed = True

                    if changed:
                        if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                      "Dimensions of this mirror must be changed in order to ensure congruence with the error profile surface, accept?",
                                                      QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                            if self.h_box.mirror_width > data.error_profile_x_dim:
                                self.h_box.mirror_width = data.error_profile_x_dim
                                self.h_box.le_mirror_width.setText(str(data.error_profile_x_dim))
                            if self.h_box.mirror_length > data.error_profile_y_dim:
                                self.h_box.mirror_length = data.error_profile_y_dim
                                self.h_box.le_mirror_length.setText(str(data.error_profile_y_dim))

                            QtWidgets.QMessageBox.information(self, "QMessageBox.information()",
                                                          "Dimensions of this mirror were changed",
                                                          QtWidgets.QMessageBox.Ok)
                else:
                    if QtWidgets.QMessageBox.information(self, "Confirm Modification",
                                                  "This mirror must become with finite dimensions in order to ensure congruence with the error surface, accept?",
                                                  QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                        self.h_box.has_finite_dimensions = 0
                        self.h_box.has_finite_dimensions_combo.setCurrentIndex(0)
                        self.h_box.mirror_width = data.error_profile_x_dim
                        self.h_box.le_mirror_width.setText(str(data.error_profile_x_dim))
                        self.h_box.mirror_length = data.error_profile_y_dim
                        self.h_box.le_mirror_length.setText(str(data.error_profile_y_dim))

                        QtWidgets.QMessageBox.warning(self, "Warning",
                                                      "Dimensions of this mirror were changed",
                                                      QtWidgets.QMessageBox.Ok)


                self.h_box.set_dimensions()
                self.h_box.set_has_surface_error()
                self.dump_dimensions_0()
                self.dump_dimensions_1()
                self.dump_surface_error_files()

    def setupUI(self):
        self.set_use_different_focal_positions()

        self.v_box.setupUI()
        self.h_box.setupUI()


class MirrorBox(QtWidgets.QWidget):
    grazing_angles_mrad = 3.0
    shape = 1
    has_finite_dimensions = 0
    mirror_width = 0.0
    mirror_length = 0.0
    reflectivity_kind = 0
    reflectivity_files = KB.NONE_SPECIFIED
    has_surface_error = 0
    surface_error_files = KB.NONE_SPECIFIED

    kb = None

    is_on_init = True

    def __init__(self,
                 kb=None,
                 parent=None,
                 grazing_angles_mrad=3.0,
                 shape=1,
                 has_finite_dimensions=0,
                 dimensions=[0.0, 0.0],
                 reflectivity_kind=0,
                 reflectivity_files=KB.NONE_SPECIFIED,
                 has_surface_error=0,
                 surface_error_files=KB.NONE_SPECIFIED):
        super().__init__(parent)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setAlignment(Qt.AlignTop)

        self.kb = kb

        self.setFixedWidth(self.kb.CONTROL_AREA_WIDTH-20)
        self.setFixedHeight(300)

        self.grazing_angles_mrad = grazing_angles_mrad
        self.shape = shape
        self.has_finite_dimensions = has_finite_dimensions
        self.mirror_width = dimensions[0]
        self.mirror_length = dimensions[1]
        self.reflectivity_kind = reflectivity_kind
        self.reflectivity_files = reflectivity_files
        self.has_surface_error = has_surface_error
        self.surface_error_files = surface_error_files

        mirror_box = oasysgui.widgetBox(self, "Mirror Input Parameters", addSpace=False, orientation="vertical", height=260)

        oasysgui.lineEdit(mirror_box, self, "grazing_angles_mrad", "Grazing Angle [mrad]", labelWidth=260, valueType=float, orientation="horizontal",
                           callback=self.kb.dump_grazing_angles_mrad)

        gui.comboBox(mirror_box, self, "shape", label="Surface Shape", labelWidth=260,
                     items=["Sphere", "Ellipse"], sendSelectedValue=False, orientation="horizontal", callback=self.kb.dump_shape)

        self.has_finite_dimensions_combo = gui.comboBox(mirror_box, self, "has_finite_dimensions", label="Dimensions", labelWidth=260,
                     items=["Finite", "Infinite"], sendSelectedValue=False, orientation="horizontal", callback=self.set_dimensions)

        self.dimension_box = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="horizontal", height=25)
        self.dimension_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=25)

        self.le_mirror_width = oasysgui.lineEdit(self.dimension_box, self, "mirror_width", "Width", labelWidth=100, valueType=float, orientation="horizontal",
                           callback=self.kb.dump_dimensions_0)

        self.le_mirror_length = oasysgui.lineEdit(self.dimension_box, self, "mirror_length", "Length", labelWidth=100, valueType=float, orientation="horizontal",
                           callback=self.kb.dump_dimensions_1)

        self.set_dimensions()

        self.reflectivity_kind_combo = gui.comboBox(mirror_box, self, "reflectivity_kind",
                                                    label="Reflectivity Kind", labelWidth=260,
                                                    items=["Ideal Reflector", "Mirror", "Multilayer"],
                                                    sendSelectedValue=False, orientation="horizontal",
                                                    callback=self.set_reflectivity_kind)

        self.reflectivity_box = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=25)
        self.reflectivity_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=25)

        file_box = oasysgui.widgetBox(self.reflectivity_box, "", addSpace=False, orientation="horizontal")

        self.le_reflectivity_files = oasysgui.lineEdit(file_box, self, "reflectivity_files", "Reflectivity File",
                                                       labelWidth=110, valueType=str, orientation="horizontal",
                                                       callback=self.kb.dump_reflectivity_files)

        gui.button(file_box, self, "...", callback=self.selectFilePrerefl)

        self.set_reflectivity_kind()

        self.has_surface_error_combo = gui.comboBox(mirror_box, self, "has_surface_error",
                                                    label="Surface Error", labelWidth=260,
                                                    items=["No", "Yes"], sendSelectedValue=False, orientation="horizontal",
                                                    callback=self.set_has_surface_error)

        self.surface_error_box = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=25)
        self.surface_error_box_empty = oasysgui.widgetBox(mirror_box, "", addSpace=False, orientation="vertical", height=25)


        file_box = oasysgui.widgetBox(self.surface_error_box, "", addSpace=False, orientation="horizontal")

        self.le_surface_error_files = oasysgui.lineEdit(file_box, self, "surface_error_files", "Surface Error File",
                                                        labelWidth=110, valueType=str,orientation="horizontal",
                                                        callback=self.kb.dump_surface_error_files)

        gui.button(file_box, self, "...", callback=self.selectFileSurfaceError)

        self.set_has_surface_error()

        self.is_on_init = False

    ############################################################
    #
    # GRAPHIC USER INTERFACE MANAGEMENT
    #
    ############################################################

    def after_change_workspace_units(self):
        label = self.le_mirror_width.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.kb.workspace_units_label + "]")
        label = self.le_mirror_length.parent().layout().itemAt(0).widget()
        label.setText(label.text() + " [" + self.kb.workspace_units_label + "]")

    def selectFilePrerefl(self):
        self.le_reflectivity_files.setText(oasysgui.selectFileFromDialog(self, self.reflectivity_files, "Select Reflectivity File", file_extension_filter="Data Files (*.dat)"))

        self.reflectivity_files = self.le_reflectivity_files.text()
        self.kb.dump_reflectivity_files()

    def selectFileSurfaceError(self):
        self.le_surface_error_files.setText(oasysgui.selectFileFromDialog(self, self.surface_error_files, "Surface Error File", file_extension_filter="Data Files (*.dat *.sha)"))

        self.surface_error_files = self.le_surface_error_files.text()
        self.kb.dump_surface_error_files()

    def get_shape(self):
        if self.shape == 0:
            return 1
        elif self.shape == 1:
            return 2
        else:
            raise ValueError("Surface Shape")

    def get_dimensions(self):
        if self.has_finite_dimensions == 0:
            return [self.mirror_width, self.mirror_length]
        elif self.has_finite_dimensions == 1:
            return [0.0, 0.0]
        else:
            raise ValueError("Dimensions")

    def get_reflectivity_files(self):
        if self.reflectivity_kind != 0:
            return bytes(congruence.checkFileName(self.reflectivity_files), 'utf-8')
        else:
            return ""

    def get_surface_error_files(self):
        if self.has_surface_error == 1:
            return bytes(congruence.checkFileName(self.surface_error_files), 'utf-8')
        else:
            return ""

    def set_dimensions(self):
        self.dimension_box.setVisible(self.has_finite_dimensions == 0)
        self.dimension_box_empty.setVisible(self.has_finite_dimensions != 0)

        if not self.is_on_init: self.kb.dump_has_finite_dimensions()

    def set_reflectivity_kind(self):
        self.reflectivity_box.setVisible(self.reflectivity_kind != 0)
        self.reflectivity_box_empty.setVisible(self.reflectivity_kind == 0)

        if not self.is_on_init: self.kb.dump_reflectivity_kind()

    def set_has_surface_error(self):
        self.surface_error_box.setVisible(self.has_surface_error != 0)
        self.surface_error_box_empty.setVisible(self.has_surface_error == 0)

        if not self.is_on_init: self.kb.dump_has_surface_error()

    def checkFields(self):
        congruence.checkPositiveNumber(self.grazing_angles_mrad, "Grazing Angle")

        if self.has_finite_dimensions == 0:
            congruence.checkStrictlyPositiveNumber(self.mirror_width, "Mirror Width")
            congruence.checkStrictlyPositiveNumber(self.mirror_length, "Mirror Length")
        elif self.has_surface_error != 0:
            raise Exception("With surface error file, dimensions cannot be infinite")

        if self.reflectivity_kind != 0:
            congruence.checkFile(self.reflectivity_files)

        if self.has_surface_error == 1:
            congruence.checkFile(self.surface_error_files)

    def setupUI(self):
        self.set_dimensions()
        self.set_reflectivity_kind()
        self.set_has_surface_error()
