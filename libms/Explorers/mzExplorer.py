# -*- coding: utf-8 -*-

from PyQt4.QtGui import  (QVBoxLayout, QDialog, QLabel, QLineEdit,\
                          QPushButton, QHBoxLayout, QComboBox)

from PyQt4.QtCore import Qt, SIGNAL

import guidata
import os


from PlottingWidgets import RtPlotter, MzPlotter
import numpy as np

from ..gui.helpers import protect_signal_handler

class MzExplorer(QDialog):

    def __init__(self):
        QDialog.__init__(self)
        self.setWindowFlags(Qt.Window)
        # Destroying the C++ object right after closing the dialog box,
        # otherwise it may be garbage-collected in another QThread
        # (e.g. the editor's analysis thread in Spyder), thus leading to
        # a segmentation fault on UNIX or an application crash on Windows
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlags(Qt.Window)

    def setup(self, peakmap):
        self.processPeakmap(peakmap)
        self.setupPlotWidgets()
        self.setupInputWidgets()
        self.connectSignalsAndSlots()
        self.setupLayout()
        self.resetMzLimits()
        self.plotChromatogramm()
        self.plotMz()

    def processPeakmap(self, pm):
        levels = pm.getMsLevels()
        if len(levels) == 1 and levels[0]>1:
            self.levelNSpecs = []
        else:
            self.levelNSpecs = [ s for s in pm.spectra if s.msLevel > 1 ]

        self.peakmap = pm.getDominatingPeakmap()

        self.rts = np.array([s.rt for s in self.peakmap.spectra])

        mzvals = np.hstack([ spec.peaks[:,0] for spec in pm.spectra ])
        self.absMinMZ = np.min(mzvals)
        self.absMaxMZ = np.max(mzvals)
        self.minMZ = self.absMinMZ
        self.maxMZ = self.absMaxMZ
        self.updateChromatogram()

        title = os.path.basename(pm.meta.get("source", ""))
        self.setWindowTitle(title)

    def updateChromatogram(self):
        min_, max_ = self.minMZ, self.maxMZ
        cc =[np.sum(spec.peaks[(spec.peaks[:,0] >= min_)\
                              *(spec.peaks[:,0] <= max_)][:, 1])\
             for spec in self.peakmap.spectra]
        self.chromatogram = np.array(cc)

    def connectSignalsAndSlots(self):
        self.connect(self.selectButton, SIGNAL("clicked()"), self.selectButtonPressed)
        self.connect(self.resetButton, SIGNAL("clicked()"), self.resetButtonPressed)
        self.connect(self.inputW2, SIGNAL("textEdited(QString)"), self.w2Updated)
        self.connect(self.inputMZ, SIGNAL("textEdited(QString)"), self.mzUpdated)
        if self.chooseLevelNSpec:
            self.connect(self.chooseLevelNSpec, SIGNAL("activated(int)"), self.levelNSpecChosen)

    @protect_signal_handler
    def selectButtonPressed(self):
        mz  = float(self.inputMZ.text())
        w2  = float(self.inputW2.text())
        self.minMZ= mz-w2
        self.maxMZ= mz+w2
        self.updateChromatogram()
        self.plotChromatogramm()

    @protect_signal_handler
    def levelNSpecChosen(self, idx):
        if idx == 0:
            self.plotMz()
        else:
            spec = self.levelNSpecs[idx-1]
            self.mzPlotter.plot([spec.peaks])
            self.mzPlotter.resetAxes()
            self.mzPlotter.replot()
        self.rtPlotter.setEnabled(idx==0)

    @protect_signal_handler
    def resetButtonPressed(self):
        self.resetMzLimits()


    def resetMzLimits(self):
        self.minMZ = self.absMinMZ
        self.maxMZ = self.absMaxMZ

        self.updateChromatogram()
        self.plotChromatogramm()

    def setupLayout(self):
        vlayout = QVBoxLayout()
        self.setLayout(vlayout)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.labelMin)
        hlayout.addWidget(self.inputMZ)
        hlayout.addWidget(self.labelMax)
        hlayout.addWidget(self.inputW2)
        hlayout.addWidget(self.selectButton)
        hlayout.addWidget(self.resetButton)

        vlayout.addLayout(hlayout)

        vlayout.addWidget(self.rtPlotter.widget)
        if self.chooseLevelNSpec:
            vlayout.addWidget(self.chooseLevelNSpec)
        vlayout.addWidget(self.mzPlotter.widget)

    def setupInputWidgets(self):
        self.labelMin = QLabel("mz")
        self.labelMax = QLabel("w/2")
        self.inputMZ = QLineEdit()
        self.inputW2 = QLineEdit()
        self.selectButton = QPushButton()
        self.selectButton.setText("Select")
        self.resetButton = QPushButton()
        self.resetButton.setText("Reset")
        self.inputW2.setText("0.05")

        if len(self.levelNSpecs):
            self.chooseLevelNSpec = QComboBox()
            self.chooseLevelNSpec.addItem("Only Level 1 Spectra")
            for s in self.levelNSpecs:
                txt = "rt=%.2fm, level=%d" % (s.rt, s.msLevel)
                mzs = [ mz for (mz, I) in s.precursors ]
                precursors = ", ".join("%.6f" % mz for mz in mzs)
                if precursors:
                    txt += ", precursor mzs=[%s]" % precursors
                self.chooseLevelNSpec.addItem(txt)
        else:
            self.chooseLevelNSpec = None

    @protect_signal_handler
    def w2Updated(self, txt):
        self.mzPlotter.setHalfWindowWidth(float(txt))

    @protect_signal_handler
    def mzUpdated(self, txt):
        txt = str(txt)
        if txt.strip()=="":
            self.mzPlotter.setCentralMz(None)
            return
        self.mzPlotter.setCentralMz(float(txt))

    def handleCPressed(self, (mz, I)):
        self.inputMZ.setText("%.6f" % mz)

    def setupPlotWidgets(self):
        self.rtPlotter = RtPlotter(self.plotMz)
        self.mzPlotter = MzPlotter(self.handleCPressed)

        self.rtPlotter.setMinimumSize(600, 300)
        self.mzPlotter.setMinimumSize(600, 300)

        self.mzPlotter.setHalfWindowWidth(0.05)

    def plotChromatogramm(self):
        self.rtPlotter.plot([(self.rts, self.chromatogram)])
        self.rtPlotter.setXAxisLimits(self.rts[0], self.rts[-1])
        self.rtPlotter.setYAxisLimits(0, max(self.chromatogram)*1.1)
        self.rtPlotter.setRangeSelectionLimits(self.rts[0], self.rts[0])
        self.rtPlotter.replot()

    def plotMz(self):
        minRT = self.rtPlotter.minRTRangeSelected
        maxRT = self.rtPlotter.maxRTRangeSelected
        peaks = self.peakmap.ms1Peaks(minRT, maxRT)
        self.mzPlotter.resetAxes()
        self.mzPlotter.plot([peaks])
        self.mzPlotter.replot()


def inspectPeakMap(peakmap):
    """
    allows the visual inspection of a peakmap
    """

    if len(peakmap) == 0:
        raise Exception("empty peakmap")

    app = guidata.qapplication() # singleton !
    win = MzExplorer()
    win.setup(peakmap)
    win.raise_()
    win.exec_()
    del win.peakmap
    del win.levelNSpecs
    del win.rts


