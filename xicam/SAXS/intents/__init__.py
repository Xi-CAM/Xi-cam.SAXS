from xicam.core.intents import ImageIntent


class SAXSImageIntent(ImageIntent):

    canvas = "saxs_image_intent_canvas"

    def __init__(self, name: str, image, *args, device_name: str = None, geometry=None, log_scale=True, **kwargs):
        super(SAXSImageIntent, self).__init__(name, image, *args, **kwargs)

        self.geometry = geometry
        self.log_scale = log_scale
        self.device_name = device_name


class GISAXSImageIntent(SAXSImageIntent):

    def __init__(self, name: str, image, *args, incidence_angle=0.0, **kwargs):
        super(GISAXSImageIntent, self).__init__(name, image, *args, **kwargs)

        self.incidence_angle = incidence_angle
