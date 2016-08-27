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


class Track:
    """Used to read a music file's main metadatas, such as its path, tags, bitrate, last modification time, etc

    Attributes:
        path (str): path to the file
        last_modification (float): timestamp of the last modification made to the file (used to detect when to refresh the information)
        info (Info): information about the file (codec, bitrate, etc)
        tags (Tags): tags of the file (album, artist, title, etc)

    """
    with open(os.path.join(os.path.dirname(__file__), "./templates/track.xml")) as file:
        XML_TEMPLATE = jinja2.Template(file.read())

    def __init__(self, path: str):
        """Reads the file's informations

        Args:
            path (str): path to the file
        """
        file = mutagen.File(path)

        self.path = os.path.abspath(path)
        self.last_modification = os.path.getmtime(path)
        self.info = Info(file)
        self.tags = Tags(file)

    def to_xml(self) -> str:
        """Serializes the informations to a xml formatted string

        Example of output:
            <track last_modification="1472219762.909762" path="D:\Dev\python\projects\audio_player\test_files\_.flac">
                <info>
                    <bitrate>705600</bitrate>
                    <bits_per_sample>16</bits_per_sample>
                    <channels>2</channels>
                    <codec>FLAC</codec>
                    <length>276.2</length>
                    <sample_rate>44100</sample_rate>
                </info>
                <tags>
                    <album>Once</album>
                    <albumartist>Nightwish</albumartist>
                    <albumartistsort>Nightwish</albumartistsort>
                    <artist>Nightwish</artist>
                    <artistsort>Nightwish</artistsort>
                    ...
                </tags>
            </track>

        Returns:
            str: xml formatted string

        """
        path = xml.sax.saxutils.escape(self.path)
        last_modification = xml.sax.saxutils.escape(str(self.last_modification))
        return Track.XML_TEMPLATE.render(path=path, last_modification=last_modification, tags_xml=self.tags.to_xml(), info_xml=self.info.to_xml())


class Info(dict):
    """dict wrapper for track information such as codec, bitrate, length, etc

    Supports FLAC and MP3 encoded files.

    Keys:
        - "codec"
        - "bitrate"
        - "channels"
        - "length"
        - "bits_per_sample"
        - "sample_rate"
        - "bitrate_mode"

    Todo:
        - add MP4 support

    """

    def __init__(self, file: mutagen.FileType):
        """Extracts the needed information from the file

        Args:
            file: mutagen.FileType object

        """
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
        """Serializes the informations to a xml formatted string

                Example of output:
                    <info>
                        <bitrate>705600</bitrate>
                        <bits_per_sample>16</bits_per_sample>
                        <channels>2</channels>
                        <codec>FLAC</codec>
                        <length>276.2</length>
                        <sample_rate>44100</sample_rate>
                    </info>

                Returns:
                    str: xml output

        """
        return "".join("<{key}>{value}</{key}>".format(key=key, value=xml.sax.saxutils.escape(str(self[key]))) for key in sorted(self) if self[key])


class Tags(dict):
    """dict wrapper for track tags

    Supports FLAC and ID3 encoded tags.

    Keys:
        same keys than library_xml.constants.tags_conversion keys

    Todo:
        - add MP4 support
        - add id3 tags formatting
        - handle discnumber id3 tag nonsense

    """

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
        """Serializes the tags to a xml formatted string

        Example of output:
            <tags>
                <album>Once</album>
                <albumartist>Nightwish</albumartist>
                <albumartistsort>Nightwish</albumartistsort>
                <artist>Nightwish</artist>
                <artistsort>Nightwish</artistsort>
                ...
            </tags>

        Returns:
            str: xml output

        """
        tags = {key: "; ".join(self[key]) for key in self}
        return "".join("<{key}>{value}</{key}>".format(key=key, value=xml.sax.saxutils.escape(tags[key])) for key in sorted(tags) if tags[key])


class Library(list):
    """[Track] wrapper

    Attributes:
        path (str): path to the root of the library

    Todo:
        - add refresh function

    """

    with open(os.path.join(os.path.dirname(__file__), "./templates/library.xml")) as file:
        XML_TEMPLATE = jinja2.Template(file.read())

    def __init__(self, path):
        """Initializes the library and imports all the music files located in path and its subfolders

        Args:
            path: path to the root of the folder to import

        """
        super().__init__()
        self.path = os.path.abspath(path)
        self.initialize()

    def initialize(self) -> None:
        """Wipes the library and import all supported music files located in self.path and its subfolders

        Music tracks that failed to be imported are ignored.

        Todo:
            - add log message when a track is ignored

        """
        super().__init__()
        paths = [os.path.join(root, name).replace("\\", "/") for root, dirs, files in os.walk(self.path) for name in files]

        for path in paths:
            try:
                self.append(Track(path))
            except:
                # TODO add log message
                pass

    def to_xml(self) -> str:
        """Serializes the library to a xml formatted string

        Example of output:
            <?xml version="1.0" ?>
            <library export_time="1472289097.903743" path="D:\Dev\python\projects\audio_player\test_files">
                <track last_modification="1472219762.909762" path="D:\Dev\python\projects\audio_player\test_files\_.flac">
                    <info>
                        <bitrate>705600</bitrate>
                        <bits_per_sample>16</bits_per_sample>
                        <channels>2</channels>
                        <codec>FLAC</codec>
                        <length>276.2</length>
                        <sample_rate>44100</sample_rate>
                    </info>
                    <tags>
                        <album>Once</album>
                        <albumartist>Nightwish</albumartist>
                        <albumartistsort>Nightwish</albumartistsort>
                        <artist>Nightwish</artist>
                        <artistsort>Nightwish</artistsort>
                        ...
                    </tags>
                </track>
            </library>

        Returns:
            str: xml containing all the library information

        """
        tracks_XML = list()

        for track in self:
            tracks_XML.append(track.to_xml())

        path = xml.sax.saxutils.escape(self.path)
        export_time = xml.sax.saxutils.escape(repr(time.time()))

        rendered = Library.XML_TEMPLATE.render(path=path, export_time=export_time, tracks=tracks_XML)
        return xml.dom.minidom.parseString(rendered).toprettyxml()
