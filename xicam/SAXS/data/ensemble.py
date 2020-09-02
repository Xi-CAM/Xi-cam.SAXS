from itertools import count

from qtpy.QtCore import Qt, QAbstractItemModel, QModelIndex
from qtpy.QtGui import QStandardItemModel

from xicam.core.msg import logMessage, WARNING
from xicam.XPCS.projectors.nexus import project_nxXPCS

from ..widgets.items import CheckableItem


class Ensemble:
    """Represents an organized collection of catalogs."""
    _count = count(1)

    def __init__(self, name=""):
        super(Ensemble, self).__init__()

        self.catalogs = []
        self._name = name
        self._count = next(self._count)

    @property
    def name(self):
        if not self._name:
            self._name = f"Ensemble {self._count}"
        return self._name

    @name.setter
    def name(self, name):
        if not name:
            return
        self._name = name

    def append_catalog(self, catalog):
        self.catalogs.append(catalog)

    def append_catalogs(self, *catalogs):
        for catalog in catalogs:
            self.append_catalog(catalog)


# TODO encapsulate the Ensemble and Catalog Items (if we need to store more info than just checkstate)
# class EnsembleItem(QStandardItem):
#     def __init__(self, *args, **kwargs):
#         super(EnsembleItem, self).__init__(*args, **kwargs)
#
#         self.setCheckable(True)
#
#


class TreeItem:

    def __init__(self, data, parentItem=None):
        self.childItems = []
        self.itemData = data
        self.parentItem = parentItem

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        if row < 0 or row >= self.childCount():
            return None
        return self.childItems[row]

    def childCount(self) -> int:
        return len(self.childItems)

    def columnCount(self) -> int:
        return len(self.itemData)

    def row(self) -> int:
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        return 0

    def data(self, column):
        if column < 0 or column > self.columnCount():
            return None
        return self.itemData[column]


class TreeModel(QAbstractItemModel):
    def __init__(self, data, parent=None):
        super(TreeModel, self).__init__(parent)
        rootItem = TreeItem(["test", "summary"])
        self._setupModelData(rootItem)

    def _setupModelData(self, rootItem):
        for i in range(5):
            rootItem.appendChild(TreeItem([f"{i}", f"{i*10}"]))

    def data(self, index, role):
        ...

    def flags(self, index):
        ...

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        ...

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem = parent
        if not parentItem.isValid():
            parentItem = parent.index

    def parent(self, index):
        ...

    def rowCount(self, parent=None):
        ...

    def columnCount(self, parent=None):
        ...


# TODO: subclass from QAbstractItemModel, book-keep the list of ensembles
# contains Ensembles, no QStandardItems
# data(index, role):
#   if index.parent().parent.isValid():
#       index_type = 'Intent'
#   elif index.parent().isValid():
#       index_type = 'Run'
#   else:
#       index_type = 'Ensemble'

#   if index.parent().isValid():
#       if role == index.data(DisplayRole)
#
class EnsembleModel(QStandardItemModel):
    """Model that stores Ensembles.

    Each ensemble may store multiple Catalogs.
    """
    def __init__(self, *args, **kwargs):
        super(EnsembleModel, self).__init__(*args, **kwargs)

    def add_ensemble(self, ensemble: Ensemble):
        ensemble_item = CheckableItem()
        ensemble_item.setData(ensemble.name, Qt.DisplayRole)
        ensemble_item.setData(ensemble, Qt.UserRole)

        for catalog in ensemble.catalogs:
            catalog_item = CheckableItem()
            catalog_name = getattr(catalog, "name", "catalog")
            catalog_item.setData(catalog_name, Qt.DisplayRole)
            catalog_item.setData(catalog, Qt.UserRole)

            try:
                hints = project_nxXPCS(catalog)
                for hint in hints:
                    hint_item = CheckableItem()
                    hint_name = hint.name
                    hint_item.setData(hint_name, Qt.DisplayRole)
                    hint_item.setData(hint, Qt.UserRole)
                    catalog_item.appendRow(hint_item)
            except AttributeError as e:
                logMessage(e, level=WARNING)

            ensemble_item.appendRow(catalog_item)

        self.appendRow(ensemble_item)

    def remove_ensemble(self, ensemble):
        # TODO
        raise NotImplementedError

    def rename_ensemble(self, ensemble, name):
        found_ensemble_items = self.findItems(ensemble.name)
        if found_ensemble_items:
            ensemble_item = found_ensemble_items[0]
            # Better way to do this (CatalogItem.setData can auto rename)
            ensemble = ensemble_item.data(Qt.UserRole)
            ensemble.name = name
            ensemble_item.setData(name, Qt.DisplayRole)

