def test_VerticalCut(data, qz):
    from ..processing.verticalcuts import VerticalCutPlugin
    t1 = VerticalCutPlugin()
    t1.data.value = data
    t1.qz.value = qz
    t1.qzminimum.value = 0.1
    t1.qzmaximum.value = 0.3
    t1.evaluate()
    print(t1.verticalcut.value())

    # assert t1.evaluate() == 3
