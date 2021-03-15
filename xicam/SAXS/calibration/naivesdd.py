from enum import Enum

import numpy as np
from xicam.plugins.operationplugin import operation, output_names, display_name, describe_input, describe_output, \
    categories, units
from pyFAI import calibrant
from pyFAI.azimuthalIntegrator import AzimuthalIntegrator
from scipy import signal

# TODO: use Multigeometry
# Create Enum containing a dict of calibrations (ordered according to keys)
calibrants = Enum("Calibrant", dict(sorted(calibrant.ALL_CALIBRANTS.all.items())))


@operation
@output_names('azimuthal_integrator')
@display_name('Sample-Detector Distance estimation (Naive)')
@describe_input('data', 'Calibrant frame image data')
@describe_input('mask', "Array (same size as image) with 1 for masked pixels, and 0 for valid pixels")
@describe_input('calibrant', "Calibrant standard record")
@describe_input('azimuthal_integrator', "Azimuthal integrator; the SDD will be modified in-place")
@describe_input('npts', "Resolution in q of the azimuthal integration used for ring detection")
@describe_input('wavelength_override', "If provided, override the wavelength provided by the input azimuthal_integrator")
@units('wavelength_override', 'm')
@describe_output('azimuthal_integrator', "Azimuthal integrator with the SDD be modified in-place")
@categories(('Scattering', 'Calibration'))
def naive_sdd(data: np.ndarray,
              azimuthal_integrator: AzimuthalIntegrator,
              calibrant: calibrants = calibrant.get_calibrant("AgBh"),
              mask: np.ndarray=None,
              wavelength_override: float = None,
              npts: int = 2000) -> AzimuthalIntegrator:
    kwargs = {}
    if mask is not None:
        kwargs['mask'] = mask

    # TODO: add a type that is a special parameter-tree item allowing enable/disable the parameter in the gui
    if wavelength_override:
        azimuthal_integrator.set_wavelength(wavelength_override)

    # slice into the first index as long as there's higher dimensionality
    while len(data.shape) > 2:
        data = data[0]

    # Un-calibrated azimuthal integration
    r, radialprofile = azimuthal_integrator.integrate1d(np.asarray(data), npts, unit='r_mm', **kwargs)

    # find peaks
    peaks = np.array(find_peaks(np.arange(len(radialprofile)), radialprofile)).T

    # get best peak
    bestpeak = None
    for peak in peaks:
        if peak[0] > 15 and not np.isinf(peak[1]):  ####This thresholds the minimum sdd which is acceptable
            bestpeak = peak[0]
            # print peak
            break

    # identify order of selected peak
    best_order = (0, 0)

    for i in range(1, 6):
        peak_ratios = ((peaks[:, 0] / (np.arange(len(peaks)))) / (bestpeak / (i + 1)))
        order = np.sum(np.logical_and(peak_ratios < 1.1, 0.9 < peak_ratios))
        if order > best_order[0]:
            best_order = (order, i)

    calibrant1stpeak = calibrant.dSpacing[best_order[1]]

    # Calculate sample to detector distance for lowest q peak

    tth = 2 * np.arcsin(0.5 * azimuthal_integrator.wavelength / calibrant1stpeak / 1.e-10)
    tantth = np.tan(tth)
    sdd = r[int(round(bestpeak))] / tantth

    # set sdd back on azimuthal integrator
    fit2dcal = azimuthal_integrator.getFit2D()
    fit2dcal['directDist'] = sdd
    azimuthal_integrator.setFit2D(**fit2dcal)

    return azimuthal_integrator


def find_peaks(x, y):
    # Default peak detection parameters
    wavelet = signal.ricker  # wavelet of choice
    widths = np.arange(1, 20)  # range of widths of the ricker wavelet to search/evaluate
    max_distances = widths / 8.  # ridgeline connectivity threshold; smaller values gives more peaks; larger values considers overlapping peaks as one
    gap_thresh = 4  # threshold number of rows for ridgeline connectivity; smaller values gives more peaks
    min_length = 3  # minimum ridgeline length; smaller values gives more peaks
    min_snr = 2  # Minimum SNR
    noise_perc = 10  # percentile of points below which to consider noise
    h = 3  # number of points skipped in finite differences
    truncationlow = 10  # low q truncation for zeros
    truncationhigh = 50

    peaks = signal.find_peaks_cwt(y, widths, wavelet, max_distances, gap_thresh, min_length, min_snr, noise_perc)
    peaks = peaks[1:]
    return list(np.array(np.vstack([x[peaks], y[peaks], peaks])))
