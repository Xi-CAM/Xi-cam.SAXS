import time
import event_model
import fabio


def edf_ingestor(paths):
    # TODO -- metadata?
    # TODO -- use Datum and Resources
    timestamp = time.time()  # TODO -- use start_doc's time (if it has one)?
    run_bundle = event_model.compose_run()
    yield "start", run_bundle.start_doc

    with fabio.open(paths[0]) as first_frame:
        field = "pilatus2M"
        source = "Beamline 7.3.3"
        shape = list(first_frame.data.shape)
        frame_data_keys = {field: {"source": source, "dtype": "number", "shape": shape}}
        frame_stream_name = "primary"
        frame_stream_bundle = run_bundle.compose_descriptor(data_keys=frame_data_keys, name=frame_stream_name)
        yield "descriptor", frame_stream_bundle.descriptor_doc

    for path in paths:
        with fabio.open(path) as frame:
            yield "event", frame_stream_bundle.compose_event(data={field: frame.data},
                                                             timestamps={field: timestamp})
    yield "stop", run_bundle.compose_stop()
