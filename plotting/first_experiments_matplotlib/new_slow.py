
print "start"
import matplotlib.pyplot as plt
import numpy as np

print "modules loaded"

class SimplePlot:
    
    def __init__(self):

        self.fig = plt.figure()
        self.ax  = self.fig.add_subplot(111)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self.colors = "gg"
        self.plot()

    def plot(self):

        self.ax.plot(0, 1, self.colors[0]+"o", linewidth=5)
        self.ax.plot(1, 1, self.colors[1]+"o", linewidth=5)
        self.ax.axis([-1, 2, 0, 2])
        

    def on_motion(self, evt):
        if evt.xdata < 0.5:
            color_new = "rg"
        else:
            color_new = "gr"
        if color_new != self.colors:
            print "switch colors"
            self.colors = color_new
            self.plot()
            self.fig.canvas.draw()
            print "draw called"


sp=SimplePlot()
plt.show()

            
        





