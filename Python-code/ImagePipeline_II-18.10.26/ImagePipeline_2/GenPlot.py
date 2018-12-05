#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct  5 09:22:07 2018

@author: mats_j
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import bokeh.plotting as bplt
import bokeh.models




class Figure():
    def __init__(self, nrows=1, ncols=1, sharex=False, linewidth=0.5):
        self.nrows = nrows
        self.ncols = ncols
        self.figure, self.axes = plt.subplots(nrows, ncols, squeeze=False, sharex=sharex)
        self.is_grid = False
        self.Savefig_dpi = 300
        self.set_linewidth = linewidth

    def plot(self, v1, v2=np.asarray([]), row=0, col=0):
        if v2.size:
            self.axes[row, col].plot(v1, v2, linewidth=self.set_linewidth)
        else:
            self.axes[row, col].plot(v1, linewidth=self.set_linewidth)
        self.axes[row, col].grid(self.is_grid)
        # plt.show()

    def plot_dot(self, v1, v2=np.asarray([]), row=0, col=0):
        if v2.size:
            self.axes[row, col].plot(v1, v2, 'o')
        else:
            self.axes[row, col].plot(v1, 'o')
        self.axes[row, col].grid(self.is_grid)
        # plt.show()

    def vert_line(self, x_positions, row=0, col=0):
        print('x_positions.shape', x_positions.shape)
        if np.isscalar(x_positions):
            self.axes[row, col].axvline(x_positions, color='r', linestyle='--', linewidth=self.set_linewidth )
        else:
            cmap = plt.get_cmap("tab10")
            for ci, x_pos in enumerate(x_positions):
                self.axes[row, col].axvline(x_pos, color=cmap(ci), linestyle='--', linewidth=self.set_linewidth )

    def legend(self, names, row=0, col=0):
        self.axes[row, col].legend(names)

    def xlabel(self, txt, row=0, col=0):
        self.axes[row, col].set_xlabel(txt)

    def ylabel(self, txt, row=0, col=0):
        self.axes[row, col].set_ylabel(txt)

    def grid(self, bool=True):
        self.is_grid = bool

    def main_title(self, txt):
        self.figure.suptitle(txt)

    def imshow(self, table, row=0, col=0):
        img_handle = self.axes[row, col].imshow(table) #, aspect="auto")
        if  (self.nrows < 2) and (self.ncols < 2):
            plt.colorbar(img_handle)

    def ms_plot(self, v1, v2, row=0, col=0):

        def squeeze_mat( a ):
            return np.squeeze( np.asarray( a ))

        self.axes[row, col].set_facecolor('w')
        y_baseline = np.zeros_like( v2 )
        self.axes[row, col].vlines( squeeze_mat( v1 ), squeeze_mat( y_baseline ),
                           squeeze_mat( v2 ), color='r', linestyles='solid',
                           linewidth=0.5)

    def save(self, Output_FileDir, FileName, title_suffix=''):
        basename_ext = os.path.basename(FileName)
        self.main_title(basename_ext+' '+title_suffix)
        if len(os.path.splitext(basename_ext)[1]) <= 4:
            basename_no_ext = os.path.splitext(basename_ext)[0]
        else: # There is point in the filename but longer extensions than 4 chars are less likely
           basename_no_ext = basename_ext
        fname = os.path.join(Output_FileDir, basename_no_ext+'_'+title_suffix+'.png')
        self.figure.savefig( fname, dpi=self.Savefig_dpi)
        plt.close(self.figure)

import bokeh.plotting as bplt
import bokeh.models
import webbrowser
bplt.output_file('temp.html')



class bkhFigure():
    def __init__(self, h=600, w=800):
        self.p = bplt.figure(width=w, height=h)
        self.p.xgrid.visible = False
        self.p.ygrid.visible = False


    def ms_plot(self, v1, v2):

        def squeeze_mat( a ):
            return np.squeeze( np.asarray( a ))

        if v1.ndim > 1:
            v1 = squeeze_mat(v1)
        if v2.ndim > 1:
            v2 = squeeze_mat(v2)

        if v1.ndim != 1 or v2.ndim != 1:
            print('Input vectors needs to be one dimensional, plot will be empty')
        else:
            mass_spec = {}
            mass_spec['MZ_tip'] = []
            mass_spec['magnitude'] = []
            mass_spec['x'] = []
            mass_spec['y'] = []

            for i in range(v1.shape[0]):
                mass_spec['x'].append([v1[i], v1[i]]) #every mass "stick" has two x in a list of sticks
                mass_spec['y'].append([0.0, v2[i]])       #every mass "stick" has the beginning of the stick at y=0 and the end at the y=value
                mass_spec['MZ_tip'].append(v1[i])
                mass_spec['magnitude'].append(v2[i])

            multi_line_source = bokeh.models.ColumnDataSource(mass_spec)
            hover_tool = bokeh.models.HoverTool(tooltips=[('m/z','@MZ_tip'), ('counts','@magnitude')])
            self.p.multi_line(xs='x', ys='y', line_width=1, line_color='red', source=multi_line_source)
            self.p.tools.append(hover_tool)


    def title(self, txt):
        titl_obj = bokeh.models.annotations.Title()
        titl_obj.text = txt
        self.p.title = titl_obj


    def xlabel(self, txt):
        self.p.xaxis.axis_label = txt

    def ylabel(self, txt):
        self.p.yaxis.axis_label = txt

    def grid(self, boolVal=True):
        self.p.xgrid.visible = boolVal
        self.p.ygrid.visible = boolVal


    def save(self, Output_FileDir, basename_ext, title_suffix=''):
        if title_suffix:
            self.title(title_suffix)
        basename_no_ext = os.path.splitext(basename_ext)[0]
        fname = os.path.join(Output_FileDir, basename_no_ext+'_'+title_suffix+'.html')
        output_file_name = os.path.join(Output_FileDir, fname)
        bplt.output_file(output_file_name)
        bplt.save(self.p, title=title_suffix)
        return output_file_name
