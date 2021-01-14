from PyQt5 import QtGui, QtCore

class UpdateStatDialog(QtGui.QDialog):

    def __init__(self, old_val, new_val, stat_name, **kwargs):
        super().__init__(**kwargs)

        self.setWindowTitle("Decision time")

        text=QtGui.QLabel(f"Update {stat_name} from {old_val} to {new_val}?")

        buttons = QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel

        self.buttonBox = QtGui.QDialogButtonBox(buttons)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtGui.QVBoxLayout()
        self.layout.addWidget(text)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)