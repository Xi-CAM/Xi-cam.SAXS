from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories
import numpy as np


@operation
@display_name('Fourier Correlation')
@output_names('g2')
@describe_input('data', 'Array of two or more dimensions.')
@describe_input('labels', 'Labeled array of the same shape as the image stack.'
                          'Each ROI is represented by sequential integers starting at one.'
                          'For example, if you have four ROIs, they must be labeled'
                          '1, 2, 3, 4. Background is labeled as 0')
@describe_output('g2', 'Normalized correlation with shape = (len(lag_steps), num_rois)')
# TODO: intent
@categories('Scattering', 'Correlation')
def fourier_correlation(data: np.ndarray,
                        labels: np.ndarray) -> np.ndarray:
    data = np.array(data)
    mask = np.logical_not(1 == labels)

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
    return g2
