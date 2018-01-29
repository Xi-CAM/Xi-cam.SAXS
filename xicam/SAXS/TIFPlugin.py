from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path
from lazyarray import larray


class TIFPlugin(DataHandlerPlugin):
    name = 'TIFPlugin'

    def __init__(self, path):
        self.path = path
        super(TIFPlugin, self).__init__()

    def __call__(self, *args, **kwargs):
        return fabio.open(self.path).data

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        return fabio.open(path).header
