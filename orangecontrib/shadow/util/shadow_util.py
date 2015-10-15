__author__ = 'labx'

import os
import random
import sys

import numpy
import xraylib
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QMessageBox, QWidget, QFont, QPalette, QColor, QGridLayout, QLabel, QFileDialog
from matplotlib.patches import FancyArrowPatch, ArrowStyle
from scipy import optimize, asarray

try:
    from orangewidget import gui

    import PyMca5.PyMcaGui.plotting.PlotWindow as PlotWindow
    import PyMca5.PyMcaGui.plotting.PlotWidget as PlotWidget

    from PyMca5.PyMcaGui import PyMcaQt as qt
    from PyMca5.PyMcaCore import PyMcaDirs
    from PyMca5.PyMcaIO import ArraySave
    from PyMca5.PyMcaGui.plotting.PyMca_Icons import IconDict
    from PyMca5.PyMcaGui.plotting.ImageView import ImageView

    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from matplotlib import figure as matfig
    import pylab
except ImportError:
    print(sys.exc_info()[1])
    pass

import Shadow.ShadowToolsPrivate as stp

class ConfirmDialog(QMessageBox):
    def __init__(self, parent, message, title):
        super(ConfirmDialog, self).__init__(parent)

        self.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        self.setIcon(QMessageBox.Question)
        self.setText(message)
        self.setWindowTitle(title)

    @classmethod
    def confirmed(cls, parent=None, message="Confirm Action?", title="Confirm Action"):
        return ConfirmDialog(parent, message, title).exec_() == QMessageBox.Ok

class ShadowGui():

    @classmethod
    def lineEdit(cls, widget, master, value, label=None, labelWidth=None,
             orientation='vertical', box=None, callback=None,
             valueType=str, validator=None, controlWidth=None,
             callbackOnType=False, focusInCallback=None,
             enterPlaceholder=False, **misc):

        lEdit = gui.lineEdit(widget, master, value, label, labelWidth, orientation, box, callback, valueType, validator, controlWidth, callbackOnType, focusInCallback, enterPlaceholder, **misc)

        if value:
            if (valueType != str):
                lEdit.setAlignment(Qt.AlignRight)

        return lEdit

    @classmethod
    def widgetBox(cls, widget, box=None, orientation='vertical', margin=None, spacing=4, height=None, width=None, **misc):

        box = gui.widgetBox(widget, box, orientation, margin, spacing, **misc)
        box.layout().setAlignment(Qt.AlignTop)

        if not height is None:
            box.setFixedHeight(height)
        if not width is None:
            box.setFixedWidth(width)

        return box

    @classmethod
    def tabWidget(cls, widget, height=None, width=None):
        tabWidget = gui.tabWidget(widget)

        if not height is None:
            tabWidget.setFixedHeight(height)
        if not width is None:
            tabWidget.setFixedWidth(width)

        return tabWidget

    @classmethod
    def createTabPage(cls, tabWidget, name, widgetToAdd=None, canScroll=False, height=None, width=None):

        tab = gui.createTabPage(tabWidget, name, widgetToAdd, canScroll)
        tab.layout().setAlignment(Qt.AlignTop)

        if not height is None:
            tab.setFixedHeight(height)
        if not width is None:
            tab.setFixedWidth(width)

        return tab

    @classmethod
    def selectFileFromDialog(cls, widget, previous_file_path="", message="Select File", start_directory=".", file_extension_filter="*.*"):
        file_path = QFileDialog.getOpenFileName(widget, message, start_directory, file_extension_filter)

        if not file_path is None and not file_path.strip() == "":
            return file_path
        else:
            return previous_file_path

    @classmethod
    def checkNumber(cls, value, field_name):
        try:
            float(value)
        except ValueError:
            raise Exception(str(field_name) + " is not a number")

        return value

    @classmethod
    def checkPositiveNumber(cls, value, field_name):
        value = ShadowGui.checkNumber(value, field_name)
        if (value < 0): raise Exception(field_name + " should be >= 0")

        return value

    @classmethod
    def checkStrictlyPositiveNumber(cls, value, field_name):
        value = ShadowGui.checkNumber(value, field_name)
        if (value <= 0): raise Exception(field_name + " should be > 0")

        return value

    @classmethod
    def checkStrictlyPositiveAngle(cls, value, field_name):
        value = ShadowGui.checkNumber(value, field_name)
        if value <= 0 or value >= 360: raise Exception(field_name + " should be > 0 and < 360 deg")

        return value

    @classmethod
    def checkPositiveAngle(cls, value, field_name):
        value = ShadowGui.checkNumber(value, field_name)
        if value < 0 or value > 360: raise Exception(field_name + " should be >= 0 and <= 360 deg")

        return value

    @classmethod
    def checkEmptyString(cls, string, field_name):

        if string is None: raise Exception(field_name + " should not be an empty string")
        if string.strip() == "": raise Exception(field_name + " should not be an empty string")

        return string

    @classmethod
    def checkFileName(cls, fileName):
        if fileName is None: raise Exception("File name is Empty")
        if fileName.strip() == "": raise Exception("File name is Empty")

        if os.path.isabs(fileName):
            filePath = fileName
        else:
            if fileName.startswith('/'):
                filePath =  os.getcwd() + fileName
            else:
                filePath = os.getcwd() + '/' + fileName

        return filePath

    @classmethod
    def checkDir(cls, fileName):
        filePath = ShadowGui.checkFileName(fileName)

        container_dir = os.path.dirname(filePath)

        if not os.path.exists(container_dir):
            raise Exception("Directory " + container_dir + " not existing")

        return filePath

    @classmethod
    def checkFile(cls, fileName):
        filePath = ShadowGui.checkDir(fileName)

        if not os.path.exists(filePath):
            raise Exception("File " + fileName + " not existing")

        return filePath

    @classmethod
    def checkEmptyBeam(cls, input_beam):
        if input_beam is None: return False
        elif not hasattr(input_beam._beam, "rays"): return False
        elif len(input_beam._beam.rays) == 0: return False
        else: return True

    @classmethod
    def checkGoodBeam(cls, input_beam):
        go = numpy.where(input_beam._beam.rays[:, 9] == 1)

        if len(input_beam._beam.rays[go]) == 0:
            return False
        else:
            return True

class ShadowStatisticData:
    intensity = 0.0
    total_number_of_rays = 0
    total_good_rays = 0
    total_lost_rays = 0

    def __init__(self, intensity = 0.0,
                 total_number_of_rays = 0,
                 total_good_rays = 0,
                 total_lost_rays = 0):
        self.intensity = intensity
        self.total_number_of_rays = total_number_of_rays
        self.total_good_rays = total_good_rays
        self.total_lost_rays = total_lost_rays

class ShadowHistoData(ShadowStatisticData):
    fwhm = 0.0
    x_fwhm_i = 0.0
    x_fwhm_f = 0.0
    y_fwhm = 0.0

    def __init__(self, intensity = 0.0,
                 total_number_of_rays = 0,
                 total_good_rays = 0,
                 total_lost_rays = 0,
                 fwhm = 0.0,
                 x_fwhm_i = 0.0,
                 x_fwhm_f = 0.0,
                 y_fwhm = 0.0):
        super().__init__(intensity, total_number_of_rays, total_good_rays, total_lost_rays)
        self.fwhm = fwhm
        self.x_fwhm_i = x_fwhm_i
        self.x_fwhm_f = x_fwhm_f
        self.y_fwhm = y_fwhm

class ShadowPlotData(ShadowStatisticData):
    fwhm_h = 0.0
    fwhm_v = 0.0

    def __init__(self, intensity = 0.0,
                 total_number_of_rays = 0,
                 total_good_rays = 0,
                 total_lost_rays = 0,
                 fwhm_h = 0.0,
                 fwhm_v = 0.0):
        super().__init__(intensity, total_number_of_rays, total_good_rays, total_lost_rays)
        self.fwhm_h = fwhm_h
        self.fwhm_v = fwhm_v

class ShadowPlot:

    #########################################################################################
    #
    # FOR TEMPORARY USE: FIX AN ERROR IN PYMCA.PLOT.IMAGEWIEW
    #
    #########################################################################################

    """Sample code to add 2D dataset saving as text to ImageView."""


    class ShadowImageView(ImageView):
        """Subclass ImageView to add save 2D dataset.

        Image origin and scale are not taken into account while saving the image.
        """
        def __init__(self, *args, **kwargs):
            super(ShadowPlot.ShadowImageView, self).__init__(*args, **kwargs)

            # Disable default save behavior and
            # connect to icon signal to get save icon events
            self._imagePlot.enableOwnSave(False)
            self.sigIconSignal.connect(self._handleSaveIcon)

            # Used in getOutputFileName
            self.outputDir = None
            self._saveFilter = None

        def getOutputFileName(self):
            """Open a FileDialog to get the image filename to save to."""
            # Copied from PyMca5.PyMcaGui.plotting.MaskImageWidget
            initdir = PyMcaDirs.outputDir
            if self.outputDir is not None:
                if os.path.exists(self.outputDir):
                    initdir = self.outputDir
            filedialog = qt.QFileDialog(self)
            filedialog.setFileMode(filedialog.AnyFile)
            filedialog.setAcceptMode(qt.QFileDialog.AcceptSave)
            filedialog.setWindowIcon(qt.QIcon(qt.QPixmap(IconDict["gioconda16"])))
            formatlist = ["ASCII Files *.dat",
                          "EDF Files *.edf",
                          'CSV(, separated) Files *.csv',
                          'CSV(; separated) Files *.csv',
                          'CSV(tab separated) Files *.csv',
                          # Added from PlotWindow._getOutputFileName for snapshot
                          'Widget PNG *.png',
                          'Widget JPG *.jpg']
            if hasattr(qt, "QStringList"):
                strlist = qt.QStringList()
            else:
                strlist = []
            for f in formatlist:
                    strlist.append(f)
            if self._saveFilter is None:
                self._saveFilter = formatlist[0]
            filedialog.setFilters(strlist)
            filedialog.selectFilter(self._saveFilter)
            filedialog.setDirectory(initdir)
            ret = filedialog.exec_()
            if not ret:
                return ""
            filename = filedialog.selectedFiles()[0]
            if len(filename):
                filename = qt.safe_str(filename)
                self.outputDir = os.path.dirname(filename)
                self._saveFilter = qt.safe_str(filedialog.selectedFilter())
                filterused = "." + self._saveFilter[-3:]
                PyMcaDirs.outputDir = os.path.dirname(filename)
                if len(filename) < 4:
                    filename = filename + filterused
                elif filename[-4:] != filterused:
                    filename = filename + filterused
            else:
                filename = ""
            return filename

        def _handleSaveIcon(self, event):
            """Handle save icon events.

            Get current active image and save it as a file.
            """
            if event['event'] == 'iconClicked' and event['key'] == 'save':
                imageData = self.getActiveImage()
                if imageData is None:
                    qt.QMessageBox.information(self, "No Data",
                                               "No image to be saved")
                    return
                data, legend, info, pixmap = imageData
                imageList = [data]
                labels = ['value']

                # Copied from MaskImageWidget.saveImageList
                filename = self.getOutputFileName()
                if not len(filename):
                    return

                # Add PNG and JPG adapted from PlotWindow.defaultSaveAction
                if 'WIDGET' in self._saveFilter.upper():
                    fformat = self._saveFilter[-3:].upper()
                    pixmap = qt.QPixmap.grabWidget(self._imagePlot)
                    # Use the following instead to grab the image + histograms
                    # pixmap = qt.QPixmap.grabWidget(self)
                    if not pixmap.save(filename, fformat):
                        msg = qt.QMessageBox(self)
                        msg.setIcon(qt.QMessageBox.Critical)
                        msg.setInformativeText(str(sys.exc_info()[1]))
                        msg.setDetailedText(traceback.format_exc())
                        msg.exec_()
                    return

                if filename.lower().endswith(".edf"):
                    ArraySave.save2DArrayListAsEDF(imageList, filename, labels)
                elif filename.lower().endswith(".csv"):
                    if "," in self._saveFilter:
                        csvseparator = ","
                    elif ";" in self._saveFilter:
                        csvseparator = ";"
                    else:
                        csvseparator = "\t"
                    ArraySave.save2DArrayListAsASCII(imageList, filename, labels,
                                                     csv=True,
                                                     csvseparator=csvseparator)
                else:
                    ArraySave.save2DArrayListAsASCII(imageList, filename, labels,
                                                     csv=False)


    #########################################################################################
    #
    # WIDGET FOR DETAILED PLOT
    #
    #########################################################################################

    class InfoBoxWidget(QWidget):
        intensity_field = ""
        total_rays_field = ""
        total_good_rays_field = ""
        total_lost_rays_field = ""
        fwhm_h_field = ""
        fwhm_v_field = ""

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0, is_2d=True):
            super(ShadowPlot.InfoBoxWidget, self).__init__()

            info_box_inner=ShadowGui.widgetBox(self, "Info")
            info_box_inner.setFixedHeight(180*y_scale_factor)
            info_box_inner.setFixedWidth(250*x_scale_factor)

            self.intensity = ShadowGui.lineEdit(info_box_inner, self, "intensity_field", "Intensity", tooltip="Intensity", labelWidth=110, valueType=str, orientation="horizontal")
            self.total_rays = ShadowGui.lineEdit(info_box_inner, self, "total_rays_field", "Total Rays", tooltip="Total Rays", labelWidth=110, valueType=str, orientation="horizontal")
            self.total_good_rays = ShadowGui.lineEdit(info_box_inner, self, "total_good_rays_field", "Total Good Rays", tooltip="Total Good Rays", labelWidth=110, valueType=str, orientation="horizontal")
            self.total_lost_rays = ShadowGui.lineEdit(info_box_inner, self, "total_lost_rays_field", "Total Lost Rays", tooltip="Total Lost Rays", labelWidth=110, valueType=str, orientation="horizontal")

            label_box_1 = ShadowGui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

            self.label_h = QLabel("FWHM ")
            self.label_h.setFixedWidth(110)
            palette =  QPalette(self.label_h.palette())
            palette.setColor(QPalette.Foreground, QColor('blue'))
            self.label_h.setPalette(palette)
            label_box_1.layout().addWidget(self.label_h)
            self.fwhm_h = ShadowGui.lineEdit(label_box_1, self, "fwhm_h_field", "", tooltip="FWHM", labelWidth=110, valueType=str, orientation="horizontal")

            if is_2d:
                label_box_2 = ShadowGui.widgetBox(info_box_inner, "", addSpace=False, orientation="horizontal")

                self.label_v = QLabel("FWHM ")
                self.label_v.setFixedWidth(110)
                palette =  QPalette(self.label_h.palette())
                palette.setColor(QPalette.Foreground, QColor('red'))
                self.label_v.setPalette(palette)
                label_box_2.layout().addWidget(self.label_v)
                self.fwhm_v = ShadowGui.lineEdit(label_box_2, self, "fwhm_v_field", "", tooltip="FWHM", labelWidth=110, valueType=str, orientation="horizontal")

            self.intensity.setReadOnly(True)
            font = QFont(self.intensity.font())
            font.setBold(True)
            self.intensity.setFont(font)
            palette = QPalette(self.intensity.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.intensity.setPalette(palette)

            self.total_rays.setReadOnly(True)
            font = QFont(self.total_rays.font())
            font.setBold(True)
            self.total_rays.setFont(font)
            palette = QPalette(self.intensity.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_rays.setPalette(palette)

            self.total_good_rays.setReadOnly(True)
            font = QFont(self.total_good_rays.font())
            font.setBold(True)
            self.total_good_rays.setFont(font)
            palette = QPalette(self.total_good_rays.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_good_rays.setPalette(palette)

            self.total_lost_rays.setReadOnly(True)
            font = QFont(self.total_lost_rays.font())
            font.setBold(True)
            self.total_lost_rays.setFont(font)
            palette = QPalette(self.total_lost_rays.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.total_lost_rays.setPalette(palette)

            self.fwhm_h.setReadOnly(True)
            font = QFont(self.intensity.font())
            font.setBold(True)
            self.fwhm_h.setFont(font)
            palette = QPalette(self.fwhm_h.palette())
            palette.setColor(QPalette.Text, QColor('dark blue'))
            palette.setColor(QPalette.Base, QColor(243, 240, 160))
            self.fwhm_h.setPalette(palette)

            if is_2d:
                self.fwhm_v.setReadOnly(True)
                font = QFont(self.fwhm_v.font())
                font.setBold(True)
                self.fwhm_v.setFont(font)
                palette = QPalette(self.fwhm_v.palette())
                palette.setColor(QPalette.Text, QColor('dark blue'))
                palette.setColor(QPalette.Base, QColor(243, 240, 160))
                self.fwhm_v.setPalette(palette)

        def clear(self):
            self.intensity.setText("0.0")
            self.total_rays.setText("0")
            self.total_good_rays.setText("0")
            self.total_lost_rays.setText("0")
            self.fwhm_h.setText("0.0000")
            if hasattr(self, "fwhm_v"):  self.fwhm_v.setText("0.0000")

    class DetailedHistoWidget(QWidget):

        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0):
            super(ShadowPlot.DetailedHistoWidget, self).__init__()

            self.plot_canvas = PlotWindow.PlotWindow(roi=False, control=False, position=False, plugins=False, logx=False, logy=False)
            self.plot_canvas.setDefaultPlotLines(True)
            self.plot_canvas.setActiveCurveColor(color='darkblue')
            self.plot_canvas.setMinimumWidth(800*x_scale_factor)
            self.plot_canvas.setMaximumWidth(800*x_scale_factor)

            self.info_box = ShadowPlot.InfoBoxWidget(x_scale_factor, y_scale_factor, is_2d=False)

            layout = QGridLayout()

            layout.addWidget(self.plot_canvas, 0, 0, 1, 1)
            layout.addWidget(self.info_box, 0, 1, 1, 1)

            layout.setColumnMinimumWidth(0, 800*x_scale_factor)
            layout.setColumnMinimumWidth(1, 250*x_scale_factor)

            self.setLayout(layout)

        def plot_histo(self, beam, col, nolost, xrange, ref, title, xtitle, ytitle, nbins = 100, xum=""):

            ticket = beam.histo1(col, nbins=nbins, xrange=xrange, nolost=nolost, ref=ref)

            factor=ShadowPlot.get_factor(col)

            if ref != 0 and not ytitle is None:  ytitle = ytitle + ' % ' + (stp.getLabel(ref-1))[0]

            histogram = ticket['histogram_path']
            bins = ticket['bin_path']*factor

            self.plot_canvas.addCurve(bins, histogram, title, symbol='', color='blue', replace=True) #'+', '^', ','
            if not xtitle is None: self.plot_canvas.setGraphXLabel(xtitle)
            if not ytitle is None: self.plot_canvas.setGraphYLabel(ytitle)
            if not title is None: self.plot_canvas.setGraphTitle(title)
            self.plot_canvas.setDrawModeEnabled(True, 'rectangle')
            self.plot_canvas.setZoomModeEnabled(True)

            if ticket['fwhm'] == None: ticket['fwhm'] = 0.0

            n_patches = len(self.plot_canvas._plot.graph.ax.patches)
            if (n_patches > 0): self.plot_canvas._plot.graph.ax.patches.remove(self.plot_canvas._plot.graph.ax.patches[n_patches-1])

            if not ticket['fwhm'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor, x_fwhm_f*factor
                y_fwhm   = max(histogram)*0.5

                self.plot_canvas._plot.graph.ax.add_patch(FancyArrowPatch([x_fwhm_i, y_fwhm],
                                                          [x_fwhm_f, y_fwhm],
                                                          arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                          color='b',
                                                          linewidth=1.5))

            self.plot_canvas.setGraphYLimits(0, max(histogram))
            self.plot_canvas.replot()

            self.info_box.intensity.setText("{:4.3f}".format(ticket['intensity']))
            self.info_box.total_rays.setText(str(ticket['nrays']))
            self.info_box.total_good_rays.setText(str(ticket['good_rays']))
            self.info_box.total_lost_rays.setText(str(ticket['nrays']-ticket['good_rays']))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm']*factor))
            self.info_box.label_h.setText("FWHM " + xum)

        def clear(self):
            self.plot_canvas.clear()
            self.info_box.clear()

    class DetailedPlotWidget(QWidget):
        def __init__(self, x_scale_factor = 1.0, y_scale_factor = 1.0):
            super(ShadowPlot.DetailedPlotWidget, self).__init__()

            self.x_scale_factor = x_scale_factor
            self.y_scale_factor = y_scale_factor

            self.plot_canvas = ShadowPlot.ShadowImageView()

            colormap = {"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256}

            self.plot_canvas._imagePlot.setDefaultColormap(colormap)
            self.plot_canvas.setMinimumWidth(800*x_scale_factor)
            self.plot_canvas.setMaximumWidth(800 * y_scale_factor)

            self.info_box = ShadowPlot.InfoBoxWidget(x_scale_factor, y_scale_factor)

            layout = QGridLayout()

            layout.addWidget(self.plot_canvas.toolBar(), 0, 0, 1, 1)
            layout.addWidget(self.plot_canvas, 1, 0, 1, 1)
            layout.addWidget(self.info_box, 0, 1, 2, 1)

            layout.setColumnMinimumWidth(0, 850*x_scale_factor)
            layout.setColumnMinimumWidth(1, 250*x_scale_factor)

            self.setLayout(layout)

            self.plot_canvas.toolBar()

        def plot_xy(self, beam, var_x, var_y, title, xtitle, ytitle, xrange=None, yrange=None, nolost=1, nbins=100, xum="", yum="", ref=23, is_footprint=False):

            matplotlib.rcParams['axes.formatter.useoffset']='False'

            ticket = beam.histo2(var_x, var_y, nbins=nbins, xrange=xrange, yrange=yrange, nolost=nolost, ref=ref)

            if is_footprint:
                factor1 = 1.0
                factor2 = 1.0
            else:
                factor1=ShadowPlot.get_factor(var_x)
                factor2=ShadowPlot.get_factor(var_y)

            xx = ticket['bin_h_edges']
            yy = ticket['bin_v_edges']

            xmin, xmax = xx.min(), xx.max()
            ymin, ymax = yy.min(), yy.max()

            origin = (xmin*factor1, ymin*factor2)
            scale = (abs((xmax-xmin)/nbins)*factor1, abs((ymax-ymin)/nbins)*factor2)

            # PyMCA inverts axis!!!! histogram must be calculated reversed
            data_to_plot = []
            for y_index in range(0, nbins):
                x_values = []
                for x_index in range(0, nbins):
                    x_values.append(ticket['histogram'][x_index][y_index])

                data_to_plot.append(x_values)

            self.plot_canvas.setImage(numpy.array(data_to_plot), origin=origin, scale=scale)

            if xtitle is None: xtitle=(stp.getLabel(var_x-1))[0]
            if ytitle is None: ytitle=(stp.getLabel(var_y-1))[0]

            self.plot_canvas.setGraphXLabel(xtitle)
            self.plot_canvas.setGraphYLabel(ytitle)
            self.plot_canvas.setGraphTitle(title)

            self.plot_canvas._histoHPlot.setGraphYLabel('Frequency')

            self.plot_canvas._histoHPlot._plot.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._plot.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._plot.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot.setGraphXLabel('Frequency')

            self.plot_canvas._histoVPlot._plot.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._plot.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._plot.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            if ticket['fwhm_h'] == None: ticket['fwhm_h'] = 0.0
            if ticket['fwhm_v'] == None: ticket['fwhm_v'] = 0.0

            n_patches = len(self.plot_canvas._histoHPlot._plot.graph.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoHPlot._plot.graph.ax.patches.remove(self.plot_canvas._histoHPlot._plot.graph.ax.patches[n_patches-1])

            if not ticket['fwhm_h'] == 0.0:
                x_fwhm_i, x_fwhm_f = ticket['fwhm_coordinates_h']
                x_fwhm_i, x_fwhm_f = x_fwhm_i*factor1, x_fwhm_f*factor1
                y_fwhm = max(ticket['histogram_h']) * 0.5

                self.plot_canvas._histoHPlot._plot.graph.ax.add_patch(FancyArrowPatch([x_fwhm_i, y_fwhm],
                                                                     [x_fwhm_f, y_fwhm],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='b',
                                                                     linewidth=1.5))

            n_patches = len(self.plot_canvas._histoVPlot._plot.graph.ax.patches)
            if (n_patches > 0): self.plot_canvas._histoVPlot._plot.graph.ax.patches.remove(self.plot_canvas._histoVPlot._plot.graph.ax.patches[n_patches-1])

            if not ticket['fwhm_v'] == 0.0:
                y_fwhm_i, y_fwhm_f = ticket['fwhm_coordinates_v']
                y_fwhm_i, y_fwhm_f = y_fwhm_i*factor2, y_fwhm_f*factor2
                x_fwhm = max(ticket['histogram_v']) * 0.5

                self.plot_canvas._histoVPlot._plot.graph.ax.add_patch(FancyArrowPatch([x_fwhm, y_fwhm_i],
                                                                     [x_fwhm, y_fwhm_f],
                                                                     arrowstyle=ArrowStyle.CurveAB(head_width=2, head_length=4),
                                                                     color='r',
                                                                     linewidth=1.5))

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()
            self.plot_canvas._imagePlot.replot()

            self.info_box.intensity.setText("{:4.3f}".format(ticket['intensity']))
            self.info_box.total_rays.setText(str(ticket['nrays']))
            self.info_box.total_good_rays.setText(str(ticket['good_rays']))
            self.info_box.total_lost_rays.setText(str(ticket['nrays']-ticket['good_rays']))
            self.info_box.fwhm_h.setText("{:5.4f}".format(ticket['fwhm_h'] * factor1))
            self.info_box.fwhm_v.setText("{:5.4f}".format(ticket['fwhm_v'] * factor2))
            self.info_box.label_h.setText("FWHM " + xum)
            self.info_box.label_v.setText("FWHM " + yum)

        def clear(self):
            self.plot_canvas.clear()

            self.plot_canvas._histoHPlot.clear()
            self.plot_canvas._histoVPlot.clear()

            self.plot_canvas._histoHPlot._plot.ax.xaxis.get_label().set_color('white')
            self.plot_canvas._histoHPlot._plot.ax.xaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoHPlot._plot.ax.xaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoVPlot._plot.ax.yaxis.get_label().set_color('white')
            self.plot_canvas._histoVPlot._plot.ax.yaxis.get_label().set_fontsize(1)
            for label in self.plot_canvas._histoVPlot._plot.ax.yaxis.get_ticklabels():
                label.set_color('white')
                label.set_fontsize(1)

            self.plot_canvas._histoHPlot.setGraphYLabel('Frequency')
            self.plot_canvas._histoVPlot.setGraphXLabel('Frequency')

            self.plot_canvas._histoHPlot.replot()
            self.plot_canvas._histoVPlot.replot()

            self.info_box.clear()

    #########################################################################################

    @classmethod
    def plotxy_preview(cls, plot_window, beam, var_x, var_y, nolost=0, title='PLOTXY', xtitle=None, ytitle=None, is_footprint=False):

        matplotlib.rcParams['axes.formatter.useoffset']='False'

        col1 = beam.getshonecol(var_x, nolost=nolost)
        col2 = beam.getshonecol(var_y, nolost=nolost)


        if is_footprint:
            factor1 = 1.0
            factor2 = 1.0
        else:
            factor1 = ShadowPlot.get_factor(var_x)
            factor2 = ShadowPlot.get_factor(var_y)

        if xtitle is None: xtitle=(stp.getLabel(var_x-1))[0]
        if ytitle is None: ytitle=(stp.getLabel(var_y-1))[0]

        plot_window.addCurve(col1*factor1, col2*factor2, title, symbol='.', color='blue', replace=True) #'+', '^', ','

        if not xtitle is None: plot_window.setGraphXLabel(xtitle)
        if not ytitle is None: plot_window.setGraphYLabel(ytitle)
        if not title is None: plot_window.setGraphTitle(title)
        plot_window.setDrawModeEnabled(True, 'rectangle')
        plot_window.setZoomModeEnabled(True)

    @classmethod
    def plot_histo_preview(cls, plot_window, beam, col, nolost, ref, title, xtitle, ytitle):

        matplotlib.rcParams['axes.formatter.useoffset']='False'

        factor=ShadowPlot.get_factor(col)

        ticket = beam.histo1(col, nbins=100, xrange=None, nolost=nolost, ref=ref)

        if ref != 0 and not ytitle is None:  ytitle = ytitle + ' % ' + (stp.getLabel(ref-1))[0]

        histogram = ticket['histogram_path']
        bins = ticket['bin_path']*factor

        plot_window.addCurve(bins, histogram, title, symbol='', color='blue', replace=True) #'+', '^', ','
        if not xtitle is None: plot_window.setGraphXLabel(xtitle)
        if not ytitle is None: plot_window.setGraphYLabel(ytitle)
        plot_window.setDrawModeEnabled(True, 'rectangle')
        plot_window.setZoomModeEnabled(True)
        plot_window.setGraphYLimits(0, max(histogram))
        plot_window.replot()

    @classmethod
    def get_factor(cls, var):
        factor = 1.0

        if var == 1 or var == 2 or var == 3:
            factor = 1e4 # cm to micron
        elif var == 4 or var == 5 or var == 6:
            factor = 1e6 # rad to urad

        return factor

class ShadowMath:

    @classmethod
    def pseudo_voigt_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)
        y_norm = y/sum(y)

        mean = sum(x*y_norm)
        sigma = numpy.sqrt(sum(y_norm*(x-mean)**2)/len(x))
        amplitude = max(data_y)
        eta = 0.01

        def pseudo_voigt_function(x, A, x0, sigma, eta):
            return A*(((1-eta)*numpy.exp(-(x-x0)**2/(2*sigma**2))) + (eta*(1/(1+((x-x0)**2/(2*sigma**2))))))

        parameters, covariance_matrix = optimize.curve_fit(pseudo_voigt_function, x, y, p0 = [amplitude, mean, sigma, eta])
        parameters.resize(5)
        parameters[4] = (2.355*parameters[2]) # FWHM

        return parameters, covariance_matrix

    @classmethod
    def gaussian_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)
        y_norm = y/sum(y)

        mean = sum(x*y_norm)
        sigma = numpy.sqrt(sum(y_norm*(x-mean)**2)/len(x))
        amplitude = max(data_y)

        def gaussian_function(x, A, x0, sigma):
            return A*numpy.exp(-(x-x0)**2/(2*sigma**2))

        parameters, covariance_matrix = optimize.curve_fit(gaussian_function, x, y, p0 = [amplitude, mean, sigma])
        parameters.resize(4)
        parameters[3] = 2.355*parameters[2]# FWHM

        return parameters, covariance_matrix

    @classmethod
    def caglioti_broadening_fit(cls, data_x, data_y):
        x = asarray(data_x)
        y = asarray(data_y)

        def caglioti_broadening_function(x, U, V, W):
            return numpy.sqrt(W + V * (numpy.tan(x*numpy.pi/360)) + U * (numpy.tan(x*numpy.pi/360))**2)

        parameters, covariance_matrix = optimize.curve_fit(caglioti_broadening_function, x, y, p0=[0.0001, 0.0001, 0.0001])

        return parameters, covariance_matrix

    @classmethod
    def vectorial_product(cls, vector1, vector2):
        result = [0, 0, 0]

        result[0] = vector1[1]*vector2[2] - vector1[2]*vector2[1]
        result[1] = -(vector1[0]*vector2[2] - vector1[2]*vector2[0])
        result[2] = vector1[0]*vector2[1] - vector1[1]*vector2[0]

        return result

    @classmethod
    def scalar_product(cls, vector1, vector2):
        return vector1[0]*vector2[0] + vector1[1]*vector2[1] + vector1[2]*vector2[2]

    @classmethod
    def vector_modulus(cls, vector):
        return numpy.sqrt(cls.scalar_product(vector, vector))

    @classmethod
    def vector_multiply(cls, vector, constant):
        result = [0, 0, 0]

        result[0] = vector[0] * constant
        result[1] = vector[1] * constant
        result[2] = vector[2] * constant

        return result

    @classmethod
    def vector_divide(cls, vector, constant):
        result = [0, 0, 0]

        result[0] = vector[0] / constant
        result[1] = vector[1] / constant
        result[2] = vector[2] / constant

        return result

    @classmethod
    def vector_normalize(cls, vector):
        return cls.vector_divide(vector, cls.vector_modulus(vector))

    @classmethod
    def vector_sum(cls, vector1, vector2):
        result = [0, 0, 0]

        result[0] = vector1[0] + vector2[0]
        result[1] = vector1[1] + vector2[1]
        result[2] = vector1[2] + vector2[2]

        return result

    @classmethod
    def vector_difference(cls, vector1, vector2):
        result = [0, 0, 0]

        result[0] = vector1[0] - vector2[0]
        result[1] = vector1[1] - vector2[1]
        result[2] = vector1[2] - vector2[2]

        return result

    ##########################################################################
    # Rodrigues Formula:
    #
    # rotated = vector * cos(rotation_angle) + 
    #           (rotation_axis x vector) * sin(rotation_angle) + 
    #           rotation_axis*(rotation_axis . vector)(1 - cos(rotation_angle))
    #
    # rotation_angle in radians
    #
    ##########################################################################
    @classmethod
    def vector_rotate(cls, rotation_axis, rotation_angle, vector):
        result_temp_1 = ShadowMath.vector_multiply(vector, numpy.cos(rotation_angle))
        result_temp_2 = ShadowMath.vector_multiply(ShadowMath.vectorial_product(rotation_axis, vector),
                                                   numpy.sin(rotation_angle))
        result_temp_3 = ShadowMath.vector_multiply(rotation_axis,
                                                   ShadowMath.scalar_product(rotation_axis, vector) * (1 - numpy.cos(rotation_angle)))

        result = ShadowMath.vector_sum(result_temp_1,
                                       ShadowMath.vector_sum(result_temp_2, result_temp_3))
        return result

    @classmethod
    def point_distance(cls, point1, point2):
        return cls.vector_modulus(cls.vector_difference(point1, point2))

class ShadowPhysics:

    ######################################
    # FROM NIST
    codata_h = numpy.array(6.62606957e-34)
    codata_ec = numpy.array(1.602176565e-19)
    codata_c = numpy.array(299792458.0)
    ######################################

    A2EV = (codata_h*codata_c/codata_ec)*1e+10
    K2EV = 2*numpy.pi/(codata_h*codata_c/codata_ec*1e+2)

    @classmethod
    def getWavelengthfromShadowK(cls, k_mod): # in cm
        return (2*numpy.pi/k_mod)*1e+8 # in Angstrom

    @classmethod
    def getShadowKFromWavelength(cls, wavelength): # in A
        return (2*numpy.pi/wavelength)*1e+8 # in cm

    @classmethod
    def getWavelengthFromEnergy(cls, energy): #in eV
        return cls.A2EV/energy # in Angstrom

    @classmethod
    def getEnergyFromWavelength(cls, wavelength): # in Angstrom
        return cls.A2EV/wavelength # in eV

    @classmethod
    def getEnergyFromShadowK(cls, k_mod): # in cm
        return  k_mod/cls.K2EV # in eV

    @classmethod
    def getShadowKFromEnergy(cls, energy): # in A
        return cls.K2EV*energy # in cm

    @classmethod
    def calculateBraggAngle(cls, wavelength, h, k, l, a):

        # lambda = 2 pi / |k| = 2 d sen(th)
        #
        # sen(th) = lambda / (2  d)
        #
        # d = a / sqrt(h^2 + k^2 + l^2)
        #
        # sen(th) = (sqrt(h^2 + k^2 + l^2) * lambda)/(2 a)

        theta_bragg = -1

        argument = (wavelength*numpy.sqrt(h**2+k**2+l**2))/(2*a)

        if argument <=1:
            result = numpy.arcsin(argument)

            if result > 0:
                theta_bragg = result

        return theta_bragg

    @classmethod
    def checkCompoundName(cls, compound_name):
        if compound_name is None: raise Exception("Compound Name is Empty")
        if str(compound_name.strip()) == "": raise Exception("Compound Name is Empty")

        compound_name = compound_name.strip()

        try:
            xraylib.CompoundParser(compound_name)
            return compound_name
        except:
            raise Exception("Compound Name is not correct")

    @classmethod
    def getMaterialDensity(cls, material_name):
        if material_name is None: return 0.0
        if str(material_name.strip()) == "": return 0.0

        try:
            compoundData = xraylib.CompoundParser(material_name)

            if compoundData["nElements"] == 1:
                return xraylib.ElementDensity(compoundData["Elements"][0])
            else:
                return 0.0
        except:
            return 0.0

    @classmethod
    def Chebyshev(cls, n, x):
        if n==0: return 1
        elif n==1: return x
        else: return 2*x*cls.Chebyshev(n-1, x)-cls.Chebyshev(n-2, x)

    @classmethod
    def ChebyshevBackground(cls, coefficients=[0,0,0,0,0,0], twotheta=0):
        coefficients_set = range(0, len(coefficients))
        background = 0

        for index in coefficients_set:
            background += coefficients[index]*cls.Chebyshev(index, twotheta)

        return background

    @classmethod
    def ChebyshevBackgroundNoised(cls, coefficients=[0,0,0,0,0,0], twotheta=0.0, n_sigma=1.0, random_generator=random.Random()):
        background = cls.ChebyshevBackground(coefficients, twotheta)
        sigma = numpy.sqrt(background) # poisson statistic

        noise = (n_sigma*sigma)*random_generator.random()
        sign_marker = random_generator.random()

        if sign_marker > 0.5:
            return int(round(background+noise, 0))
        else:
            return int(round(background-noise, 0))

    @classmethod
    def ExpDecay(cls, h, x):
      return numpy.exp(-h*x)

    @classmethod
    def ExpDecayBackground(cls, coefficients=[0,0,0,0,0,0], decayparams=[0,0,0,0,0,0], twotheta=0):
        coefficients_set = range(0, len(coefficients))
        background = 0

        for index in coefficients_set:
            background += coefficients[index]*cls.ExpDecay(decayparams[index], twotheta)

        return background

    @classmethod
    def ExpDecayBackgroundNoised(cls, coefficients=[0,0,0,0,0,0], decayparams=[0,0,0,0,0,0], twotheta=0, n_sigma=1, random_generator=random.Random()):
        background = cls.ExpDecayBackground(coefficients, decayparams, twotheta)
        sigma = numpy.sqrt(background) # poisson statistic

        noise = (n_sigma*sigma)*random_generator.random()
        sign_marker = random_generator.random()

        if sign_marker > 0.5:
            return int(round(background+noise, 0))
        else:
            return int(round(background-noise, 0))

import re
import time

class Properties(object):
    def __init__(self, props=None):
        self._props = {}
        self._origprops = {}
        self._keymap = {}
        self.othercharre = re.compile(r'(?<!\\)(\s*\=)|(?<!\\)(\s*\:)')
        self.othercharre2 = re.compile(r'(\s*\=)|(\s*\:)')
        self.bspacere = re.compile(r'\\(?!\s$)')

    def __str__(self):
        s='{'
        for key,value in self._props.items():
            s = ''.join((s,key,'=',value,', '))

        s=''.join((s[:-2],'}'))
        return s

    def __parse(self, lines):
        # Every line in the file must consist of either a comment
        # or a key-value pair. A key-value pair is a line consisting
        # of a key which is a combination of non-white space characters
        # The separator character between key-value pairs is a '=',
        # ':' or a whitespace character not including the newline.
        # If the '=' or ':' characters are found, in the line, even
        # keys containing whitespace chars are allowed.
        # A line with only a key according to the rules above is also
        # fine. In such case, the value is considered as the empty string.
        # In order to include characters '=' or ':' in a key or value,
        # they have to be properly escaped using the backslash character.

        # Some examples of valid key-value pairs:
        #
        # key     value
        # key=value
        # key:value
        # key     value1,value2,value3
        # key     value1,value2,value3 \
        #         value4, value5
        # key
        # This key= this value
        # key = value1 value2 value3

        # Any line that starts with a '#' is considered a comment
        # and skipped. Also any trailing or preceding whitespaces
        # are removed from the key/value.

        # This is a line parser. It parses the
        # contents like by line.

        lineno=0
        i = iter(lines)

        for line in i:
            lineno += 1
            line = line.strip()

            if not line: continue
            if line[0] == '#': continue

            sepidx = -1

            m = self.othercharre.search(line)
            if m:
                first, last = m.span()
                start, end = 0, first
                wspacere = re.compile(r'(?<![\\\=\:])(\s)')
            else:
                if self.othercharre2.search(line):
                    wspacere = re.compile(r'(?<![\\])(\s)')

                start, end = 0, len(line)

            m2 = wspacere.search(line, start, end)
            if m2:
                first, last = m2.span()
                sepidx = first
            elif m:
                first, last = m.span()
                sepidx = last - 1

            while line[-1] == '\\':
                nextline = i.next()
                nextline = nextline.strip()
                lineno += 1
                line = line[:-1] + nextline

            if sepidx != -1:
                key, value = line[:sepidx], line[sepidx+1:]
            else:
                key,value = line,''

            self.processPair(key, value)

    def processPair(self, key, value):
        oldkey = key
        oldvalue = value

        keyparts = self.bspacere.split(key)

        strippable = False
        lastpart = keyparts[-1]

        if lastpart.find('\\ ') != -1:
            keyparts[-1] = lastpart.replace('\\','')

        elif lastpart and lastpart[-1] == ' ':
            strippable = True

        key = ''.join(keyparts)
        if strippable:
            key = key.strip()
            oldkey = oldkey.strip()

        oldvalue = self.unescape(oldvalue)
        value = self.unescape(value)

        self._props[key] = value.strip()

        if self._keymap.__contains__(key):
            oldkey = self._keymap.get(key)
            self._origprops[oldkey] = oldvalue.strip()
        else:
            self._origprops[oldkey] = oldvalue.strip()
            self._keymap[key] = oldkey

    def escape(self, value):
        newvalue = value.replace(':','\:')
        newvalue = newvalue.replace('=','\=')

        return newvalue

    def unescape(self, value):
        newvalue = value.replace('\:',':')
        newvalue = newvalue.replace('\=','=')

        return newvalue

    def load(self, stream):
        if not hasattr(stream, 'read'):
            raise TypeError('Argument should be a file object!')
        if stream.mode != 'r':
            raise ValueError ('Stream should be opened in read-only mode!')

        try:
            lines = stream.readlines()
            self.__parse(lines)
        except IOError as e:
            raise e

    def getProperty(self, key):
        return self._props.get(key)

    def setProperty(self, key, value):
        if type(key) is str and type(value) is str:
            self.processPair(key, value)
        else:
            raise TypeError('both key and value should be strings!')

    def propertyNames(self):
        return self._props.keys()

    def list(self, out=sys.stdout):
        out.write('-- listing properties --\n')
        for key,value in self._props.items():
            out.write(''.join((key,'=',value,'\n')))

    def store(self, out, header=""):
        if out.mode[0] != 'w':
            raise ValueError('Steam should be opened in write mode!')

        try:
            out.write(''.join(('#',header,'\n')))
            tstamp = time.strftime('%a %b %d %H:%M:%S %Z %Y', time.localtime())
            out.write(''.join(('#',tstamp,'\n')))
            for prop, val in self._origprops.items():
                out.write(''.join((prop,'=',self.escape(val),'\n')))

            out.close()
        except IOError as e:
            raise e

    def getPropertyDict(self):
        return self._props

    def __getitem__(self, name):
        return self.getProperty(name)

    def __setitem__(self, name, value):
        self.setProperty(name, value)

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            if hasattr(self._props,name):
                return getattr(self._props, name)

if __name__ == "__main__":

    print(ShadowGui.checkFileName("pippo.dat"))
    print(ShadowGui.checkFileName("Files/pippo.dat"))
    print(ShadowGui.checkFileName("Files/pippo.dat"))
    print(ShadowGui.checkFileName("/Users/labx/Desktop/pippo.dat"))


    '''
    print(ShadowPhysics.A2EV)

    print(ShadowPhysics.Chebyshev(4, 21))
    print(ShadowPhysics.Chebyshev(0, 35))

    coefficients = [5.530814e+002, 2.487256e+000, -2.004860e-001, 2.246427e-003, -1.044517e-005, 1.721576e-008]
    random_generator=random.Random()

    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 10, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 11, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 12, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 13, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 14, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 15, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 16, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 17, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 18, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 19, random_generator=random_generator))
    print(ShadowPhysics.ChebyshevBackgroundNoised(coefficients, 20, random_generator=random_generator))
    '''
