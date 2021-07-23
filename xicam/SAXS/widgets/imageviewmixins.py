from databroker import Broker
from qtpy.QtWidgets import QPushButton, QSizePolicy
import numpy as np

from xicam.gui.widgets.imageviewmixins import BetterLayout, ProcessingView, XArrayView

from xicam.SAXS.operations.correction import correct


class BackgroundCorrected(BetterLayout, ProcessingView):
    """Toggle background correction for an image or image series."""
    def __init__(self, *args, darks=None, **kwargs):
        super(BackgroundCorrected, self).__init__(*args, **kwargs)
        self._darks = None
        self._bg_correction = False
        self._bg_correct_btn = QPushButton("BG Correction")
        self._bg_correct_btn.setEnabled(False)
        self._bg_correct_btn.setCheckable(True)
        self._bg_correct_btn.clicked.connect(self._toggle_bg_correction)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(1)
        size_policy.setHeightForWidth(self._bg_correct_btn.sizePolicy().hasHeightForWidth())
        self._bg_correct_btn.setSizePolicy(size_policy)

        self.set_darks(darks)

        self.ui.right_layout.addWidget(self._bg_correct_btn)

    def setImage(self, img, *args, darks=None, **kwargs):
        """Override to add additional `darks` kwarg for dark image."""
        super(BackgroundCorrected, self).setImage(img, *args, **kwargs)
        if darks is not None and self._darks is not None:
            self._darks = darks
        self.set_darks(darks)  # Can't do this before... self.image won't be set until super call

    def set_darks(self, darks):
        """Set dark image for this image view."""
        if darks is not None:
            self._darks = darks
            self._bg_correct_btn.setEnabled(True)
            self._toggle_bg_correction(True)

    def _toggle_bg_correction(self, value):
        """Slot to handle when bg correction button is clicked."""
        self._bg_correction = value
        self._bg_correct_btn.setChecked(value)
        self.getProcessedImage()  # TODO: how do we make this work for a single frame image / update current frame?

    def process(self, image):
        """Either returns the raw image or the correct image, depending on the bg correction button state."""
        if self._bg_correction:
            flats = np.ones_like(image)
            if self._darks is None:
                return image
            else:
                return correct(np.expand_dims(image, 0), flats, self._darks)[0]
        return image
