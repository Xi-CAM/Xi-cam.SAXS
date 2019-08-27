from xicam.plugins.datahandlerplugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
    embedded_local_event_doc

import os
import fabio
import uuid
import re
import functools
from pathlib import Path




class TIFPlugin(DataHandlerPlugin):
    name = 'TIFPlugin'

    DEFAULT_EXTENTIONS = ['.tiff', '.tif']

    descriptor_keys = ['object_keys']

    def __call__(self, *args, **kwargs):
        return fabio.open(self.path).data

    def __init__(self, path):
        super(TIFPlugin, self).__init__()
        self.path = path
        self.fimg = fabio.open(path)

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        md = fabio.open(path).header
        md.update({'object_keys': {'pilatus2M': ['primary']}})
        return md

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})
