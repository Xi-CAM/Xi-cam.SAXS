import numpy as np
import pytest

from xicam.SAXS.processing.twotime import two_time_correlation


def test_twotime(self):
    # use dinesh's data


def test_twotime(self):
    data = np.random.random((100, 10, 10))
    labels = np.ones(data.shape[1:])
    print(data.shape)
    print(labels.shape)
    op = two_time_correlation()
    result = op(data=data, labels=labels)
    print(result)


    asssert result == some_twotime_data