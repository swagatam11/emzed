from exceptions import Exception
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QPainter
from guiqwt.curve import CurvePlot, CurveItem
from guiqwt.events import ObjectHandler, KeyEventMatch, setup_standard_tool_filter, QtDragHandler
from guiqwt.signals import SIG_MOVE, SIG_START_TRACKING, SIG_STOP_NOT_MOVING, SIG_STOP_MOVING, SIG_RANGE_CHANGED
from guiqwt.tools import InteractiveTool

from guiqwt.shapes import Marker, SegmentShape, XRangeSelection
import numpy as np


def memoize(function):
    """ decorator for caching results """
    memo = {}

    def wrapper(*args):
        if args in memo:
            return memo[args]
        else:
            rv = function(*args)
            memo[args] = rv
            return rv

    return wrapper


class ModifiedCurveItem(CurveItem):
    """ modification(s):
          selection (which plots a square at each (x,y) ) is turned off
    """

    def can_select(self):
        return False


class RtSelectionTool(InteractiveTool):
    """
        modified event handling:
            - enter, space, backspace, lift crsr and right crsr keys trigger handlers in baseplot
    """
    TITLE = "Rt Selection"
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
                         KeyEventMatch((Qt.Key_Right,)),
                         baseplot.do_right_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Left,)),
                         baseplot.do_left_pressed, start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace,)),
                         baseplot.do_backspace_pressed, start_state)

        return setup_standard_tool_filter(filter, start_state)


class MzSelectionTool(InteractiveTool):
     """
        modified event handling:
            - space and backspac keys trigger handlers in baseplot
            - calling handlers for dragging with mouse
     """

     TITLE = "mZ Selection"
     ICON = "selection.png"
     CURSOR = Qt.CrossCursor

     def setup_filter(self, baseplot):
        filter = baseplot.filter
        # Initialisation du filtre
        start_state = filter.new_state()
        # Bouton gauche :

        #start_state = filter.new_state()
        handler = QtDragHandler(filter, Qt.LeftButton, start_state=start_state)

        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Space,)),
                         baseplot.do_space_pressed, start_state)
        filter.add_event(start_state,
                         KeyEventMatch((Qt.Key_Backspace,)),
                         baseplot.do_backspace_pressed, start_state)

        self.connect(handler, SIG_MOVE, baseplot.move_in_drag_mode)
        self.connect(handler, SIG_START_TRACKING, baseplot.start_drag_mode)
        self.connect(handler, SIG_STOP_NOT_MOVING, baseplot.stop_drag_mode)
        self.connect(handler, SIG_STOP_MOVING, baseplot.stop_drag_mode)

        return setup_standard_tool_filter(filter, start_state)


class ModifiedCurvePlot(CurvePlot):
    """ modifications:
            - zooming preserves x asix at bottom of plot
            - panning is only in x direction
            - handler for backspace, called by RtSelectionTool and MzSelectionTool
    """

    def do_zoom_view(self, dx, dy, lock_aspect_ratio=False):
        """ modified do_zoom_view such that y=0 stays at bottom of plot """

        dy = dy[0], dy[1], self.transform(0, 0), dy[3]
        return super(ModifiedCurvePlot, self).do_zoom_view(dx, dy, lock_aspect_ratio)

    def do_pan_view(self, dx, dy):
        """ modified do_zoom_view such that only panning in x-direction happens """

        dy = dy[2], dy[2], dy[2], dy[3]
        return super(ModifiedCurvePlot, self).do_pan_view(dx, dy)


    def do_backspace_pressed(self, filter, evt):
        """ reset axes of plot """

        self.reset_x_limits()

    @memoize
    def get_items_of_class(self, clz):
        for item in self.items:
            if isinstance(item, clz):
                yield item

    @memoize
    def get_unique_item(self, clz):
        items = list(self.get_items_of_class(clz))
        if len(items) != 1:
            raise Exception("%d instance(s) of %s among CurvePlots items !" % (len(items), clz))
        return items[0]


    def reset_x_limits(self):
        xvals = []
        Delta = 0
        for item in self.items:
            if isinstance(item, CurveItem):
                x, _ = item.get_data()
                xvals.extend(list(x))

        xmin, xmax = min(xvals), max(xvals)
        self.update_plot_xlimits(xmin, xmax)

    def update_plot_xlimits(self, xmin, xmax):
        _, _, ymin, ymax = self.get_plot_limits()
        self.set_plot_limits(xmin, xmax, ymin, ymax)
        self.setAxisAutoScale(self.yLeft) # y-achse
        self.updateAxes()
        self.replot()


class RtPlot(ModifiedCurvePlot):
    """ modified behaviour:
            - space zooms to selected rt range
            - enter puts range marker to middle of currenct rt plot view
            - right crsr + left csrs + shift and alt modifiers move boundaries of selection tool
    """
    def do_space_pressed(self, filter, evt):
        """ zoom to limits of snapping selection tool """

        item = self.get_unique_item(SnappingRangeSelection)
        if item._min != item._max:
            min_neu = min(item._min, item._max)
            max_neu = max(item._min, item._max)
            self.update_plot_xlimits(min_neu, max_neu)

    def do_enter_pressed(self, filter, evt):
        """ set snapping selection tool to center of actual x-range """

        xmin, xmax, _, _ = self.get_plot_limits()
        mid = (xmin + xmax) / 2.0

        item = self.get_unique_item(SnappingRangeSelection)
        item.move_point_to(0, (mid, 0), None)
        item.move_point_to(1, (mid, 0), None)
        filter.plot.replot()

    def do_move_marker(self, evt):
        """ called when mouse moving over canvas.
            no extra actions in this plot
        """
        pass

    def move_selection_bounds(self, evt, filter_, selector):
        shift_pressed = evt.modifiers() == Qt.ShiftModifier
        alt_pressed = evt.modifiers() == Qt.AltModifier

        item = self.get_unique_item(SnappingRangeSelection)
        neu1 = neu0 = None
        if not alt_pressed:
            neu1 = selector(item.get_neighbour_xvals(item._max))
        if not shift_pressed:
            neu0 = selector(item.get_neighbour_xvals(item._min))

        _min, _max = sorted((item._min, item._max))
        if neu0 is not None and (neu0 <= _max or neu0 == neu1):
            item.move_point_to(0, (neu0, 0), True)
        if neu1 is not None and (neu1 >= _min or neu0 == neu1):
            item.move_point_to(1, (neu1, 0), True)

        filter_.plot.replot()

    def do_left_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_, lambda (a, b): a)

    def do_right_pressed(self, filter_, evt):
        self.move_selection_bounds(evt, filter_, lambda (a, b): b)


class MzPlot(ModifiedCurvePlot):

    """ modifications:
            - showing marker at peak next to mouse cursor
            - mouse drag handling for measuring distances between peaks
            - showing information about current peak and distances if in drag mode
    """

    def label_info(self, curve, x, y):
        # label next to cursor turned off:
        return None

    def on_plot(self, curve, x, y):
        """ callback for marker: determine marked point based on cursors coordinates """
        return self.next_peak_to(x, y)

    def next_peak_to(self, mz, I):
        item = self.get_unique_item(CurveItem)
        mzs, Is = item.get_data()
        # as xs and ys are on different scales we have to normalize distances
        mzmin, mzmax, Imin, Imax = self.get_plot_limits()
        mzs_scaled = (mzs - mz) / (mzmax - mzmin)
        Is_scaled  = (Is - I) / (Imax - Imin)
        distances = mzs_scaled ** 2 + Is_scaled ** 2
        imin = np.argmin(distances)
        return mzs[imin], Is[imin]

    def do_move_marker(self, evt):
        marker = self.get_unique_item(Marker)
        marker.move_local_point_to(0, evt.pos())
        marker.setVisible(True)
        self.replot()

    def do_space_pressed(self, filter, evt):
        """ finds 10 next (distance in mz) peaks tu current marker and zooms to them
        """

        mz = self.get_unique_item(Marker).xValue()
        mzs, _ = self.get_unique_item(CurveItem).get_data()

        isort = np.argsort(np.abs(mzs - mz))
        xsel = mzs[isort[:10]]
        xmin, xmax = np.min(xsel), np.max(xsel)

        self.update_plot_xlimits(xmin, xmax)

    def start_drag_mode(self, filter_, evt):
        mz = self.invTransform(self.xBottom, evt.x())
        I = self.invTransform(self.yLeft, evt.y())
        self.start_coord = self.next_peak_to(mz, I)

    def move_in_drag_mode(self, filter_, evt):
        mz = self.invTransform(self.xBottom, evt.x())
        I = self.invTransform(self.yLeft, evt.y())
        current_coord = self.next_peak_to(mz, I)

        line = self.get_unique_item(SegmentShape)
        line.set_rect(self.start_coord[0], self.start_coord[1], current_coord[0], current_coord[1])
        line.setVisible(1)

        self.replot()

    def stop_drag_mode(self, filter_, evt):
        line = self.get_unique_item(SegmentShape)
        line.setVisible(0)
        self.replot()



class ModifiedSegment(SegmentShape):
    """
        This is plottet as a line
        modifications are:
            - no point int the middle of the line
            - no antialising for the markers
    """

    def set_rect(self, x1, y1, x2, y2):
        """
        Set the start point of this segment to (x1, y1)
        and the end point of this line to (x2, y2)
        """
        # the original shape has a extra point in the middle
        # of the line, which is the last tuple, I moved this point to the beginning:

        self.set_points([(x1, y1), (x2, y2), (x1, y1)])

    def draw(self, painter, xMap, yMap, canvasRect):
        # code copied and rearanged such that line has antialiasing,
        # but symbols have not.
        pen, brush, symbol = self.get_pen_brush(xMap, yMap)

        painter.setPen(pen)
        painter.setBrush(brush)

        points = self.transform_points(xMap, yMap)
        if self.ADDITIONNAL_POINTS:
            shape_points = points[:-self.ADDITIONNAL_POINTS]
            other_points = points[-self.ADDITIONNAL_POINTS:]
        else:
            shape_points = points
            other_points = []

        for i in xrange(points.size()):
            symbol.draw(painter, points[i].toPoint())

        painter.setRenderHint(QPainter.Antialiasing)
        if self.closed:
            painter.drawPolygon(shape_points)
        else:
            painter.drawPolyline(shape_points)

        if self.LINK_ADDITIONNAL_POINTS and other_points:
            pen2 = painter.pen()
            pen2.setStyle(Qt.DotLine)
            painter.setPen(pen2)
            painter.drawPolyline(other_points)


class SnappingRangeSelection(XRangeSelection):

    """ modification:
            - only limit bars can be moved
            - snaps to given rt-values which are in general not equally spaced
    """

    def __init__(self, min_, max_, xvals):
        super(SnappingRangeSelection, self).__init__(min_, max_)

    def move_local_point_to(self, hnd, pos, ctrl=None):
        """ had to rewrite this function as the orginal does not give
            the ctrl parameter value to self.move_point_to method
        """
        val = self.plot().invTransform(self.xAxis(), pos.x())
        self.move_point_to(hnd, (val, 0), ctrl)

    def get_xvals(self):
        xvals = []
        for item in self.plot().get_items():
            if isinstance(item, CurveItem):
                xvals.append(np.array(item.get_data()[0]))

        return np.sort(np.hstack(xvals))

        # TODO: hit_test ?!?!??!

    def move_point_to(self, hnd, pos, ctrl=None):
        val, y = pos
        xvals = self.get_xvals()

        # modify pos to the next x-value
        # may be binary search for val in xvals ? -> cython
        #imin = np.searchsorted(xvals, val)
        imin = np.argmin(np.fabs(val-xvals))
        pos = xvals[imin], y

        if self._min == self._max and not ctrl:
            XRangeSelection.move_point_to(self, 0, pos, ctrl)
            XRangeSelection.move_point_to(self, 1, pos, ctrl)
        else:
            XRangeSelection.move_point_to(self, hnd, pos, ctrl)

        self.plot().emit(SIG_RANGE_CHANGED, self, self._min, self._max)

    def get_neighbour_xvals(self, x):
        """ used for moving boundaries """
    
        xvals = self.get_xvals()
        imin = np.argmin(np.fabs(x-xvals))
        if imin == 0: return xvals[0], xvals[1]
        if imin == len(xvals)-1 : return xvals[imin-1], xvals[imin]
        return xvals[imin-1], xvals[imin+1]

    def move_shape(self, old_pos, new_pos):
        # disabled, that is: do nothing !
        return