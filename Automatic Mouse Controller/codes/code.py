from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QThread, QCoreApplication,pyqtSignal
from form import form
from pynput import mouse, keyboard
import time

#main python file that handles most of the processes on the app

#worker thread
class mouseObserverThread(QThread): #dis observes the mouse movement
    signalFinish = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.movements = []
        self._running = True  # Flag to control stopping
        self.listener = None  # Store listener reference

    def run(self):
        print("mouse observer worker thread started, now observing the mouse movements")
        #record mouse movement
        def onMove(x, y):
            if self._running:
                self.movements.append(("move",(x,y)))
            

        def onClick(x, y, button, pressed):
            if pressed and self._running:
                self.movements.append(("click",(x,y)))

        #assign the functions above(onMove, onClick and onScroll) to the mouse listener's action list
        while self._running:
            self.listener = mouse.Listener(on_move = onMove, on_click = onClick)
            self.listener.start()
            self.listener.join() #start the listener

    def getMovements(self): #get mouse movement
        return self.movements 

    def stopListening(self):
        print("Mouse observer stopping...")
        self._running = False #stop the loop
        print("Mouse Listernet stopping...")
        if self.listener:
            self.listener.stop() #stop the listener
        print("mouse observer and mouse listener stopped successfully")
        self.quit()
        self.wait()
    
    def restart(self):
        self.stopListening()  # Stop the listener and wait for the thread to finish
        self.wait()  # Ensure the thread is fully stopped before proceeding
        self.movements.clear()
        self.movements = []
        self._running = True  # Set _running to True for the new listener
        self.start()  # Start a new thread with the new listener

    def stop(self):
        self.stopListening()

class keyboardObserverThread(QThread): #dis thread listen to keyboard
    enterPressed = pyqtSignal()
    stopPlayback = pyqtSignal()
    modeReceiver = pyqtSignal(str)
    signalFinish = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._running = True
        self.listener = None
        self.mode = None
        self.modeReceiver.connect(self.modeSetter)

    def run(self):
        print(f"keyboard worker thread started, now listening on key press and mode {self.mode}")
        def onEnterPress(key):
            try:
                if key == keyboard.Key.enter and self.mode == "mouse recording" and self._running:
                    self.enterPressed.emit()
                elif key == keyboard.Key.enter and self.mode == "mouse playback" and self._running:
                    self.stopPlayback.emit()
                else:
                    print(f"wrong key: ")
                    print(f"mode received: {self.mode}")
            except AttributeError:
                pass
    
 # Assign the function above (onEnterPress) to keyboard listener's action key
        self.listener = keyboard.Listener(on_press=onEnterPress)
        self.listener.start()

        while self.listener.running:
            time.sleep(0.1)

        if self.listener:
            self.listener.stop()

    def modeSetter(self, modee):
        self.mode = modee

    def startListening(self):
        if not self.isRunning():
            self._running = True
            self.start()

    def stopListening(self):
        print("Keyboard observer stopping...")
        self._running = False
        print("keyboard listener stopping...")
        if self.listener:
            self.listener.stop()
        self.mode = None
        print("Keyboard observer and lister stopped succesfully")
        self.quit()
        self.wait()

    def restart(self):
        self.stopListening()  # Stop the listener and wait for the thread to finish
        self.wait()  # Ensure the thread is fully stopped before proceeding
        self._running = True  # Set _running to True for the new listener
        self.start()  # Start a new thread with the new listener

    def stop(self):
        self.stopListening()

class mouseMoverThread(QThread): #thread for playing the recorded mouse movements
    movementReceiver = pyqtSignal(list, int)
    mouseMoverThreadFinish = pyqtSignal()
    signalFinish = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.movementReceiver.connect(self.movementProcessor)
        self._running = True
        self.listener = None

    def run(self):
        print("mouse mover worker thread is started")

    def movementProcessor(self, movement, loopCount):
        print(f"loop count: {loopCount}")
        if loopCount == 0:
            loopa = 0
            while self._running:
                for action, coords in movement:
                    if not self._running:
                        break
                    x, y = coords
                    if action == 'click':
                        mouse.Controller().position = (x,y)
                        mouse.Controller().click(mouse.Button.left)
                    elif action == 'move':
                        mouse.Controller().position = (x,y)
                    self.msleep(12) 
                    QCoreApplication.processEvents()
                loopa += 1
                print(f"looped {loopa} times")
        elif loopCount != 0:
            for i in range(1, loopCount  + 1):
                for action, coords in movement:
                    if not self._running:
                        break
                    x, y = coords
                    if action == 'click':
                        mouse.Controller().position = (x,y)
                        mouse.Controller().click(mouse.Button.left)
                    elif action == 'move':
                        mouse.Controller().position = (x,y)
                    self.msleep(12) 
                    QCoreApplication.processEvents()
                print(f"looped {i} times")
            print("loop finished now quiting thread")
        self.mouseMoverThreadFinish.emit()

    def stop(self):
        self._running = False
        self.quit()
        self.wait()

#main thread
class windowForm(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = form.Ui_Widget()
        self.ui.setupUi(self) 

    # app setup
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowCloseButtonHint)    

    #threads
        self.mouseObserver = mouseObserverThread()
        self.keyboardObserver = keyboardObserverThread()
        self.mouseMover = mouseMoverThread()
        self.keyboardObserver.enterPressed.connect(self.enterPressed)
        self.keyboardObserver.stopPlayback.connect(self.stopPlayback)
        self.mouseMover.mouseMoverThreadFinish.connect(self.mouseMoverCloseThread)

    #widgets placed into variables
        self.btnRecord = self.ui.buttonRecord
        self.btnPlay = self.ui.buttonPlay

        self.counterLoopCount = self.ui.counterLoopValue

        self.selectedMovement = self.ui.labelMovementName
        self.status = self.ui.labelStatus

        self.loopCount = self.counterLoopCount.value()
        self.btnPlay.setEnabled(True)
    #widget functions
        self.btnRecord.clicked.connect(self.on_btn_press_btnRecord)
        self.btnPlay.clicked.connect(self.on_btn_press_btnPlay)

    #default values
        self.statusValues = ["idle", "working", "recording", "playing", "gioghet"]
        self.selectedMovementValues = ["press Enter to stop recording"]    

        self.currentMovement = []

        self.mode = "None"

    #UI Settings
        self.btnPlay.setEnabled(False)

#functions when a widget is pressed
    def on_btn_press_btnRecord(self):
        print("btnRecord is pressed")
        self.recordMouseMovement()
    
    def on_btn_press_btnSave(self):
        print("btnSave is pressed")

    def on_btn_press_btnPlay(self):
        print("btnplay is pressed")
        self.mousePlay()

#callable functions 
    def recordMouseMovement(self):
        self.currentMovement = []
        self.btnRecord.setEnabled(False)
        self.btnPlay.setEnabled(False)
        self.status.setText(self.statusValues[2])
        self.selectedMovement.setText(self.selectedMovementValues[0])
        self.currentMovement.clear()

        if not self.mouseObserver.isRunning():
            self.mouseObserver.restart()
            print("starting mouse worker thread")

        if not self.keyboardObserver.isRunning():
            self.keyboardObserver.restart()
            self.keyboardObserver.modeReceiver.emit("mouse recording")
            print("starting keyboard worker thread")

    def recordMouseMovementFinished(self):
        self.btnRecord.setEnabled(True)
        self.btnPlay.setEnabled(True)
        self.btnPlay.setEnabled(True)
        self.status.setText(self.statusValues[0])
        self.selectedMovement.setText("Recorded movement using record button")

    def saveMouseMovement(self):
        pass

    def mousePlay(self):
        print("playing selected mouse movement")
        self.btnRecord.setEnabled(False)
        self.btnPlay.setEnabled(False)
        self.status.setText("working")

        self.selectedMovement.setText("Press enter to stop mouse playback")
        if not self.mouseObserver.isRunning():
            self.keyboardObserver.restart()
            self.keyboardObserver.modeSetter("mouse playback")

        if not self.mouseMover.isRunning():
            self.mouseMover.start()
            self.mouseMover._running = True
            self.mouseMover.movementReceiver.emit(self.currentMovement, self.counterLoopCount.value())

    def enterPressed(self):
        self.currentMovement = []
        self.currentMovement = self.mouseObserver.getMovements()
        self.mouseObserver.stop()
        self.keyboardObserver.stop()
        self.recordMouseMovementFinished()
        
    def mouseMoverCloseThread(self):
        self.btnRecord.setEnabled(True)
        self.btnPlay.setEnabled(True)
        self.btnPlay.setEnabled(True)
        self.status.setText(self.statusValues[0])
        self.mouseMover.stop()
        self.keyboardObserver.stop()
        print("Mouse mover done")

    def stopPlayback(self):
        self.btnRecord.setEnabled(True)
        self.btnPlay.setEnabled(True)
        self.btnPlay.setEnabled(True)
        self.status.setText(self.statusValues[0])
        self.mouseMover.stop()
        self.keyboardObserver.stop()
        print("Mouse mover done")
