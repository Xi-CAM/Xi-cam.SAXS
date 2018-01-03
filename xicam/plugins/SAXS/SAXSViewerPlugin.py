from xicam.plugins import QWidgetPlugin
from pyqtgraph import ImageView
import lazyarray


class SAXSViewerPlugin(QWidgetPlugin):
    class widget(ImageView):
        def __init__(self,*args,**kwargs):
            super(SAXSViewerPlugin.widget, self).__init__(*args,**kwargs)
            self.document = None

        def setDocument(self, document, *args, **kwargs):
            # make lazy array from document



            super(SAXSViewerPlugin.widget, self).setImage(data,*args,**kwargs)
