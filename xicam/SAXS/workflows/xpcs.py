import time

import event_model

from xicam.core.execution import Workflow

from ..operations.average_intensity import average_intensity
from ..operations.fitting import fit_scattering_factor
from ..operations.fourierautocorrelator import fourier_correlation
from ..operations.onetime import one_time_correlation
from ..operations.twotime import two_time_correlation
from ..operations.correction import correct_fastccd_image
from ..operations.diffusion_coefficient import diffusion_coefficient


class ProcessingAlgorithms:
    """Convenience class to get the available algorithms that can be used for 1-time and 2-time correlations."""
    @staticmethod
    def algorithms():
        """Returns the available 1-time algorithms and 2-time algorithms."""
        return {
            TwoTimeAlgorithms.name: TwoTimeAlgorithms.algorithms(),
            OneTimeAlgorithms.name: OneTimeAlgorithms.algorithms()
        }

    @staticmethod
    def default():
        pass


class TwoTimeAlgorithms(ProcessingAlgorithms):
    name = '2-Time Algorithms'

    @staticmethod
    def algorithms():
        """Returns a dict where keys are the algorithm (workflow) names, values are the algorithms (workflows)."""
        return {TwoTime.name: TwoTime}

    @staticmethod
    def default():
        """Returns the default algorithm name to use."""
        return TwoTime.name


class OneTimeAlgorithms(ProcessingAlgorithms):
    name = '1-Time Algorithms'

    @staticmethod
    def algorithms():
        """Returns a dict where keys are the algorithm (workflow) names, values are the algorithms (workflows)."""
        return {OneTime.name: OneTime,
                FourierAutocorrelator.name: FourierAutocorrelator}

    @staticmethod
    def default():
        """Returns the default algorithm name to use."""
        return OneTime.name


class XPCSWorkflow(Workflow):
    def __init__(self):
        super(XPCSWorkflow, self).__init__()
        self.correct_image = correct_fastccd_image()
        self.add_operation(self.correct_image)


class TwoTime(XPCSWorkflow):
    name = '2-Time Correlation'

    def __init__(self):
        super(TwoTime, self).__init__()
        twotime = two_time_correlation()
        self.add_operation(twotime)
        self.add_link(self.correct_image, twotime, 'images', 'images')

    @staticmethod
    def document(**kwargs):
        results = kwargs.get('results')
        roi = kwargs.get('roi')
        workflow = kwargs.get('workflow_pickle')

        timestamp = time.time()

        run_bundle = event_model.compose_run()
        yield 'start', run_bundle.start_doc

        source = 'Xi-cam'

        peek_result = results[0]
        g2_shape = peek_result['g2'].value.shape[0]
        tau_shape = peek_result['tau'].value.shape[0]
        workflow = []
        workflow_shape = len(workflow)

        reduced_data_keys = {
            'norm-0-g2': {'source': source, 'dtype': 'number', 'shape': [g2_shape]},
            'tau': {'source': source, 'dtype': 'number', 'shape': [tau_shape]},
            'dqlist': {'source': source, 'dtype': 'string', 'shape': []},  # todo -- shape
            'workflow': {'source': source, 'dtype': 'string', 'shape': [workflow_shape]}
        }
        reduced_stream_name = 'reduced'
        reduced_stream_bundle = run_bundle.compose_descriptor(data_keys=reduced_data_keys,
                                                              name=reduced_stream_name)
        yield 'descriptor', reduced_stream_bundle.descriptor_doc

        # todo -- peek frame shape
        frame_data_keys = {'frame': {'source': source, 'dtype': 'number', 'shape': []}}
        frame_stream_name = 'primary'
        frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                            name=frame_stream_name)
        yield 'descriptor', frame_stream_bundle.descriptor_doc

        # todo -- store only paths? store the image data itself (memory...)
        # frames = header.startdoc['paths']
        frames = []
        for frame in frames:
            yield 'event', frame_stream_bundle.compose_event(
                data={frame},
                timestamps={timestamp}
            )

        for result in results:
            yield 'event', reduced_stream_bundle.compose_event(
                data={'norm-0-g2': result['g2'].value,
                      'tau': result['tau'].value,
                      'dqlist': roi,
                      'workflow': workflow},
                timestamps={'norm-0-g2': timestamp,
                            'tau': timestamp,
                            'dqlist': timestamp,
                            'workflow': workflow}
            )

        yield 'stop', run_bundle.compose_stop()


class OneTime(XPCSWorkflow):
    name = '1-Time Correlation'

    def __init__(self):
        super(OneTime, self).__init__()
        onetime = one_time_correlation()
        fitting = fit_scattering_factor()
        average_i = average_intensity()
        diffusion = diffusion_coefficient()

        self.add_operation(onetime)
        self.add_operation(average_i)
        self.add_operation(fitting)
        # self.add_operation(diffusion)

        # Manually set up connections (redundant if using this with LinearWorkflowEditor)
        self.add_link(self.correct_image, onetime, "images", "images")
        self.add_link(onetime, average_i, "images", "images")
        self.add_link(onetime, fitting, "g2", "g2")
        self.add_link(onetime, fitting, "tau", "tau")

    @staticmethod
    def document(**kwargs):
        results = kwargs.get('results')
        roi = kwargs.get('roi')
        workflow = kwargs.get('workflow_pickle')

        timestamp = time.time()

        run_bundle = event_model.compose_run()
        yield 'start', run_bundle.start_doc

        source = 'Xi-cam'

        peek_result = results[0]
        g2_shape = peek_result['g2'].value.shape[0]
        import numpy as np
        g2_err = np.zeros(g2_shape)
        g2_err_shape = g2_shape
        tau_shape = peek_result['tau'].value.shape[0]
        workflow = []
        workflow_shape = len(workflow)

        reduced_data_keys = {
            'norm-0-g2': {'source': source, 'dtype': 'number', 'shape': [g2_shape]},
            'norm-0-stderr': {'source': source, 'dtype': 'number', 'shape': [g2_err_shape]},
            'tau': {'source': source, 'dtype': 'number', 'shape': [tau_shape]},
            'g2avgFIT1': {'source': source, 'dtype': 'number', 'shape': [tau_shape]},
            'dqlist': {'source': source, 'dtype': 'string', 'shape': []},  # todo -- shape
            'workflow': {'source': source, 'dtype': 'string', 'shape': [workflow_shape]}
        }
        reduced_stream_name = 'reduced'
        reduced_stream_bundle = run_bundle.compose_descriptor(data_keys=reduced_data_keys,
                                                              name=reduced_stream_name)
        yield 'descriptor', reduced_stream_bundle.descriptor_doc

        # todo -- peek frame shape
        frame_data_keys = {'frame': {'source': source, 'dtype': 'number', 'shape': []}}
        frame_stream_name = 'primary'
        frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys,
                                                            name=frame_stream_name)
        yield 'descriptor', frame_stream_bundle.descriptor_doc

        # todo -- store only paths? store the image data itself (memory...)
        # frames = header.startdoc['paths']
        frames = []
        for frame in frames:
            yield 'event', frame_stream_bundle.compose_event(
                data={frame},
                timestamps={timestamp}
            )

        for result in results:
            yield 'event', reduced_stream_bundle.compose_event(
                data={'norm-0-g2': result['g2'].value,
                      'norm-0-stderr': g2_err,
                      'tau': result['tau'].value,
                      'g2avgFIT1': result['fit_curve'].value,
                      'dqlist': roi,
                      'workflow': workflow},
                timestamps={'norm-0-g2': timestamp,
                            'norm-0-stderr': timestamp,
                            'tau': timestamp,
                            'g2avgFIT1': timestamp,
                            'dqlist': timestamp,
                            'workflow': workflow}
            )

        yield 'stop', run_bundle.compose_stop()


class FourierAutocorrelator(XPCSWorkflow):
    name = 'Fourier Correlation'

    def __init__(self):
        super(FourierAutocorrelator, self).__init__()
        fourier = FourierCorrelation()
        self.addProcess(fourier)
