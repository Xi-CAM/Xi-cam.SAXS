def test_VerticalCut():
    from xicam.plugins.SAXS.processing.verticalcuts import VerticalCutPlugin
    import numpy as np
    t1 = VerticalCutPlugin()
    t1.data.value = np.zeros((20,20))
    t1.qz.value = np.tile(np.linspace(0,1, 20), (1, 20))
    t1.qzminimum.value = 0.1
    t1.qzmaximum.value = 0.3
    t1.evaluate()
    print(t1.verticalcut.value())

    # assert t1.evaluate() == 3
