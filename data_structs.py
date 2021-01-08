from typing import NamedTuple
import PyQt5 #import QWidgets, QtGui
from dataclasses import dataclass

# class myStat(NamedTuple):
#     name: str
#     value: float
#     qlabel=PyQt5.QtGui.QLabel()
#     # qlabel: PyQt5.QWidgets.QLabel
#     display_element: PyQt5.QWidgets.QLCDNumber = PyQt5.QtGui.QLCDNumber()

@dataclass
class myStat:
    name: str
    value: float
    qlabel:None
    display_element:None
    # qlabel=PyQt5.QtGui.QLabel()
    # # qlabel: PyQt5.QWidgets.QLabel
    # display_element: PyQt5.QWidgets.QLCDNumber = PyQt5.QtGui.QLCDNumber()
