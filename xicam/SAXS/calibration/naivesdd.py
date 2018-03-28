import numpy as np
from scipy import signal
from xicam.plugins import ProcessingPlugin, Input, Output, InOut
from pyFAI import AzimuthalIntegrator, calibrant
from scipy import signal


class NaiveSDD(ProcessingPlugin):
    name = 'SDD Estimation (Naive)'

    data = Input(description='Calibrant frame image data',
                 type=np.ndarray)
    mask = Input(description='Array (same size as image) with 1 for masked pixels, and 0 for valid pixels',
                 type=np.ndarray)
    calibrant = Input(description='Calibrant standard record', type=calibrant.Calibrant)
    ai = InOut(description='Azimuthal integrator; the SDD will be modified in-place', type=AzimuthalIntegrator)
    npts = Input(description='Resolution in q of the azimuthal integration  used for ring detection', default=2000)

    # TODO: use Multigeometry
    def evaluate(self):
        # Un-calibrated azimuthal integration
        r, radialprofile = self.ai.value.integrate1d(self.data.value, self.npts.value, unit='r_mm')

        # find peaks
        peaks = np.array(self.findpeaks(np.arange(len(radialprofile)), radialprofile)).T

        # get best peak
        bestpeak = None
        for peak in peaks:
            if peak[0] > 15 and not np.isinf(peak[1]):  ####This thresholds the minimum sdd which is acceptable
                bestpeak = peak[0]
                # print peak
                break

        # identify order of selected peak
        N = 1
        stds = [np.std((peaks[:, 0] / (np.arange(len(peaks)) + i))[:4]) for i in range(1, 5)]
        if min(stds) < 5:  # threshold accepting peak as higher N
            N = np.argmin(stds) + 1  # index of the first detected peak
        calibrant1stpeak = self.calibrant.value.dSpacing[N - 1]

        # Calculate sample to detector distance for lowest q peak

        tth = 2 * np.arcsin(0.5 * self.ai.value.wavelength / calibrant1stpeak / 1.e-10)
        tantth = np.tan(tth)
        sdd = r[int(round(bestpeak))] / tantth

        # set sdd back on azimuthal integrator
        fit2dcal = self.ai.value.getFit2D()
        fit2dcal['directDist'] = sdd
        self.ai.value.setFit2D(**fit2dcal)

    @staticmethod
    def findpeaks(x, y):

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
