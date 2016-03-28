from enum import Enum


class playlist_type(Enum):
    custom = 0
    album = 1


class playlist:
    def __init__(self, tracks, typ=playlist_type.custom, image=None, random=None):
        self._tracks = tracks
        self._typ = typ
        if image is None:
            self._image = tracks[0]
        else:
            self._image = image
        self._random = random
    
    def play(self):
        pass