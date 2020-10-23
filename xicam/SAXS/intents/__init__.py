from xicam.core.intents import ImageIntent


class SAXSImageIntent(ImageIntent):

    canvas = "saxs_image_intent_canvas"

    def __init__(self, image, *args, **kwargs):
        super(SAXSImageIntent, self).__init__(image, *args, **kwargs)
