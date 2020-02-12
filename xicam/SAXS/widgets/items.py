from qtpy.QtGui import QStandardItem


class CheckableItem(QStandardItem):
    """Convenience class for having a checkable standard item."""
    def __init__(self, *args, **kwargs):
        super(QStandardItem, self).__init__(*args, **kwargs)

        self.setCheckable(True)
