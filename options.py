import pathlib
import os


class Options:
    def __init__(self, options_obj=None):
        if options_obj:
            self.__dict__ = options_obj
        else:
            self.paths = [os.path.join(pathlib.Path.home(), "Pictures")]
            self.image_time = 2000
            self.randomize = False
            self.no_video = False
            self.no_gif = False
            self.mute = False
            self.autodisplay = False
