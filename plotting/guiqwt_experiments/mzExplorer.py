# -*- coding: utf-8 -*-
#
# Copyright © 2009-2010 CEA
# Pierre Raybaut
# Licensed under the terms of the CECILL License
# (see guiqwt/__init__.py for details)

"""Simple filter testing application based on PyQt and guiqwt"""

SHOW = True # Show test in GUI-based test launcher

from PyQt4.QtGui import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDialog
from PyQt4.QtCore import SIGNAL

#---Import plot widget base class
from guiqwt.plot import CurveWidget, BaseCurveWidget, PlotManager, SubplotWidget
from guiqwt.builder import make
from guiqwt.curve import CurvePlot
from guiqwt.signals import SIG_RANGE_CHANGED
from guiqwt.shapes import XRangeSelection
from guidata.configtools import get_icon
from guiqwt.tools import *
#---
import numpy as np
import sys, cPickle
import new

sys.path.insert(0, "../../pyOpenMS")


class R(XRangeSelection):

    def __init__(self, min_, max_, xvals):
        super(R, self).__init__(min_, max_)
        self.xvals = np.array(xvals)

    def move_local_point_to(self, hnd, pos, ctrl=None):
        val = self.plot().invTransform(self.xAxis(), pos.x())
        self.move_point_to(hnd, (val, 0), ctrl)

    def move_point_to(self, hnd, pos, ctrl=None):
        val, y = pos
        imin = np.argmin(np.fabs(val-self.xvals))
        pos = self.xvals[imin], y
        print "move to ", pos[0]
        if self._min == self._max and not ctrl: 
            XRangeSelection.move_point_to(self, 0, pos, ctrl)
            XRangeSelection.move_point_to(self, 1, pos, ctrl)
        else:    
            XRangeSelection.move_point_to(self, hnd, pos, ctrl)

        self.plot().emit(SIG_RANGE_CHANGED, self, self._min, self._max)

        
    def move_shape(self, old_pos, new_pos):
        return

class MzSelectTool(InteractiveTool):
    """
    Graphical Object Selection Tool
    """
    TITLE = "mZ Selection"
    ICON = "selection.png"
    CURSOR = Qt.ArrowCursor


    def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre
        start_state = filter.new_state()
        # Bouton gauche :
        ObjectHandler(filter, Qt.LeftButton, start_state=start_state)
        ObjectHandler(filter, Qt.LeftButton, mods=Qt.ControlModifier,
                      start_state=start_state, multiselection=True)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Enter, Qt.Key_Return,)),

                         baseplot.do_enter_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)),
                         baseplot.do_space_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch(((Qt.Key_A, Qt.ControlModifier),)),
                         self.select_all_items, start_state)

        return setup_standard_tool_filter(filter, start_state)

    def select_all_items(self, filter, event):
        pass


class OnlyXZoomCurvePlot(CurvePlot):

    
    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """
        Change the scale of the active axes (zoom/dezoom) according to dx, dy
        dx, dy are tuples composed of (initial pos, dest pos)
        We try to keep initial pos fixed on the canvas as the scale changes
        """
   
        dy = dy[2],dy[2],dy[2],dy[3]
        return super(OnlyXZoomCurvePlot, self).do_zoom_view(dx, dy, lock_aspect_ratio)

    def do_pan_view(self, dx, dy):

        dy = dy[2],dy[2],dy[2],dy[3]

        return super(OnlyXZoomCurvePlot, self).do_pan_view(dx, dy)

    def do_space_pressed(self, filter, evt):

        for item in self.items:
            if isinstance(item, R):
                if item._min != item._max:
                    xmin, xmax, ymin, ymax= self.get_plot_limits() 
                    min_ = min(item._min, item._max)
                    max_ = max(item._min, item._max)
                    self.set_plot_limits(min_, max_, ymin, ymax)
                    self.replot()
        
    def do_enter_pressed(self, filter, evt):
        print filter, evt

        xmin, xmax, _, _ = self.get_plot_limits() 
        mid = (xmin+xmax)/2.0
        print mid
        
        for item in self.items:
            if isinstance(item, R):
                item.move_point_to(0, (mid, 0), None)
                item.move_point_to(1, (mid, 0), None)
                filter.plot.replot()
                
                
        


    
class TestWindow(QDialog):
    def __init__(self, peakmap):
        QDialog.__init__(self)
    
        self.peakmap = peakmap
        self.rts = np.array([ s.RT for s in self.peakmap ])
        self.chromatogram = np.array([ np.sum(spec.peaks[:,1]) for spec in peakmap])

        self.minRT = np.min(self.rts)
        self.maxRT = self.minRT

        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        self.widget1 = CurveWidget(xlabel="RT", ylabel="log I")
        self.widget2 = CurveWidget(xlabel="m/z", ylabel="log I")


        self.widget1.plot.__class__ = OnlyXZoomCurvePlot
        self.widget2.plot.__class__ = OnlyXZoomCurvePlot


        self.curve_item1 = make.curve([], [], color='b')
        self.curve_item2 = make.curve([], [], color='b', curvestyle="Sticks")

        self.widget1.plot.add_item(self.curve_item1)
        self.widget2.plot.add_item(self.curve_item2)


        self.pm = PlotManager(self.widget1)
        self.pm.add_plot(self.widget1.plot)
        self.pm.add_plot(self.widget2.plot)
        self.pm.set_default_plot(self.widget1.plot)

        t = self.pm.add_tool(MzSelectTool)
        self.pm.set_default_tool(t)
        t.activate()
        #self.pm.add_tool(RectZoomTool)
        #self.pm.register_standard_tools()

        range_ = R(self.minRT, self.maxRT, self.rts)
        self.widget1.plot.add_item(range_)

        def release(evt):
            self.updateMZ()
            
        self.widget1.plot.mouseReleaseEvent = release
        
        self.layout().addWidget(self.widget1)
        self.layout().addWidget(self.widget2)

        self.curve_item1.set_data(self.rts, self.chromatogram)
        self.curve_item1.plot().replot()

        self.updateMZ()
    
        self.connect(range_.plot(), SIG_RANGE_CHANGED, self.sighandler)

    def sighandler(self, obj, min_, max_):
        # right handle might be to the left of the left one !
        self.minRT, self.maxRT = sorted((min_, max_))
        self.updateMZ()

    def updateMZ(self):

        si = [ s for s in self.peakmap if self.minRT <= s.RT <=self.maxRT ]

        all_ = np.vstack((s.peaks for s in si))
        all_sorted = all_[np.argsort(all_[:,0]),:]

        self.curve_item2.set_data(all_sorted[:,0], all_sorted[:,1])

        self.curve_item2.plot().replot()
        
        

def test():
    """Testing this simple Qt/guiqwt example"""
    from PyQt4.QtGui import QApplication

    peakmap = cPickle.load(file("peakmap.pickled", "rb")) 
    
    app = QApplication([])
    win = TestWindow(peakmap)

    win.show()
    app.exec_()
        
        
if __name__ == '__main__':
    test()
    