"""
View portion of sample app
"""

import datetime
from itertools import izip_longest

from PyQt4 import Qt, QtGui, QtCore
import PyQt4.Qwt5 as Qwt


class TimeScaleDraw(Qwt.QwtScaleDraw):
    """Scale to display time values in month/year"""

    def label(self, value):
        """
        Convert time value into string-friendly label to be placed on a plot
        """

        super(TimeScaleDraw, self).label(value)

        date = datetime.datetime.fromtimestamp(value)
        return Qwt.QwtText((date.strftime("%b/%Y")))


class ProductionByMonthDialog(QtGui.QDialog):
    """Dialog to plot oil production by month"""

    def __init__(self, parent):
        """init"""

        super(ProductionByMonthDialog, self).__init__(parent)

        self._plot = Qwt.QwtPlot()

        self._plot.setCanvasBackground(QtCore.Qt.white)
        self._plot.setTitle("Oil Production for USA by Month")
        self._plot.setAxisTitle(Qwt.QwtPlot.xBottom, "Date")
        self._plot.setAxisTitle(Qwt.QwtPlot.yLeft, "Barrels (in thousands)")

        self._curve = Qwt.QwtPlotCurve("Barrels (in thousands)")
        self._curve.attach(self._plot)

        # Need custom scale to set labels to month/year
        self._plot.setAxisScaleDraw(Qwt.QwtPlot.xBottom, TimeScaleDraw())

        hlayout = QtGui.QHBoxLayout()
        hlayout.setMargin(0)
        hlayout.addWidget(self._plot)

        self.setLayout(hlayout)
        self.setWindowTitle('Production by month')

    def loadData(self, x_vals, y_vals):
        """Load data into plot"""

        self._curve.setData(x_vals, y_vals)
        self._plot.replot()


class FilterStateProductionDialog(QtGui.QDialog):
    """Dialog to filter production data in/out"""

    filter_range = QtCore.pyqtSignal(str, float, float)
    filter_max = QtCore.pyqtSignal(str, float)
    reset_values = QtCore.pyqtSignal(str)
    state_selected = QtCore.pyqtSignal(str)

    def __init__(self, states, parent=None):
        """init"""

        super(FilterStateProductionDialog, self).__init__(parent)

        self._main_layout = QtGui.QVBoxLayout()

        self._min_label = QtGui.QLabel('Min')
        self._max_label = QtGui.QLabel('Max')
        self._min_txtbox = QtGui.QLineEdit('')
        self._max_txtbox = QtGui.QLineEdit('')

        # Look QLabel supports rich-text/html!
        self._filter_by_max_label = QtGui.QLabel('<b>Filter Maximum:</b>')
        self._filter_range_label = QtGui.QLabel('<b>Filter Range:</b>')

        self._state_btns = []

        # Note that this is not exactly an 'optimal' or 'pretty' UI layout and
        # the filter widgets somewhat overlap in functionality.  However, it's
        # useful to see how more than 1 input widget can be used for this
        # demonstration.
        self._setup_state_radio_buttons(states)
        self._setup_filter_by_max_ui()
        self._setup_filter_by_range_ui()
        self._setup_button_ui()

        self.setLayout(self._main_layout)
        self.setWindowTitle('Filter state production')
        self.setMinimumHeight(240)
        self.setMinimumWidth(480)

    def _setup_state_radio_buttons(self, states):
        """Setup state radio buttons"""

        hlayout = QtGui.QHBoxLayout()

        for state in states:
            btn = QtGui.QRadioButton(state)
            self._state_btns.append(btn)
            btn.clicked.connect(self._state_selected)
            hlayout.addWidget(btn)

        self._main_layout.addLayout(hlayout)

    def _setup_filter_by_max_ui(self):
        """Setup ui for filtering by maximum"""

        # Visual separator for components
        frame = QtGui.QFrame()
        frame.setFrameShape(QtGui.QFrame.HLine)
        self._main_layout.addWidget(frame)

        # NOTE: PyQwt has some nice built-in widgets that matplotlib doesn't,
        # of course matplotlib has some nice plots PyQwt doesn't :)
        self._slider = Qwt.QwtSlider(self, Qt.Qt.Horizontal,
                                    Qwt.QwtSlider.BottomScale)
        self._slider.valueChanged.connect(self._slider_changed)

        self._main_layout.addWidget(self._filter_by_max_label)
        self._main_layout.addWidget(self._slider)

    def _setup_filter_by_range_ui(self):
        """Setup UI for filtering by range"""

        # Visual separator for components
        frame = QtGui.QFrame()
        frame.setFrameShape(QtGui.QFrame.HLine)
        self._main_layout.addWidget(frame)

        self._main_layout.addWidget(self._filter_range_label)

        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self._min_label)
        hlayout.addWidget(self._min_txtbox)
        self._main_layout.addLayout(hlayout)

        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self._max_label)
        hlayout.addWidget(self._max_txtbox)
        self._main_layout.addLayout(hlayout)

    def _setup_button_ui(self):
        """Setup button box"""

        btn_flags = (QtGui.QDialogButtonBox.Apply | QtGui.QDialogButtonBox.Reset)
        button_box = QtGui.QDialogButtonBox(btn_flags)
        button_box.button(Qt.QDialogButtonBox.Apply).clicked.connect(
                                                            self._filter_range)
        button_box.button(Qt.QDialogButtonBox.Reset).clicked.connect(
                                                                self._reset)
        button_box.button(Qt.QDialogButtonBox.Apply).setText('Filter Range')
        button_box.button(Qt.QDialogButtonBox.Reset).setText('Reset Filters')
        self._main_layout.addWidget(button_box)

    def show(self):
        """Show dialog"""

        super(FilterStateProductionDialog, self).show()

        # Default last one as first checked when shown so others can already
        # have their signals connected
        self._state_btns[-1].click()

    def _state_selected(self):
        """New state radio button clicked"""

        self.state_selected.emit(self._selected_state())

    def _reset(self):
        """Reset button clicked"""

        self.reset_values.emit(self._selected_state())

    def _slider_changed(self, val):
        """Slide changed to given val"""

        self.filter_max.emit(self._selected_state(), val)

    def filter_boundaries(self, min_val, max_val):
        """Setup the filter boundaries"""

        self._min_txtbox.setText(str(min_val))
        self._max_txtbox.setText(str(max_val))
        self._slider.setRange(min_val, max_val)
        # Show everything by default and filter from max to min
        self._slider.setValue(max_val)

    def _selected_state(self):
        """Get name of selected state radio button"""

        for btn in self._state_btns:
            if btn.isChecked():
                return str(btn.text())


    def _filter_range(self):
        """Filter values"""

        # FIXME: Should handle users entering data that cannot be converted to
        # float here
        self.filter_range.emit(self._selected_state(),
                               float(self._min_txtbox.text()),
                               float(self._max_txtbox.text()))


class StateProductionDialog(QtGui.QDialog):
    """Plot production by state"""

    def __init__(self, states, parent=None):
        """init"""

        super(StateProductionDialog, self).__init__(parent)

        self._plot = Qwt.QwtPlot()

        self._plot.setCanvasBackground(QtCore.Qt.white)
        self._plot.setTitle("Oil Production by State")
        self._plot.setAxisTitle(Qwt.QwtPlot.xBottom, "Date")
        self._plot.setAxisTitle(Qwt.QwtPlot.yLeft, "Barrels (in thousands)")
        self._plot.insertLegend(Qwt.QwtLegend())

        # Need custom scale to set labels to month/year
        self._plot.setAxisScaleDraw(Qwt.QwtPlot.xBottom, TimeScaleDraw())

        self._curves = {}
        colors = [QtCore.Qt.green, QtCore.Qt.black, QtCore.Qt.blue,
                  QtCore.Qt.red]

        for color, st in izip_longest(colors, states, fillvalue=QtCore.Qt.red):
            self._curves[st] = create_curve(st, color)
            self._curves[st].attach(self._plot)

        vlayout = QtGui.QVBoxLayout()
        vlayout.setMargin(0)
        vlayout.addWidget(self._plot)

        self.setLayout(vlayout)
        self.setWindowTitle('Oil production by state')

    def loadData(self, state, x_vals, y_vals):
        """Load data into plot"""

        self._curves[state].setData(x_vals, y_vals)
        self._plot.replot()


class MainWindow(QtGui.QMainWindow):
    """Main"""

    def __init__(self, states, parent=None):
        super(MainWindow, self).__init__(parent)

        self.month_prod_dialog = ProductionByMonthDialog(self)
        self.state_prod_dialog = StateProductionDialog(states, self)
        self.filter_dialog = FilterStateProductionDialog(states, self)

        self.month_prod_dialog.setGeometry(self.x(), self.y(), 800, 600)
        self.state_prod_dialog.setGeometry(self.x(), self.y(), 800, 600)

        self.setWindowTitle('Sample App')
        self.setCentralWidget(self.state_prod_dialog)

        self._file_menu = self.menuBar().addMenu('File')

        state_action = self._file_menu.addAction('Production by &Month')
        state_action.triggered.connect(self.month_prod_dialog.show)

        filter_action = self._file_menu.addAction('&Filter')
        filter_action.triggered.connect(self.filter_dialog.show)

    def show(self):
        """Show view"""

        self.state_prod_dialog.show()


def create_curve(title, color):
    """Helper to create a new curve with given data and color"""

    curve = Qwt.QwtPlotCurve(title)
    curve.setPen(QtGui.QPen(color))
    curve.setCurveType(Qwt.QwtPlotCurve.Yfx)
    curve.setStyle(Qwt.QwtPlotCurve.Lines)

    return curve
