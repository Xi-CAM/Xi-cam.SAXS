# from databroker.core import BlueskyRun
# from xicam.XPCS.projectors.nexus import g2_projection_key, g2_error_projection_key
#
#
# class Hint:
#     def __init__(self, data):
#         self._data = data
#
#
#
# class PlotHint(Hint):
#     def __init__(self, *args, **kwargs):
#         super(PlotHint, self).__init__(*args, **kwargs)
#
#
# class ImageHint(Hint):
#     def __init__(self, *args, **kwargs):
#         super(ImageHint, self).__init__(*args, **kwargs)
#
#
# # Hints --> easily swappable with whatever databroker hint system is used eventually
#         # a function call, extract_hints(catalog) -> [Hint]
#         # eg. extract_hints(catalog_with_g2_curves) -> [PlotHint]
#         # extract_hints needs to be context specific (e.g. nxXPCS) -> xpcs_extract_hints, uses assumed knowledge of the
#         # keys in nexus that can be displayed in some way
#
# def extract_hints(catalog: BlueskyRun) -> [Hint]:
#     hints = []
#     getattr(catalog, stream)
#     g2_hint = PlotHint(ca