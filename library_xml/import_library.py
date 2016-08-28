import os
import os.path
import time

import re

import xml.sax.saxutils
import xml.etree.ElementTree as ET

import mutagen
import mutagen.mp3
import mutagen.id3
import mutagen.flac

from library_xml.constants import tags_conversion, tags_names


class Track:
    """Used to read a music file's main metadatas, such as its path, tags, bitrate, last modification time, etc

    Attributes:
        path (str): path to the file
        last_modification (float): timestamp of the last modification made to the file (used to detect when to refresh the information)
        info (Info): information about the file (codec, bitrate, etc)
        tags (Tags): tags of the file (album, artist, title, etc)

    """

    def __init__(self, path, last_modification, info, tags):
        self.path = path
        self.last_modification = last_modification
        self.info = info
        self.tags = tags

    @staticmethod
    def from_path(path: str):
        """Reads the file's informations

        Args:
            path (str): path to the file

        Returns:
            Track
        """
        file = mutagen.File(path)

        path = os.path.abspath(path)
        last_modification = os.path.getmtime(path)
        info = Info.from_mutagen_file(file)
        tags = Tags.from_mutagen_file(file)

        return Track(path, last_modification, info, tags)

    def __repr__(self) -> str:
        return 'Track("{}")'.format(self.path)

    def has_file_changed(self) -> bool:
        """Compares the last modification timestamp of the file with self.last_modification to determine if the file has changed since its import

        Returns:
            bool: file changed ?

        """
        return os.path.getmtime(self.path) != self.last_modification

    def refresh(self) -> bool:
        """Checks the file has been modified since import and re-import it if it has

        Returns:
            bool, file refreshed ?

        """
        if self.has_file_changed():
            file = mutagen.File(self.path)
            self.last_modification = os.path.getmtime(self.path)
            self.info = Info.from_mutagen_file(file)
            self.tags = Tags.from_mutagen_file(file)
            return True
        else:
            return False

    @staticmethod
    def from_root_tree(root: ET.Element):
        path = root.attrib["path"]
        last_modification = root.attrib["last_modification"]
        info = Info.from_root_tree(root.find("info"))
        tags = Tags.from_root_tree(root.find("tags"))
        return Track(path, last_modification, info, tags)

    def to_root_tree(self) -> ET.Element:
        root = ET.Element("track")
        root.attrib["path"] = xml.sax.saxutils.escape(self.path)
        root.attrib["last_modification"] = xml.sax.saxutils.escape(str(self.last_modification))

        root.append(self.info.to_root_tree())
        root.append(self.tags.to_root_tree())

        return root

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
        return ET.tostring(self.to_root_tree(), encoding="utf-8").decode("utf-8")


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

    @staticmethod
    def from_mutagen_file(file: mutagen.FileType):
        """Extracts the needed information from the file

        Args:
            file: mutagen.FileType object

        Returns:
            Info

        """
        info = Info()

        # FLAC
        if isinstance(file.info, mutagen.flac.StreamInfo):
            info["codec"] = "FLAC"
            info["bitrate"] = file.info.bits_per_sample * file.info.sample_rate
            info["channels"] = file.info.channels
            info["sample_rate"] = file.info.sample_rate
            info["bits_per_sample"] = file.info.bits_per_sample
            info["length"] = file.info.length


        # MP3
        elif isinstance(file.info, mutagen.mp3.MPEGInfo):
            info["codec"] = "MP3"
            info["bitrate"] = file.info.bitrate
            info["bitrate_mode"] = str(file.info.bitrate_mode)
            info["channels"] = file.info.channels
            info["sample_rate"] = file.info.sample_rate
            info["length"] = file.info.length

        else:
            # TODO add MP4
            raise NotImplementedError("Not implemented format: {}".format(file.filename))

        return info

    @staticmethod
    def from_root_tree(root: ET.Element):
        info = Info()
        keys = {"codec", "bitrate", "channels", "sample_rate", "bits_per_sample", "length", "bitrate_mode"}

        for key in keys:
            subelement = root.find(key)

            if subelement is not None:
                info[key] = subelement.text

        return info

    def to_root_tree(self) -> ET.Element:
        root = ET.Element("info")

        for key in self:
            element = ET.Element(key)
            element.text = xml.sax.saxutils.escape(str(self[key]))
            root.append(element)

        return root

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
        return ET.tostring(self.to_root_tree(), encoding="utf-8").decode("utf-8")


class Tags(dict):
    """dict wrapper for track tags

    Supports FLAC and ID3 encoded tags.

    Keys:
        same keys than library_xml.constants.tags_conversion keys

    Todo:
        - add MP4 support
        - add id3 tags formatting
        - handle discnumber id3 tag nonsense -> discnumber/totaldiscs and tracknumber/totaltracks done \o/

    """

    RE_ID3_NUMBER_TOTAL = re.compile(r"(?P<number>[1-9]+[0-9]*)/(?P<total>[1-9]+[0-9]*)")

    @staticmethod
    def from_mutagen_file(file: mutagen.FileType):
        """Load tags from the file

        Args:
            file: mutagen.FileType

        Returns:
            Tags

        """
        tags = Tags()

        # FLAC
        if isinstance(file.tags, mutagen.flac.VCFLACDict):
            formt = "flac"
            get_tags = lambda key: list(set(filter(lambda e: e, sum([file.tags.get(converted, []) for converted in tags_conversion[formt][key]], []))))
            # this lambda is useful because some tags can have 2 different field names, it reads both values and then join the two lists of tags obtained

            for key in tags_conversion[formt]:
                tags[key] = get_tags(key)

        # MP3
        elif isinstance(file.tags, mutagen.id3.ID3Tags):
            formt = "mp3"
            get_tags = lambda key: list(filter(lambda e: e, sum([[file.tags.get(converted, None)] for converted in tags_conversion[formt][key] if file.tags.get(converted, None) is not None], [])))
            # this lambda is useful because some tags can have 2 different field names, it reads both values and then join the two lists of tags obtained

            for key in tags_conversion[formt]:
                tags[key] = get_tags(key)

            # TODO handle tags formatting for some tags

            # discnumber / disctotal
            discnumber_tag_value = tags["discnumber"][0].text[0]
            discnumber_regex_result = Tags.RE_ID3_NUMBER_TOTAL.match(discnumber_tag_value)

            if discnumber_regex_result:
                tags["discnumber"] = [discnumber_regex_result.group("number")]
                tags["totaldiscs"] = [discnumber_regex_result.group("total")]
            else:
                # TODO add log message
                tags.pop("discnumber")

            # tracknumber / tracktotal
            track_number_tag_value = tags["tracknumber"][0].text[0]
            track_number_regex_result = Tags.RE_ID3_NUMBER_TOTAL.match(track_number_tag_value)

            if track_number_regex_result:
                tags["tracknumber"] = [track_number_regex_result.group("number")]
                tags["totaltracks"] = [track_number_regex_result.group("total")]
            else:
                # TODO add log message
                tags.pop("tracknumber")

            for key in tags_conversion[formt]:
                tags[key] = list(map(str, tags[key]))

        else:
            # TODO add MP4
            raise NotImplementedError("Not implemented format: {}".format(file.filename))

        return tags

    @staticmethod
    def from_root_tree(root: ET.Element):
        tags = Tags()
        keys = tags_names

        for key in keys:
            subelement = root.find(key)

            if subelement is not None:
                tags[key] = list(map(str.strip, str(subelement.text).split(";")))

        return tags

    def to_root_tree(self) -> ET.Element:
        root = ET.Element("tags")

        for key in self:
            if self[key]:
                element = ET.Element(key)
                element.text = xml.sax.saxutils.escape(str(";".join(self[key])))
                root.append(element)

        return root

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
        return ET.tostring(self.to_root_tree(), encoding="utf-8").decode(encoding="utf-8")


class Library(list):
    """[Track] wrapper

    Attributes:
        path (str): path to the root of the library

    Todo:
        - add refresh function

    """

    def __init__(self, path: str):
        """Creates a Library but DOES NOT import the music files

        Args:
            path: path to the root of the folder to import
        """
        super().__init__()
        self.path = os.path.abspath(path)

    @staticmethod
    def from_path(path: str):
        """Initializes the library and imports all the music files located in path and its subfolders

        Args:
            path: path to the root of the folder to import

        """
        lib = Library(path)
        lib.import_untracked_files()
        return lib

    def clean_deleted_files(self) -> None:
        """Deletes tracks which have a path doesn't point to a file

        Todo:
            - add log message

        """
        super().__init__(list(filter(lambda track: os.path.isfile(track.path), self)))

    def refresh_tracked_files(self) -> None:
        """Refreshes all the tracked music files using Track.refresh

        If the refresh of a track fails, the track is deleted from the library.

        Todo:
            - add log message

        """
        failed = list()
        for track in self:
            try:
                track.refresh()
            except:
                # TODO add log message
                failed.append(track)

        for track in failed:
            self.remove(track)

    def import_untracked_files(self) -> None:
        """Looks for untracked files located in self.path and its subfolders and adds then to the library

        Untracked music files that failed to be imported are ignored.

        Todo:
            - add log message

        """
        tracked_paths = {track.path for track in self}
        all_paths = {os.path.abspath(os.path.join(root, name)) for root, dirs, files in os.walk(self.path) for name in files}

        for path in all_paths.difference(tracked_paths):
            try:
                # TODO add log message
                self.append(Track.from_path(path))
            except Exception as e:
                print(path, e)
                # TODO add log message
                pass

    def refresh(self) -> None:
        """Refreshes the library

        Refresh the library =
            + clean_deleted_files
            + refresh_tracked_files
            + import_untracked_files

        Todo:
            - add log message

        """
        # TODO add log message
        self.clean_deleted_files()
        self.refresh_tracked_files()
        self.import_untracked_files()

    def to_root_tree(self) -> ET.Element:
        root = ET.Element("library")
        root.attrib["path"] = xml.sax.saxutils.escape(self.path)
        root.attrib["export_time"] = xml.sax.saxutils.escape(str(time.time()))

        for track in self:
            root.append(track.to_root_tree())

        return root

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
        return ET.tostring(self.to_root_tree(), encoding="utf-8").decode("utf-8")


