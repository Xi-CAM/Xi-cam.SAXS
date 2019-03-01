from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import fabio


class TIFPlugin(DataHandlerPlugin):
    name = 'TIFPlugin'

    DEFAULT_EXTENTIONS = ['.tif', '.tiff']

    descriptor_keys = []

    def __init__(self, path):
        super(TIFPlugin, self).__init__()
        self.path = path
        self.fimg = fabio.open(path)

    def __call__(self, *args, **kwargs):
        return self.fimg.data
