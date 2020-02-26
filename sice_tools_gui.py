# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 18:51:39 2020

@author: Adrien Wehrlé, GEUS (Geological Survey of Denmark and Greenland)


"""


import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import rasterio
from rasterio.plot import show
import numpy as np
import scipy
import scipy.ndimage
import math
import pandas as pd
import urllib


class MainWindow(QMainWindow):
    def __init__(self):
        
        QMainWindow.__init__(self)

        self.title = 'SICE_tools_GUI'
        #dims = QDesktopWidget().screenGeometry(0)
        #self.setFixedSize(dims.width(), dims.height()) 
        self.left = 0
        self.top = 0
        #self.width = dims.width()
        #self.height = dims.height()
        self.width=1600
        self.height=900
        self.coords=[]
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        font = QFont()
        font.setPointSize(30)

        self.statusBar().showMessage('Ready')
        
        
        self.label = QLabel(self)
        url = 'https://i2.wp.com/snow.geus.dk/wp-content/uploads/GEUS.png?zoom=1.5&resize=166%2C204'
        front_img1= urllib.request.urlopen(url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(front_img1)
        self.label.setPixmap(pixmap)
        self.label.setGeometry((635+100)*self.width/1600, 450*self.height/900, 800*self.width/1600, 400*self.height/900)
        
        self.label2 = QLabel(self)
        url = 'https://i0.wp.com/snow.geus.dk/wp-content/uploads/cropped-Sentinel-3_over_Greenland-1.png?w=1200'
        front_img2= urllib.request.urlopen(url).read()
        pixmap = QPixmap()
        pixmap.loadFromData(front_img2)
        self.label2.setPixmap(pixmap)
        self.label2.setGeometry((100+100)*self.width/1600,160*self.height/900,1300*self.width/1600,400*self.height/900)
        
        self.label3 = QLabel(self)
        self.label3.setText('SICE tools GUI')
        self.label3.setGeometry((589+100)*self.width/1600,20*self.height/900,500*self.width/1600,300*self.height/900)
        self.label3.setFont(font)
        
        self.showMaximized()
        

        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)
        fileMenu = mainMenu.addMenu('File')
        showMenu = mainMenu.addMenu('View')
        toolsmenu = mainMenu.addMenu('Tools')
        createprofilemenu=toolsmenu.addMenu('Profile tool')
        helpMenu = mainMenu.addMenu('Help')
        
        helpinstructions = QAction('Help Contents', self)
        helpinstructions.setShortcut('Ctrl+H')
        helpinstructions.setStatusTip('Help Contents')
        helpinstructions.triggered.connect(self.open_new_dialog)
        helpMenu.addAction(helpinstructions)
        
        importraster = QAction('Import raster...', self)
        importraster.setShortcut('Ctrl+O')
        importraster.setStatusTip('Open raster')
        importraster.triggered.connect(self.file_open)
        fileMenu.addAction(importraster)
        
        exitButton = QAction(QIcon('exit24.png'), 'Exit...', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)
        
        showraster = QAction('Show raster...', self)
        showraster.setShortcut('Ctrl+R')
        showraster.setStatusTip('Show raster')
        showraster.triggered.connect(self.launch_plot)
        showMenu.addAction(showraster)
        

        createprofile = QAction('Select points...', self)
        createprofile.setShortcut('Ctrl+P')
        createprofile.setStatusTip('Select points')
        createprofile.triggered.connect(self.connect_figure)
        createprofilemenu.addAction(createprofile)
        
        clearprofile = QAction('Clear profile...', self)
        clearprofile.setShortcut('Ctrl+C')
        clearprofile.setStatusTip('Clear profile')
        clearprofile.triggered.connect(self.clear_profile)
        createprofilemenu.addAction(clearprofile)
        
        saveprofile = QAction('Save profile...', self)
        saveprofile.setShortcut('Ctrl+S')
        saveprofile.setStatusTip('Save profile')
        saveprofile.triggered.connect(self.save_profile)
        createprofilemenu.addAction(saveprofile)
            
            
    def file_open(self):
       # need to make name an tupple otherwise i had an error and app crashed
       global name
       name, _ = QFileDialog.getOpenFileName(self, 'Open File')
       
        
    def save_profile(self):
        name_to_save, _ = QFileDialog.getSaveFileName(self, 'Save File')
        xticks=np.arange(0,len(zi))*distance/len(zi)
        data_to_save=pd.DataFrame([xticks,zi]).T
        data_to_save.columns = ['meters', variable_name]
        data_to_save.to_csv(name_to_save)
       
       
    def launch_plot(self):
        widget =  QWidget(self)
        self.setCentralWidget(widget)
        vlay = QVBoxLayout(widget)
        # hlay = QHBoxLayout()
        # vlay.addLayout(hlay)
        # self.nameLabel = QLabel('Name:', self)
        # self.line = QLineEdit(self)
        # self.nameLabel2 = QLabel('Result', self)

        # hlay.addWidget(self.nameLabel)
        # hlay.addWidget(self.line)
        # hlay.addWidget(self.nameLabel2)
        # hlay.addItem(QSpacerItem(1000, 10, QSizePolicy.Expanding))
        # hlay2 = QHBoxLayout()
        # hlay2.addItem(QSpacerItem(1000, 10, QSizePolicy.Expanding))
        # vlay.addLayout(hlay2)
        m = WidgetPlot(self)
        vlay.addWidget(m)

        
    def select_points(self,event):
            # Only use event within the axes.
            if not event.inaxes == ax1:
                return
            global ix, iy
            ix, iy = event.xdata, event.ydata
            self.coords.append((ix, iy))
            print('x = %d, y = %d'%(
                  ix, iy))
            #ax1.scatter(self.coords[-1][0],self.coords[-1][1],'r')
            #disconnect if two points are given
            if len(self.coords) == 2:
                fig.canvas.mpl_disconnect(cid)
                self.profile()
                
    
    def connect_figure(self):
        global cid
        cid = fig.canvas.mpl_connect('button_press_event', self.select_points)
    
                
    def profile(self):
        
        data = rasterio.open(name)
        resolution=data.transform[0]
        rdata=data.read(1)
        #two points of the line as clicked
        x0, y0 = self.coords[0][0], self.coords[0][1] 
        x1, y1 = self.coords[1][0], self.coords[1][1]
        
        
        def calculateDistance(x1,y1,x2,y2):  
              dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)  
              return dist 
        
        global distance
        distance=calculateDistance(x0,y0,x1,y1)
        
        #100 times more points than resolution allows, just to be sure we get all of them before interpolation
        num = np.int(distance/resolution)*100
        
        #convert georeferenced coordinates to pixel numbers
        with data as src:
            x0_pix, y0_pix = rasterio.transform.rowcol(src.transform, x0, y0)
            x1_pix, y1_pix = rasterio.transform.rowcol(src.transform, x1, y1)
            
        x, y = np.linspace(x0_pix, x1_pix, num), np.linspace(y0_pix, y1_pix, num)
        
        # Extract the values along the line, using cubic interpolation
        #use indexing directly for nearest neighbor sampling
        global zi
        zi = scipy.ndimage.map_coordinates(rdata, np.vstack((x,y)))
        
        #-- Plot...
        #show((data, 1), interpolation='none', ax=ax)
        plt.ion()
        global ln
        ln=ax1.plot([x0, x1], [y0, y1], 'ro-')
        ax1.axis('image')
        global ax2
        ax2=fig.add_subplot(121)
        ax2.plot(zi,color='black')
        ax2.set_xlabel('Meters',fontsize=20)
        ax2.set_ylabel(variable_name,fontsize=20)
        fig.canvas.draw()
        fig.canvas.flush_events()
        
        
    def clear_profile(self):
        ln.pop(0).remove()
        fig.delaxes(ax2)
        fig.canvas.draw()
        fig.canvas.flush_events()
        self.coords=[]
        
    
    def open_new_dialog(self):
        self.nd = Help_window(self)
        self.nd.show()

    
class WidgetPlot(QWidget):
    def __init__(self,MainWindow, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        self.setLayout(QVBoxLayout())
        self.canvas = PlotCanvas(self, width=10, height=8)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas)

class PlotCanvas(FigureCanvas):
    def __init__(self, MainWindow,parent=None, width=10, height=8, dpi=100):
        global fig
        fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        global data
        data = rasterio.open(name)
        #assuming that a resolution <1 is associated with degrees
        #Ugly but temporary
        if data.res[0]<1:
            units='Degrees'
        else:
            units='Meters'
            
        global variable_name
        variable_name=name.split('/')[-1].split('.')[0]
        global ax1
        ax1 = self.figure.add_subplot(122)
        show((data, 1), interpolation='none', ax=ax1)
        ax1.set_title(variable_name,fontsize=20)
        ax1.set_xlabel(units,fontsize=20)
        ax1.set_ylabel(units,fontsize=20)
        self.draw()
        


class Help_window(QWidget):

    def __init__(self, text):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.label = QLabel("""Menus and actions currently implemented:
                            
            File:
                -"Import raster...": Imports a raster to the GUI (.tif, .img, .asc currently supported).
                -"Exit...": Quit the GUI.
                
            View:
                -"Show raster...": Display the raster conserving its projection.
                
            Tools:
                -"Profile tool": Create a 1D profile through the imported raster.
                    -"Select points...": Compute the profile based starting and ending points clicked by the user.
                    -"Save profile...": Save the resulting values and distance along profile in a .csv file.
                    -"Clear profile...": Delete the current profile to create a new one.
            
             Help:
                Help window to display this message.""")
        font = QFont()
        font.setPointSize(15)
        font.setBold(True)
        self.label.setFont(font)                               
        self.layout.addWidget(self.label)
        self.setWindowTitle("Help")
        self.setLayout(self.layout)
        

        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit( app.exec_())