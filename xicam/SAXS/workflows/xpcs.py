import time

import event_model

from xicam.core.execution import Workflow
from xicam.plugins import ProcessingPlugin

from ..processing.fitting import FitScatteringFactor
from ..processing.fourierautocorrelator import FourierCorrelation
from ..processing.onetime import OneTimeCorrelation
from ..processing.twotime import TwoTimeCorrelation


class XPCSWorkflow(Workflow):
    ...


class TwoTime(XPCSWorkflow):
    name = '2-Time Correlation'

    def __init__(self):
        super(TwoTime, self).__init__()
        self.addProcess(TwoTimeCorrelation())

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
        tau_shape = peek_result['lag_steps'].value.shape[0]
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
                      'tau': result['lag_steps'].value,
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
        onetime = OneTimeCorrelation()
        self.addProcess(onetime)
        fitting = FitScatteringFactor()
        self.addProcess(fitting)
        self.autoConnectAll()

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
        tau_shape = peek_result['lag_steps'].value.shape[0]
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
                      'tau': result['lag_steps'].value,
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
