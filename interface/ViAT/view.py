'''View ViAT
Created on 2020

@author: Verónica Henao Isaza

WorkerSignals: Defines the signals available from a running worker thread.
    
Worker: Inherits from QRunnable to handler worker thread setup,
        signals and wrap-up.
    
    By: https://www.learnpyqt.com/courses/concurrent-execution
    /multithreading-pyqt-applications-qthreadpool/
    
    
ViAT: Initial user view, allows you to record or view patient data
    
LoadRegistration: View of the data required by each patient
    
DataAcquisition: Visualization of the electrode configuration, the impedance of
                 each one and the verification of connected devices.
    
AcquisitionSignal: It allows to acquire the signal and the mark, under visual 
                    stimulation
    
DataBase: Allows you to view current information in the database

'''

from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFileDialog, QMessageBox, QDialog
from PyQt5.QtGui import QIntValidator
from PyQt5 import QtCore, QtWidgets
from matplotlib.figure import Figure
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import scipy.io as sio
import numpy as np
from scipy.signal import welch
import pandas as pd
from PyQt5.QtGui import QIcon, QPixmap
import wmi
from Stimulation_Acuity import Stimulus
from randData import RandData
import os
from PyQt5.QtWidgets import QWidget, QProgressBar, QPushButton, QLCDNumber
from PyQt5.QtCore import QBasicTimer
import pygame
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import traceback
import sys
from pylsl import StreamInfo, StreamOutlet
from pylsl import StreamInlet, resolve_stream
from datetime import datetime
import csv
import subprocess
import errno
import pyqtgraph as pg

from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtWidgets import QMessageBox
from PyQt5.uic import loadUi
from PyQt5.QtGui import QIcon, QPixmap
from datetime import datetime

# In[]
class WorkerSignals(QObject):
    '''
    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    '''
    finished = pyqtSignal() # with no data to indicate when the task is complete
    error = pyqtSignal(tuple) # which receives a tuple of Exception type, 
                              # Exception value and formatted traceback.
    result = pyqtSignal(object) # receiving any object type from the executed function.
    progress = pyqtSignal(int)

# In[]
class Worker(QRunnable):
    '''
    Worker thread

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # Return the result of the processing
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()  # Done

# In[]
class ViAT(QMainWindow):
    '''First user view
    
    Load a .ui type view designed in Qt designer
    
    :setup: this function contains the condition to move to the other views
    '''
    def __init__(self):
        super(ViAT, self).__init__()
        #The designed view is exported in qt designer
        loadUi('ViAT.ui', self)
        self.setWindowTitle('Inicio')
        self.setWindowIcon(QIcon('icono.png')) #window icon
        self.setup() 
        self.show()

    def assignController(self, controller):
        # create connection to controller
        self.my_controller = controller
        
    def asignar_controlador(self, controlador):
        self.__controlador = controlador

    def setup(self):
        self.startRegistration.clicked.connect(self.loadRegistration)
        self.patientData.clicked.connect(self.loadData)
        self.exit.clicked.connect(self.end)
        pixmap = QPixmap('Logo.png')
        self.logo.setPixmap(pixmap)

    def loadRegistration(self):
        self.__registry = LoadRegistration(self,self.__controlador,self.my_controller)
        self.__registry.show()
        self.hide()

    def loadData(self):
        self.__registry = DataBase(self,self.__controlador,self.my_controller)
        self.__registry.show()
        self.hide()

    def end(self):
        self.hide()
        exit()

# In[]        
#class LoadRegistration(QMainWindow):
#    '''Take data
#    
#        Allows you to collect basic information from patients or subjects
#    
#        :setup: this function contains the condition to move to the other views
#        
#        :clinicalhistoryInformation: Compare the data entered in the database to 
#        autocomplete the stationary fields
#        
#        :dataAcquisition: Check that the fields are completely filled
#        
#        :param variable controller: allows me to communicate with the model 
#        through the controller 
#    '''
#    def __init__(self, LR, controller):
#        super(LoadRegistration, self).__init__()
#        #The designed view is exported in qt designer
#        loadUi('Registro-HistoriaClinica.ui', self)
#        self.setWindowTitle('Registro')
#        self.setWindowIcon(QIcon('icono.png'))
#        self.setup()
#        self.show()
#        self.my_controller = controller # define controller variable
#
#        self.__parentLoadRegistration = LR
#
#    def setup(self):
#        self.back.clicked.connect(self.loadStart)
#        self.next.clicked.connect(self.dataAcquisition)
#        self.historyInfo.clicked.connect(self.info)
#        pixmap = QPixmap('blanclogo.png')
#        self.logo.setPixmap(pixmap)
#        
#    def info(self):
#        msg = QMessageBox()
#        msg.setIcon(QMessageBox.Warning)
#        msg.setText("Si el paciente o sujeto a registrar es nuevo, por favor complete todos los campos, si el sujetos ya se ha registrado antes unicamente llene los datos que han cambiado desde el ultimo registro")
#        msg.setWindowTitle("Ayuda")
#        x = msg.exec_()
#        
#    def clinicalhistoryInformation(self):
#        
#        self.my_controller.clinicalhistoryInformation(self.idAnswer.text(), 
#                                         self.nameAnswer.text(), 
#                                         self.lastnameAnswer.text(), 
#                                         self.ccAnswer.text(),
#                                         self.sexAnswer.currentIndex(), 
#                                         self.eyeAnswer.currentIndex(),
#                                         self.ageAnswer.value(),
#                                         self.glassesAnswer.currentIndex(),
#                                         self.snellenAnswer.currentIndex(),
#                                         self.CorrectionAnswer.currentIndex(),
#                                         self.stimulusAnswer.currentIndex(),
#                                         self.timeAnswer.text(),
#                                         self.responsibleAnswer.text())
#    def loadStart(self):
#        self.__parentLoadRegistration.show()
#        self.hide()
#
#    def dataAcquisition(self):
#        #        if not (self.idAnswer.text() and self.nameAnswer.text() and
#        #                self.lastnameAnswer.text() and self.responsibleAnswer.text() and self.ccAnswer.text()):
#        #            msg = QMessageBox()
#        #            msg.setIcon(QMessageBox.Warning)
#        #            msg.setText("Todos los campos marcados con * deben estar diligenciados")
#        #            msg.setWindowTitle("Alerta!")
#        #            x = msg.exec_()
#        #        else:
#        self.__registry = DataAcquisition(self, self.my_controller)
#        self.__registry.show()
#        self.clinicalhistoryInformation()
#        self.hide()

# In[]
class DataAcquisition(QMainWindow):
    '''Electrodes and devices
    
        Verify that the application can continue with the registration
    
        :setup: This function allows to:
                1. Initiate communication with OpenBCI
                2. Verify the existence of a second connected display 
                to show stimulation
                3. Observe the impedance at each electrode
                
        :param variable controller: allows me to communicate with the model 
        through the controller
    '''
    #Contains restrictions to follow the actions in an orderly manner
    def __init__(self, DA, controller):
        super(DataAcquisition, self).__init__()
        #The designed view is exported in qt designer
        loadUi('Adquisicion.ui', self)
        self.setWindowTitle('Adquisición')
        self.setWindowIcon(QIcon('icono.png'))
        self.setup()
        self.show()
        self.__parentDataAcquisition = DA
        self.threadpool = QThreadPool() #creating a group of threads in qt
        self.my_controller = controller

    def setup(self):
        self.back.clicked.connect(self.loadStart)
        self.infoAdquisition.clicked.connect(self.info)
        self.next.setEnabled(False)
        self.StopZ.setEnabled(False)
        self.detectDevice.setEnabled(False)
        self.startDevice.clicked.connect(self.Startdevice)
        self.FCz.setEnabled(False)
        self.Oz.setEnabled(False)
        self.O1.setEnabled(False)
        self.PO7.setEnabled(False)
        self.O2.setEnabled(False)
        self.PO8.setEnabled(False)
        self.PO3.setEnabled(False)
        self.PO4.setEnabled(False)
        self.GND.clicked.connect(self.startMeasurement)
        self.REF.clicked.connect(self.startMeasurement)
        self.FCz.clicked.connect(self.startMeasurement)
        self.PO3.clicked.connect(self.startMeasurement)
        self.PO4.clicked.connect(self.startMeasurement)
        self.PO7.clicked.connect(self.startMeasurement)
        self.PO8.clicked.connect(self.startMeasurement)
        self.O1.clicked.connect(self.startMeasurement)
        self.O2.clicked.connect(self.startMeasurement)
        self.Oz.clicked.connect(self.startMeasurement)
        
        pixmap = QPixmap('M.png')
        self.mounting.setPixmap(pixmap)
        pixmap1 = QPixmap('blanclogo.png')
        self.logo.setPixmap(pixmap1)
        
    def info(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Comience identificando que el dispositivo esta conectado y que puede comenzar a adquirir los datos, se abrirá una ventana negra en la cual se muestran los datos adquiridos, presione 'Miminizar' y a continuación verifique que la pantalla de estimulación se encuentra conectada y ahora, para verificar la impedancia presione cualquiera de los electrodos de la configuración. Antes de pasar a la siguiente etapa recuerde detener la medición de la impedancia ")
        msg.setWindowTitle("Ayuda")
        x = msg.exec_()
        
    def loadStart(self):
        self.__parentDataAcquisition.show()
        self.hide()

    def executeAcquisition(self):
        self.next.setEnabled(False) #Revisar genera delay
        self.__registry = AcquisitionSignal(self, self.my_controller)
        self.__registry.show()
        self.hide()
        
        
    def returnLastZ(self):
        return self.my_controller.returnLastZ()

    def startMeasurement(self):
        self.my_controller.startZ()
        self.StopZ.setEnabled(True)
        self.StopZ.clicked.connect(self.StopMeasurement)
        
        print("Iniciar medicion")
        self.timer = QtCore.QTimer(self) #creating a time thread
        self.timer.timeout.connect(self.printZ)
        self.timer.start(22)  # speed in milliseconds discriminated by human eye


    def fGND(self):
        self.GND.setEnabled(False)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Verifique la conexion del electrodo")
        msg.setWindowTitle("Alerta!")
        x = msg.exec_()

    def fREF(self):
        self.REF.setEnabled(False)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Verifique la conexion del electrodo")
        msg.setWindowTitle("Alerta!")
        x = msg.exec_()
        
    def printZ(self):
        Z = self.returnLastZ()
        self.impedanceFCZ.display(Z[0])
        self.impedanceOZ.display(Z[1])
        self.impedanceO1.display(Z[2])
        self.impedancePO7.display(Z[3])
        self.impedanceO2.display(Z[4])
        self.impedancePO8.display(Z[5])
        self.impedancePO3.display(Z[6])
        self.impedancePO4.display(Z[7])
    
    def StopMeasurement(self):
        self.timer.stop()
        self.my_controller.stopZ()
        print("detener impedancia")
        self.next.setEnabled(True)
        self.next.clicked.connect(self.executeAcquisition)

    def Startdevice(self):
        #use worker function explained at startup
        self.worker = Worker(self.execute_this_fn)
        self.worker.signals.result.connect(self.print_output)  # s
        self.worker.signals.finished.connect(self.thread_complete)
        self.worker.signals.progress.connect(self.progress_fn)  # n
        # Execute
        self.threadpool.start(self.worker)
        
        
        self.detectDevice.setEnabled(True)
        self.detectDevice.clicked.connect(self.device)
        
    def device(self):
       
        self.FCz.setEnabled(True)
        self.Oz.setEnabled(True)
        self.O1.setEnabled(True)
        self.PO7.setEnabled(True)
        self.O2.setEnabled(True)
        self.PO8.setEnabled(True)
        self.PO3.setEnabled(True)
        self.PO4.setEnabled(True)
        self.my_controller.startData()

        ##Allows to detect if there is a second screen connected
#        obj = wmi.WMI().Win32_PnPEntity(ConfigManagerErrorCode=0)
#        displays = [x for x in obj if 'DISPLAY' in str(x)]
#        num=len(displays)
#        if num==3:
#            self.next.setEnabled(True)
#            self.next.clicked.connect(self.executeAcquisition)
#        else:
#            msg = QMessageBox()
#            msg.setIcon(QMessageBox.Warning)
#            msg.setText("Debe conectar una segunda pantalla para poder iniciar la adquisición")
#            msg.setWindowTitle("Alerta!")
#            num=0
#            x = msg.exec_()
        self.detectDevice.setEnabled(False)
       
    def progress_fn(self, n):
        pass

    def execute_this_fn(self, progress_callback):
        self.my_controller.startDevice()
        

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE!")

# In[]
class AcquisitionSignal(QMainWindow):
    '''
        This module allows to start the visual stimulation, and allows 
        to visualize the acquired signals in real time.

        It is divided into two sections:
        
        1. The first view allows you to start and restart the stimulus. 
        Disconnecting the device will observe the results of the subject 
        that has been registered
        2. The second part only allows to view the signals in real time
    
        :param variable controller: allows me to communicate with the model 
        through the controller    
    '''
    def __init__(self, AS, controller):
        super(AcquisitionSignal, self).__init__()
        #The designed view is exported in qt designer
        loadUi('Adquisicion_accion.ui', self)
        self.setWindowTitle('Adquisición')
        self.setWindowIcon(QIcon('icono.png'))
        self.setup()
        self.show()
        self.counter = 0
        self.__parentAcquisitionSignal = AS
        self.threadpool = QThreadPool() #creating a group of threads in qt
        print("Multithreading with maximum %d threads" %
        self.threadpool.maxThreadCount())
        self.timer = QTimer()  #creating a time thread
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()
        self.my_controller = controller
        self.step = 0
        

    def setup(self):
        pixmap1 = QPixmap('blanclogo.png')
        self.logo.setPixmap(pixmap1)
        self.play.clicked.connect(self.startPlay)
        self.stop.setEnabled(False)
#        self.patientData.clicked.connect(self.loadData)
        self.back.clicked.connect(self.loadStart)
        self.exit.clicked.connect(self.end)
        self.playGraph.clicked.connect(self.startGraph)
        self.stopGraph.clicked.connect(self.haltGraph)
        self.adquisitionInfo.clicked.connect(self.info)
        self.stopDevice.clicked.connect(self.stopProcess)
    
    def closeData(self,data):
        data.close()
        
        
    def info(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("En la parte superior encontrara dos pestañas, la de inicio, en la que se encuentra actualmente y la de visualización, en la cual podra observar la señal adquirida en tiempo real. Primero debe presionar el botón inicio en la pestaña actual, luego, pase a la pestaña de visualización y presione 'visualiza', en la primera pestaña podra observar una barra de proceso que le anunciara que el estimulo esta a punto de presentarse. Al terminar podra visualizar los resultados de la estimulación en esta misma pestaña, para visualizar resultados anteriores o de otro pacientes, dirijase a 'Base de datos pacientes'  ")
        msg.setWindowTitle("Ayuda")
        x = msg.exec_()

    def startPlay(self):
        self.stop.setEnabled(True)
        self.stop.clicked.connect(self.stopEnd)
        self.play.setEnabled(False)
        try:
            pygame.init()
            # Any other args, kwargs are passed to the run function
            self.worker = Worker(self.execute_this_fn)
            self.play.setEnabled(False)
            pygame.quit()
            self.worker.signals.result.connect(self.print_output)  # s
            self.worker.signals.finished.connect(self.thread_complete)
            self.worker.signals.progress.connect(self.progress_fn)  # n
            # Execute
            self.threadpool.start(self.worker)
        except:
            pygame.quit()

    def progress_fn(self, n):
        pass


    def execute_this_fn(self, progress_callback):
        veces=0
        while veces<10:
            time.sleep(veces) #increment one second when entering while
            value = self.alert.value()
            if value < 100:
                value = value + 10 #progress bar
                self.alert.setValue(value)
            else:
                self.timer.stop()
            veces=veces+1
#        time.sleep(15)  # if the while is not used for the progress bar
        self.my_controller.startStimulus()
        self.my_controller.stopStimulus()


    
    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("COMPLETE!")

    def stopEnd(self):#Reset
        self.play.setEnabled(True)
        pygame.quit()
        self.alert.setValue(0)

    def loadData(self):
        self.__registry = DataBase(self,self.__controlador,self.my_controller)
        self.__registry.show()
        self.hide()

    def loadStart(self):
        self.__parentAcquisitionSignal.show()
        self.hide()
    
    def end(self):
        self.hide()
        exit()

    def recurring_timer(self):
        pass

    def returnLastData(self):
        return self.my_controller.returnLastData()
    
    def stopProcess(self):
        self.my_controller.stopDevice()
        
        

    def graphData(self):
        ''' This function allows to graph and save the registry data
            data arrives from the model, where it is acquired by the device 
            and configured, passes through the controller before reaching the view
            The date is also saved to have control of the acquisition and to
            be able to carry out the processing with the marks associated with the stimulus.
        '''
        data, Powers, freq, laplace, Plaplace, flaplace = self.returnLastData()
        data = data - np.mean(data, 0)
        if data.ndim == 0:
            print("Lista vacia")
            return
        print('valor frecuencia',freq[-1])
        self.welchPlot.clear()
        self.welchPlot.plot(x=freq,y=Powers[1,:],pen=('#208A8A'))
        self.welchPlot.repaint()
        self.welchLaplace.clear()
        self.welchLaplace.plot(x=flaplace,y=Plaplace[0,:], pen=('#0D6B9D'))
        self.welchLaplace.repaint()
        self.viewSignalOz.clear()
        self.viewSignalOz.plot(np.round(data[1, :], 1), pen=('#CD10B4'))
        self.viewSignalOz.repaint()
        self.viewSignalO1.clear()
        self.viewSignalO1.plot(np.round(data[2, :], 1), pen=('#1014CD'))
        self.viewSignalO1.repaint()
        self.viewSignalPO7.clear()
        self.viewSignalPO7.plot(np.round(data[3, :], 1), pen=('#10CD14'))
        self.viewSignalPO7.repaint()
        self.viewSignalO2.clear()
        self.viewSignalO2.plot(np.round(data[4, :], 1), pen=('#F7FB24'))
        self.viewSignalO2.repaint()
        self.viewSignalPO8.clear()
        self.viewSignalPO8.plot(np.round(data[5, :], 1), pen=('#FBB324'))
        self.viewSignalPO8.repaint()
        self.viewSignalPO3.clear()
        self.viewSignalPO3.plot(np.round(data[6, :], 1), pen=('#E53923'))
        self.viewSignalPO3.repaint()
        self.viewSignalPO4.clear()
        self.viewSignalPO4.plot(np.round(data[7, :], 1), pen=('#806123'))
        self.viewSignalPO4.repaint()


    def startGraph(self):
        '''
        call the data in the controller
        '''
        self.my_controller.startData()

        print("Iniciar senal")
        self.timer = QtCore.QTimer(self)
        # timer.setSingleShot(True)
        self.timer.timeout.connect(self.graphData)
        self.timer.start(22)  # milisegundos ojo humano
        # print(self.timer.isActive())

    def haltGraph(self):
        self.timer.stop()
        self.my_controller.stopData()
        print("detener senal")

# In[]
#class DataBase(QMainWindow):
#    '''
#        This module allows searching the patient's database for the history 
#        and observing their results and the signs associated with that subject.
#    
#        :param variable controller: allows me to communicate with the model 
#        through the controller    
#    '''
#    def __init__(self, DB, controller):
#        super(DataBase, self).__init__()
#        loadUi('Adquisicion_datos.ui', self)
#        self.setWindowTitle('Base de datos')
#        self.setWindowIcon(QIcon('icono.png'))
#        self.setup()
#        self.show()
#        self.__parentDataBase = DB
#        self.my_controller = controller
#
#    def setup(self):
#        pixmap1 = QPixmap('blanclogo.png')
#        pixmap2 = QPixmap('nube.png')
#        self.logo.setPixmap(pixmap1)
#        self.cloud.setPixmap(pixmap2)
#        self.cloudButton.clicked.connect(self.cloudData)
#        self.behind.clicked.connect(self.delaySignal)
#        self.before.clicked.connect(self.forwardSignal)
#        self.patientAcquisition.clicked.connect(self.dataAcquisition)
#        self.back.clicked.connect(self.loadStart)
#        self.exit.clicked.connect(self.end)
#        self.stopDevice.clicked.connect(self.stopData)
#        self.adquisitionInfo.clicked.connect(self.info)
#        self.adquisitionInfo_2.clicked.connect(self.info2)
#        self.stopDevice.clicked.connect(self.stopProcess)
#        self.dataSet.clicked.connect(self.searchData)
#        
#    
#    def cloudData(self):
#        print('se subio a la nube')
#        self.my_controller.webclinicalhistoryInformation()
#        
#    def searchData(self):
#        self.my_controller.searchClinicalhistory()
#        
#    def info(self):
#        msg = QMessageBox()
#        msg.setIcon(QMessageBox.Warning)
#        msg.setText("En la parte superior encontrara dos pestañas, la de inicio, en la que se encuentra actualmente y la de visualización, en la cual podra observar la señal registrada. Primero debe buscar del sujeto de interes por ID, CC o fecha de registro, presione buscar y seleccione el registro que desea visualizar. Se recomienda desconectar el dispositivo si no se realizaran más registros durante la exploración de los datos. Podra visualizar los resultados de la estimulación en esta misma pestaña y visualizar la señal en la pestaña 'Visualización'  ")
#        msg.setWindowTitle("Ayuda")
#        x = msg.exec_()
#    
#    def info2(self):
#        msg = QMessageBox()
#        msg.setIcon(QMessageBox.Warning)
#        msg.setText("Puede observar el espectro de la señal de interes al presiónar el canal o desplazarse por las señales en cada canal al mover las flechas")
#        msg.setWindowTitle("Ayuda")
#        x = msg.exec_()
#
#    def delaySignal(self):#Atras
#        pass
#    
#    def stopData(self):
#        pass
#
#    def forwardSignal(self):#Adelante
#        pass
#
#    def dataAcquisition(self):
#        self.__registry = DataAcquisition(self,self.my_controller)
#        self.__registry.show()
#        self.hide()
#
#    def loadStart(self):
#        self.__parentDataBase.show()
#        self.hide()
#    
#    def stopProcess(self):
#        self.my_controller.stopDevice()
#
#    def end(self):
#        self.hide()
#        exit()

# In[]
class LoadRegistration(QDialog):
    def __init__(self, LR, controlador , controller):
        super(LoadRegistration, self).__init__()
        loadUi("Agregardatos.ui", self)
        self.setup()
        self.setWindowTitle('Base de datos')
        self.setWindowIcon(QIcon('icono.png'))
        self.setup()
        self.show()
        self.__parentLoadRegistration = LR
        self.__controlador = controlador
        self.my_controller = controller
        
    def setup(self):
        self.btn_buscar.clicked.connect(self.buscar)
        self.btn_agregar.clicked.connect(self.agregar)
        self.btn_mostrar.clicked.connect(self.mostrar)
        self.back.clicked.connect(self.loadStart)
        self.next.clicked.connect(self.dataAcquisition)
        pixmap1 = QPixmap('blanclogo.png')
        self.logo.setPixmap(pixmap1)
        
    def asignar_controlador(self, controlador):
        self.__controlador = controlador
    
    def desactivar(self):
       self.nombre.setEnabled(False)
       self.apellidos.setEnabled(False)
       self.d.setEnabled(False)
       self.cc.setEnabled(False)
       self.sexo.setEnabled(False)
       self.dominante.setEnabled(False)
       self.glasses.setEnabled(False)
       self.snellen.setEnabled(False)
       self.correction.setEnabled(False)
       self.stimulus.setEnabled(False)
       self.edad.setEnabled(False)
       self.time.setEnabled(False)
       self.rp.setEnabled(False)
        
    def buscar(self):
        buscar = self.cc.text()
        result = self.__controlador.obtener_uno(buscar)
        if result != False:
            self.show_info(result)
            self.desactivar()
        else:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Información no encontrada")
            msg.show()
            
            self.activar()
            
    def activar(self):
    		self.nombre.setEnabled(True)
    		self.apellidos.setEnabled(True)
    		self.cc.setEnabled(True)
    		self.sexo.setEnabled(True)
    		self.d.setEnabled(True)
    		self.dominante.setEnabled(True)
    		self.glasses.setEnabled(True)
    		self.snellen.setEnabled(True)
    		self.correction.setEnabled(True)
    		self.stimulus.setEnabled(True)
    		self.edad.setEnabled(True)
    		self.time.setEnabled(True)
    		self.rp.setEnabled(True)
    		self.btn_agregar.setEnabled(True)
    		self.d.setText("")
    		self.nombre.setText("")
    		self.apellidos.setText("")
    		self.cc.setText("")
    		self.sexo.setText("")
    		self.dominante.setText("")
    		self.cc.setText("")
    		self.glasses.setText("")
    		self.snellen.setText("")
    		self.correction.setText("")
    		self.stimulus.setText("")
    		self.edad.setText("")
    		self.time.setText("")
    		self.rp.setText("")
    
    def show_info(self, result):
        info = result[0]
        self.materias = result[1]
        self.d.setText(info[0])
        self.nombre.setText(info[1])
        self.apellidos.setText(str(info[2]))
        self.cc.setText(str(info[3]))
        self.sexo.setText(str(info[4]))
        self.dominante.setText(str(info[5]))
        self.glasses.setText(str(info[6]))
        self.snellen.setText(str(info[7]))
        self.correction.setText(str(info[8]))
        self.stimulus.setText(str(info[9]))
        self.edad.setText(str(info[10]))
        self.time.setText(str(info[11]))
        self.rp.setText(str(info[12]))
        self.cc.setText("")
        self.btn_agregar.setEnabled(False)
            
    def agregar(self):
        data = {
            "d":self.d.text(),
			"nombre":self.nombre.text(),
			"apellidos": self.apellidos.text(),
			"Materias": [],
			"cc":self.cc.text(),
            "sexo":(self.sexo.text()),
            "dominante":(self.dominante.text()),
			"gafas":(self.glasses.text()),
			"snellen":(self.snellen.text()),
			"corregida":(self.correction.text()),
			"estimulo":(self.stimulus.text()),
			"edad":(self.edad.text()),
			"tiempo":(self.time.text()),
			"rp":(self.rp.text())
		}
        bandera = self.__controlador.agregar_datos(data)
        if bandera == True:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Information)
            msg.setText("Información Agregada")
            msg.show()
        self.activar()
        self.btn_agregar_materia.setEnabled(True)
        
    def mostrar(self):
            self.__registry = DataBase(self,self.__controlador,self.my_controller)
            self.__registry.show()
            self.hide()
        
    def loadStart(self):
        self.__parentLoadRegistration.show()
        self.hide()

    def dataAcquisition(self):
        self.__registry = DataAcquisition(self, self.my_controller)
        self.__registry.show()
        self.hide()
    
# In[]
        
class DataBase(QDialog):
    def __init__(self, DB,controlador , controller):
        super(DataBase, self).__init__()
        loadUi("Buscardatos.ui", self)
        self.setWindowTitle('Base de datos')
        self.setWindowIcon(QIcon('icono.png'))
        self.setup()
        self.show()
        self.configurar_TreeWidget()
        self.__parentDataBase = DB
        self.__controlador = controlador
        self.my_controller = controller
        
    def configurar_TreeWidget(self):
    		self.tabla.setStyleSheet('Background-color:rgba(255, 215, 255,20);')
    		self.tabla.setColumnWidth(0, 150)
    		self.tabla.setColumnWidth(1, 110)
    		self.tabla.setColumnWidth(2, 110)
    		self.tabla.setColumnWidth(3, 110)
    		self.tabla.setColumnWidth(4, 110)
    		self.tabla.setColumnWidth(5, 110)
            
    def asignar_controlador(self, controlador):
        self.__controlador = controlador
    
    def setup(self):
        self.le_buscar.setPlaceholderText("Cedula del sujeto")
        self.btn_mostrar.clicked.connect(self.mostrar_todo)
        self.btn_buscar.clicked.connect(self.buscar)
        self.tabla.itemDoubleClicked.connect(self.dbclick)
        self.back.clicked.connect(self.loadStart)

        pixmap1 = QPixmap('blanclogo.png')
        self.logo.setPixmap(pixmap1)
        
    def mostrar_todo(self):
        results = self.__controlador.obtener_integrantes()
        self.mostrar(results)
        
            
    def buscar(self):
    		buscar = self.le_buscar.text()
    		self.le_buscar.setText("")
    		self.le_buscar.setPlaceholderText("Cedula del sujeto")
    		results = self.__controlador.buscar_integrantes(buscar)
    		self.mostrar(results)
            
    def mostrar(self, results):
        self.tabla.clear()
        for result in results:
            item = QTreeWidgetItem(self.tabla)
            for i in range(14):
                item.setText(i,str(result[i]))
                
    def dbclick(self):
        data = self.tabla.currentItem()
        buttonReply = QMessageBox.question(self, 'Borrar Información', 
			u"¿Desea borrar a %s de la lista de integrantes?"%data.text(0), 
			QMessageBox.Yes | QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.__controlador.borrar(data.text(0))
            self.mostrar_todo()
        if buttonReply == QMessageBox.No:
            pass
        if buttonReply == QMessageBox.Cancel:
            pass

    def loadStart(self):
        self.__parentDataBase.show()
        self.hide()
    	

