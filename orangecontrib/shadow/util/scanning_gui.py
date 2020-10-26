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

from oasys.util.scanning_gui import HistogramData, get_sigma

from Shadow import Beam


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
            centroid = xrange[0] + (xrange[1] - xrange[0])*0.5

            if not fwhm is None:
                xrange = [centroid - 2*fwhm , centroid + 2*fwhm]

        ticket = beam._beam.histo1(col, xrange=xrange, nbins=nbins, nolost=1, ref=ref)

        if not ytitle is None:  ytitle = ytitle + ' weighted by ' + ShadowPlot.get_shadow_label(ref)

        histogram = ticket['histogram_path']
        bins = ticket['bin_path']*factor

        histogram_stats = ticket['histogram']
        bins_stats = ticket['bin_center']

        fwhm = ticket['fwhm']

        sigma = get_sigma(histogram_stats, bins_stats)*factor
        fwhm = sigma*2.35 if fwhm is None else fwhm*factor

        peak_intensity = numpy.average(histogram_stats[numpy.where(histogram_stats>=numpy.max(histogram_stats)*0.85)])
        integral_intensity = numpy.sum(histogram_stats)

        rcParams['axes.formatter.useoffset']='False'

        self.set_xrange(bins)
        self.set_labels(title=title, xlabel=xtitle, ylabel=scan_variable_name, zlabel=ytitle)

        self.add_histo(scan_variable_value, histogram, has_colormap, colormap, histo_index)

        return HistogramData(histogram_stats, bins_stats, 0.0, xrange, fwhm, sigma, peak_intensity, integral_intensity)

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
            centroid = xrange[0] + (xrange[1] - xrange[0])*0.5

            if not fwhm is None:
                xrange = [centroid - 2*fwhm , centroid + 2*fwhm]

        ticket = beam._beam.histo1(col, xrange=xrange, nbins=nbins, nolost=1, ref=ref)

        if not ytitle is None:  ytitle = ytitle + ' weighted by ' + ShadowPlot.get_shadow_label(ref)

        histogram = ticket['histogram_path']
        bins = ticket['bin_path']*factor

        histogram_stats = ticket['histogram']
        bins_stats = ticket['bin_center']

        fwhm = ticket['fwhm']

        sigma = get_sigma(histogram_stats, bins_stats)*factor
        fwhm = sigma*2.35 if fwhm is None else fwhm*factor

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

        return HistogramData(histogram_stats, bins_stats, offset, xrange, fwhm, sigma, peak_intensity, integral_intensity)

    def add_empty_curve(self, histo_data):
        self.plot_canvas.addCurve(numpy.array([histo_data.get_centroid()]),
                                  numpy.zeros(1),
                                 "Click on curve to highlight it",
                                  xlabel="",
                                  ylabel="",
                                  symbol='',
                                  color='white')

        self.plot_canvas.setActiveCurve("Click on curve to highlight it")

from silx.gui.plot import Plot2D
from orangecontrib.shadow.util.shadow_util import ShadowPlot

class PowerPlotXYWidget(QWidget):
    
    def __init__(self, parent=None):
        pass
    
        super(QWidget, self).__init__(parent=parent)

        self.plot_canvas = None
        self.cumulated_power_plot = 0.0
        self.cumulated_previous_power_plot = 0.0

        self.setLayout(QVBoxLayout())

    def manage_empty_beam(self, ticket_to_add, nbins, xrange, yrange, var_x, var_y, cumulated_total_power, energy_min, energy_max, energy_step, show_image, to_mm):
        if not ticket_to_add is None:
            ticket      = copy.deepcopy(ticket_to_add)
            last_ticket = copy.deepcopy(ticket_to_add)
        else:
            ticket = {}
            ticket["histogram"] = numpy.zeros((nbins, nbins))
            ticket['intensity'] = numpy.zeros((nbins, nbins))
            ticket['nrays']     = 0
            ticket['good_rays'] = 0

            if not xrange is None and not yrange is None:
                ticket['bin_h_center'] = numpy.arange(xrange[0], xrange[1], nbins)*to_mm
                ticket['bin_v_center'] = numpy.arange(yrange[0], yrange[1], nbins)*to_mm
            else:
                raise ValueError("Beam is empty and no range has been specified: Calculation is impossible")

        self.plot_power_density_ticket(ticket, var_x, var_y, cumulated_total_power, energy_min, energy_max, energy_step, show_image)

        if not ticket_to_add is None:
            return ticket, last_ticket
        else:
            return ticket, None

    def plot_power_density(self, shadow_beam, var_x, var_y, total_power, cumulated_total_power, energy_min, energy_max, energy_step,
                           nbins=100, xrange=None, yrange=None, nolost=1, ticket_to_add=None, to_mm=1.0, show_image=True,
                           kind_of_calculation=0,
                           replace_poor_statistic=0,
                           good_rays_limit=100,
                           center_x = 0.0,
                           center_y = 0.0,
                           sigma_x=1.0,
                           sigma_y=1.0,
                           gamma=1.0):

        n_rays = len(shadow_beam._beam.rays[:, 0]) # lost and good!

        if n_rays == 0:
            return self.manage_empty_beam(ticket_to_add,
                                          nbins,
                                          xrange,
                                          yrange,
                                          var_x,
                                          var_y,
                                          cumulated_total_power,
                                          energy_min,
                                          energy_max,
                                          energy_step,
                                          show_image,
                                          to_mm)

        history_item = shadow_beam.getOEHistory(oe_number=shadow_beam._oe_number)

        previous_beam = None

        if shadow_beam.scanned_variable_data and shadow_beam.scanned_variable_data.has_additional_parameter("incident_power"):
            self.cumulated_previous_power_plot += shadow_beam.scanned_variable_data.get_additional_parameter("incident_power")
        elif not history_item is None and not history_item._input_beam is None:
            previous_ticket = history_item._input_beam._beam.histo2(var_x, var_y, nbins=nbins, xrange=None, yrange=None, nolost=1, ref=23)
            previous_ticket['histogram'] *= (total_power/n_rays) # power

            self.cumulated_previous_power_plot += previous_ticket['histogram'].sum()

        if nolost>1: # must be calculating only the rays the become lost in the last object
            current_beam = shadow_beam

            if history_item is None or history_item._input_beam is None:
                beam = shadow_beam._beam
            else:
                previous_beam = previous_beam if previous_beam else history_item._input_beam.duplicate(history=False)

                if nolost==2:
                    lost = numpy.where(current_beam._beam.rays[:, 9] != 1)

                    current_lost_rays = current_beam._beam.rays[lost]
                    lost_rays_in_previous = previous_beam._beam.rays[lost]

                    beam = Beam()
                    beam.rays = current_lost_rays[numpy.where(lost_rays_in_previous[:, 9] == 1)]# lost rays that were good after the previous OE
                else:
                    incident_rays = previous_beam._beam.rays
                    transmitted_rays = current_beam._beam.rays

                    incident_intensity = incident_rays[:, 6]**2  + incident_rays[:, 7]**2  + incident_rays[:, 8]**2 +\
                                         incident_rays[:, 15]**2 + incident_rays[:, 16]**2 + incident_rays[:, 17]**2
                    transmitted_intensity = transmitted_rays[:, 6]**2  + transmitted_rays[:, 7]**2  + transmitted_rays[:, 8]**2 +\
                                            transmitted_rays[:, 15]**2 + transmitted_rays[:, 16]**2 + transmitted_rays[:, 17]**2

                    electric_field = numpy.sqrt(incident_intensity - transmitted_intensity)
                    electric_field[numpy.where(electric_field == numpy.nan)] = 0.0

                    beam = Beam()
                    beam.rays = copy.deepcopy(shadow_beam._beam.rays)

                    beam.rays[:, 6]  = electric_field
                    beam.rays[:, 7]  = 0.0
                    beam.rays[:, 8]  = 0.0
                    beam.rays[:, 15] = 0.0
                    beam.rays[:, 16] = 0.0
                    beam.rays[:, 17] = 0.0
        else:
            beam = shadow_beam._beam

        if len(beam.rays) == 0:
            return self.manage_empty_beam(ticket_to_add,
                                          nbins,
                                          xrange,
                                          yrange,
                                          var_x,
                                          var_y,
                                          cumulated_total_power,
                                          energy_min,
                                          energy_max,
                                          energy_step,
                                          show_image,
                                          to_mm)

        ticket = beam.histo2(var_x, var_y, nbins=nbins, xrange=xrange, yrange=yrange, nolost=1 if nolost != 2 else 2, ref=23)

        ticket['bin_h_center'] *= to_mm
        ticket['bin_v_center'] *= to_mm

        bin_h_size = (ticket['bin_h_center'][1] - ticket['bin_h_center'][0])
        bin_v_size = (ticket['bin_v_center'][1] - ticket['bin_v_center'][0])

        if kind_of_calculation > 0:
            if replace_poor_statistic == 0 or (replace_poor_statistic==1 and ticket['good_rays'] < good_rays_limit):
                if kind_of_calculation == 1: # FLAT
                    PowerPlotXYWidget.get_flat_2d(ticket['histogram'], ticket['bin_h_center'], ticket['bin_v_center'])
                elif kind_of_calculation == 2: # GAUSSIAN
                    PowerPlotXYWidget.get_gaussian_2d(ticket['histogram'], ticket['bin_h_center'], ticket['bin_v_center'],
                                                       sigma_x, sigma_y, center_x, center_y)
                elif kind_of_calculation == 3: #LORENTZIAN
                    PowerPlotXYWidget.get_lorentzian_2d(ticket['histogram'], ticket['bin_h_center'], ticket['bin_v_center'],
                                                        gamma, center_x, center_y)
                # rinormalization
                ticket['histogram'] *= ticket['intensity']

        ticket['histogram'][numpy.where(ticket['histogram'] < 1e-9)] = 0.0
        ticket['histogram'] *= (total_power / n_rays)  # power

        if ticket_to_add == None:
            self.cumulated_power_plot = ticket['histogram'].sum()
        else:
            self.cumulated_power_plot += ticket['histogram'].sum()

        ticket['histogram'] /= (bin_h_size * bin_v_size)  # power density

        if not ticket_to_add is None:
            last_ticket = copy.deepcopy(ticket)

            ticket['histogram'] += ticket_to_add['histogram']
            ticket['intensity'] += ticket_to_add['intensity']
            ticket['nrays']     += ticket_to_add['nrays']
            ticket['good_rays'] += ticket_to_add['good_rays']

        self.plot_power_density_ticket(ticket, var_x, var_y, cumulated_total_power, energy_min, energy_max, energy_step, show_image)

        if not ticket_to_add is None:
            return ticket, last_ticket
        else:
            return ticket, None

    def plot_power_density_ticket(self, ticket, var_x, var_y, cumulated_total_power, energy_min, energy_max, energy_step, show_image=True):
        if show_image:
            histogram = ticket['histogram']

            average_power_density = numpy.average(histogram[numpy.where(histogram > 0.0)])

            title = "Power Density [W/mm\u00b2] from " + str(round(energy_min, 2)) + " to " + str(round(energy_max+energy_step, 2)) + " [eV], Current Step: " + str(round(energy_step, 2)) + "\n" + \
                    "Power [W]: Plotted=" + str(round(self.cumulated_power_plot, 2)) + \
                    ", Incident=" + str(round(self.cumulated_previous_power_plot, 2)) + \
                    ", Total=" + str(round(cumulated_total_power, 2)) + \
                    ", <P.D.>=" + str(round(average_power_density, 2)) + " W/mm\u00b2"

            xx = ticket['bin_h_center']
            yy = ticket['bin_v_center']

            if not isinstance(var_x, str): var_x = self.get_label(var_x)
            if not isinstance(var_y, str): var_y = self.get_label(var_y)

            ticket['h_label'] = var_x
            ticket['v_label'] = var_y

            self.plot_data2D(histogram, xx, yy, title, var_x, var_y)

    def get_label(self, var):
        if var == 1: return "X [mm]"
        elif var == 2: return "Y [mm]"
        elif var == 3: return "Z [mm]"

    def plot_data2D(self, data2D, dataX, dataY, title="", xtitle="", ytitle=""):
        if self.plot_canvas is None:
            self.plot_canvas = Plot2D()

            self.plot_canvas.resetZoom()
            self.plot_canvas.setXAxisAutoScale(True)
            self.plot_canvas.setYAxisAutoScale(True)
            self.plot_canvas.setGraphGrid(False)
            self.plot_canvas.setKeepDataAspectRatio(False)
            self.plot_canvas.yAxisInvertedAction.setVisible(False)

            self.plot_canvas.setXAxisLogarithmic(False)
            self.plot_canvas.setYAxisLogarithmic(False)
            self.plot_canvas.getMaskAction().setVisible(False)
            self.plot_canvas.getRoiAction().setVisible(False)
            self.plot_canvas.getColormapAction().setVisible(True)

        origin = (dataX[0],dataY[0])
        scale = (dataX[1]-dataX[0],dataY[1]-dataY[0])

        self.plot_canvas.addImage(numpy.array(data2D.T),
                                  legend="power",
                                  scale=scale,
                                  origin=origin,
                                  colormap={"name":"temperature", "normalization":"linear", "autoscale":True, "vmin":0, "vmax":0, "colors":256},
                                  replace=True)

        self.plot_canvas.setActiveImage("power")

        self.plot_canvas.setGraphXLabel(xtitle)
        self.plot_canvas.setGraphYLabel(ytitle)
        self.plot_canvas.setGraphTitle(title)

        self.plot_canvas.resetZoom()
        self.plot_canvas.setXAxisAutoScale(True)
        self.plot_canvas.setYAxisAutoScale(True)

        layout = self.layout()
        layout.addWidget(self.plot_canvas)
        self.setLayout(layout)

    def clear(self):
        if not self.plot_canvas is None:
            self.plot_canvas.clear()
            self.cumulated_power_plot = 0.0
            self.cumulated_previous_power_plot = 0.0

    @classmethod
    def get_flat_2d(cls, z, x, y):
        for i in range(len(x)):
            z[i, :] = 1

        norm = numpy.sum(z)
        z[:,:] /= norm

    @classmethod
    def get_gaussian_2d(cls, z, x, y, sigma_x, sigma_y, center_x=0.0, center_y=0.0):
        for i in range(len(x)):
            z[i, :] = numpy.exp(-1*(0.5*((x[i]-center_x)/sigma_x)**2 + 0.5*((y-center_y)/sigma_y)**2))

        norm = numpy.sum(z)
        z[:,:] /= norm

    @classmethod
    def get_lorentzian_2d(cls, z, x, y, gamma, center_x=0.0, center_y=0.0):
        for i in range(len(x)):
            z[i, :] = gamma/(((x[i]-center_x)**2 + (y-center_y)**2 + gamma**2))

        norm = numpy.sum(z)
        z[:,:] /= norm


if __name__=="__main__":

    x2 = numpy.linspace(-40e-6, 40e-6, 100)
    y2 = numpy.linspace(-40e-6, 40e-6, 100)

    x, y = numpy.meshgrid(x2, y2)
    z = numpy.ones((100, 100))

    #PowerPlotXYWidget.get_gaussian_2d(z, x2, y2, 1e-5, 2e-5)
    PowerPlotXYWidget.get_lorentzian_2d(z, x2, y2, 1.5e-6)
    #z = PowerPlotXYWidget.get_flat_2d(x2, y2)

    from matplotlib import pyplot as plt

    fig=plt.figure();
    ax=fig.add_subplot(111, projection='3d')
    surf=ax.plot_surface(x, y, z)

    plt.show()
