from xicam.plugins.processingplugin import ProcessingPlugin, Input, Output, InOut
import skbeam.core.correlation as corr
from scipy.signal import fftconvolve
import numpy as np


class FourierCorrelation(ProcessingPlugin):
    data = Input(description='Array of two or more dimensions.', type=np.ndarray, visible=False)

    labels = Input(description="""Labeled array of the same shape as the image stack.
        Each ROI is represented by sequential integers starting at one.  For
        example, if you have four ROIs, they must be labeled 1, 2, 3,
        4. Background is labeled as 0""", type=np.ndarray, visible=False)

    g2 = Output(description="""the normalized correlation shape is (len(lag_steps), num_rois)""", type=np.array)

    def evaluate(self):
        data = np.array(self.data.value)
        mask = np.logical_not(1 == self.labels.value)

        x = np.asarray(data)
        N, NX, NY = x.shape
        x_mean = x.mean(axis=0)
        x_std = x.std(axis=0)
        x = x - x_mean

        # zero pad
        x = np.r_[x, np.zeros((N - 1, NX, NY))]
        s = np.fft.fft(x, axis=0)
        result = np.real(np.fft.ifft(s * s.conj(), axis=0))
        result = result[:N, :, :] / N / x_std
        g2 = np.ma.average(
            np.ma.masked_array(np.nan_to_num(result), mask=np.broadcast_to(mask, (result.shape[0],) + mask.shape)),
            axis=(1, 2)).data
        self.g2.value = g2

        # correlation = fftconvolve(data, data, axes=0)
        #
        # for label in np.unique(self.labels.value):
        #     if label==0: continue
        #
        #     mask = np.logical_not(label == self.labels.value)
        #     g2 = np.ma.sum(np.ma.masked_array(correlation, mask=np.broadcast_to(mask,(correlation.shape[0],)+mask.shape)), axis=(1,2)).data
        #     g2 = g2[int(len(g2)/2):]
        #     self.g2.value = g2
        #
