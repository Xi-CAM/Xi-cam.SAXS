import pytest


def test_VerticalCut():
    import numpy as np

    from qtpy.QtWidgets import QApplication
    app = QApplication([])
    from xicam.SAXS.operations.verticalcuts import VerticalCutPlugin
    t1 = VerticalCutPlugin()
    t1.data.value = np.ones((10, 10))
    t1.qz.value = np.tile(np.arange(10), (1, 10))
    t1.qzminimum.value = 3
    t1.qzmaximum.value = 6
    t1.evaluate()
    assert np.sum(t1.verticalcut.value) == 60
