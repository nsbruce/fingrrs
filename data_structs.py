from PyQt5 import QtWidgets, QtGui
from dataclasses import dataclass, field


@dataclass
class Stat:
    name: str
    qlabel:QtWidgets.QLabel = field(default_factory=QtWidgets.QLabel)
    display_element:QtWidgets.QLCDNumber=field(default_factory=QtWidgets.QLCDNumber)
    _value: float = 0.0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val
        self.display_element.display(val)
    

@dataclass
class plotOption:
    def __init__(self, label):
        self.label=label
        self.button=QtGui.QRadioButton(self.label)
    # label: str
    # button: QtWidgets.QRadioButton=field(default_factory=QtWidgets.QRadioButton)
