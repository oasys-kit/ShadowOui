import numpy

from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QApplication, QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting

from oasys.widgets.widget import OWWidget
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from silx.gui import qt
import silx.gui.hdf5
from silx.gui.data.DataViewerFrame import DataViewerFrame
from silx.gui.data.DataViewer import DataViewer, DataViews
from silx.gui.hdf5._utils import H5Node
from silx.gui.plot.PlotWindow import Plot2D, Plot1D

from h5py import Dataset

class Hdf5TreeViewWidget(qt.QWidget):
    x_scale = None
    y_scale = None

    def __init__(self, file_name=None):
        qt.QWidget.__init__(self)

        self.__treeview = silx.gui.hdf5.Hdf5TreeView(self)
        self.__text = qt.QTextEdit(self)
        self.__dataViewer = DataViewerFrame(self)

        box = oasysgui.widgetBox(self, "", orientation="vertical")

        box.layout().addWidget(self.__dataViewer)
        self.box_scale = oasysgui.widgetBox(box, "", orientation="horizontal")

        gui.button(self.box_scale, self, "Apply Coordinates", callback=self.rescale)

        vSplitter = qt.QSplitter(qt.Qt.Vertical)
        vSplitter.addWidget(box)
        vSplitter.addWidget(self.__text)
        vSplitter.setSizes([10, 0])

        splitter = qt.QSplitter(self)
        splitter.addWidget(self.__treeview)
        splitter.addWidget(vSplitter)
        splitter.setStretchFactor(1, 1)

        layout = qt.QVBoxLayout()
        layout.addWidget(splitter)
        layout.setStretchFactor(splitter, 1)
        self.setLayout(layout)

        # append all files to the tree
        if not file_name is None:
            self.__treeview.findHdf5TreeModel().removeRow(0)
            self.__treeview.findHdf5TreeModel().appendFile(file_name)

        self.__treeview.activated.connect(self.displayData)

    def displayData(self):
        """Called to update the dataviewer with the selected data.
        """
        selected = list(self.__treeview.selectedH5Nodes())
        if len(selected) == 1:
            data = selected[0]
            self.__dataViewer.setData(data)

            self.is_histogram_v = "histogram_v" in data.h5py_object.name
            self.object_name = data.basename

            file = data.h5py_object.file

            try:
                self.x_scale = file["coordinates/X"].value
                self.x_label = file["coordinates"].attrs["x_label"]
                try:
                    self.y_scale = file["coordinates/Y"].value
                    self.y_label = file["coordinates"].attrs["y_label"]
                except:
                    self.y_scale = None
                    self.y_label = None

                self.box_scale.setVisible(True)
            except:
                self.box_scale.setVisible(False)

    def rescale(self):
        current_view = self.__dataViewer.displayedView()
        if isinstance(current_view, DataViews._Plot1dView):
            if self.is_histogram_v:
                min_x = numpy.min(self.y_scale)
                max_x = numpy.max(self.y_scale)
                scale = self.y_scale
                label = self.y_label
            else:
                min_x = numpy.min(self.x_scale)
                max_x = numpy.max(self.x_scale)
                scale = self.x_scale
                label = self.x_label

            widget = current_view.getWidget()

            if isinstance(widget, Plot1D):
                curve = widget.getAllCurves()[0]
                curve.setData(scale, curve.getYData())
                widget.setGraphXLimits(min_x, max_x)
                widget.setGraphXLabel(label)
                widget.setGraphYLabel(self.object_name)

        elif isinstance(current_view, DataViews._ImageView):
            min_x = numpy.min(self.x_scale)
            max_x = numpy.max(self.x_scale)
            nbins_x = len(self.x_scale)
            min_y = numpy.min(self.y_scale)
            max_y = numpy.max(self.y_scale)
            nbins_y = len(self.y_scale)

            origin = (min_x, min_y)
            scale = (abs((max_x-min_x)/nbins_x), abs((max_y-min_y)/nbins_y))

            for view in current_view.availableViews():
                widget = view.getWidget()

                if isinstance(widget, Plot2D):
                    widget.getActiveImage().setOrigin(origin)
                    widget.getActiveImage().setScale(scale)
                    widget.setGraphXLimits(min_x, max_x)
                    widget.setGraphYLimits(min_y, max_y)
                    widget.setGraphXLabel(self.x_label)
                    widget.setGraphYLabel(self.y_label)
                    widget.setKeepDataAspectRatio(False)
                    widget.resetZoom()

    def load_file(self, filename):
        self.__treeview.findHdf5TreeModel().insertFile(filename)

    def set_text(self, text):
        self.__text.setText(text)

    def __hdf5ComboChanged(self, index):
        function = self.__hdf5Combo.itemData(index)
        self.__createHdf5Button.setCallable(function)

    def __edfComboChanged(self, index):
        function = self.__edfCombo.itemData(index)
        self.__createEdfButton.setCallable(function)


class OWPlotFileReader(OWWidget):
    name = "Plot File Reader"
    id = "plot_file_reader"
    description = "Plot File Reader"
    icon = "icons/hdf5.png"
    author = "Luca Rebuffi"
    maintainer_email = "lrebuffi@anl.gov"
    priority = 3
    category = ""
    keywords = ["hdf5_file_reader"]

    want_main_area = 1
    want_control_area = 1

    MAX_WIDTH = 1320
    MAX_HEIGHT = 700

    IMAGE_WIDTH = 860
    IMAGE_HEIGHT = 645

    CONTROL_AREA_WIDTH = 405
    TABS_AREA_HEIGHT = 618

    hdf5_file_name = Setting('file.hdf5')

    def __init__(self):
        super().__init__()

        geom = QApplication.desktop().availableGeometry()
        self.setGeometry(QRect(round(geom.width() * 0.05),
                               round(geom.height() * 0.05),
                               round(min(geom.width() * 0.98, self.MAX_WIDTH)),
                               round(min(geom.height() * 0.95, self.MAX_HEIGHT))))

        self.setMaximumHeight(self.geometry().height())
        self.setMaximumWidth(self.geometry().width())

        gui.separator(self.controlArea)

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Load HDF5 file", callback=self.load_file)
        button.setFixedHeight(45)

        input_box_l = oasysgui.widgetBox(self.controlArea, "Input", addSpace=True, orientation="horizontal", height=self.TABS_AREA_HEIGHT)

        self.le_hdf5_file_name = oasysgui.lineEdit(input_box_l, self, "hdf5_file_name", "HDF5 File Name",
                                                        labelWidth=120, valueType=str, orientation="horizontal")

        gui.button(input_box_l, self, "...", callback=self.selectPlotXYFile)

        self.tree_view = Hdf5TreeViewWidget()

        self.mainArea.layout().addWidget(self.tree_view)

        gui.rubber(self.mainArea)


    def load_file(self):
        try:
            hdf5_file_name = congruence.checkDir(self.hdf5_file_name)

            self.tree_view.load_file(hdf5_file_name)
            self.tree_view.set_text("Loaded File: " + hdf5_file_name)

        except Exception as exception:
            QMessageBox.critical(self, "Error", exception.args[0], QMessageBox.Ok)

            if self.IS_DEVELOP: raise exception

    def selectPlotXYFile(self):
        self.le_hdf5_file_name.setText(oasysgui.selectFileFromDialog(self, self.hdf5_file_name, "Select Input File", file_extension_filter="HDF5/EDF Files (*.hdf5 *.h5 *.hdf *.edf)"))
