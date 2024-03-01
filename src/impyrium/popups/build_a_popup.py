import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QSlider
from PyQt6.QtCore import QTimer, Qt
from ..widgets.item_scroll_view import ItemScrollView
from ..inputless_combo import InputlessCombo
from ..aitpi.src import aitpi
from .. import common_css
from ..aitpi_signal import AitpiSignal, AitpiSignalExecutor
import pynput
from .popup import Popup

class Input():
    def __init__(self) -> None:
        self.value = None
        self.widget = None

    def reset(self):
        self.widget = None

    def getWidget(self):
        return self.widget

    def getValue(self):
        return self.value

    def handleKeyEvent(self, char, event):
        pass

    def handleChange(self, newValue):
        self.value = newValue

class Output():
    def __init__(self) -> None:
        self.value = None

    def reset(self):
        self.widget = None

    def getWidget(self):
        return self.widget

    def setValue(self, value):
        pass

class TextOutput(Output):
    def __init__(self, value="") -> None:
        self.widget = None
        self.value = value

    def getWidget(self):
        self.widget = QLabel()
        self.widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.widget.setStyleSheet("text-align: left")
        self.setValue(self.value)
        return self.widget

    def setValue(self, value):
        self.value = value
        if self.widget is not None:
            self.widget.setText(self.value)

class SliderInput(Input):
    def __init__(self, range, valueChangedFun=None, styleSheet="") -> None:
        self.valueChangedFun = valueChangedFun
        self.styleSheet = styleSheet
        self.range = range
        self.value = range[0]

    def valueChange(self, value):
        self.value = value
        self.valueChangedFun(value)

    def getWidget(self):
        self.widget = QSlider(Qt.Orientation.Horizontal)
        self.widget.setMinimum(self.range[0])
        self.widget.setMaximum(self.range[1])
        self.widget.setMinimumHeight(25)
        self.value = self.widget.value()
        if self.valueChangedFun is not None:
            self.widget.valueChanged.connect(self.valueChange)
        self.widget.setStyleSheet(self.styleSheet)
        return self.widget


class TextInput(Input):
    def __init__(self, valueChangedFun=None, styleSheet="", height=100, banned=["\t"]):
        self.value = ""
        self.banned = banned
        self.widget = None
        self.height = height
        self.valueChangedFun = valueChangedFun
        self.styleSheet = styleSheet

    def getWidget(self):
        self.widget = QTextEdit()
        self.widget.setMaximumHeight(self.height)
        self.widget.textChanged.connect(self.valueChanged)
        self.widget.setStyleSheet(self.styleSheet)
        self.setValue(self.value)
        return self.widget

    def valueChanged(self):
        self.value = self.widget.toPlainText()
        for item in self.banned:
            if item in self.value:
                self.value = self.value.replace(item, "")
                self.setValue(self.value)

        if self.valueChangedFun is not None:
            self.valueChangedFun(self.value)

    def setValue(self, value):
        if self.widget is not None and self.widget:
            self.widget.setText(str(value))
        self.value = str(value)

class NumberInput(TextInput):
    def __init__(self, valueChangedFun=None, styleSheet="", height = 25, max=100000000000):
        self.height = height
        self.max = 100000000000
        self.value = ""
        self.widget = None
        self.valueChangedFun = valueChangedFun
        self.styleSheet = styleSheet
        self.preventRecurse = False

    def valueChanged(self):
        val = self.widget.toPlainText()
        nums = [str(i) for i in range(0, 10)]
        actualValue = ""
        sign = 1
        if len(val) >= 1:
            if val[0] == "-":
                sign = -1
        for char in val:
            if char in nums:
                actualValue += str(char)
        if actualValue != "":
            self.value = int(actualValue) * sign
            if sign == -1:
                actualValue = "-" + actualValue
        elif actualValue == "" and sign == -1:
            actualValue = "-"
        else:
            self.value = None
        if actualValue != val:
            self.widget.setPlainText(actualValue)
        self.valueChangedFun(self.value)
        return self.value

class ComboInput():
    pass

class BuildAPopup(Popup):
    def __init__(self, doneFun, name, devices, components, parent: QWidget = None):
        super().__init__(parent)
        self.shouldReturnValue = False
        self.setStyleSheet(common_css.MAIN_STYLE)
        self.doneFun = doneFun
        self.focusIdx = 0
        self.mainLayout = QVBoxLayout(self)
        self.instructions = QLabel(self)
        self.name = name
        self.devices = devices
        self.instructions.setText(name)
        self.setWindowTitle(self.name)
        self.setMinimumWidth(800)
        if len(devices) == 1:
            self.devices = devices
        else:
            self.devices = ["All", *devices]
        self.instructions.setText(name)

        self.devIndex = 0
        self.index = None
        self.devcombo = InputlessCombo(self)
        for dev in self.devices:
            if type(dev) is str:
                self.devcombo.addItem(dev)
            else:
                self.devcombo.addItem(dev.getName())
        self.devcombo.currentIndexChanged.connect(self.changeType)
        self.devcomboLabel = QLabel("Select Device")
        self.devcomboLabel.setBuddy(self.devcombo)

        self.mainLayout.addWidget(self.instructions)
        self.mainLayout.addWidget(self.devcomboLabel)
        self.mainLayout.addWidget(self.devcombo)

        self.components = components
        first = None
        for name, item in self.components.items():
            temp = QWidget(self)
            lay = QHBoxLayout()
            widget = item.getWidget()
            if first is None and issubclass(type(item), Input):
                first = widget
                # TODO: We want the first input to be focused automatically
                # So do something here for that
                first.setFocus()

            label = QLabel(self)
            label.setText(name)
            lay.addWidget(label)
            lay.addWidget(widget)
            temp.setLayout(lay)
            self.mainLayout.addWidget(temp)

    def changeType(self, index):
        self.devIndex = index
        self.update()

    # Required to allow us to handle on a QT thread
    def consume(self, msg):
        if msg == "CLOSE":
            self.shouldReturnValue = True
            self.close()
        if msg == "CLOSE_NO_RESULT":
            self.shouldReturnValue = False
            self.close()
        if msg == "SHIFT_FOCUS":
            self.focusIdx += 1
            if self.focusIdx >= len(self.components):
                self.focusIdx = 0
            self.components[list(self.components.keys())[self.focusIdx]].widget.setFocus()

    def handleKeyEvent(self, char, event):
        if event == aitpi.BUTTON_PRESS:
            if char == pynput.keyboard.Key.enter:
                self.msgQt("CLOSE")
            elif char == pynput.keyboard.Key.esc:
                self.msgQt("CLOSE_NO_RESULT")
            elif char == pynput.keyboard.Key.tab:
                self.msgQt("SHIFT_FOCUS")


    def changeDev(self, dev):
        self.device = dev

    def getResults(self):
        ret = {}
        for key, comp in self.components.items():
            if issubclass(type(comp), Input):
                ret[key] = comp.getValue()
        return ret

    def popUp(self):
        super().exec()
        dev = []
        if self.devIndex != 0:
            dev = [self.devices[self.devIndex]]
        result = self.getResults()
        return dev, result if self.shouldReturnValue else None

if __name__ == '__main__':
    class TestApp(QMainWindow):
        def __init__(self):
            super().__init__()

            self.setWindowTitle("My App")
            button = QPushButton("Press me for a dialog!")
            button.clicked.connect(self.button_clicked)
            self.setCentralWidget(button)
            self.executor = AitpiSignalExecutor()
            self.executor.start()

        def signalTimer(self):
            AitpiSignal.run()

        def addInput(self, t, item):
            print(t, item)

        def button_clicked(self, s):
            toolbox = TextOutput("Something")
            dlg = BuildAPopup(
                self.addInput,
                "Something",
                ["one", "two"],
                {
                    "Something": TextInput(valueChangedFun=lambda value: toolbox.setValue(value)),
                    "Else": SliderInput((0, 100), print),
                    "Value": toolbox
                }
            )
            value = dlg.popUp()
            print("BUttont", value)

        def closeEvent(self, event):
            self.end()
            event.accept()

        def close(self):
            self.end()
            super().close()

        def end(self):
            self.executor.stop()

    app = QApplication(sys.argv)

    aitpi.TerminalKeyInput.startKeyListener()

    window = TestApp()
    window.show()

    app.exec()