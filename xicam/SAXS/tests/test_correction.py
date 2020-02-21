import pytest

import numpy as np

from xicam.SAXS.processing.correction import CorrectImage


# TODO: don't hard code the gain masks inside the tests
# TODO: test endianess
# TODO: test non-uint16 inputs?

@pytest.fixture
def op() -> CorrectImage:
    op = CorrectImage()
    op.images.value = np.arange(24, dtype=np.uint16).reshape((4, 3, 2))
    return op


class TestCorrectImage:

    def test_default(self, op):
        op.evaluate()
        assert np.array_equal(op.corrected_images.value, op.images.value * op.gains.value[0])

    def test_simple_darks(self, op):
        op.darks.value = np.ones(shape=(1, *op.images.value.shape[1:]))
        op.evaluate()
        assert np.array_equal(op.corrected_images.value, op.images.value * op.gains.value[0] - 1)

    def test_multiple_darks(self, op):
        # Should average to dark array of 2's
        op.darks.value = np.array([np.ones(op.images.value.shape[1:]),
                                   np.ones(op.images.value.shape[1:]) * 3])
        op.evaluate()
        print(op.corrected_images.value)
        print(op.images.value - 2)
        assert np.array_equal(op.corrected_images.value, op.images.value * op.gains.value[0] - 2)

    def test_simple_flats(self, op):
        op.flats.value = np.ones(shape=op.images.value.shape[1:]) * 2
        op.evaluate()
        assert np.array_equal(op.corrected_images.value, op.images.value * op.gains.value[0] * 2)

    def test_gain_1(self, op):
        # gain1: 0b11 -> 1100 -> 0xC
        op.images.value = np.bitwise_or(0xC000, op.images.value)
        # np.set_printoptions(formatter={'int': hex})
        print(op.images.value)
        op.evaluate()
        truth_value = np.bitwise_and(0x1FFF, op.images.value * op.gains.value[2])
        print(truth_value)
        assert np.array_equal(op.corrected_images.value, truth_value)

    def test_gain_2(self, op):
        # gain2: 0b10 -> 1000 -> 0x8
        op.images.value = np.bitwise_or(0x8000, op.images.value)
        op.evaluate()
        truth_value = np.bitwise_and(0x1FFF, op.images.value * op.gains.value[1])
        assert np.array_equal(op.corrected_images.value, truth_value)

    def test_gain_8(self, op):
        # gain8: 0b00 -> 0000 -> 0x0
        op.gains.value = (8, 1, 1)
        op.evaluate()
        print(op.corrected_images.value)
        print(op.images.value * 8)
        assert np.array_equal(op.corrected_images.value, op.images.value * 8)

    def test_bad_pixel(self, op):
        # bad pixel: -> 0010 -> 0x2
        op.images.value[:, -1, -1] = np.bitwise_or(0x2000, op.images.value[:, -1, -1])
        op.evaluate()
        truth_value = np.bitwise_and(0x1FFF, op.images.value * op.gains.value[0])
        truth_value[:, -1, -1] = np.nan
        print(op.corrected_images.value)
        print(truth_value)
        assert np.array_equal(op.corrected_images.value, truth_value)

    def test_no_input_images(self, op):
        op.images.value = None
        with pytest.raises(TypeError):
            op.evaluate()

    def test_empty_input_images(self, op):
        op.images.value = []
        with pytest.raises(TypeError):
            op.evaluate()

    def test_bad_input_images_shape(self, op):
        op.images.value = np.ones(shape=(10, 10))
        with pytest.raises(ValueError):
            op.evaluate()

    def test_bad_flat_shape(self, op):
        op.flats.value = np.ones(shape=(10, 10, 10))
        with pytest.raises(ValueError):
            op.evaluate()

    def test_bad_flat_type(self, op):
        op.flats.value = []
        with pytest.raises(TypeError):
            op.evaluate()

    def test_bad_darks_shape(self, op):
        op.darks.value = np.zeros(shape=(10, 10))
        with pytest.raises(ValueError):
            op.evaluate()

    def test_bad_darks_type(self, op):
        op.darks.value = []
        with pytest.raises(TypeError):
            op.evaluate()