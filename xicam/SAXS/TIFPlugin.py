from xicam.plugins.DataHandlerPlugin import DataHandlerPlugin, start_doc, descriptor_doc, event_doc, stop_doc, \
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

    def __call__(self, path,  *args, **kwargs):
        return fabio.open(path).data

    @staticmethod
    @functools.lru_cache(maxsize=10, typed=False)
    def parseDataFile(path):
        md = fabio.open(path).header
        md.update({'object_keys': {'Unkown Device': ['pilatus2M_image']}})
        return md

    @classmethod
    def getStartDoc(cls, paths, start_uid):
        return start_doc(start_uid=start_uid, metadata={'paths': paths})