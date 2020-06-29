from qtpy.QtCore import Qt
from .SAXSToolbar import FieldSelector, ROIs, SAXSToolbarBase


# TODO -- move these to more reusable area
class Button(SAXSToolbarBase):
    def __init__(self, *args, button_icon_path=None, button_text="", receiver=None, **kwargs):
        super(Button, self).__init__(*args, **kwargs)
        action = self.mkAction(button_icon_path, button_text, receiver, **kwargs)
        self.addAction(action)
        if button_text:
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)


class ProcessButton(Button):
    """Defines a button that can be used to start a process."""
    def __init__(self, *args, button_receiver=None, **kwargs):
        super(ProcessButton, self).__init__(*args,
                                            button_icon_path="icons/run.png",
                                            button_text="Process",
                                            receiver=button_receiver,
                                            **kwargs)


class XPCSToolBar(ROIs):
    pass