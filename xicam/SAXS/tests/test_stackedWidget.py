import sys
from qtpy.QtWidgets import QLineEdit, QListWidget, QFormLayout, QHBoxLayout, QRadioButton,\
                           QWidget, QStackedWidget, QCheckBox, QToolButton, QStyle, QLabel, QGraphicsView, QApplication

from xicam.SAXS.widgets.views import StackedResultsWidget


if __name__ ==  "__main__":
    app = QApplication(sys.argv)
    ex = StackedResultsWidget()
    sys.exit(app.exec_())

