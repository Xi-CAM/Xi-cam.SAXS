import pytest

import numpy as np

from xicam.SAXS.processing.correction import CorrectFastCCDImage

# Try to compare against the csxtools implementation...
# Differences:
#     * csxtools returns a float array (see fastccd.h:data_t)
#         - values below the dark array are negative
#         - bad pixels set to NaN
#     * we return a uint16 array
#         - values below the dark array become 0 (they do NOT wrap around the uint16)
#         - bad pixels set to 0
CSX_TOOLS = False
try:
    from xicam.SAXS.processing.correction import CSXCorrectImage
    CSX_TOOLS = True
except ImportError:
    CSXCorrectImage = None

# Disable testing against csxtools here
TEST_CSX_TOOLS = True and CSX_TOOLS


# TODO: test endianess
# TODO: test non-uint16 inputs?


@pytest.fixture
def op() -> CorrectFastCCDImage:
    op = CorrectFastCCDImage()
    op.images.value = np.arange(24, dtype=np.uint16).reshape((4, 3, 2))
    return op

@pytest.fixture
def old():
    if TEST_CSX_TOOLS:
        op = CSXCorrectImage()
        op.bitmasked_images.value = np.arange(24, dtype=np.uint16).reshape((4, 3, 2))
        return op
    else:
        return None


class TestCorrectImage:

    def test_default(self, op, old):
        op.evaluate()
        assert np.array_equal(op.corrected_images.value, op.images.value * op.gains.value[0])
        if TEST_CSX_TOOLS:
            old.evaluate()
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_simple_darks(self, op, old):
        op.darks.value = np.ones(shape=(1, *op.images.value.shape[1:]))  # darks of 1's
        op.evaluate()
        truth_value = np.array(op.images.value * op.gains.value[0] - op.darks.value, dtype=np.uint16)
        truth_value[op.darks.value > op.images.value] = 0
        assert np.array_equal(op.corrected_images.value, truth_value)
        if TEST_CSX_TOOLS:
            old.dark_images.value = op.darks.value
            old.evaluate()
            # csxtools gives us negative values; our code will zero out values less than the dark values
            old.corrected_images.value = np.where(old.corrected_images.value < 0, 0, old.corrected_images.value)
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_multiple_darks(self, op, old):
        # Should average to dark array of 2's
        op.darks.value = np.array([np.ones(op.images.value.shape[1:]),
                                   np.ones(op.images.value.shape[1:]) * 3])
        op.evaluate()
        truth_value = np.array(op.images.value * op.gains.value[0] - 2, dtype=np.uint16)
        truth_value[2 > op.images.value] = 0
        assert np.array_equal(op.corrected_images.value, truth_value)
        if TEST_CSX_TOOLS:
            old.dark_images.value = op.darks.value
            old.evaluate()
            # csxtools gives us negative values; our code will zero out values less than the dark values
            old.corrected_images.value = np.where(old.corrected_images.value < 0, 0, old.corrected_images.value)
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_simple_flats(self, op, old):
        op.flats.value = np.ones(shape=op.images.value.shape[1:]) * 2
        op.evaluate()
        truth_value = np.array(op.images.value * op.gains.value[0] * op.flats.value, dtype=np.uint16)
        assert np.array_equal(op.corrected_images.value, truth_value)
        if TEST_CSX_TOOLS:
            old.flat_field.value = op.flats.value
            old.evaluate()
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_gain_1(self, op, old):
        # gain1: 0b11 -> 1100 -> 0xC
        op.images.value = np.bitwise_or(0xC000, op.images.value)
        op.evaluate()
        truth_value = np.bitwise_and(0x1FFF, op.images.value * op.gains.value[2])
        assert np.array_equal(op.corrected_images.value, truth_value)
        if TEST_CSX_TOOLS:
            old.bitmasked_images.value = op.images.value
            old.evaluate()
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_gain_2(self, op, old):
        # gain2: 0b10 -> 1000 -> 0x8
        op.images.value = np.bitwise_or(0x8000, op.images.value)
        op.evaluate()
        truth_value = np.bitwise_and(0x1FFF, op.images.value * op.gains.value[1])
        assert np.array_equal(op.corrected_images.value, truth_value)
        if TEST_CSX_TOOLS:
            old.bitmasked_images.value = op.images.value
            old.evaluate()
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_gain_8(self, op, old):
        # gain8: 0b00 -> 0000 -> 0x0
        op.gains.value = (2, 1, 1)  # explicitly set our gain8 channel to 2
        op.images.value = np.bitwise_or(0x0000, op.images.value)
        op.evaluate()
        assert np.array_equal(op.corrected_images.value, op.images.value * op.gains.value[0])
        if TEST_CSX_TOOLS:
            old.bitmasked_images.value = op.images.value
            old.gain.value = op.gains.value
            old.evaluate()
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    def test_bad_pixel(self, op, old):
        # bad pixel: -> 0010 -> 0x2
        op.images.value[:, -1, -1] = np.bitwise_or(0x2000, op.images.value[:, -1, -1])
        op.evaluate()
        truth_value = np.bitwise_and(0x1FFF, op.images.value * op.gains.value[0])
        truth_value[:, -1, -1] = np.nan
        assert np.array_equal(op.corrected_images.value, truth_value)
        
        # csxtools gives back NaN for bad pixels; we give back 0's
        if TEST_CSX_TOOLS:
            old.bitmasked_images.value = op.images.value
            old.evaluate()
            # Convert the NaN's to 0
            old.corrected_images.value = np.where(np.isnan(old.corrected_images.value), 0, old.corrected_images.value)
            assert np.array_equal(old.corrected_images.value, op.corrected_images.value)

    # def test_no_input_images(self, op, old):
    #     op.images.value = None
    #     with pytest.raises(TypeError):
    #         op.evaluate()
    #
    # def test_empty_input_images(self, op, old):
    #     op.images.value = []
    #     with pytest.raises(TypeError):
    #         op.evaluate()

    def test_bad_input_images_shape(self, op, old):
        op.images.value = np.ones(shape=(10, 10))
        with pytest.raises(ValueError):
            op.evaluate()

    def test_bad_flat_shape(self, op, old):
        op.flats.value = np.ones(shape=(10, 10, 10))
        with pytest.raises(ValueError):
            op.evaluate()

    # def test_bad_flat_type(self, op, old):
    #     op.flats.value = []
    #     with pytest.raises(TypeError):
    #         op.evaluate()

    def test_bad_darks_shape(self, op, old):
        op.darks.value = np.zeros(shape=(10, 10))
        with pytest.raises(ValueError):
            op.evaluate()

    # def test_bad_darks_type(self, op, old):
    #     op.darks.value = []
    #     with pytest.raises(TypeError):
    #         op.evaluate()