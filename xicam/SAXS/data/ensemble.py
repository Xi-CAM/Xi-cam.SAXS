from itertools import count

from qtpy.QtCore import Qt
from qtpy.QtGui import QStandardItem, QStandardItemModel

from xicam.SAXS.widgets.items import CheckableItem


class Ensemble:
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


# class EnsembleItem(QStandardItem):
#     def __init__(self, *args, **kwargs):
#         super(EnsembleItem, self).__init__(*args, **kwargs)
#
#         self.setCheckable(True)
#
#

class EnsembleModel(QStandardItemModel):
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

            projections = getattr(catalog, "projections", None) or ["projection 1", "projection 2"]
            for projection in projections:
                projection_item = CheckableItem()
                projection_name = getattr(projection, "name", "projection")
                projection_item.setData(projection_name, Qt.DisplayRole)
                projection_item.setData(projection, Qt.UserRole)
                catalog_item.appendRow(projection_item)

            ensemble_item.appendRow(catalog_item)

        self.appendRow(ensemble_item)

    def remove_ensemble(self, ensemble):
        ...

    def rename_ensemble(self, ensemble, name):
        found_ensemble_items = self.findItems(ensemble.name)
        if found_ensemble_items:
            ensemble_item = found_ensemble_items[0]
            # Better way to do this (CatalogItem.setData can auto rename)
            ensemble = ensemble_item.data(Qt.UserRole)
            ensemble.name = name
            ensemble_item.setData(name, Qt.DisplayRole)

