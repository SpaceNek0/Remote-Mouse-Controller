from PyQt6.QtWidgets import QApplication, QWidget
from codes.code import windowForm

# main script, used to run the app

def runWidget():
    app = QApplication([])
    window = windowForm() 
    window.show()
    app.exec() 

if __name__ == "__main__":
    runWidget()