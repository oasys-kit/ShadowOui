#!/usr/bin/env python
# -*- coding: utf-8 -*-
# #########################################################################
# Copyright (c) 2018, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2018. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

import copy, numpy

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from matplotlib import cm, rcParams
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.colors import colorConverter, ListedColormap

try:
    from mpl_toolkits.mplot3d import Axes3D  # mandatory to load 3D plot
except:
    pass

from oasys.widgets import gui as oasysgui

from oasys.util.oasys_util import get_sigma, get_average
from oasys.util.scanning_gui import HistogramData
from orangecontrib.shadow.util.shadow_util import ShadowPlot


class AbstractScanHistoWidget(QWidget):

    def __init__(self, workspace_units_to_cm):
        super(AbstractScanHistoWidget, self).__init__()

        self.workspace_units_to_cm=workspace_units_to_cm

    def plot_histo(self,
                   beam,
                   col,
                   nbins=100,
                   ref=23,
                   title="",
                   xtitle="",
                   ytitle="",
                   histo_index=0,
                   scan_variable_name="Variable",
                   scan_variable_value=0,
                   offset=0.0,
                   xrange=None,
                   show_reference=True,
                   add_labels=True,
                   has_colormap=True,
                   colormap=cm.rainbow):
        raise NotImplementedError("this methid is abstract")


class Scan3DHistoWidget(AbstractScanHistoWidget):
    class PlotType:
        LINES = 0
        SURFACE = 1

    def __init__(self, workspace_units_to_cm, image_height=645, image_width=860, type=PlotType.LINES):
        super(Scan3DHistoWidget, self).__init__(workspace_units_to_cm)

        self.figure = Figure(figsize=(image_height, image_width))
        self.figure.patch.set_facecolor('white')

        self.axis = self.figure.add_subplot(111, projection='3d')
        self.axis.set_title("")
        self.axis.clear()

        self.colorbar = None

        self.plot_canvas = FigureCanvasQTAgg(self.figure)

        layout = QVBoxLayout()

        layout.addWidget(self.plot_canvas)

        self.setLayout(layout)

        self.xx = None
        self.yy = None
        self.zz = None

        self.title = ""
        self.xlabel = ""
        self.ylabel = ""
        self.zlabel = ""

        self.__type=type
        self.__cc = lambda arg: colorConverter.to_rgba(arg, alpha=0.5)

    def clear(self):
        self.reset_plot()
        try:
            self.plot_canvas.draw()
        except:
            pass

    def reset_plot(self):
        self.xx = None
        self.yy = None
        self.zz = None
        self.axis.set_title("")
        self.axis.clear()

    def set_labels(self, title, xlabel, ylabel, zlabel):
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.zlabel = zlabel

    def restore_labels(self):
        self.axis.set_title(self.title)
        self.axis.set_xlabel(self.xlabel)
        self.axis.set_ylabel(self.ylabel)
        self.axis.set_zlabel(self.zlabel)

    def set_xrange(self, xrange):
            self.xx = xrange

    def plot_histo(self,
                   beam,
                   col,
                   nbins=100,
                   ref=23,
                   title="",
                   xtitle="",
                   ytitle="",
                   histo_index=0,
                   scan_variable_name="Variable",
                   scan_variable_value=0,
                   offset=0.0,
                   xrange=None,
                   show_reference=True,
                   add_labels=True,
                   has_colormap=True,
                   colormap=cm.rainbow):
        factor=ShadowPlot.get_factor(col, conv=self.workspace_units_to_cm)

        if histo_index==0 and xrange is None:
            ticket = beam._beam.histo1(col, xrange=None, nbins=nbins, nolost=1, ref=ref)

            fwhm = ticket['fwhm']
            xrange = ticket['xrange']
            centroid = get_average(ticket['histogram'], ticket['bin_center'])

            if not fwhm is None: xrange = [centroid - 2*fwhm , centroid + 2*fwhm]

        ticket = beam._beam.histo1(col, xrange=xrange, nbins=nbins, nolost=1, ref=ref)

        if not ytitle is None:  ytitle = ytitle + ' weighted by ' + ShadowPlot.get_shadow_label(ref)

        histogram = ticket['histogram_path']
        bins = ticket['bin_path']*factor

        histogram_stats = ticket['histogram']
        bins_stats = ticket['bin_center']

        sigma = get_sigma(histogram_stats, bins_stats)*factor
        fwhm = sigma*2.35 if ticket['fwhm'] is None else ticket['fwhm']*factor
        centroid = get_average(histogram_stats, bins_stats)*factor

        peak_intensity = numpy.average(histogram_stats[numpy.where(histogram_stats>=numpy.max(histogram_stats)*0.90)])
        integral_intensity = numpy.sum(histogram_stats)

        rcParams['axes.formatter.useoffset']='False'

        self.set_xrange(bins)
        self.set_labels(title=title, xlabel=xtitle, ylabel=scan_variable_name, zlabel=ytitle)

        self.add_histo(scan_variable_value, histogram, has_colormap, colormap, histo_index)

        return HistogramData(histogram=histogram_stats,
                             bins=bins_stats,
                             xrange=xrange,
                             fwhm=fwhm,
                             sigma=sigma,
                             centroid=centroid,
                             peak_intensity=peak_intensity,
                             integral_intensity=integral_intensity)

    def add_histo(self, scan_value, intensities, has_colormap, colormap, histo_index):
        if self.xx is None: raise ValueError("Initialize X range first")
        if self.xx.shape != intensities.shape: raise ValueError("Given Histogram has a different binning")

        if isinstance(scan_value, str):
            self.yy = numpy.array([1]) if self.yy is None else numpy.append(self.yy, len(self.yy)+1)
        else:
            self.yy = numpy.array([scan_value]) if self.yy is None else numpy.append(self.yy, scan_value)

        if self.zz is None:
            self.zz = numpy.array([intensities])
        else:
            self.zz = numpy.append(self.zz, intensities)

        self.axis.clear()

        self.restore_labels()

        x_to_plot, y_to_plot = numpy.meshgrid(self.xx, self.yy)
        zz_to_plot = self.zz.reshape(len(self.yy), len(self.xx))

        if self.__type==Scan3DHistoWidget.PlotType.SURFACE:
            if has_colormap:
                self.axis.plot_surface(x_to_plot, y_to_plot, zz_to_plot,
                                       rstride=1, cstride=1, cmap=colormap, linewidth=0.5, antialiased=True)
            else:
                self.axis.plot_surface(x_to_plot, y_to_plot, zz_to_plot,
                                       rstride=1, cstride=1, color=self.__cc('black'), linewidth=0.5, antialiased=True)

        elif self.__type==Scan3DHistoWidget.PlotType.LINES:

            if has_colormap:
                self.plot_lines_colormap(x_to_plot, y_to_plot, zz_to_plot, colormap, histo_index)
            else:
                self.plot_lines_black(x_to_plot, zz_to_plot)

            xmin = numpy.min(self.xx)
            xmax = numpy.max(self.xx)
            ymin = numpy.min(self.yy)
            ymax = numpy.max(self.yy)
            zmin = numpy.min(self.zz)
            zmax = numpy.max(self.zz)

            self.axis.set_xlim(xmin,xmax)
            self.axis.set_ylim(ymin,ymax)
            self.axis.set_zlim(zmin,zmax)

        self.axis.mouse_init()

        try:
            self.plot_canvas.draw()
        except:
            pass

    def add_empty_curve(self, histo_data):
        pass

    def plot_lines_black(self, X, Z):
        verts = []
        for i in range(len(self.yy)):
            verts.append(list(zip(X[i], Z[i, :])))

        self.axis.add_collection3d(LineCollection(verts, colors=[self.__cc('black')]), zs=self.yy, zdir='y')

    def plot_lines_colormap(self, X, Y, Z, colormap, histo_index):

        import matplotlib.pyplot as plt

        # Set normalization to the same values for all plots
        norm = plt.Normalize(numpy.min(self.zz), numpy.max(self.zz))

        # Check sizes to loop always over the smallest dimension
        n,m = Z.shape

        if n>m:
            X=X.T; Y=Y.T; Z=Z.T
            m,n = n,m

        transparent_colormap = colormap(numpy.arange(colormap.N))
        transparent_colormap[:,-1] = 0.5*numpy.ones(colormap.N)
        transparent_colormap = ListedColormap(transparent_colormap)


        for j in range(n):
            # reshape the X,Z into pairs
            points = numpy.array([X[j,:], Z[j,:]]).T.reshape(-1, 1, 2)
            segments = numpy.concatenate([points[:-1], points[1:]], axis=1)
            lc = LineCollection(segments, cmap=transparent_colormap, norm=norm)

            # Set the values used for colormapping
            lc.set_array((Z[j,1:]+Z[j,:-1])/2)
            lc.set_linewidth(2) # set linewidth a little larger to see properly the colormap variation
            self.axis.add_collection3d(lc, zs=(Y[j,1:]+Y[j,:-1])/2,  zdir='y') # add line to axes

        if histo_index==0:
            self.colorbar = self.figure.colorbar(lc) # add colorbar, as the normalization is the same for all,

        self.colorbar.update_normal(lc)
        self.colorbar.draw_all()
        self.colorbar.update_bruteforce(lc)

class ScanHistoWidget(AbstractScanHistoWidget):

    def __init__(self, workspace_units_to_cm):
        super(ScanHistoWidget, self).__init__(workspace_units_to_cm)

        self.plot_canvas = oasysgui.plotWindow(parent=None,
                                               backend=None,
                                               resetzoom=True,
                                               autoScale=True,
                                               logScale=False,
                                               grid=True,
                                               curveStyle=True,
                                               colormap=False,
                                               aspectRatio=False,
                                               yInverted=False,
                                               copy=True,
                                               save=True,
                                               print_=True,
                                               control=True,
                                               position=True,
                                               roi=False,
                                               mask=False,
                                               fit=True)

        layout = QVBoxLayout()

        layout.addWidget(self.plot_canvas)

        self.setLayout(layout)


    def plot_histo(self,
                   beam,
                   col,
                   nbins=100,
                   ref=23,
                   title="",
                   xtitle="",
                   ytitle="",
                   histo_index=0,
                   scan_variable_name="Variable",
                   scan_variable_value=0,
                   offset=0.0,
                   xrange=None,
                   show_reference=True,
                   add_labels=True,
                   has_colormap=True,
                   colormap=cm.rainbow):

        factor=ShadowPlot.get_factor(col, conv=self.workspace_units_to_cm)

        if histo_index==0 and xrange is None:
            ticket = beam._beam.histo1(col, xrange=None, nbins=nbins, nolost=1, ref=ref)

            fwhm = ticket['fwhm']
            xrange = ticket['xrange']
            centroid = get_average(ticket['histogram'], ticket['bin_center'])

            if not fwhm is None:
                xrange = [centroid - 2*fwhm , centroid + 2*fwhm]

        ticket = beam._beam.histo1(col, xrange=xrange, nbins=nbins, nolost=1, ref=ref)

        if not ytitle is None:  ytitle = ytitle + ' weighted by ' + ShadowPlot.get_shadow_label(ref)

        histogram = ticket['histogram_path']
        bins = ticket['bin_path']*factor

        histogram_stats = ticket['histogram']
        bins_stats = ticket['bin_center']

        sigma = get_sigma(histogram_stats, bins_stats)*factor
        fwhm = sigma*2.35 if ticket['fwhm'] is None else ticket['fwhm']*factor
        centroid = get_average(histogram_stats, bins_stats)*factor

        peak_intensity = numpy.average(histogram_stats[numpy.where(histogram_stats>=numpy.max(histogram_stats)*0.85)])
        integral_intensity = numpy.sum(histogram_stats)

        if histo_index==0 and show_reference:
            h_title = "Reference"
        else:
            h_title = scan_variable_name + ": " + str(scan_variable_value)

        color="#000000"

        import matplotlib
        matplotlib.rcParams['axes.formatter.useoffset']='False'

        if histo_index== 0:
            offset = int(peak_intensity*0.3)

        self.plot_canvas.addCurve(bins, histogram + offset*histo_index, h_title, symbol='', color=color, xlabel=xtitle, ylabel=ytitle, replace=False) #'+', '^', ','

        if add_labels: self.plot_canvas._backend.ax.text(xrange[0]*factor*1.05, offset*histo_index*1.05, h_title)

        if not xtitle is None: self.plot_canvas.setGraphXLabel(xtitle)
        if not ytitle is None: self.plot_canvas.setGraphYLabel(ytitle)
        if not title is None:  self.plot_canvas.setGraphTitle(title)

        for label in self.plot_canvas._backend.ax.yaxis.get_ticklabels():
            label.set_color('white')
            label.set_fontsize(1)

        self.plot_canvas.setActiveCurveColor(color="#00008B")

        self.plot_canvas.setInteractiveMode('zoom', color='orange')
        self.plot_canvas.resetZoom()
        self.plot_canvas.replot()

        self.plot_canvas.setGraphXLimits(xrange[0]*factor, xrange[1]*factor)

        self.plot_canvas.setActiveCurve(h_title)

        self.plot_canvas.setDefaultPlotLines(True)
        self.plot_canvas.setDefaultPlotPoints(False)

        self.plot_canvas.getLegendsDockWidget().setFixedHeight(510)
        self.plot_canvas.getLegendsDockWidget().setVisible(True)

        self.plot_canvas.addDockWidget(Qt.RightDockWidgetArea, self.plot_canvas.getLegendsDockWidget())

        return HistogramData(histogram=histogram_stats,
                             bins=bins_stats,
                             offset=offset,
                             xrange=xrange,
                             fwhm=fwhm,
                             sigma=sigma,
                             centroid=centroid,
                             peak_intensity=peak_intensity,
                             integral_intensity=integral_intensity)

    def add_empty_curve(self, histo_data):
        self.plot_canvas.addCurve(numpy.array([histo_data.centroid]),
                                  numpy.zeros(1),
                                 "Click on curve to highlight it",
                                  xlabel="",
                                  ylabel="",
                                  symbol='',
                                  color='white')

        self.plot_canvas.setActiveCurve("Click on curve to highlight it")


