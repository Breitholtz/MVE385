# -*- coding: utf-8 -*-
"""
Created on Wed Dec 28 09:32:35 2016

@author: mats_j
"""
IPL_version = '2018-10-26'
#TODO Fix problem with name collisions of data sets in HySp cache when data is read from an again exported as unfolded data
#Done Add selection of number of components for PCA and NMF modelling

import os, sys, shutil, glob
import time
sys.path.append(".")#added changed ImagePipeline_II to ImagePipeline_2

if sys.version_info < (3,3):
    print('\nThis program was developed for running in at least Python 3.3' )
    print( os.path.basename(sys.argv[0]) +' was exited prematurely')
    exit()

import configparser
import numpy as np
import scipy
from PIL import Image

try:
    #print(sys.path)
    import Data_IO
    print('Loading development version of Data_IO')
except ImportError:
    import ImagePipeline_2.Data_IO as Data_IO
    #from ImagePipeline_2 import Data_IO

try:
    import MatDataIO
    print('Loading development version of MatDataIO')
except ImportError:
    import ImagePipeline_2.MatDataIO as MatDataIO

try:
    import GenPlot
    print('Loading development version of GenPlot')
except ImportError:
    import ImagePipeline_2.GenPlot as GenPlot

try:
    import hyperspectral_cache as hsc
    print('Loading development version of hyperspectral_cache')
except ImportError:
    import ImagePipeline_2.hyperspectral_cache as hsc

try:
    import PreProcFunctions as PreProc
    print('Loading development version of PreProcFunctions')
except ImportError:
    import ImagePipeline_2.PreProcFunctions as PreProc

try:
    import MVA_Lib
    print('Loading development version of MVA_Lib')
except ImportError:
    import ImagePipeline_2.MVA_Lib as MVA_Lib


import matplotlib
if sys.version_info >= (3,3) and sys.version_info <= (3,5):
    matplotlib.use('Qt4Agg')
    matplotlib.rcParams['backend.qt4']='PySide'

import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.backend_bases import key_press_handler
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
try:
    from matplotlib.backends import qt_compat
    print('Loading qt_compat from matplotlib.backends')
except ImportError:
    from matplotlib.backends import qt4_compat as qt_compat
    print('Loading qt4_compat from matplotlib.backends')

if sys.version_info >= (3,3) and  sys.version_info <= (3,5):
    import PySide.QtCore as QtCore
    import PySide.QtGui as QtGui
    import PySide.QtGui as QtWidgets
#    import PySide.QtGui as Side
elif sys.version_info > (3,5):
    import PyQt5.QtCore as QtCore
    import PyQt5.QtGui as QtGui
    import PyQt5.QtWidgets as QtWidgets
#    import PyQt5.QtWidgets as Side


##import PySide.QtGui as Side
#import PyQt5.QtCore as QtCore
##import PyQt5.QtGui as Side
#import PyQt5.QtGui
#import PyQt5.QtWidgets as Side
#import PyQt5.QtWidgets
import subprocess


#use_pyside = qt_compat.QT_API == qt_compat.QT_API_PYSIDE
#
#if not use_pyside:
#    print('Could not find QT4 compatible pyside backend')
#else:
#    import PySide.QtCore as QtCore
#    import PySide.QtGui as QtGui
#else:
#    import PyQt4.QtCore as QtCore
#    import PyQt4.QtGui as QtGui


def datetime_stamp():
    stamp = '%4d-%02d-%02d_%02d.%02d.%02d' % time.localtime()[:6]
    return stamp

def timestamped_filename( base_filename ):
    filename = base_filename+datetime_stamp()
    return filename


def squeeze_mat( a ):
    return np.squeeze( np.asarray( a ))

def neutralFunc(X):
    return X

def fourthRoot(X):
    return np.power(X, 1/4)

def log10_eps(X):
    eps = 0.5
    return np.log10(X+eps)

def invert_image(X):
    return -X


def toggle_selector(event):
    print(' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        print(' RectangleSelector deactivated.')
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        print(' RectangleSelector activated.')
        toggle_selector.RS.set_active(True)


class WorkThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        self.Script_strings = []

    def __del__(self):
        self.wait()

    def set_ScriptStrings(self, s):
        self.Script_strings = s

    def run(self):
        trace = False
#        self.Script_strings.append('python3')
#        self.Script_strings.append('/home/mats_j/ProgDev/Python3.4/Files2Script/Latest_version/Mk_log_output_for_test.py')
        p = subprocess.Popen(self.Script_strings, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0, universal_newlines=True)
        collected_stdout = []
        while True:
            line = p.stdout.readline()
            collected_stdout.append(line)
            if trace:
                print( 'Script log:', line) #, end='')

            self.emit( QtCore.SIGNAL("update01(QString)"), line )


            if ((line == "b''") or (line == '')) and p.poll() != None:
                self.emit( QtCore.SIGNAL("update02(QString)"), 'Finished' )
                if trace:
                    print( "Files2Script_3 WorkThread --- EndOfScript" )
                break
        return


class InpDataSetsQtModel(QtGui.QStandardItemModel):
    def __init__(self, parent=None):
        super(InpDataSetsQtModel, self).__init__(parent)
        self.setHorizontalHeaderLabels(["Image class","class label"])

    def AppendClassItem(self, class_num):
        self.last_item = QtGui.QStandardItem('Class '+str(class_num))
        self.appendRow([self.last_item])

    def AppendImageItem(self, DsetName):
        childItem = QtGui.QStandardItem(DsetName)
        self.last_item.appendRow(childItem)

    def AppendImageItems(self, InpDataSetNames):
        for DsetName in InpDataSetNames:
            self.AppendImageItem(DsetName)


class CustomTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(CustomTreeView, self).__init__(parent=parent)
        self.InpDataSetsStructure = InpDataSetsQtModel()
        self.setModel(self.InpDataSetsStructure)

    def currentItem(self, index):
        if self.InpDataSetsStructure.itemFromIndex(index).text()[0:6] == 'Class ':
            return None
        else:
            return self.InpDataSetsStructure.itemFromIndex(index)

    def AppendClass(self, InpDataSets, class_num=1):
        self.InpDataSetsStructure.AppendClassItem(class_num)
        self.InpDataSetsStructure.AppendImageItems( InpDataSets )

    def clear(self):
        self.InpDataSetsStructure.clear()



class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, fileName=None):
        super(MainWindow, self).__init__()
        self.init()

    def init(self):
        _DOCK_OPTS = QtWidgets.QMainWindow.AnimatedDocks
        _DOCK_OPTS |= QtWidgets.QMainWindow.AllowNestedDocks
        _DOCK_OPTS |= QtWidgets.QMainWindow.AllowTabbedDocks

        matplotlib_ver = matplotlib.__version__.split('.')
        self.is_matplotlib_v2 = (int(matplotlib_ver[0]) >= 2)
        if self.is_matplotlib_v2:
            plt.style.use('dark_background')

        self.createActions()
        self.createMenus()
        tab5_vbox = self.createTabGroupBox()

        self.view1_data = self.get_data_empty()
#        self.view1_slice_info = ''
        self.create_view_frame1()
        self.view1_draw()

        self.view2_data = self.get_data_empty()
#        self.view2_slice_info = ''
        self.create_view_frame2()
        self.view2_draw()
#        self.on_plot2()

        self.view3_data = self.get_data_empty()
#        self.view3_slice_info = ''
        self.create_view_frame3()
        self.view3_draw()

        self.view4_data = self.get_data_empty()
#        self.view4_data['image'] = self.get_color_data(self.view1_data, self.view2_data, self.view3_data)
#        self.view4_slice_info = ''
        self.create_view_frame4()
        self.view4_draw()

        self.view10_data = {}
#        self.view10_slice_info = ''
        self.create_view_frame10()
        self.on_draw10()

        self.ScriptLogText = QtWidgets.QTextEdit()
        self.ScriptLogText.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
        self.ScriptLogText.setMinimumWidth(300)
        self.PlotDummyText1 = QtWidgets.QTextEdit()
        self.PlotDummyText2 = QtWidgets.QTextEdit()
#        self.ScriptLogText.setPlainText("Log for the running script .....")
#        for log_num in range(50):
#            ScriptLogText.append('Logging item ' + str(log_num))

        self.view_frame5 = self.create_view_frame5(tab5_vbox)

        self.createStatusBar()
        self.setCentralWidget(self.tabGroupBox)
#        self.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks)
        self.setDockOptions(_DOCK_OPTS)


        self.DockScriptLog = QtWidgets.QDockWidget('Script log', objectName='dockobj_Script_log') #objectMame needed to save state
        DockView1 = QtWidgets.QDockWidget('View 1', objectName='dockobj_View_1')
        DockView2 = QtWidgets.QDockWidget('View 2', objectName='dockobj_View_2')
        DockView10 = QtWidgets.QDockWidget('Scatter plot', objectName='dockobj_View_10')
        DockView3 = QtWidgets.QDockWidget('View 3', objectName='dockobj_View_3')
        DockView4 = QtWidgets.QDockWidget('View 4', objectName='dockobj_View_4')
        DockView5 = QtWidgets.QDockWidget('Plot options', objectName='dockobj_View_5')

        self.DockScriptLog.setWidget(self.ScriptLogText)
#        DockWidget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
#        DockWidget.setMaximumWidth(350)

        DockView1.setWidget(self.view_frame1)
        DockView2.setWidget(self.view_frame2)
        DockView10.setWidget(self.view_frame10)
        DockView3.setWidget(self.view_frame3)
        DockView4.setWidget(self.view_frame4)
        DockView5.setWidget(self.view_frame5)
#        DockView1.dockLocationChanged.connect(self.On_DockWindowChange) # Tried to detect diffrent configuration of docked windows
                                                                         # but is also sensitive to main window resize

        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.DockScriptLog)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, DockView1, QtCore.Qt.Horizontal)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, DockView2, QtCore.Qt.Vertical)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, DockView10, QtCore.Qt.Horizontal)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, DockView3, QtCore.Qt.Horizontal)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, DockView4, QtCore.Qt.Horizontal)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, DockView5, QtCore.Qt.Horizontal)
#        self.splitDockWidget(DockView1, DockView2, QtCore.Qt.Horizontal)

        self.setCorner( QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea )

#        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, QtWidgets.QLabel('Script log:'))
        self.setWindowTitle('ImagePipeline II - '+IPL_version)
#        self.setMaximumWidth(350)

#TODO avoid reading settings if the soure is non-existent
        self.readSettings()

        self.MainSavedState = self.saveState() # Save the original state of all docking windows
        self.PreviousSavedState = self.saveState()

        self.ListOfFiles = []
        self.ListOfScriptInputFiles = []
        self.ListOfScripts = []
        self.ListOfScriptNames = []
        self.OutputRepository = Data_IO.DataRepository()

        # Automated placement and handling of cache files
        IPL_name = os.path.basename(os.path.splitext(sys.argv[0])[0])
        self.CacheFiles = Data_IO.TempFiles(IPL_name)
        self.auto_check_cachefiles()
        CacheFilePath = os.path.join( self.CacheFiles.get_location(), timestamped_filename('HySp_cache_')+'.hdf5')
        self.hysp_cache = hsc.HyperSpectralCache(CacheFilePath)

        self.threadPool = []
        self.CopyInputFiles = False
        self.is_import_ScriptOutput = False
        self.Class_number = 1
        self.Selection3_DataSetName = ''


        # Setup ConfigParser
#        self.FirstSelection = True
        self.config = configparser.ConfigParser(interpolation=None)
        self.appPath = os.path.abspath(os.path.dirname(os.path.join(sys.argv[0])))
#        self.inifile = os.path.join(self.appPath, "ImagePipeline_2.config")
        self.inifile = Data_IO.getConfigFile('ImagePipeline_2')

        if os.path.exists(self.inifile):
            self.config.read(self.inifile)
            self.is_ScriptParams_as_FileName = self.config.getboolean('Scripts','is_ScriptParams_as_FileName')

            self.ListOfScripts = eval(self.config.get('Scripts', 'ListOfScripts'))
            self.ActiveScriptCombo.clear()
            for ScriptFullFileName in self.ListOfScripts:
                ScriptBaseFileName = os.path.basename(ScriptFullFileName)
                if ScriptBaseFileName not in self.ListOfScriptNames:# avoid same name twice, newly loaded will come first
                    self.ListOfScriptNames.append( ScriptBaseFileName )
                    self.ActiveScriptCombo.addItem( ScriptBaseFileName )
            self.ActiveScriptCombo.setToolTip(self.ListOfScripts[self.ActiveScriptCombo.currentIndex()])

        else:
            self.is_ScriptParams_as_FileName = False
            self.config.add_section('FileLocation')
            self.config.set( 'FileLocation', 'CurrentInputFileLocation', self.appPath)
            self.config.set( 'FileLocation', 'CurrentScriptInputFileLocation', self.appPath)
            self.config.set( 'FileLocation', 'CurrentScriptFileLocation', self.appPath)
            self.config.set( 'FileLocation', 'CurrentAppendFileLocation', self.appPath)
            self.config.set( 'FileLocation', 'CurrentOutputFileLocation', self.appPath)
            self.config.add_section('Scripts')
            self.config.set( 'Scripts', 'SelectedScript', 'Undefined')
            self.config.set( 'Scripts', 'ListOfScripts', repr(['Undefined']) )
            self.config.set( 'Scripts', 'ScriptParameters', '')
            self.config.set( 'Scripts', 'is_ScriptParams_as_FileName', str(False))
            self.config.set( 'Scripts', 'LastUsedScript', '' )
            self.config.add_section('Input')
            self.config.set( 'Input', 'ListOfInput', repr([]) )
            self.config.set( 'Input', 'isCopyInput', str(False) )

            config_dir = os.path.dirname(self.inifile)
            Data_IO.make_dir_if_absent(config_dir)
            ConfigFile = open( self.inifile, mode='w')
            self.config.write(ConfigFile)
            ConfigFile.close()
        # End Setup ConfigParser




    def createMenus(self):
        self.fileMenu = self.menuBar().addMenu("&File")
#        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
#        self.fileMenu.addAction(self.appendAct)
#        self.fileMenu.addAction(self.openDirAct)
        self.fileMenu.addAction(self.clearAct)
#        self.fileMenu.addAction(self.openParamsAct)
#        self.fileMenu.addAction(self.clearParamsAct)
#        self.fileMenu.addAction(self.saveAct)
#        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addAction(self.openScriptInputFilesAct)
#        self.fileMenu.addAction(self.ImportFilesAct)
        self.ResultsSubMenu = self.fileMenu.addMenu("&Save Results...")
        self.ResultsSubMenu.addAction(self.save_pictures_to_RepositoryAct)
        self.fileMenu.addAction(self.exportUnfoldedAct)
        self.fileMenu.addAction(self.exportUnfolded_SelectionAct)

#        self.fileMenu.addSeparator()
#        self.fileMenu.addAction(self.closeAct)
        self.fileMenu.addAction(self.exitAct)

        self.scriptMenu = self.menuBar().addMenu("&Script")
        self.scriptMenu.addAction(self.openScriptAct)
        self.scriptMenu.addAction(self.runImportScriptAct)
        self.scriptMenu.addAction(self.runScriptAct)
        self.scriptMenu.addAction(self.runScript_DataToSourceAct)

        self.scriptMenu.addAction(self.reloadInputAct)

        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.addAction(self.reset_DockingGeometryAct)
        self.viewMenu.addAction(self.keep_DockingGeometryAct)

        self.settingsMenu = self.menuBar().addMenu("&Settings")
        self.settingsMenu.addAction(self.show_repository_location_SettingsAct)
        self.settingsMenu.addAction(self.set_repository_location_SettingsAct)

#        self.editMenu = self.menuBar().addMenu("&Edit")
#        self.editMenu.addAction(self.cutAct)
#        self.editMenu.addAction(self.copyAct)
#        self.editMenu.addAction(self.pasteAct)

        self.menuBar().addSeparator()

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
#        self.helpMenu.addAction(self.aboutQtAct)




    def createActions(self):
#        self.newAct = QtWidgets.QAction("&New",
#                self, shortcut=QtWidgets.QKeySequence.New,
#                statusTip="Create a new file", triggered=self.newFile)
#
        self.openAct = QtWidgets.QAction("&Open...", self, shortcut=QtGui.QKeySequence.Open,
                statusTip="Open existing file(s)", triggered=self.OpenFile)

#        self.appendAct = QtWidgets.QAction("&Append...", self,
#                statusTip="Append existing file(s)", triggered=self.AppendFile)
#
#        self.openDirAct = QtWidgets.QAction("&Open directory...", self,
#                statusTip="Open all files in directory tree", triggered=self.OpenDir)
#
        self.clearAct = QtWidgets.QAction("&Clear...", self,
                statusTip="Clear file list", triggered=self.ClearFileList)

        self.openScriptInputFilesAct = QtWidgets.QAction("Open files for &script input...", self,
                statusTip="Open file(s) as input to general and import scripts", triggered=self.openScriptInputFiles)

#        self.ImportFilesAct = QtWidgets.QAction("&Open script input...", self,
#                statusTip="Open file(s) as input to general and import scripts", triggered=self.ImportFiles)

        self.exportUnfoldedAct = QtWidgets.QAction("&Export unfolded images", self,
                statusTip="Export unfolded images in separate mat7.3 files", triggered=self.exportUnfolded)

        self.exportUnfolded_SelectionAct = QtWidgets.QAction("Export unfolded selected spectra", self,
                statusTip="Export unfolded spectra from image into mat7.3 file", triggered=self.exportUnfolded_Selected)

        self.save_pictures_to_RepositoryAct = QtWidgets.QAction("&Save View 1 dataset pictures to repository", self,
                statusTip="save_pictures from hyperspectral image to the Repository", triggered=self.save_pictures_to_Repository)

#
#        self.openParamsAct = QtWidgets.QAction("&Open param file...", self,
#                statusTip="Open file with parameters to script", triggered=self.OpenParamFile)
#
#        self.clearParamsAct = QtWidgets.QAction("&Clear parameters", self,
#                statusTip="Clear previously entered parameters", triggered=self.ClearParams)

        self.reloadInputAct = QtWidgets.QAction("&Reload previous input", self,
                statusTip="Reload previous Input files and parameters", triggered=self.ReloadPreviousScriptInputSelections)

        self.runScriptAct = QtWidgets.QAction("&Run script", self,
                statusTip="Run open script", triggered=self.RunScript)

        self.runScript_DataToSourceAct = QtWidgets.QAction("&Run script - data to source location", self,
                statusTip="Run open script and put output data in the source location", triggered=self.RunScript_w_data2source)

        self.runImportScriptAct = QtWidgets.QAction("&Run import", self,
                statusTip="Run import script", triggered=self.RunImportScript)

        self.openScriptAct = QtWidgets.QAction("&Open script", self,
                statusTip="Open existing script", triggered=self.OpenScript)

        self.reset_DockingGeometryAct = QtWidgets.QAction("&Reset docking windows", self,
                statusTip="Put the docking windows in their starting positions", triggered=self.reset_docking_windows)

        self.keep_DockingGeometryAct = QtWidgets.QAction("&Keep docking windows configuration", self,
                statusTip="Keep the present postions of the docking windows", triggered=self.keep_docking_windows_configuration)

        self.show_repository_location_SettingsAct = QtWidgets.QAction("&Show data repository location", self,
                statusTip="Show the location of the  data repository", triggered=self.show_data_repository)

        self.set_repository_location_SettingsAct = QtWidgets.QAction("&Set data repository location", self,
                statusTip="Set the location of the data repository", triggered=self.set_data_repository)
#
#        self.saveAct = QtWidgets.QAction("&Save", self, shortcut=QtWidgets.QKeySequence.Save,
#                statusTip="Save the document to disk", triggered=self.save)
#
#        self.saveAsAct = QtWidgets.QAction("Save &As...", self,
#                shortcut=QtWidgets.QKeySequence.SaveAs,
#                statusTip="Save the document under a new name",
#                triggered=self.saveAs)
#
#        self.closeAct = QtWidgets.QAction("&Close", self, shortcut="Ctrl+W",
#                statusTip="Close this window", triggered=self.close)

        self.exitAct = QtWidgets.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application",
                triggered=QtWidgets.qApp.closeAllWindows)
#
#        self.cutAct = QtWidgets.QAction("Cu&t",
#                self, enabled=False, shortcut=QtWidgets.QKeySequence.Cut,
#                statusTip="Cut the current selection's contents to the clipboard",
#                triggered=self.textEdit.cut)
#
#        self.copyAct = QtWidgets.QAction("&Copy", self, enabled=False, shortcut=QtWidgets.QKeySequence.Copy,
#                statusTip="Copy the current selection's contents to the clipboard",
#                triggered=self.textEdit.copy)
#
#        self.pasteAct = QtWidgets.QAction("&Paste", self, shortcut=QtWidgets.QKeySequence.Paste,
#                statusTip="Paste the clipboard's contents into the current selection",
#                triggered=self.textEdit.paste)

        self.aboutAct = QtWidgets.QAction("&About", self,
                statusTip="Show the application's About box",
                triggered=self.about)

#        self.aboutQtAct = QtWidgets.QAction("About &Qt", self,
#                statusTip="Show the Qt library's About box",
#                triggered=QtWidgets.qApp.aboutQt)

#        self.textEdit.copyAvailable.connect(self.cutAct.setEnabled)
#        self.textEdit.copyAvailable.connect(self.copyAct.setEnabled)





    def createStatusBar(self):
        self.statusText = QtWidgets.QLabel("Ready")
        self.statusBar().addWidget(self.statusText, 1)

    def about(self):
        QtWidgets.QMessageBox.about(self, "About Files",
                "<b>ImagePipeline II</b> is a GUI to read, convert, view, and process hyperspectral images. "
                "Processing is done by selectable Python scripts. "
                "The output will be placed in a Data_repository that has to be set once "
                "before scripts can be executed.\n Version: "+str(IPL_version)+" /Mats Josefson")


    def createTabGroupBox(self):
        self.tabGroupBox = QtWidgets.QGroupBox()

        self.tab_widget_01 = QtWidgets.QTabWidget()
        tab0 = QtWidgets.QWidget()
        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()
        tab3 = QtWidgets.QWidget()
        tab4 = QtWidgets.QWidget()
        self.tab5 = QtWidgets.QWidget()

        tab0_vbox = QtWidgets.QVBoxLayout(tab0)
        tab1_vbox = QtWidgets.QVBoxLayout(tab1)
        tab2_vbox = QtWidgets.QVBoxLayout(tab2)
        tab3_vbox = QtWidgets.QVBoxLayout(tab3)
        tab4_vbox = QtWidgets.QVBoxLayout(tab4)
        tab5_vbox = QtWidgets.QVBoxLayout(self.tab5)

        """ Data tab """
        self.InpDataSetsListBox = QtWidgets.QListWidget()
        self.InpDataSetsListBox.itemClicked.connect(self.OnInpDataSetsListBox_ItemClicked)
        self.InpDataSetsTreeView = CustomTreeView()
        self.InpDataSetsTreeView.clicked.connect(self.OnInpDataSetsTreeView_ItemClicked)
        self.NumOfFilesLineEdit_tab0 = QtWidgets.QLineEdit()
        self.NumOfFilesLineEdit_tab0.setReadOnly(True)
        self.NumOfFilesLineEdit_tab0.setText(str(0)+' input files')
        Split_button1 = QtWidgets.QPushButton("Split images")
        Split_button1.clicked.connect(self.OnSplit_Images)
        tab0_vbox.addWidget(self.InpDataSetsListBox)
        tab0_vbox.addWidget(self.InpDataSetsTreeView)
        tab0_vbox.addWidget(self.NumOfFilesLineEdit_tab0)
        tab0_vbox.addStretch(1)
        tab0_vbox.addWidget(Split_button1)

        """ View tab """
        tab1_hbox = QtWidgets.QHBoxLayout()
        view01_vbox = QtWidgets.QVBoxLayout()
        view02_vbox = QtWidgets.QVBoxLayout()
        view03_vbox = QtWidgets.QVBoxLayout()
        self.SliceListBox01 = QtWidgets.QListWidget()
        self.SliceListBox01.currentRowChanged.connect(self.OnSliceListBox01_update)
        self.SliceListBox02 = QtWidgets.QListWidget()
        self.SliceListBox02.currentRowChanged.connect(self.OnSliceListBox02_update)
        self.SliceListBox03 = QtWidgets.QListWidget()
        self.SliceListBox03.currentRowChanged.connect(self.OnSliceListBox03_update)
        self.ActiveData01_Combo = QtWidgets.QComboBox()
        self.ActiveData01_Combo.currentIndexChanged.connect(self.OnActiveData01_changed)
        self.ActiveData02_Combo = QtWidgets.QComboBox()
        self.ActiveData02_Combo.currentIndexChanged.connect(self.OnActiveData02_changed)
        self.ActiveData03_Combo = QtWidgets.QComboBox()
        self.ActiveData03_Combo.currentIndexChanged.connect(self.OnActiveData03_changed)
        self.Color01_Combo = QtWidgets.QComboBox()
        self.Color02_Combo = QtWidgets.QComboBox()
        self.Color03_Combo = QtWidgets.QComboBox()
        self.Colors = ['no color', 'red', 'green', 'blue']
        self.Color01_Combo.addItems(self.Colors)
        self.Color02_Combo.addItems(self.Colors)
        self.Color03_Combo.addItems(self.Colors)
        self.Color01_Combo.setCurrentIndex(1)
        self.Color02_Combo.setCurrentIndex(2)
        self.Color03_Combo.setCurrentIndex(3)
        self.Color01_Combo.currentIndexChanged.connect(self.OnColor_changed)
        self.Color02_Combo.currentIndexChanged.connect(self.OnColor_changed)
        self.Color03_Combo.currentIndexChanged.connect(self.OnColor_changed)

        view01_hdr = QtWidgets.QHBoxLayout()
        view01_hdr.addWidget(QtWidgets.QLabel('View 1'))
        view01_hdr.addStretch(1)
        self.chained_ActiveData01 = QtWidgets.QCheckBox(chr(0x1F512))
        self.chained_ActiveData01.stateChanged.connect(self.OnActiveData_SyncChange)
        self.chained_ActiveData01.setToolTip('Select chained or unchained selection of dataset for viewing')
        view01_hdr.addWidget(self.chained_ActiveData01)

        view02_hdr = QtWidgets.QHBoxLayout()
        view02_hdr.addWidget(QtWidgets.QLabel('View 2'))
        view02_hdr.addStretch(1)
        self.chained_ActiveData02 = QtWidgets.QCheckBox(chr(0x1F512))
        self.chained_ActiveData02.setToolTip('Select chained or unchained selection of dataset for viewing')
        self.chained_ActiveData02.setEnabled(False)
        view02_hdr.addWidget(self.chained_ActiveData02)

        view03_hdr = QtWidgets.QHBoxLayout()
        view03_hdr.addWidget(QtWidgets.QLabel('View 3'))
        view03_hdr.addStretch(1)
        self.chained_ActiveData03 = QtWidgets.QCheckBox(chr(0x1F512))
        self.chained_ActiveData03.setToolTip('Select chained or unchained selection of dataset for viewing')
        self.chained_ActiveData03.setEnabled(False)
        view03_hdr.addWidget(self.chained_ActiveData03)
        self.chained_ActiveData01.setCheckState(QtCore.Qt.Checked)

#        view01_vbox.addWidget(QtWidgets.QLabel('View 1'))
        view01_vbox.addLayout(view01_hdr)
        view01_vbox.addWidget(self.ActiveData01_Combo)
        view01_vbox.addWidget(self.Color01_Combo)
        view01_vbox.addWidget(self.SliceListBox01)

#        view02_vbox.addWidget(QtWidgets.QLabel('View 2'))
        view02_vbox.addLayout(view02_hdr)
        view02_vbox.addWidget(self.ActiveData02_Combo)
        view02_vbox.addWidget(self.Color02_Combo)
        view02_vbox.addWidget(self.SliceListBox02)

#        view03_vbox.addWidget(QtWidgets.QLabel('View 3'))
        view03_vbox.addLayout(view03_hdr)
        view03_vbox.addWidget(self.ActiveData03_Combo)
        view03_vbox.addWidget(self.Color03_Combo)
        view03_vbox.addWidget(self.SliceListBox03)

        view_settings_hbox1 = QtWidgets.QHBoxLayout()
        view_settings_hbox1.addWidget(QtWidgets.QLabel('Lists order'))
        self.ListsOrder_Combo = QtWidgets.QComboBox()
        self.SortOrders = ['original', 'sum magnitude', 'max magnitude']
        self.ListsOrder_Combo.addItems(self.SortOrders)
        view_settings_hbox1.addWidget(self.ListsOrder_Combo)
        self.ListsOrder_Combo.currentIndexChanged.connect(self.OnViewListSorting_changed)

        view_settings_hbox2 = QtWidgets.QHBoxLayout()
        self.PixInterp_Combo = QtWidgets.QComboBox()
        self.PixInterp_Combo.addItems(['bicubic', 'bilinear', 'gaussian', 'nearest', 'none'])
        view_settings_hbox2.addWidget(QtWidgets.QLabel('pixel interpolation'))
        view_settings_hbox2.addWidget(self.PixInterp_Combo)

        view_settings_hbox3 = QtWidgets.QHBoxLayout()
        self.MakeClassesButton = QtWidgets.QPushButton('Make classes')
        self.MakeClassesButton.clicked.connect(self.OnMakeClasses)

        self.ClassColors_Combo = QtWidgets.QComboBox()
        view_settings_hbox3.addWidget(self.MakeClassesButton)
        view_settings_hbox3.addWidget(QtWidgets.QLabel('# colored classes'))
        view_settings_hbox3.addWidget(self.ClassColors_Combo)

        tab1_hbox.addLayout(view01_vbox)
        tab1_hbox.addLayout(view02_vbox)
        tab1_hbox.addLayout(view03_vbox)
        tab1_vbox.addLayout(tab1_hbox)
        tab1_vbox.addLayout(view_settings_hbox1)
        tab1_vbox.addLayout(view_settings_hbox2)
        tab1_vbox.addLayout(view_settings_hbox3)

        """ Method tab """
        tab2_hbox = QtWidgets.QHBoxLayout()
        method01_vbox = QtWidgets.QVBoxLayout()
        method02_vbox = QtWidgets.QVBoxLayout()

        method01_vbox.addWidget(QtWidgets.QLabel('Method settings'))
        method01_vbox.addWidget(QtWidgets.QLabel('Binning power 0,1,2...: 2^0'+chr(0x2192)+'1 pixel, 2^1'+chr(0x2192)+'4 pixels, 2^2'+chr(0x2192)+'16 pixels, etc.'))
        self.SetBinning_Spin = QtWidgets.QSpinBox()
        self.SetBinning_Spin.setMinimum(0)
        method01_vbox.addWidget(self.SetBinning_Spin)
        method01_vbox.addStretch(1)

        method02_vbox.addWidget(QtWidgets.QLabel('-'))

        tab2_hbox.addLayout(method01_vbox)
        tab2_hbox.addLayout(method02_vbox)
        tab2_vbox.addLayout(tab2_hbox)

        """"Model tab"""
        model01_hbox = QtWidgets.QHBoxLayout()
        model01_hbox.addWidget(QtWidgets.QLabel('Pre-processing'))
        self.PreProcSelector_Combo = QtWidgets.QComboBox()
        self.PreProcSelector_Combo.addItems(['None', 'Norm_by_Sdev (SNV part 2)', 'Poisson scaling'])
        model01_hbox.addWidget(self.PreProcSelector_Combo)

        model02_hbox = QtWidgets.QHBoxLayout()
        model02_hbox.addWidget(QtWidgets.QLabel('Variable scaling'))
        self.VarScale_Combo = QtWidgets.QComboBox()
        self.VarScale_Combo.addItems(['Center','None'])
        model02_hbox.addWidget(self.VarScale_Combo)

        model03_hbox = QtWidgets.QHBoxLayout()
        model03_hbox.addWidget(QtWidgets.QLabel('Model type'))
        self.ModelSelector_Combo = QtWidgets.QComboBox()
        self.ModelSelector_Combo.addItems(['PCA', 'Non-neg matrix factorization'])
        self.ModelSelector_Combo.currentIndexChanged.connect(self.OnModelChange)
        model03_hbox.addWidget(self.ModelSelector_Combo)

        model04_hbox = QtWidgets.QHBoxLayout()
        model04_hbox.addWidget(QtWidgets.QLabel('Model components'))
        self.ModelComponents = QtWidgets.QSpinBox()
        self.ModelComponents.setRange(1, 70)
        self.ModelComponents.setValue(4)
        self.ModelComponents.setToolTip('The number of model components needs attention as there is currently no automated stopping criterion employed')
        model04_hbox.addWidget(self.ModelComponents)

        model05_hbox = QtWidgets.QHBoxLayout()
        self.MakeModelButton = QtWidgets.QPushButton("&Make", self)
        model05_hbox.addWidget(self.MakeModelButton)
        self.MakeModelButton.setToolTip('Make one MVA model for each loaded image according to the selections above')
        self.MakeModelButton.clicked.connect(self.OnMakeModel)

        tab3_vbox.addLayout(model01_hbox)
        tab3_vbox.addLayout(model02_hbox)
        tab3_vbox.addLayout(model03_hbox)
        tab3_vbox.addLayout(model04_hbox)
        tab3_vbox.addLayout(model05_hbox)
        tab3_vbox.addStretch(1)


        """ Script tab """
        self.ActiveScriptCombo = QtWidgets.QComboBox()
        self.ActiveScriptCombo.addItem('Undefined')
        self.ActiveScriptCombo.currentIndexChanged.connect(self.OnActiveScriptChange)
        ScriptParams = QtWidgets.QLabel('Script parameters:')
        self.ScriptParamsLineEdit = QtWidgets.QLineEdit()
        self.ScriptParamsLineEdit.textChanged.connect(self.OnScriptParamsChange)
        self.NumOfFilesLineEdit_tab4 = QtWidgets.QLineEdit()
        self.NumOfFilesLineEdit_tab4.setReadOnly(True)
        self.NumOfFilesLineEdit_tab4.setText(str(0)+' input files')
        self.InpFilesListBox = QtWidgets.QListWidget()
        self.InpFilesListBox.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.RunImportButton = QtWidgets.QPushButton("Run import script", self)
        self.RunImportButton.setToolTip('Run a script beginning with "Import" in the name with the files \npresent in the list box as input.')
        self.RunImportButton.clicked.connect(self.RunImportScript)
        self.RunButton = QtWidgets.QPushButton("&Run general script", self)
        self.RunButton.setToolTip('Run the active non-import script with the files \npresent in the list box as input.')
        self.RunButton.clicked.connect(self.RunScript)

        tab4_vbox.addWidget(self.ActiveScriptCombo)
        tab4_vbox.addWidget(ScriptParams)
        tab4_vbox.addWidget(self.ScriptParamsLineEdit)

        tab4_vbox.addWidget(self.NumOfFilesLineEdit_tab4)
        tab4_vbox.addWidget(self.InpFilesListBox)
        tab4_vbox.addWidget(self.RunImportButton)
        tab4_vbox.addWidget(self.RunButton)


        """ Plot options tab """
        Option01_hbox = QtWidgets.QHBoxLayout()
        Option01_hbox.addWidget(QtWidgets.QLabel('Image scales'))
        self.ImgScales_Combo = QtWidgets.QComboBox()
        self.ImgScales_Combo.addItems(['Individual', 'Same for all'])
        Option01_hbox.addWidget(self.ImgScales_Combo)
        tab5_vbox.addLayout(Option01_hbox)

        Option02_hbox = QtWidgets.QHBoxLayout()
        Option02_hbox.addWidget(QtWidgets.QLabel('Color map'))
        self.ColorMap_Combo = QtWidgets.QComboBox()
        self.ColorMap_Combo.addItems(['viridis', 'hot', 'seismic', 'magma', 'gray'])
        self.highlightColor = {}
        self.highlightColor['viridis'] = 'magenta'
        self.highlightColor['hot'] = 'lightgreen'
        self.highlightColor['seismic'] = 'lightgreen'
        self.highlightColor['magma'] = 'lightgreen'
        self.highlightColor['gray'] = 'lightgreen'
        self.missingColor = {}
        self.missingColor['viridis'] = '0.5'
        self.missingColor['hot'] = '0.5'
        self.missingColor['seismic'] = '0.5'
        self.missingColor['magma'] = '0.5'
        self.missingColor['gray'] = 'green'
        Option02_hbox.addWidget(self.ColorMap_Combo)
        tab5_vbox.addLayout(Option02_hbox)

        Option03_hbox = QtWidgets.QHBoxLayout()
        PercThresholds = QtWidgets.QLabel('Percentile thresholds (%×10)')
        PercThresholds.setToolTip(
        '''This was called "Outlier removal" in the application PlotHeatMap.
        If the thresholds are set too close, they will be inactivated and the regular plot will be shown.
        This will occur often with low magnitude resolution such as non-binned TOF-SIMS''')
        Option03_hbox.addWidget(PercThresholds)
        self.SetLow_Spin = QtWidgets.QSpinBox()
        self.SetHigh_Spin = QtWidgets.QSpinBox()
        self.SetLow_Spin.setRange(0, 1000)
        self.SetLow_Spin.setToolTip('This is the floor of variation shown in the image set by the low percentile')
        self.SetHigh_Spin.setRange(0, 1000)
        self.SetHigh_Spin.setValue(1000)
        self.SetHigh_Spin.setToolTip('This is the ceiling of variation shown in the image set by the high percentile')
        Option03_hbox.addWidget(self.SetLow_Spin)
        Option03_hbox.addWidget(self.SetHigh_Spin)
        tab5_vbox.addLayout(Option03_hbox)

        Option04_hbox = QtWidgets.QHBoxLayout()
        self.Percentile_chkbox = QtWidgets.QCheckBox('Percentile scaling')
        Option04_hbox.addWidget(self.Percentile_chkbox)
        self.Percentile_Spin = QtWidgets.QSpinBox()
        self.Percentile_Spin.setRange(1, 99)
        self.Percentile_Spin.setValue(90)
        Option04_hbox.addWidget(self.Percentile_Spin)
        self.Percentile_Auto_Combo = QtWidgets.QComboBox()
        self.Percentile_Auto_Combo.addItems(['If needed', 'Always'])
        Option04_hbox.addWidget(self.Percentile_Auto_Combo)
        tab5_vbox.addLayout(Option04_hbox)

        Option05_vbox = QtWidgets.QVBoxLayout()
        self.TransfSelector = QtWidgets.QComboBox()
        self.TransfSelector.addItems(['View 1', 'View1 and View 2'])
        Option05_vbox.addWidget(self.TransfSelector)
        self.Log10_chkbox = QtWidgets.QCheckBox('Log10(magnitude)')
        self.Log10_chkbox.stateChanged.connect(self.Update_transformations)
        Option05_vbox.addWidget(self.Log10_chkbox)
        self.SqRt_chkbox = QtWidgets.QCheckBox('sqrt(magnitude)')
        self.SqRt_chkbox.stateChanged.connect(self.Update_transformations)
        Option05_vbox.addWidget(self.SqRt_chkbox)
        self.FourthRt_chkbox = QtWidgets.QCheckBox('fourth_root(magnitude)')
        self.FourthRt_chkbox.stateChanged.connect(self.Update_transformations)
        Option05_vbox.addWidget(self.FourthRt_chkbox)
        self.Invert_image_chkbox = QtWidgets.QCheckBox('Invert image')
        self.Invert_image_chkbox.stateChanged.connect(self.Update_transformations)
        Option05_vbox.addWidget(self.Invert_image_chkbox)
        self.Omit_zero_pixel_indices_chkbox = QtWidgets.QCheckBox('Pixel indices range: 1-max')
        self.Omit_zero_pixel_indices_chkbox.stateChanged.connect(self.Update_transformations)
        Option05_vbox.addWidget(self.Omit_zero_pixel_indices_chkbox)
        tab5_vbox.addLayout(Option05_vbox)
        tab5_vbox.addStretch(1)


        self.tab_widget_01.addTab(tab0, "Input")
        self.tab_widget_01.addTab(tab1, "Data")
        self.tab_widget_01.addTab(tab2, "Method")
        self.tab_widget_01.addTab(tab3, "Model")
        self.tab_widget_01.addTab(tab4, "Script")
#        self.tab_widget_01.addTab(self.tab5, "Plot options")
#        print('a', self.tab_widget_01.currentIndex())
        self.tab_widget_01.setCurrentIndex(0)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.tab_widget_01)
        self.tabGroupBox.setLayout(vbox)
        self.tabGroupBox.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
#        print('b', self.tab_widget_01.currentIndex())
#        self.tabGroupBox.setMaximumWidth(350)
        self.tabGroupBox.setMinimumWidth(300)

#        self.tabGroupBox.setGeometry(400,400,400,400)
        return tab5_vbox


    def showEvent(self, showEvent):
        self.restoreState(self.MainSavedState)
#        QtWidgets.QMessageBox.information(self,"Information!","Window has been shown...")

    def resizeEvent(self, resizeEvent):
        self.restoreState(self.PreviousSavedState)
#        QtWidgets.QMessageBox.information(self,"Information!","Window has been resized...")

    def closeEvent(self, event):
        settings = QtCore.QSettings("MVA_tools", "ImagePipeline_2")
        settings.setValue("mainWindow/geometry", self.saveGeometry())
        settings.setValue("mainWindow/windowState", self.saveState())
        settings.setValue("viewTab/PixInterp", self.PixInterp_Combo.currentIndex())
        settings.setValue("plotOptions/ColorMap", self.ColorMap_Combo.currentIndex())
        QtWidgets.QMainWindow.closeEvent(self, event)

    def readSettings(self):
        settings = QtCore.QSettings("MVA_tools", "ImagePipeline_2")
        self.restoreGeometry(settings.value("mainWindow/geometry", b""))#added b""
        self.restoreState(settings.value("mainWindow/windowState", b""))#added b""
        if settings.contains("viewTab/PixInterp"):
            self.PixInterp_Combo.setCurrentIndex(int(settings.value("viewTab/PixInterp")))
        if settings.contains("plotOptions/ColorMap"):
            self.ColorMap_Combo.setCurrentIndex(int(settings.value("plotOptions/ColorMap")))

#    def On_DockWindowChange(self):
#        self.PreviousSavedState = self.saveState()
#        QtWidgets.QMessageBox.information(self,"Information!","On_DockWindowChange activated")


    def Update_tab1(self, InpDataSets):
        self.ActiveData01_Combo.addItems(InpDataSets)
        self.ActiveData02_Combo.addItems(InpDataSets)
        self.ActiveData03_Combo.addItems(InpDataSets)
        """Select last entry to select model output automatically"""
        #TODO Check if this works for multiple input images
        self.ActiveData01_Combo.setCurrentIndex(self.ActiveData01_Combo.count()-1)

    def Clear_tab1(self):
         self.ActiveData01_Combo.clear()
         self.ActiveData02_Combo.clear()
         self.ActiveData03_Combo.clear()


    def load_new_HySp_cache_file(self, fname):
        InpDataSets = []
        self.hysp_cache.close()
        CacheFilePath = fname
        self.ListOfFiles= []
        self.ListOfFiles.append(fname)
        self.hysp_cache = hsc.HyperSpectralCache(CacheFilePath)
        for Dname in self.hysp_cache.get_ListOfDataSets():
            if Dname:
                InpDataSets.append(Dname)
        return InpDataSets


    def Update_transformations(self):
        if self.Log10_chkbox.isChecked():
            self.hysp_cache.set_Transformation(log10_eps)
        elif self.SqRt_chkbox.isChecked():
            self.hysp_cache.set_Transformation(np.sqrt)
        elif self.FourthRt_chkbox.isChecked():
            self.hysp_cache.set_Transformation(fourthRoot)
        else:
            self.hysp_cache.set_Transformation(neutralFunc)

        if self.Invert_image_chkbox.isChecked():
            self.hysp_cache.set_Transformation2(invert_image)
        else:
            self.hysp_cache.set_Transformation2(neutralFunc)



    def OpenFile(self):
#        print('begin OpenFile')
        caption = 'Open file'
        InpDataSets = []
        old_path = self.config.get( 'FileLocation',  'CurrentInputFileLocation')
        filter_mask = "All files (*.*);;IONTOF files (*.BIF6 *.zip);;HDF5 [matlab 7.3] (*.mat);; XL files (*.xls *.xlsx)"
        filenames = QtWidgets.QFileDialog.getOpenFileNames(None, caption, old_path, filter_mask)[0]
        if filenames:
#            print(filenames)  # test
            self.statusText.setText("Opening files...")
            for fname in filenames:
                if os.path.splitext(fname)[1] == '.zip':
                    DataSetNames = self.hysp_cache.load_ZippedBIF6_files(fname, self.Class_number)
                    if DataSetNames:
                        self.ListOfFiles.append(fname)
                        for Dname in DataSetNames:
                            InpDataSets.append(Dname)

                elif os.path.splitext(fname)[1] == '.BIF6':
                    Dname = self.hysp_cache.load_BIF6_file(fname, self.Class_number)
                    if Dname:
                        self.ListOfFiles.append(fname)
                        InpDataSets.extend(Dname)

                elif os.path.splitext(fname)[1] == '.mat':
                    Dnames = self.hysp_cache.load_HDF5_mat_file(fname)
                    if Dnames:
                        self.ListOfFiles.append(fname)
                        for Dname in Dnames:
                            InpDataSets.append(Dname)

                elif  os.path.splitext(fname)[1] == '.tif':
                    Dname = self.hysp_cache.load_tiff_stack_file(fname, IPL_version)
                    if Dname:
                        self.ListOfFiles.append(fname)
                        InpDataSets.append(Dname)

                elif os.path.splitext(fname)[1] == '.hdf5':
                    if fname != filenames[0]:
                        print('Cannot load more than one hyperspectral cache file')
                    else:
                        InpDataSets = self.load_new_HySp_cache_file( fname )

                else:
                    print('File extension not recognized for:', os.path.basename(fname))

            if InpDataSets:
                self.InpDataSetsListBox.addItems( InpDataSets )
                self.InpDataSetsTreeView.AppendClass(InpDataSets, self.Class_number )
                self.Class_number += 1
                self.InpDataSetsTreeView.expandAll()
                self.InpDataSetsTreeView.resizeColumnToContents(0)
                self.Update_tab1(InpDataSets)

            self.UpdateFilelocation( filenames[0], 'CurrentInputFileLocation' )
            self.config.set( 'Input',  'ListOfInput', repr(self.ListOfFiles))
            ConfigFile = open( self.inifile, mode='w')
            self.config.write(ConfigFile)
            self.statusText.setText(str(len(self.ListOfFiles))+ ' files are selected')
            if len(self.ListOfFiles) == 1:
                self.NumOfFilesLineEdit_tab0.setText(str(len(self.ListOfFiles))+' input file')
            else:
                self.NumOfFilesLineEdit_tab0.setText(str(len(self.ListOfFiles))+' input files')

        else:
            self.statusText.setText("No files were selected")


    def ClearFileList(self):
        self.InpDataSetsListBox.clear()
        self.InpDataSetsTreeView.clear()
        self.Class_number = 1
        self.Clear_tab1()
        self.ListOfFiles = []
#        self.config.set( 'Input',  'ListOfInput', repr(self.ListOfFiles))
#        ConfigFile = open( self.inifile, mode='w')
#        self.config.write(ConfigFile)
        self.statusText.setText(str(len(self.ListOfFiles))+ ' files are selected')
        self.NumOfFilesLineEdit_tab0.setText(str(len(self.ListOfFiles))+' input files')

        # Open a new fresh cache file
        self.hysp_cache.close()
        CacheFilePath = os.path.join( self.CacheFiles.get_location(), timestamped_filename('HySp_cache_')+'.hdf5')
        self.hysp_cache = hsc.HyperSpectralCache(CacheFilePath)


#    def ImportFiles(self):
##        print('begin Import files')
#        caption = 'Import files'
#        old_path = self.config.get( 'FileLocation',  'CurrentScriptInputFileLocation')
#        filter_mask = "All files (*.*);;Data files (*.txt *.csv *.mat );; XL files (*.xls *.xlsx)"
#        filenames = QtWidgets.QFileDialog.getOpenFileNames(None, caption, old_path, filter_mask)[0]
#        if filenames:
##            print(filenames)  # test
#            self.statusText.setText("Importing files...")
#            self.InpFilesListBox.clear()
#            self.ListOfScriptInputFiles = []
#            for fname in filenames:
#                self.InpFilesListBox.addItem( os.path.basename(fname) )
#                self.ListOfScriptInputFiles.append(fname)
#            self.UpdateFilelocation( filenames[0], 'CurrentScriptInputFileLocation' )
#            self.config.set( 'Scripts',  'ListOfInput', repr(self.ListOfScriptInputFiles))
#            ConfigFile = open( self.inifile, mode='w')
#            self.config.write(ConfigFile)
#            self.statusText.setText(str(len(self.ListOfScriptInputFiles))+ ' files are selected')
#            self.NumOfFilesLineEdit_tab4.setText(str(len(self.ListOfScriptInputFiles))+' input files')
#            self.is_import_ScriptOutput = True # Flag to open the HySp_cache after running the import script
#            self.tab_widget_01.setCurrentIndex(4)
#        else:
#            self.statusText.setText("No files were selected")


    def openScriptInputFiles(self):
#        print('begin Import files')
        caption = 'Import files'
        old_path = self.config.get( 'FileLocation',  'CurrentScriptInputFileLocation')
        filter_mask = "All files (*.*);;Data files (*.txt *.csv *.mat );; XL files (*.xls *.xlsx)"
        filenames = QtWidgets.QFileDialog.getOpenFileNames(None, caption, old_path, filter_mask)[0]
        if filenames:
#            print(filenames)  # test
            self.statusText.setText("Opening files for script input...")
            self.InpFilesListBox.clear()
            self.ListOfScriptInputFiles = []
            for fname in filenames:
                self.InpFilesListBox.addItem( os.path.basename(fname) )
                self.ListOfScriptInputFiles.append(fname)
            self.UpdateFilelocation( filenames[0], 'CurrentScriptInputFileLocation' )
            self.config.set( 'Scripts',  'ListOfInput', repr(self.ListOfScriptInputFiles))
            ConfigFile = open( self.inifile, mode='w')
            self.config.write(ConfigFile)
            self.statusText.setText(str(len(self.ListOfScriptInputFiles))+ ' files are selected')
            self.NumOfFilesLineEdit_tab4.setText(str(len(self.ListOfScriptInputFiles))+' input files')
            self.DockScriptLog.raise_()
            self.tab_widget_01.setCurrentIndex(4)
        else:
            self.statusText.setText("No files were selected")


    def exportUnfolded(self):
        old_path = self.config.get( 'FileLocation',  'CurrentOutputFileLocation')
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        directory = dialog.getExistingDirectory(self, 'Choose directory for export of unfolded image files', old_path)
        if directory:
            self.statusText.setText("Export to: %s" % directory)
            self.hysp_cache.Save_all_unfolded_spectra(directory, self.SetBinning_Spin.value(), matlab_compatible=True)
            self.UpdateFilelocation( os.path.join(directory, 'dummyFname'), 'CurrentOutputFileLocation' )
        else:
            self.statusText.setText('Error ---- Export was not done')

    def exportUnfolded_Selected(self):
        old_path = self.config.get( 'FileLocation',  'CurrentOutputFileLocation')
        filter_mask = "All files (*.*);;HDF5 [matlab 7.3] (*.mat)"
        FileName = QtWidgets.QFileDialog.getSaveFileName(self, "Export selected spectra to file", old_path, filter_mask)[0]
        if FileName:
            self.statusText.setText("Export selected spectra to: %s" % FileName)
            self.Save_Unfolded_SelectedSpectra( FileName )
            directory = os.path.dirname(FileName)
            self.UpdateFilelocation( os.path.join(directory, 'dummyFname'), 'CurrentOutputFileLocation' )
        else:
            self.statusText.setText('Error ---- Export was not done')

    def get_New_RepositoryDir(self, RepositoryId):
        CurrentDataDir = self.OutputRepository.get_new_entry_in_data_repository(RepositoryId)
        if not CurrentDataDir:
            self.set_data_repository()
            CurrentDataDir = self.OutputRepository.get_new_entry_in_data_repository(RepositoryId)
        Data_IO.make_dir_if_absent(CurrentDataDir)
        return CurrentDataDir

    def save_BW_picture(self, img, OutDir, Filename, suffix, cnt):
        min_img =  np.min(img)
        max_img =  np.max(img)
        ImageFlt = (img - min_img)/(max_img - min_img)
        ImageInt = np.uint8( 255*ImageFlt )
        pict = Image.fromarray( ImageInt )
        EntireFileName = Filename+suffix+str(cnt).zfill(2)+'.png'
        pict.save(os.path.join(OutDir, EntireFileName))
        scaling = (EntireFileName, min_img, max_img, 0, 255)
        return scaling

    def save_pictures_to_Repository(self):
        print('Enter save_pictures_to_Repository')
        metadata = []
        if not self.ActiveData01_Combo.currentText():
            print('No hyperspectral image present in View 1')
        else:
            DataSetName = self.ActiveData01_Combo.currentText()
            OutDir = self.get_New_RepositoryDir(DataSetName)
            Shape = self.hysp_cache.get_DataSize(DataSetName, 'IMAGE')
            print('DataSetName', DataSetName, Shape)
            binp = self.SetBinning_Spin.value()
            # get repository
            for i in range(Shape[2]):
                img = self.hysp_cache.get_binned_3Dslice(DataSetName, 'IMAGE', i, bin_size_power=binp)
                scaling = self.save_BW_picture(img, OutDir, 'img', '_BW', i+1)
                metadata.append(scaling)
            hdr = [['filename', 'min', 'max', 'img_min', 'img_max']]
            XLSXfile = os.path.join(OutDir, 'metadata')
            MatDataIO.Save_XLSX_table(XLSXfile, 'img_scaling', hdr, metadata)
            slice_IDs = self.hysp_cache.get_IDs(DataSetName, 'VARID1')

            if 'LOADINGS' in self.hysp_cache.get_RecordNames(DataSetName):
                P = self.hysp_cache.get_Data(DataSetName, 'LOADINGS')
                if 'LOADINGS_X1' in self.hysp_cache.get_RecordNames(DataSetName):
                    x_IDs = self.hysp_cache.get_IDs(DataSetName, 'LOADINGS_X1')
                if 'LOADINGS_X2' in self.hysp_cache.get_RecordNames(DataSetName):
                    x_scale0 = self.hysp_cache.get_Data(DataSetName, 'LOADINGS_X2')
                    x_scale = self.hysp_cache.get_Data(DataSetName, 'LOADINGS_X2')
                    print('LOADINGS_X2', type(x_scale0), type(x_scale))
                else:
                    x_scale = np.arange(0,P.shape[1])

                f = []
                bokeh_f = []
                for i in range(P.shape[0]):
                    f.append(GenPlot.Figure())
                    f[i].ms_plot(x_scale, P[i,:])
                    f[i].xlabel('m/z')
                    f[i].ylabel('p '+str(i+1))
                    f[i].save(OutDir, 'Loading', title_suffix=slice_IDs[i])
                    bokeh_f.append(GenPlot.bkhFigure())
#                    print('x_scale, P[i,:]', type(x_scale), x_scale.shape, type(P[i,:]), P[i,:].shape)
                    bokeh_f[i].ms_plot(x_scale, P[i,:].T)
                    bokeh_f[i].xlabel('m/z')
                    bokeh_f[i].ylabel('p '+str(i+1))
                    bokeh_f[i].save(OutDir, 'Loading', title_suffix=slice_IDs[i])

                P_binary_save = {}
                P_binary_save['DATA'] = P
                P_binary_save['VARID1'] = x_IDs
                P_binary_save['VARID2'] = x_scale
                P_binary_save['OBSID1'] = self.hysp_cache.get_IDs(DataSetName, 'VARID1')
                MatDataIO.WriteData(os.path.join(OutDir, 'loadings'), P_binary_save)


    def reset_docking_windows(self):
        self.restoreState(self.MainSavedState)
        print('self.MainSavedState',len(self.MainSavedState))

    def keep_docking_windows_configuration(self):
        self.PreviousSavedState = self.saveState()

    def OnActiveScriptChange(self):
        self.ActiveScriptCombo.setToolTip(self.ListOfScripts[self.ActiveScriptCombo.currentIndex()])

    def OnScriptParamsChange(self):
        self.is_ScriptParams_as_FileName = False
        self.config.set('Scripts','is_ScriptParams_as_FileName', str(self.is_ScriptParams_as_FileName))
        ConfigFile = open( self.inifile, mode='w')
        self.config.write(ConfigFile)

    """ Script handling section, start """

    def InsertScript(self, FullFileName):
        self.ListOfScripts.insert(0, FullFileName )
        BaseFileName = os.path.basename(FullFileName)
        self.ListOfScriptNames.insert(0, BaseFileName )
        self.ActiveScriptCombo.clear()
        TmpListOfScriptNames = []
        for ActiveScript in self.ListOfScriptNames:
            if ActiveScript not in TmpListOfScriptNames:# avoid same name twice, newly loaded will come first
                TmpListOfScriptNames.append( ActiveScript )
                self.ActiveScriptCombo.addItem( ActiveScript )

        self.statusText.setText("Selected script: %s" % BaseFileName)

        self.config.set( 'Scripts',  'SelectedScript', FullFileName)
        ListOfScripts_max_len = min(7, len(self.ListOfScripts))
        self.config.set( 'Scripts',  'ListOfScripts', repr(self.ListOfScripts[0:ListOfScripts_max_len]))
        CurrentDir = os.path.dirname(FullFileName)
        self.config.set( 'FileLocation',  'CurrentScriptFileLocation', CurrentDir)

        ConfigFile = open( self.inifile, mode='w')
        self.config.write(ConfigFile)


    def OpenScript(self):
#        print('begin OpenScript')
        caption = 'Open file'
        old_path = self.config.get( 'FileLocation',  'CurrentScriptFileLocation')
        filter_mask = "Python/Matlab scripts (*.py *.pyw *.m)"
        script_names = QtWidgets.QFileDialog.getOpenFileNames(None, caption, old_path, filter_mask)[0]
        if script_names:
    #        print(script_name)  # test
            self.statusText.setText("Opening a script")
            self.InsertScript(script_names[0])
#            self.UpdateFilelocation( script_name, 'SelectedScript' )
        else:
            self.statusText.setText("No script was opened")


    def WriteInputFileNamesToFile(self, ListOfFiles, OutputFileName ):
#        print( 'WriteInputFileNamesToFile')
#        print( 'ListOfFiles ', ListOfFiles)
#        print( 'OutputFileName ', OutputFileName)

        try:
            outfile01 = open(OutputFileName, mode='w')
            try:
                for s in ListOfFiles:
                    outfile01.write(s +"\n")
            finally:
                outfile01.close()
        except IOError as e:
            QtWidgets.QMessageBox.information(self, 'Error', 'Error saving file\n' + str(e))


    def WriteScriptFileNameToFile(self, ScriptName, OutputFileName ):
        try:
            outfile02 = open(OutputFileName, mode='w')
            try:
                outfile02.write(ScriptName +"\n")
            finally:
                outfile02.close()
        except IOError as e:
            QtWidgets.QMessageBox.information(self, 'Error', 'Error saving file ',OutputFileName+'\n' + str(e))


    def Write_log_file(self, Filename, log_text):
        log_file = open(Filename, mode='w')
        log_file.writelines(log_text)
        log_file.close()


    def save_a_copy_of_the_py_script(self, ScriptStrings, local_ScriptInputFileName ):
        # Copy the running script to the data location for documentation and possible re-run
        # and also copy the parameter file if it exists
        ScriptEngine = ScriptStrings[0]
        ScriptName = ScriptStrings[1]
        if local_ScriptInputFileName != '':
            ScriptInputFileName = local_ScriptInputFileName
        else:
            ScriptInputFileName = ScriptStrings[2]
        ScriptOutputName = ScriptStrings[3]
        if len(ScriptStrings) > 4:
            ScriptParameters = ScriptStrings[4:]
        else:
            ScriptParameters = None

        shutil.copy2(ScriptName, os.path.join(os.path.dirname(ScriptOutputName), os.path.basename(ScriptName)) )
        cmd_for_rerun = ScriptEngine+' '+ os.path.basename(ScriptName) +' "'+os.path.basename(ScriptInputFileName)+'" "$PWD/dummyFname"'
        if ScriptParameters:
            if os.path.isfile(ScriptParameters[0]):
                cmd_for_rerun = cmd_for_rerun+' "'+os.path.basename(ScriptParameters[0])+'"'
                shutil.copy2(ScriptParameters[0], os.path.join(os.path.dirname(ScriptOutputName), os.path.basename(ScriptParameters[0])) )
            else:
                cmd_for_rerun = cmd_for_rerun+' '+" ".join(ScriptParameters)
        cmd_file = open(os.path.join(os.path.dirname(ScriptOutputName), 'cmd_for_primary_rerun.sh'), 'w')
        cmd_file.write(cmd_for_rerun)
        cmd_file.close()


    def MakeLogUpdate(self, line):
#        print('MakeLogUpdate self.collected_stdout', self.collected_stdout)
        self.log_file.write(line)
        self.ScriptLogText.moveCursor(QtWidgets.QTextCursor.End)
        self.ScriptLogText.insertPlainText(line)
#        self.ScriptLogText.ensureCursorVisible()


    def WorkerIsFinished(self, s):
        if s == 'Finished':
            self.log_file.close()
            if self.is_import_ScriptOutput and os.path.isfile(self.ImportScript_OutputFilePathName):
                InpDataSets = self.load_new_HySp_cache_file( self.ImportScript_OutputFilePathName )
                if InpDataSets:
                    self.tab_widget_01.setCurrentIndex(0)
                    self.InpDataSetsListBox.addItems( InpDataSets )
                    self.Update_tab1(InpDataSets)
                self.is_import_ScriptOutput = False

        else:
            print('Log file was not closed properly')


    def RunScriptWorker(self, Script_strings):
        self.threadPool.append( WorkThread() )
        self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update01(QString)"), self.MakeLogUpdate )
        self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update02(QString)"), self.WorkerIsFinished )
        self.threadPool[len(self.threadPool)-1].set_ScriptStrings(Script_strings)
        self.threadPool[len(self.threadPool)-1].start()
        # This only starts the worker but does not wait for output


    def RunScriptMain( self, ScriptName, InputFileList, ScriptOutputName, is_data2source, is_import, ScriptParams='' ):
        is_save_copy_of_script = True
        trace = False
        if trace:
            print('Enter RunScriptMain')
        ScriptExt = os.path.splitext(ScriptName)[1]
        ScriptBaseName_NoExt = os.path.splitext(os.path.basename(ScriptName) )[0]
        ScriptDir = os.path.dirname(ScriptName)
        OutputDataDirectory = os.path.dirname(ScriptOutputName)
        if self.CopyInputFiles:
            ScriptInputFileName, local_ScriptInputFileName = self.CopyInputFiles_to_DataRepository(InputFileList, ScriptOutputName, ScriptName)
        else:
            local_ScriptInputFileName = ''
            ScriptInputFileName = os.path.join( OutputDataDirectory, ScriptBaseName_NoExt + '_input_' +datetime_stamp()+'.txt')
            if os.path.exists(ScriptInputFileName): #wait 1 s
                time.sleep(2)
                ScriptInputFileName = os.path.join( OutputDataDirectory, ScriptBaseName_NoExt + '_input_' +datetime_stamp()+'.txt')
            self.WriteInputFileNamesToFile( InputFileList, ScriptInputFileName )

        IdOfUsedScriptFileName = os.path.join( OutputDataDirectory, ScriptBaseName_NoExt + '_script_location_' +datetime_stamp()+'.txt')
        self.WriteScriptFileNameToFile(ScriptName, IdOfUsedScriptFileName)
        if ScriptExt == '.py':
            if sys.platform.startswith('linux'):
                Script_strings = ['python3']
            else: # Windows
                Script_strings = ['C:\Python34\python']


            Script_strings.append( ScriptName )
            Script_strings.append( ScriptInputFileName )
            Script_strings.append( ScriptOutputName )
#            if self.ScriptParamsLineEdit.text() != '':
#                Script_strings.append( self.ScriptParamsLineEdit.text() )
            if is_data2source:
                Script_strings.append( '-d2src' )
            if  ScriptParams:
                Script_strings.extend( ScriptParams )
            if is_save_copy_of_script:
                self.save_a_copy_of_the_py_script( Script_strings, local_ScriptInputFileName )
        elif ScriptExt == '.m':
            matlab_log = os.path.splitext(ScriptOutputName)[0] +'_matlab.log'
            Script_strings = ['matlab', '-nodesktop', '-nosplash', '-logfile', matlab_log ,'-r']
            mat_command_string = 'cd '+ScriptDir+';'+ScriptBaseName_NoExt + "( '" + ScriptInputFileName + "','" + ScriptOutputName + "');exit"
#            mat_command_string = 'cd '+ScriptDir+';try;'+ScriptBaseName_NoExt + "( '" + ScriptInputFileName + "','" + ScriptOutputName + "');catch;exit(1);end;exit(0)"
            Script_strings.append( mat_command_string )
            # Script_strings.append( BaseName_NoExt )
            self.save_a_copy_of_the_m_script( Script_strings, ScriptName, ScriptInputFileName, ScriptOutputName, local_ScriptInputFileName )
        else:
            QtWidgets.QMessageBox.information(self, 'Error', 'Unrecognized script extension\n' + ScriptExt )

        print('Script_strings:', Script_strings)


        Log_file_name = os.path.splitext(ScriptOutputName)[0] +'.log'
        self.log_file = open(Log_file_name, mode='w')

        if is_import:
            self.ImportScript_OutputFilePathName = ScriptOutputName
            self.is_import_ScriptOutput = True
        self.RunScriptWorker( Script_strings )



    def RunScript(self, is_data2source=False, is_import=False):
        trace = False
        SelectedScript = self.ActiveScriptCombo.currentText()
        if trace:
            print('SelectedScript',SelectedScript)
        if SelectedScript == 'Undefined':
            QtWidgets.QMessageBox.information(self, 'Error', 'Please open a script')
        else:
            ScriptIndex = self.ListOfScriptNames.index(SelectedScript)
            if not os.path.isfile(self.ListOfScripts[ScriptIndex]):
                QtWidgets.QMessageBox.information(self, 'Error', 'File not found:\n' + self.ListOfScripts[ScriptIndex] )
            else:
                ScriptExt = os.path.splitext(self.ListOfScripts[ScriptIndex])[1]
                if not (ScriptExt in ['.py','.pyw']):
                    QtWidgets.QMessageBox.information(self, 'Error', 'Unrecognized script extension\n' + ScriptExt )

                elif len(self.ListOfScriptInputFiles) < 1:
                    QtWidgets.QMessageBox.information(self, 'Error', 'Please enter filenames to be processes by the script')
                else:
                    print()
                    print('---------------------------------------------------------')
                    print('Run the script: ', self.ListOfScripts[ScriptIndex])
                    ScriptBaseName_NoExt = os.path.splitext(os.path.basename(self.ListOfScripts[ScriptIndex]))[0]
#                    if is_import:
#                        ScriptOutputName = os.path.join( self.CacheFiles.get_location(), timestamped_filename('Imported_cache_')+'.hdf5')
#                    else:
                    """Output to the data repository"""
                    RepositoryId = ScriptBaseName_NoExt
                    if is_data2source:
                        DataLocationDir = os.path.join(os.path.dirname(self.ListOfScriptInputFiles[0]), 'result')
                        CurrentDataDir = self.OutputRepository.get_new_entry_at_data_location(DataLocationDir, RepositoryId)
                    else:
                        CurrentDataDir = self.OutputRepository.get_new_entry_in_data_repository(RepositoryId)
                        if not CurrentDataDir:
                            self.set_data_repository()
                            CurrentDataDir = self.OutputRepository.get_new_entry_in_data_repository(RepositoryId)
                    Data_IO.make_dir_if_absent(CurrentDataDir)
                    """filespec is the default output name that will be used for a script,
                       a generic script may or may not use this suggested filename"""
                    filespec = ScriptBaseName_NoExt + '_cache_' +datetime_stamp()  + '.hdf5'
                    ScriptOutputName = os.path.join(CurrentDataDir, filespec)

                    if self.ScriptParamsLineEdit.text() != '':
                        ScriptParams = self.ScriptParamsLineEdit.text()
                    else:
                        ScriptParams = ''
                    self.config.set( 'Scripts', 'ScriptParameters', ScriptParams)
                    self.config.set( 'Scripts', 'LastUsedScript', SelectedScript )
                    ConfigFile = open( self.inifile, mode='w')
                    self.config.write(ConfigFile)
                    if self.is_ScriptParams_as_FileName:
                        ScriptParamList = []
                        ScriptParamList.append(ScriptParams) # This is now a list
                    else:
                        ScriptParamList = ScriptParams.split(' ')
                    try:
                       self.statusText.setText("Running script: %s" % ScriptBaseName_NoExt)
                       self.RunScriptMain( self.ListOfScripts[ScriptIndex], self.ListOfScriptInputFiles, ScriptOutputName,
                                           is_data2source, is_import, ScriptParamList )
                    finally:
                        pass


    def RunScript_w_data2source(self):
        self.RunScript(is_data2source=True)


    def RunImportScript(self):
        self.RunScript(is_data2source=False, is_import=True)


    def ReloadPreviousScriptInputSelections(self):
        self.ScriptParamsLineEdit.setText(self.config.get('Scripts', 'ScriptParameters') )
        if os.path.isfile(self.ScriptParamsLineEdit.text()):
            self.is_ScriptParams_as_FileName = True
            self.config.set('Scripts','is_ScriptParams_as_FileName', str(self.is_ScriptParams_as_FileName))
            ConfigFile = open( self.inifile, mode='w')
            self.config.write(ConfigFile)

        self.ListOfScriptInputFiles = eval(self.config.get('Scripts', 'ListOfInput'))
        self.InpFilesListBox.clear()
        for fname in self.ListOfScriptInputFiles:
            self.InpFilesListBox.addItem( os.path.basename(fname) )
        self.NumOfFilesLineEdit_tab4.setText(str(len(self.ListOfScriptInputFiles))+' input files')

        Script_selector = self.config.get('Scripts', 'LastUsedScript')
        ScriptIndex = self.ActiveScriptCombo.findText(Script_selector)
        self.ActiveScriptCombo.setCurrentIndex(ScriptIndex)
        self.DockScriptLog.raise_()
        self.tab_widget_01.setCurrentIndex(4)


    """ Script handling section, end """


    def show_data_repository(self):
        if self.OutputRepository.get_location():
            QtWidgets.QMessageBox.information(self,'Location', 'Current location of data repository is \n' +self.OutputRepository.get_location())
        else:
            QtWidgets.QMessageBox.information(self, 'Location', 'Current location of data repository is not set, \n Please set it by: Settings, Set data repository location')


    def set_data_repository(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        directory = dialog.getExistingDirectory(self, 'Choose directory for results repository', os.path.curdir)
        if directory:
            self.statusText.setText("Selected repository: %s" % directory)
            self.OutputRepository.set_location(directory)
        else:
            if self.OutputRepository.get_location():
                self.statusText.setText('Info ---- data repository was kept at: '+self.OutputRepository.get_location())
            else:
                self.statusText.setText('Error ---- data repository was not set')


    def set_cachefiles_location(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.Directory)
        dialog.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        directory = dialog.getExistingDirectory(self, 'Place directory for temp-files on fast local disk', os.path.curdir)
        if directory:
            self.statusText.setText("Selected location: %s" % directory)
            self.CacheFiles.set_location(directory)
        else:
            if self.CacheFiles.get_location():
                self.statusText.setText('Info ---- cache files location was kept at: '+self.CacheFiles.get_location())
            else:
                self.statusText.setText('Error ---- cache files location was not set')


    def auto_check_cachefiles(self):
        retries = 4
        while (retries > 0) and not self.CacheFiles.get_location():
            self.set_cachefiles_location()
            retries -= 1

        self.CacheFiles.delete_old_files(hours_to_expiry=2, file_extension='.hdf5' )


    def OnInpDataSetsListBox_ItemClicked(self):
        DataSetName = self.InpDataSetsListBox.currentItem().text()
        self.View1_DataName.setText(DataSetName)
        self.view1_data['image'] = self.hysp_cache.get_ImageSum(DataSetName, 'IMAGE' )
        self.view1_data['pixel_MinMax'] = (np.min(self.view1_data['image']), np.max(self.view1_data['image']))
        self.view1_data['highlight'] =  np.zeros_like(self.view1_data['image'], dtype=np.bool)
        self.view1_data['slice_info'] = 'Total sum'
        self.view1_draw()
        self.View2_DataName.setText(DataSetName)
        self.view2_y = self.hysp_cache.get_SpectralSum(DataSetName, 'IMAGE')
#        print('view2_y', self.view2_y.shape)
        self.view2_x = self.hysp_cache.get_Data(DataSetName, 'VARID2')
        self.on_vlines2()

    def OnInpDataSetsTreeView_ItemClicked(self, index):
        if self.InpDataSetsTreeView.currentItem(index):
            DataSetName = self.InpDataSetsTreeView.currentItem(index).text()
            self.View1_DataName.setText(DataSetName)
            self.view1_data['image'] = self.hysp_cache.get_ImageSum(DataSetName, 'IMAGE' )
            self.view1_data['pixel_MinMax'] = (np.min(self.view1_data['image']), np.max(self.view1_data['image']))
            self.view1_data['highlight'] =  np.zeros_like(self.view1_data['image'], dtype=np.bool)
            self.view1_data['slice_info'] = 'Total sum'
            self.view1_draw()
            self.View2_DataName.setText(DataSetName)
            self.view2_y = self.hysp_cache.get_SpectralSum(DataSetName, 'IMAGE')
            self.view2_x = self.hysp_cache.get_Data(DataSetName, 'VARID2')
            self.on_vlines2()


    def OnActiveData01_changed(self):
        self.SliceListBox01.clear()
        DataSetName = self.ActiveData01_Combo.currentText()
        print('OnActiveData01_changed, DataSetName =', DataSetName, len(DataSetName))
        if DataSetName:
            x_axis_list = self.hysp_cache.get_IDs(DataSetName, 'VARID1' )
            self.SliceListBox01.addItems(x_axis_list)
            if self.chained_ActiveData01.isChecked():
                newData02_selection = self.ActiveData02_Combo.findText(DataSetName)
                self.ActiveData02_Combo.setCurrentIndex(newData02_selection)
                newData03_selection = self.ActiveData03_Combo.findText(DataSetName)
                self.ActiveData03_Combo.setCurrentIndex(newData03_selection)

            if 'ClusterColors' in self.hysp_cache.get_RecordNames(DataSetName):
                ClstColors_obj = self.hysp_cache.get_Data(DataSetName, 'ClusterColors')
                print('ClstColors_obj.shape',ClstColors_obj.shape)
                num_of_cluster_color_definitions = ClstColors_obj.shape[2]
                for Clst in range(num_of_cluster_color_definitions):
                    Cdef = np.ravel(self.hysp_cache.get_3Dslice(DataSetName, 'ClusterColors', Clst ))
                    num_of_clusters = len(set(Cdef))
                    self.ClassColors_Combo.addItem(str(num_of_clusters)+' clusters')
            else:
                self.ClassColors_Combo.clear()


    def OnActiveData02_changed(self):
        self.SliceListBox02.clear()
        DataSetName = self.ActiveData02_Combo.currentText()
        print('OnActiveData02_changed, DataSetName =', DataSetName, len(DataSetName))
        if DataSetName:
            x_axis_list = self.hysp_cache.get_IDs(DataSetName, 'VARID1' )
            self.SliceListBox02.addItems(x_axis_list)


    def OnActiveData03_changed(self):
        self.SliceListBox03.clear()
        DataSetName = self.ActiveData03_Combo.currentText()
        print('OnActiveData03_changed, DataSetName =', DataSetName, len(DataSetName))
        if DataSetName:
            x_axis_list = self.hysp_cache.get_IDs(DataSetName, 'VARID1' )
            self.SliceListBox03.addItems(x_axis_list)

    def OnActiveData_SyncChange(self):
        propagated_state = self.chained_ActiveData01.checkState()
        self.chained_ActiveData02.setCheckState(propagated_state)
        self.chained_ActiveData03.setCheckState(propagated_state)

    def OnColor_changed(self):
        self.view4_data['image'], self.view4_data['slice_info'] = self.get_color_data(self.view1_data, self.view2_data, self.view3_data)
        self.view4_draw()

    def OnViewListSorting_changed(self):
        DataSetName01 = self.ActiveData01_Combo.currentText()
        if DataSetName01:
            sort_order = self.ListsOrder_Combo.currentIndex()
            sorted_x_axis_list = self.hysp_cache.get_sorted_IDs(DataSetName01, 'VARID1', sort_order)
            self.SliceListBox01.clear()
            self.SliceListBox01.addItems(sorted_x_axis_list)

        DataSetName02 = self.ActiveData01_Combo.currentText()
        if DataSetName02:
            sort_order = self.ListsOrder_Combo.currentIndex()
            sorted_x_axis_list = self.hysp_cache.get_sorted_IDs(DataSetName02, 'VARID1', sort_order)
            self.SliceListBox02.clear()
            self.SliceListBox02.addItems(sorted_x_axis_list)

        DataSetName03 = self.ActiveData01_Combo.currentText()
        if DataSetName03:
            sort_order = self.ListsOrder_Combo.currentIndex()
            sorted_x_axis_list = self.hysp_cache.get_sorted_IDs(DataSetName03, 'VARID1', sort_order)
            self.SliceListBox03.clear()
            self.SliceListBox03.addItems(sorted_x_axis_list)


    def OnSliceListBox01_update(self):
#        print('self.SliceListBox01.currentItem()', self.SliceListBox01.currentItem() )
        if self.SliceListBox01.currentItem():
            DataSetName = self.ActiveData01_Combo.currentText()
            x_axis_list = self.hysp_cache.get_IDs(DataSetName, 'VARID1' )
            SelectedSlice = self.SliceListBox01.currentItem().text() #is text, may be sorted wihtout affecting the link to data
            SliceIndex = x_axis_list.index(SelectedSlice)
            self.view1_data['slice_info'] = x_axis_list[SliceIndex]
            self.view1_data['image'] = self.hysp_cache.get_Trans_3Dslice(DataSetName, 'IMAGE', SliceIndex)
            if self.ImgScales_Combo.currentText() == 'Individual':
                self.view1_data['pixel_MinMax'] = \
                    self.hysp_cache.get_OneTrans_3DSlice_MinMax_from_percentiles( DataSetName,
                                                                             SliceIndex,
                                                                             self.SetLow_Spin.value(),
                                                                             self.SetHigh_Spin.value() )
            else:
                self.view1_data['pixel_MinMax'] = \
                    self.hysp_cache.get_Overall_3DSlice_MinMax_from_percentiles( DataSetName,
                                                                                 SliceIndex,
                                                                                 self.SetLow_Spin.value(),
                                                                                 self.SetHigh_Spin.value() )

            self.view1_data['highlight'] =  np.zeros_like(self.view1_data['image'], dtype=np.bool)
            self.View1_DataName.setText(DataSetName)
            self.view1_draw()
            self.view10_data['x-axis'] = np.reshape(self.view1_data['image'], self.view1_data['image'].shape[0]*self.view1_data['image'].shape[1], 1)
            self.view10_data['x-axis_label'] = self.view1_data['slice_info']

            # Getting color info only from view1, so far
            #Done Make some kind of check to see if 'ClusterColors' is present, and do not use them if they are absent
            if 'ClusterColors' in self.hysp_cache.get_RecordNames(DataSetName):
                self.view1_data['clusters'] = self.hysp_cache.get_Trans_3Dslice(DataSetName, 'ClusterColors', self.ClassColors_Combo.currentIndex() )
                self.view10_data ['color_nums'] = np.reshape(self.view1_data['clusters'],
                                self.view1_data['clusters'].shape[0]*self.view1_data['clusters'].shape[1], 1)
                self.number_of_clusters = len(set(self.view10_data ['color_nums']))
                cm_subsection = np.linspace(0.0, 1.0, self.number_of_clusters)
#                unique_colors = matplotlib.cm.bwr(cm_subsection)
                self.unique_colors = matplotlib.cm.hot(cm_subsection)
#                unique_colors = matplotlib.cm.jet(cm_subsection)
#                print('unique_colors', self.unique_colors)
                self.view10_data ['colors'] = self.unique_colors[self.view10_data ['color_nums']]
            else:
                self.view10_data .pop('colors', None) #Remove key and do not fail if the key is not present
#            print("self.view10_data ['colors']", self.view10_data ['colors'].shape, self.view10_data ['colors'][0:50])
            self.on_draw10()
            self.view4_data['image'], self.view4_data['slice_info'] = self.get_color_data(self.view1_data, self.view2_data, self.view3_data)
            self.view4_draw()


    def OnSliceListBox02_update(self):
        if self.SliceListBox02.currentItem():
            DataSetName = self.ActiveData02_Combo.currentText()
            x_axis_list = self.hysp_cache.get_IDs(DataSetName, 'VARID1' )
            SelectedSlice = self.SliceListBox02.currentItem().text() #is text, may be sorted wihtout affecting the link to data
            SliceIndex = x_axis_list.index(SelectedSlice)
            self.view2_data['slice_info'] = x_axis_list[SliceIndex]
            self.view2_data['image'] = self.hysp_cache.get_Trans_3Dslice(DataSetName, 'IMAGE', SliceIndex )
            if self.ImgScales_Combo.currentText() == 'Individual':
                self.view2_data['pixel_MinMax'] = \
                    self.hysp_cache.get_OneTrans_3DSlice_MinMax_from_percentiles( DataSetName,
                                                                                  SliceIndex,
                                                                                  self.SetLow_Spin.value(),
                                                                                  self.SetHigh_Spin.value() )
            else:
                self.view2_data['pixel_MinMax'] = \
                    self.hysp_cache.get_Overall_3DSlice_MinMax_from_percentiles( DataSetName,
                                                                                 SliceIndex,
                                                                                 self.SetLow_Spin.value(),
                                                                                 self.SetHigh_Spin.value() )

#            self.view2_data['overall_MinMax'] = self.hysp_cache.get_Total_3DSlice_MinMax( SliceIndex )
            self.view2_data['highlight'] =  np.zeros_like(self.view2_data['image'], dtype=np.bool)
            self.View2_DataName.setText(DataSetName)
            self.view10_data ['y-axis'] = np.reshape(self.view2_data['image'], self.view2_data['image'].shape[0]*self.view2_data['image'].shape[1], 1)
            self.view10_data ['y-axis_label'] = self.view2_data['slice_info']
            self.view2_draw()
            self.on_draw10()
            self.view4_data['image'], self.view4_data['slice_info'] = self.get_color_data(self.view1_data, self.view2_data, self.view3_data)
            self.view4_draw()


    def OnSliceListBox03_update(self):
        if self.SliceListBox03.currentItem():
            DataSetName = self.ActiveData03_Combo.currentText()
            x_axis_list = self.hysp_cache.get_IDs(DataSetName, 'VARID1' )
            SelectedSlice = self.SliceListBox03.currentItem().text() #is text, may be sorted wihtout affecting the link to data
            SliceIndex = x_axis_list.index(SelectedSlice)
            self.view3_data['slice_info'] = x_axis_list[SliceIndex]
            self.view3_data['image'] = self.hysp_cache.get_Trans_3Dslice(DataSetName, 'IMAGE', SliceIndex )
            if self.ImgScales_Combo.currentText() == 'Individual':
                self.view3_data['pixel_MinMax'] = \
                    self.hysp_cache.get_OneTrans_3DSlice_MinMax_from_percentiles( DataSetName,
                                                                                  SliceIndex,
                                                                                  self.SetLow_Spin.value(),
                                                                                  self.SetHigh_Spin.value() )
            else:
                self.view3_data['pixel_MinMax'] = \
                    self.hysp_cache.get_Overall_3DSlice_MinMax_from_percentiles( DataSetName,
                                                                                 SliceIndex,
                                                                                 self.SetLow_Spin.value(),
                                                                                 self.SetHigh_Spin.value() )

            self.view3_data['highlight'] =  np.zeros_like(self.view3_data['image'], dtype=np.bool)
            self.View3_DataName.setText(DataSetName)
            self.view3_draw()
            self.view4_data['image'], self.view4_data['slice_info'] = self.get_color_data(self.view1_data, self.view2_data, self.view3_data)
            self.view4_draw()


    def get_data_empty(self):
        view_data = {}
        view_data['image'] = np.arange(20).reshape([4, 5])
        view_data['pixel_MinMax'] = (np.min(view_data['image']), np.max(view_data['image']))
        view_data['highlight'] =  np.zeros_like(view_data['image'], dtype=np.bool)
        view_data['slice_info'] = ''
        return view_data


    def get_color_data(self, v1, v2, v3):
        ColorMapInt = np.zeros( (v1['image'].shape[0], v1['image'].shape[1], 3), dtype=np.uint8 )
        color_info = ['','','']
        view_color0 = self.Colors.index(self.Color01_Combo.currentText())
        view_color1 = self.Colors.index(self.Color02_Combo.currentText())
        view_color2 = self.Colors.index(self.Color03_Combo.currentText())

        if view_color0 != 0:
            ix1 = view_color0-1
            ColorMapInt[:,:,ix1] = np.uint8( 255*(v1['image'] - np.nanmin(v1['image']) )/(np.nanmax(v1['image'])  - np.nanmin(v1['image'])))
            color_info[ix1] = v1['slice_info']
        if view_color1 != 0:
            ix2 = view_color1-1
            try:
                ColorMapInt[:,:,ix2] = np.uint8( 255*(v2['image'] - np.nanmin(v2['image']) )/(np.nanmax(v2['image'])  - np.nanmin(v2['image'])))
                color_info[ix2] = v2['slice_info']
            except ValueError:
                pass
        if view_color2 != 0:
            ix3 = view_color2-1
            try:
                ColorMapInt[:,:,ix3] = np.uint8( 255*(v3['image'] - np.nanmin(v3['image']) )/(np.nanmax(v3['image'])  - np.nanmin(v3['image'])))
                color_info[ix3] = v3['slice_info']
            except ValueError:
                pass

        return ColorMapInt, color_info

    """#TODO Do not forget to select pyside in the Spyder: Tools, Preferences, Python console, External modules
       Keep this comment as a reminder.
    """

    def create_view_frame1(self):
        self.view_frame1 = QtWidgets.QWidget()
        self.fig1 = Figure((5.0, 4.0), dpi=100) #, facecolor=self.figure_facecolor)
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setParent(self.view_frame1)
        self.canvas1.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas1.setFocus()

        self.mpl_toolbar1 = NavigationToolbar(self.canvas1, self.view_frame1)

        self.canvas1.mpl_connect('key_press_event1', self.on_key_press1)

        self.View1_DataName = QtWidgets.QLineEdit()
        self.View1_DataName.setReadOnly(True)
#        self.View1_DataName.setText()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas1)  # the matplotlib canvas
        vbox.addWidget(self.View1_DataName)
        vbox.addWidget(self.mpl_toolbar1)
        self.view_frame1.setLayout(vbox)
        self.view_frame1.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


    def create_view_frame2(self):
        self.view_frame2 = QtWidgets.QWidget()

        self.fig2 = Figure((5.0, 4.0), dpi=100) #, facecolor=self.figure_facecolor)
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setParent(self.view_frame2)
        self.canvas2.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas2.setFocus()

        self.mpl_toolbar2 = NavigationToolbar(self.canvas2, self.view_frame2)

        self.canvas2.mpl_connect('key_press_event2', self.on_key_press2)

        self.View2_DataName = QtWidgets.QLineEdit()
        self.View2_DataName.setReadOnly(True)
#        self.View2_DataName.setText()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas2)  # the matplotlib canvas
        vbox.addWidget(self.View2_DataName)
        vbox.addWidget(self.mpl_toolbar2)
        self.view_frame2.setLayout(vbox)
        self.view_frame2.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)


    def create_view_frame3(self):
        self.view_frame3 = QtWidgets.QWidget()

        self.fig3 = Figure((5.0, 4.0), dpi=100) #, facecolor=self.figure_facecolor)
        self.canvas3 = FigureCanvas(self.fig3)
        self.canvas3.setParent(self.view_frame3)
        self.canvas3.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas3.setFocus()

        self.mpl_toolbar3 = NavigationToolbar(self.canvas3, self.view_frame3)

        self.canvas3.mpl_connect('key_press_event3', self.on_key_press3)

        self.View3_DataName = QtWidgets.QLineEdit()
        self.View3_DataName.setReadOnly(True)
#        self.View3_DataName.setText()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas3)  # the matplotlib canvas
        vbox.addWidget(self.View3_DataName)
        vbox.addWidget(self.mpl_toolbar3)
        self.view_frame3.setLayout(vbox)
        self.view_frame3.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def create_view_frame4(self):
        self.view_frame4 = QtWidgets.QWidget()

        self.fig4 = Figure((5.0, 4.0), dpi=100) #, facecolor=self.figure_facecolor)
        self.canvas4 = FigureCanvas(self.fig4)
        self.canvas4.setParent(self.view_frame4)
        self.canvas4.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas4.setFocus()

        self.mpl_toolbar4 = NavigationToolbar(self.canvas4, self.view_frame4)

        self.canvas4.mpl_connect('key_press_event4', self.on_key_press4)

        self.View4_DataName = QtWidgets.QLineEdit()
        self.View4_DataName.setReadOnly(True)
#        self.View4_DataName.setText()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas4)  # the matplotlib canvas
        vbox.addWidget(self.View4_DataName)
        vbox.addWidget(self.mpl_toolbar4)
        self.view_frame4.setLayout(vbox)
        self.view_frame4.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def create_view_frame5(self, tab5_vbox):
        view_frame5 = QtWidgets.QWidget()
        view_frame5.setLayout(tab5_vbox)
        view_frame5.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        return view_frame5


    def line_select_callback(self, eclick, erelease):
        trace = True
        'eclick and erelease are the press and release events'
        x_start, y_start = eclick.xdata, eclick.ydata
        x_stop, y_stop = erelease.xdata, erelease.ydata
        if x_start < x_stop:
            x1 = x_start
            x2 = x_stop
        else:
            x2 = x_start
            x1 = x_stop

        if y_start < y_stop:
            y1 = y_start
            y2 = y_stop
        else:
            y2 = y_start
            y1 = y_stop

        view1_above_low  = (self.view1_data['image'] >= x1)
        view1_below_high  = (self.view1_data['image'] <= x2)
#        self.view1_data['highlight'] = view1_above_low & view1_below_high
        view1_range = view1_above_low & view1_below_high
        view2_above_low  = (self.view2_data['image'] >= y1)
        view2_below_high  = (self.view2_data['image'] <= y2)
#        self.view2_data['highlight'] = view2_above_low & view2_below_high
        view2_range = view2_above_low & view2_below_high
        if view1_range.shape == view2_range.shape:
            self.view1_data['highlight'] = view1_range & view2_range
            self.view2_data['highlight'] = view1_range & view2_range
            if trace:
                print("view1_range", view1_range.shape, np.count_nonzero(view1_range))
                print("view2_range", view2_range.shape, np.count_nonzero(view2_range))
                print("self.view1_data['highlight']", self.view1_data['highlight'].shape, np.count_nonzero(self.view1_data['highlight']))
                print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
                print(" The button you used was: %s %s" % (eclick.button, erelease.button))
            self.view1_draw()
            self.view2_draw()
        else: # Use data only from View 1
            self.view1_data['highlight'] = view1_range
            self.view1_draw()

        DataSetNameForSumOfSelectedFromView1 = self.ActiveData01_Combo.currentText()
        Name_RawDataSet = self.hysp_cache.get_Name_RawDataSet(DataSetNameForSumOfSelectedFromView1)

        full_data = np.asarray(self.hysp_cache.get_Data(Name_RawDataSet, 'IMAGE'))
        print('full_data',  full_data.shape)

        Sum_of_selected_spectra = np.zeros((full_data.shape[2]))
        for img_num in range(full_data.shape[2]):
            Sum_of_selected_spectra[img_num] = np.sum(full_data[self.view1_data['highlight'], img_num])

        print('Sum_of_selected_spectra', Sum_of_selected_spectra.shape)
        self.view3_x = self.hysp_cache.get_Data(Name_RawDataSet, 'VARID2')
        self.view3_y = Sum_of_selected_spectra
        self.View3_DataName.setText('Spectral sum from: '+ Name_RawDataSet)
        self.Selection3_DataSetName = Name_RawDataSet
        self.Selection3_Highlight = self.view1_data['highlight']
        self.on_vlines3()


    def Save_Unfolded_SelectedSpectra(self, FileName ):
        print('Enter Save_Unfolded_SelectedSpectra')
        if self.Selection3_DataSetName:
            self.hysp_cache.Save_selected_unfolded_from_one_image(self.Selection3_DataSetName, self.Selection3_Highlight, FileName, matlab_compatible=True)
        else:
            QtWidgets.QMessageBox.information(self,"No selected spectra were present","Please make a selection before saving it")


#    def Save_folded_pictures_to_Repository(self):
#        print('Enter Save_folded_pictures_to_Repository')



    def create_view_frame10(self):
        self.view_frame10 = QtWidgets.QWidget()
#        self.fig3 = Figure((5.0, 4.0), dpi=100)

        self.fig10, self.axes10 = plt.subplots(1,1, dpi=100) #, facecolor=self.figure_facecolor)
        self.canvas10 = FigureCanvas(self.fig10)
        self.canvas10.setParent(self.view_frame10)
        self.canvas10.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas10.setFocus()
        toggle_selector.RS = RectangleSelector(self.axes10, self.line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='pixels')

        plt.connect('key_press_event', toggle_selector)

        self.mpl_toolbar10 = NavigationToolbar(self.canvas10, self.view_frame10)

        self.canvas10.mpl_connect('key_press_event10', self.on_key_press10)

        self.View10_DataName = QtWidgets.QLineEdit()
        self.View10_DataName.setReadOnly(True)
#        self.View2_DataName.setText()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.canvas10)  # the matplotlib canvas
        vbox.addWidget(self.View10_DataName)
        vbox.addWidget(self.mpl_toolbar10)
        self.view_frame10.setLayout(vbox)
        self.view_frame10.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def remove_ticks(self, axes):
        axes.set_xticklabels([])
        axes.set_xticks([])
        axes.set_yticklabels([])
        axes.set_yticks([])

    def mask_nan(self, img, color_composition=0 ) :
        """Set missing values to grey, or for BW images set missing values to green"""
        currentColorMap = self.ColorMap_Combo.currentText()
        cmap_adj = matplotlib.cm.get_cmap(currentColorMap)
        cmap_adj.set_bad(self.missingColor[currentColorMap], 1.0)
        masked_array = np.ma.array(img, mask=np.isnan(img))
        return masked_array, cmap_adj


    def mask_highlight(self, img, mask ):
        currentColorMap = self.ColorMap_Combo.currentText()
        cmap_adj = matplotlib.cm.get_cmap(currentColorMap)
        cmap_adj.set_bad(self.highlightColor[currentColorMap], 1.0)
        masked_array = np.ma.array(img, mask=mask)
        return masked_array, cmap_adj

    def min_max_from_percentiles(self, img, lower_permille_tile, upper_permille_tile ):
        lower_percentile = 0.1*lower_permille_tile
        upper_percentile = 0.1*upper_permille_tile
        all_pixels = np.ravel( img )
        no_NaNs = np.isfinite(all_pixels)
        NoNaNpixels = all_pixels[no_NaNs]
        if NoNaNpixels.shape[0] > 0:
            if (upper_percentile < 100) and (upper_percentile > 0):
                local_max = scipy.stats.scoreatpercentile( NoNaNpixels, per=upper_percentile)
            else:
                local_max = np.nanmax(all_pixels)

            if (lower_percentile < 100) and (lower_percentile > 0):
                local_min = scipy.stats.scoreatpercentile( NoNaNpixels, per=lower_percentile)
            else:
                local_min = np.nanmin(all_pixels)
        else:
            local_min = None
            local_max = None
        return local_min, local_max


    def draw_pixels(self, view_data, axes):
        trace = False
        appearance = self.PixInterp_Combo.currentText()
        masked_array, cmap_adj = self.mask_highlight( view_data['image'], view_data['highlight'] )
        pixel_min, pixel_max = view_data['pixel_MinMax']
        if trace:
            local_check_min = np.min(view_data['image'])
            local_check_max = np.max(view_data['image'])
            print('local_check_min, local_check_max', local_check_min, local_check_max )
            print('pixel_min, pixel_max', pixel_min, pixel_max )
            print('isclose', np.isclose(pixel_min, pixel_max))

        if np.isclose(pixel_min, pixel_max):
            if trace:
                print('    ', 'not using min-max')
            im_handle = axes.imshow(masked_array, cmap=cmap_adj, interpolation=appearance)
        else:
            if trace:
                print('    ', 'using min-max')
            im_handle = axes.imshow(masked_array, cmap=cmap_adj,
                                    interpolation=appearance,
                                    vmin=pixel_min, vmax=pixel_max)
        return im_handle



    def view1_draw(self):
        self.fig1.clear()
        self.axes1 = self.fig1.add_subplot(111)
        im = self.draw_pixels(self.view1_data, self.axes1)

        divider = make_axes_locatable(self.axes1)
        colorbar_axis = divider.append_axes("right", size="4%", pad=0.03)
        self.fig1.colorbar(im, cax=colorbar_axis)
        data_size = '('+str(self.view1_data['image'].shape[0])+', '+str(self.view1_data['image'].shape[1])+')'
        self.axes1.set_xlabel(self.view1_data['slice_info']+' '+data_size)
        self.remove_ticks(self.axes1)
        self.canvas1.draw()


    def view2_draw(self):
        self.fig2.clear()
        self.axes2 = self.fig2.add_subplot(111)
        im = self.draw_pixels(self.view2_data, self.axes2)
#        imshow_interp = self.PixInterp_Combo.currentText()
#        overall_min = np.min(self.view2_data['image'])
#        overall_max = np.max(self.view2_data['image'])
#        masked_array, cmap_adj = self.mask_highlight( self.view2_data['image'], self.view2_data['highlight'] )
#        im = self.axes2.imshow(masked_array, cmap=cmap_adj,
#                               interpolation=imshow_interp,
#                               vmin=overall_min, vmax=overall_max)
        divider = make_axes_locatable(self.axes2)
        colorbar_axis = divider.append_axes("right", size="4%", pad=0.03)
        self.fig2.colorbar(im, cax=colorbar_axis)
        data_size = '('+str(self.view2_data['image'].shape[0])+', '+str(self.view2_data['image'].shape[1])+')'
        self.axes2.set_xlabel(self.view2_data['slice_info']+' '+data_size)
        self.remove_ticks(self.axes2)
        self.canvas2.draw()


    def on_draw10(self):
#        self.fig3.clear()
#        self.axes3 = self.fig3.add_subplot(111)
        self.axes10.cla()
        if self.is_matplotlib_v2:
            self.axes10.set_facecolor('w')
        if ('x-axis' in self.view10_data.keys()) and ('y-axis' in self.view10_data.keys()):
            if 'colors' in self.view10_data.keys():
#                print('Enter multicolor plot')
#                self.axes3.scatter(self.view10_data ['x-axis'], self.view10_data ['y-axis'],
#                                   c=self.view10_data ['colors'], marker='o', edgecolor ='k',
#                                   linewidth=0.5, alpha=.3) #scatter is slower for many (>200000) points

                for one_color in range(self.number_of_clusters):
                    selected_color = (self.view10_data['color_nums'] == one_color)
                    x_data = self.view10_data['x-axis'][selected_color]
                    y_data = self.view10_data['y-axis'][selected_color]
                    self.axes10.plot(x_data, y_data, 'o', c=self.unique_colors[one_color],
                                    alpha=.3, linewidth=0.5, markeredgecolor='k')
            else:
                self.axes10.plot(self.view10_data['x-axis'], self.view10_data['y-axis'], '.', c='b', alpha=.3)
            self.axes10.set_xlabel(self.view10_data['x-axis_label'])
            self.axes10.set_ylabel(self.view10_data['y-axis_label'])

        elif 'x-axis' in self.view10_data.keys():
            self.axes10.plot(self.view10_data['x-axis'], self.view10_data['x-axis'],'b.', alpha=.3)
            self.axes10.set_xlabel(self.view10_data['x-axis_label'])
        elif 'y-axis' in self.view10_data.keys():
            self.axes10.plot(self.view10_data['y-axis'], self.view10_data['y-axis'],'b.', alpha=.3)
            self.axes10.set_ylabel(self.view10_data['y-axis_label'])
        self.canvas10.draw()


    def view3_draw(self):
        self.fig3.clear()
        self.axes3 = self.fig3.add_subplot(111)
        im = self.draw_pixels(self.view3_data, self.axes3)
#        imshow_interp = self.PixInterp_Combo.currentText()
#        overall_min = np.min(self.view3_data['image'])
#        overall_max = np.max(self.view3_data['image'])
#        masked_array, cmap_adj = self.mask_highlight( self.view3_data['image'], self.view3_data['highlight'] )
#        im = self.axes3.imshow(masked_array, cmap=cmap_adj,
#                               interpolation=imshow_interp,
#                               vmin=overall_min, vmax=overall_max)
        divider = make_axes_locatable(self.axes3)
        colorbar_axis = divider.append_axes("right", size="4%", pad=0.03)
        self.fig3.colorbar(im, cax=colorbar_axis)
        data_size = '('+str(self.view3_data['image'].shape[0])+', '+str(self.view3_data['image'].shape[1])+')'
        self.axes3.set_xlabel(self.view3_data['slice_info']+' '+data_size)
        self.remove_ticks(self.axes3)
        self.canvas3.draw()


    def view4_draw(self):
        self.fig4.clear()
        self.axes4 = self.fig4.add_subplot(111)
        appearance = self.PixInterp_Combo.currentText()
        im = self.axes4.imshow(self.view4_data['image'],
                               interpolation=appearance)
        image_info = ''
        color_info = self.view4_data['slice_info']
        if color_info:
            if len(color_info) == 3:
                image_info = 'red: '+color_info[0]+ \
                             '  green: '+color_info[1]+ \
                             '  blue: '+color_info[2]

        data_size = '('+str(self.view4_data['image'].shape[0])+', '+str(self.view4_data['image'].shape[1])+')'

        self.axes4.set_xlabel(image_info+' '+data_size)
        self.remove_ticks(self.axes4)
        self.canvas4.draw()


    def on_plot2(self):
        self.fig2.clear()
        self.axes2 = self.fig2.add_subplot(111)
        self.axes2.plot(self.view2_x, self.view2_y)
#        self.axes2.imshow(self.view2_data['image'], interpolation='nearest')
#        self.axes2.plot([1,2,3])
        self.canvas2.draw()

    def on_vlines2(self):
        self.fig2.clear()
        self.axes2 = self.fig2.add_subplot(111)
        if self.is_matplotlib_v2:
            self.axes2.set_facecolor('w')
        y_baseline = np.zeros_like( self.view2_y )
        self.axes2.vlines( squeeze_mat( self.view2_x ), squeeze_mat( y_baseline ),
                           squeeze_mat( self.view2_y ), color='r', linestyles='solid',
                           linewidth=0.5)
        self.canvas2.draw()

    def on_vlines3(self):
        self.fig3.clear()
        self.axes3 = self.fig3.add_subplot(111)
        if self.is_matplotlib_v2:
            self.axes3.set_facecolor('w')
        y_baseline = np.zeros_like( self.view3_y )
        self.axes3.vlines( squeeze_mat( self.view3_x ), squeeze_mat( y_baseline ),
                           squeeze_mat( self.view3_y ), color='r', linestyles='solid',
                           linewidth=0.5)
        self.canvas3.draw()

    def on_key_press1(self, event):
        print('you pressed', event.key)
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas1, self.mpl_toolbar1)

    def on_key_press2(self, event):
        print('you pressed', event.key)
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas2, self.mpl_toolbar2)

    def on_key_press10(self, event):
        print('you pressed', event.key)
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas10, self.mpl_toolbar10)

    def on_key_press3(self, event):
        print('you pressed', event.key)
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas3, self.mpl_toolbar3)

    def on_key_press4(self, event):
        print('you pressed', event.key)
        # implement the default mpl key press events described at
        # http://matplotlib.org/users/navigation_toolbar.html#navigation-keyboard-shortcuts
        key_press_handler(event, self.canvas4, self.mpl_toolbar4)

    def UpdateFilelocation( self, FullFileName, Selector ):
        trace = False
        if trace:
            print()
            print( 'UpdateFilelocation ', type( FullFileName ))
            print( FullFileName )

        if Selector in ['CurrentInputFileLocation', 'CurrentScriptInputFileLocation',
                        'CurrentOutputFileLocation', 'CurrentAppendFileLocation' ]:
            CurrentDir = os.path.dirname(FullFileName)
            self.config.set( 'FileLocation',  Selector, CurrentDir)
            ConfigFile = open( self.inifile, mode='w')
            if trace:
                print( 'ConfigFile.encoding' , ConfigFile.encoding )
            self.config.write(ConfigFile)

        else: print( 'Internal error, Wrong selector for File location in ini-file' )


    def OnSplit_Images(self):
        print('OnSplit_Images')
        DsetList = self.hysp_cache.get_ListOfDataSets()
        split_exponent = 1
        for Dset in DsetList:
            if Dset[0:6] in ['nmf_T_', 'pca_T_']:
                pass
            else:
                print('    Processing dataset:', Dset)
                SplittedDataSets, all_pixels = self.hysp_cache.Split_image(Dset, split_exponent)
                if SplittedDataSets:
                    self.InpDataSetsListBox.addItems( SplittedDataSets )
                    self.Update_tab1( SplittedDataSets )
        print('OnSplit_Images finished')


    def OnMakeClasses(self):
        print('OnMakeClasses')
        DataSetName = self.ActiveData01_Combo.currentText()
        if 'ClusterColors' in self.hysp_cache.get_RecordNames(DataSetName):
            print("'ClusterColors' already defined for", DataSetName)
        else:
            self.hysp_cache.Add_cluster_colors(DataSetName)
            ClstColors_obj = self.hysp_cache.get_Data(DataSetName, 'ClusterColors')
            print('ClstColors_obj.shape',ClstColors_obj.shape)
            num_of_cluster_color_definitions = ClstColors_obj.shape[2]
            for Clst in range(num_of_cluster_color_definitions):
                Cdef = np.ravel(self.hysp_cache.get_3Dslice(DataSetName, 'ClusterColors', Clst ))
                num_of_clusters = len(set(Cdef))
                self.ClassColors_Combo.addItem(str(num_of_clusters)+' clusters')
            print('Finished defining clusters')

    def hasPrefix(self, DataSetName, prefix):
        return (DataSetName[0:len(prefix)] == prefix)


    def OnModelChange(self):
        if self.ModelSelector_Combo.currentText() == 'Non-neg matrix factorization':
            if self.VarScale_Combo.currentText() == 'Center':
                self.VarScale_Combo.setCurrentIndex( self.VarScale_Combo.findText('None') )


    def OnMakeModel(self):
        trace = True
        prefix = 'undef_'
        components = self.ModelComponents.value()
        binning=0
        ModDataSets = []

        get_UnfoldedData

        if trace:
            print()
            for cnt, Dset in enumerate(DsetList):
                print(cnt, Dset)

        if self.ModelSelector_Combo.currentText() == 'PCA':
            prefix = 'pca_T_'
        elif self.ModelSelector_Combo.currentText() == 'Non-neg matrix factorization':
            prefix = 'nmf_T_'

        """
        Remove previous models of same type if present"""
        for Dset in DsetList:
            if Dset[0:len(prefix)] == prefix:
                self.hysp_cache.remove(Dset)

        DsetList = self.hysp_cache.get_ListOfDataSets()

        if trace:
            print()
            for cnt, Dset in enumerate(DsetList):
                print(cnt, Dset)

        for Dset in DsetList:
            if (prefix == 'nmf_T_') and self.hasPrefix(Dset, 'pca_T_'):
                pass
            else:
                X0, img_index, y_index, x_index = self.hysp_cache.get_UnfoldedData(Dset, 'IMAGE', binning)
    #            x_scale = self.hysp_cache.get_Data(Dset, 'VARID2')

                if self.PreProcSelector_Combo.currentText() == 'Norm_by_Sdev (SNV part 2)':
                    X, SDev = PreProc.Norm_by_Sdev(X0)
                elif self.PreProcSelector_Combo.currentText() == 'Poisson scaling':
                    X = PreProc.Poisson_scaling(X0, np.mean(X0, axis=0))
                else:
                    X = X0

                if self.VarScale_Combo.currentText() == 'Center':
                    Xin, centrum = MVA_Lib.center(X)
                else:
                    Xin = X
                if self.ModelSelector_Combo.currentText() == 'PCA':
    #                with hsc.Timer('Normal SVD'):
    #                    T, P, S = MVA_Lib.PCA_by_SVD(Xin, components)
                    with hsc.Timer('Randomized SVD'):
                        T, P, S = MVA_Lib.PCA_by_randomizedSVD(Xin, components)
                elif self.ModelSelector_Combo.currentText() == 'Non-neg matrix factorization':
                    T, P = MVA_Lib.NMF(Xin, components)

                destDataSetName = self.hysp_cache.load_scores(Dset, prefix, y_index, x_index, T, loadings=P)
                ModDataSets.append(destDataSetName)

        if ModDataSets:
            self.InpDataSetsListBox.addItems( ModDataSets )
            self.InpDataSetsTreeView.AppendClass(ModDataSets, self.Class_number )
            self.Class_number += 1
            self.InpDataSetsTreeView.expandAll()
            self.InpDataSetsTreeView.resizeColumnToContents(0)
            self.Update_tab1(ModDataSets)

        print('OnMakeModel finished')





def main():
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
