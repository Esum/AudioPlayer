from mutagen.flac import FLAC
from mutagen.mp3 import MP3


def get_tag_value(tagList, tag: str, valueType=str):
    for k in range(len(tagList)):
        if tagList[k][:len(tag)] == tag:
            return valueType(tagList[k][len(tag)+1:])
    return None


class audio_file:
    def __init__(self, path: str, formt: str=''):
        self.path = path
        if formt == '':
            self.format = path.split('.')[-1]
        else:
            self.format = formt
        self.properties = {'title': '',
                           'album': '',
                           'album_artist': '',
                           'composer': '',
                           'artist': '',
                           'date': '',
                           'genre': '',
                           'disc': None,
                           'totaldiscs': None,
                           'track': None,
                           'totaltracks': None}
        if formt.upper() == 'MP3':
            tagList = MP3(path).pprint().split('\n')
            self.properties['title'] = get_tag_value(tagList, 'TOAL')
            self.properties['album'] = get_tag_value(tagList, 'TALB')
            self.properties['composer'] = get_tag_value(tagList, 'TCOM')
            self.properties['artist'] = get_tag_value(tagList, 'TOPE')
            self.properties['date'] = get_tag_value(tagList, 'TYER')
            self.properties['disc'] = get_tag_value(tagList, 'TPOS')
            self.properties['track'] = get_tag_value(tagList, 'TRCK')
        elif formt.upper() == 'FLAC':
            tagList = FLAC(path).pprint().split('\n')
            self.properties['title'] = get_tag_value(tagList, 'TITLE')
            self.properties['album'] = get_tag_value(tagList, 'ALBUM')
            self.properties['artist'] = get_tag_value(tagList, 'ARTIST')
            self.properties['date'] = get_tag_value(tagList, 'DATE')
            self.properties['genre'] = get_tag_value(tagList, 'GENRE')
            self.properties['track'] = get_tag_value(tagList, 'TRACKNUMBER')

audio_files = {}