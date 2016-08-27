import os
import os.path
import time

import xml.sax.saxutils
import xml.dom.minidom

import mutagen
import mutagen.mp3
import mutagen.id3
import mutagen.flac

import jinja2

from library_xml.constants import tags_conversion


# TODO add documentation

class Track:
    with open(os.path.join(os.path.dirname(__file__), "./templates/track.xml")) as file:
        XML_TEMPLATE = jinja2.Template(file.read())

    def __init__(self, path: str):
        file = mutagen.File(path)

        self.path = os.path.abspath(path)
        self.last_modification = os.path.getmtime(path)
        self.info = Info(file)
        self.tags = Tags(file)

    def to_xml(self) -> str:
        path = xml.sax.saxutils.escape(self.path)
        last_modification = xml.sax.saxutils.escape(str(self.last_modification))
        return Track.XML_TEMPLATE.render(path=path, last_modification=last_modification, tags_xml=self.tags.to_xml(), info_xml=self.info.to_xml())


class Info(dict):
    def __init__(self, file: mutagen.FileType):
        super().__init__()

        # FLAC
        if isinstance(file.info, mutagen.flac.StreamInfo):
            self["codec"] = "FLAC"
            self["bitrate"] = file.info.bits_per_sample * file.info.sample_rate
            self["channels"] = file.info.channels
            self["sample_rate"] = file.info.sample_rate
            self["bits_per_sample"] = file.info.bits_per_sample
            self["length"] = file.info.length


        # MP3
        elif isinstance(file.info, mutagen.mp3.MPEGInfo):
            self["codec"] = "MP3"
            self["bitrate"] = file.info.bitrate
            self["bitrate_mode"] = str(file.info.bitrate_mode)
            self["channels"] = file.info.channels
            self["sample_rate"] = file.info.sample_rate
            self["length"] = file.info.length

        else:
            # TODO add MP4
            raise NotImplementedError("Not implemented format: {}".format(file.filename))

    def to_xml(self) -> str:
        return "".join("<{key}>{value}</{key}>".format(key=key, value=xml.sax.saxutils.escape(str(self[key]))) for key in sorted(self) if self[key])


class Tags(dict):
    def __init__(self, file: mutagen.FileType):
        super().__init__()

        # FLAC
        if isinstance(file.tags, mutagen.flac.VCFLACDict):
            formt = "flac"
            get_tags = lambda key: list(set(filter(lambda e: e, sum([file.tags.get(converted, []) for converted in tags_conversion[formt][key]], []))))
            # this lambda is useful because some tags can have 2 different field names, it reads both values and then join the two lists of tags obtained

            for key in tags_conversion[formt]:
                self[key] = get_tags(key)

        # MP3
        elif isinstance(file.tags, mutagen.id3.ID3Tags):
            formt = "mp3"
            get_tags = lambda key: list(filter(lambda e: e, sum([[file.tags.get(converted, None)] for converted in tags_conversion[formt][key] if file.tags.get(converted, None) is not None], [])))
            # this lambda is useful because some tags can have 2 different field names, it reads both values and then join the two lists of tags obtained

            for key in tags_conversion[formt]:
                self[key] = get_tags(key)

            # TODO handle tags formatting for some tags

            for key in tags_conversion[formt]:
                self[key] = list(map(str, self[key]))

        else:
            # TODO add MP4
            raise NotImplementedError("Not implemented format: {}".format(file.filename))

    def to_xml(self) -> str:
        tags = {key: "; ".join(self[key]) for key in self}
        return "".join("<{key}>{value}</{key}>".format(key=key, value=xml.sax.saxutils.escape(tags[key])) for key in sorted(tags) if tags[key])


class Library(list):
    with open(os.path.join(os.path.dirname(__file__), "./templates/library.xml")) as file:
        XML_TEMPLATE = jinja2.Template(file.read())

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.initialize()

    def initialize(self):
        super().__init__()
        paths = [os.path.join(root, name).replace("\\", "/") for root, dirs, files in os.walk(self.path) for name in files]

        for path in paths:
            try:
                self.append(Track(path))
            except:
                # TODO add log message
                pass

    def to_xml(self) -> str:
        tracks_XML = list()

        for track in self:
            tracks_XML.append(track.to_xml())

        path = xml.sax.saxutils.escape(self.path)
        export_time = xml.sax.saxutils.escape(repr(time.time()))

        rendered = Library.XML_TEMPLATE.render(path=path, export_time=export_time, tracks=tracks_XML)
        return xml.dom.minidom.parseString(rendered).toprettyxml()
