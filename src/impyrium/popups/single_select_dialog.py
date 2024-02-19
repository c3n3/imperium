import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QPushButton, QWidget, QVBoxLayout, QLabel, QComboBox, QHBoxLayout

from ..inputless_combo import InputlessCombo

class SingleSelectDialog(QDialog):
    def __init__(self, doneFun, name, items, devices, parent: QWidget = None):
        super().__init__(parent)
        self.doneFun = doneFun
        self.mainLayout = QVBoxLayout(self)
        self.instructions = QLabel(self)
        self.name = name
        self.instructions.setText(name)
        self.setWindowTitle(self.name)
        self.setMinimumWidth(450)

        self.combo = InputlessCombo(self)
        self.items = items
        for item in self.items:
            self.combo.addItem(item)
        self.combo.currentIndexChanged.connect(self.changeType)
        self.comboLabel = QLabel("Select")
        self.comboLabel.setBuddy(self.combo)

        self.devcombo = InputlessCombo(self)
        self.items = items
        for item in self.items:
            self.devcombo.addItem(item)
        self.devcombo.currentIndexChanged.connect(self.changeType)
        self.devcomboLabel = QLabel("Select Device")
        self.devcomboLabel.setBuddy(self.devcombo)

        self.resultWidget = QWidget()
        self.resultLayout = QHBoxLayout()
        self.resultLayout.addWidget(self.results[0])
        self.resultWidget.setLayout(self.resultLayout)


        self.mainLayout.addWidget(self.instructions)
        self.mainLayout.addWidget(self.comboLabel)
        self.mainLayout.addWidget(self.combo)
        self.mainLayout.addWidget(self.devcomboLabel)
        self.mainLayout.addWidget(self.devcombo)
        self.mainLayout.addWidget(self.resultWidget)

        self.setLayout(self.mainLayout)
        self.keysList = [set(), set()]
        self.pressed = set()
        self.keysIndex = 0


    def changeType(self, index):
        if index == 0:
            self.type = 'button'
            self.results[1].setText("")
            self.resultLayout.removeWidget(self.results[1])
        elif index == 1:
            self.type = 'encoder'
            self.resultLayout.addWidget(self.results[1])

        self.update()

    def getString(self, index):
        keylist = []
        for key in self.keysList[index]:
            if key is None:
                continue
            elif (hasattr(key, 'char')):
                keylist.append(key.char+"+")
            elif len(key.name) > 1:
                keylist.insert(0, f"<{key.name}>+")
            else:
                raise Exception("Invalid key" + key)
        return ("".join(keylist))[:-1]

    def keyPressEvent(self, event):
        self.pressed.add(pyqt6Map[event.key()])
        self.keysList[self.keysIndex].add(pyqt6Map[event.key()])
        self.results[self.keysIndex].setText(self.getString(self.keysIndex))
        self.update()

    def keyReleaseEvent(self, event):
        if pyqt6Map[event.key()] in self.pressed:
            self.pressed.remove(pyqt6Map[event.key()])
        if len(self.keysList[self.keysIndex]) == 0:
            return
        if len(self.pressed) == 0 and self.type == 'button':
            self.doneFun(self.type, [self.getString(0)])
            self.close()
        if len(self.pressed) == 0 and self.type == 'encoder':
            if self.keysIndex == 1:
                self.doneFun(self.type, [self.getString(0), self.getString(1)])
                self.close()
                self.keysIndex = 0
            else:
                self.keysIndex += 1


if __name__ == '__main__':
    class TestApp(QMainWindow):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("My App")

            button = QPushButton("Press me for a dialog!")
            button.clicked.connect(self.button_clicked)
            self.setCentralWidget(button)

        def addInput(self, t, item):
            print(t, item)

        def button_clicked(self, s):
            print("click", s)

            dlg = KeyComboDialog(self.addInput, self)
            dlg.exec()

    app = QApplication(sys.argv)

    window = TestApp()
    window.show()

    app.exec()