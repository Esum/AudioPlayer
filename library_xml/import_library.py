import os
import os.path

import xml.sax.saxutils
import xml.dom.minidom

import mutagen
import mutagen.mp3
import mutagen.flac

import jinja2

import library_xml.constants

with open(os.path.join(os.path.dirname(__file__), "./templates/track.xml")) as file:
    TEMPLATE_XML_TRACK = jinja2.Template(file.read())

with open(os.path.join(os.path.dirname(__file__), "./templates/library.xml")) as file:
    TEMPLATE_XML_LIBRARY = jinja2.Template(file.read())

# TODO add documentation

def audio_file_to_tags_dict(file: mutagen.FileType) -> dict:
    tags = dict()

    conversion = library_xml.constants.tags_conversion

    if isinstance(file.tags, mutagen.flac.VCFLACDict):
        get_tags = lambda key: list(set(filter(lambda e: e, sum([file.tags.get(converted, []) for converted in conversion["flac"][key]], []))))
        # this lambda is useful because the totaltracks and totaldiscs tags can have 2 different field names, it reads both values and then join the two lists of tags obtained
        tags = {key: get_tags(key) for key in conversion["flac"]}

    # TODO add MP3, MP4

    return tags


def audio_file_to_info_dict(file: mutagen.FileType) -> dict:
    info = dict()

    info["path"] = file.filename.replace("\\", "/")
    info["last_modification_time"] = os.path.getmtime(file.filename)

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

    # TODO add MP4

    return info


def audio_file_to_xml(file: mutagen.FileType) -> str:
    tags = audio_file_to_tags_dict(file)
    tags = {key: "; ".join(tags[key]) for key in tags}

    info = audio_file_to_info_dict(file)
    path = xml.sax.saxutils.escape(info.pop("path"))
    last_modification = xml.sax.saxutils.escape(str(info.pop("last_modification_time")))

    tags_xml = "".join("<{key}>{value}</{key}>".format(key=key, value=xml.sax.saxutils.escape(tags[key])) for key in sorted(tags) if tags[key])
    info_xml = "".join("<{key}>{value}</{key}>".format(key=key, value=xml.sax.saxutils.escape(str(info[key]))) for key in sorted(info) if info[key])

    return TEMPLATE_XML_TRACK.render(path=path, last_modification=last_modification, tags_xml=tags_xml, info_xml=info_xml)


def library_to_xml(path: str) -> str:
    files = [os.path.join(root, name).replace("\\", "/") for root, dirs, files in os.walk(path) for name in files][:10]

    tracks_XML = list()

    for file in files:
        try:
            tracks_XML.append(audio_file_to_xml(mutagen.File(file)))
        except:
            # TODO add log message
            pass

    rendered = TEMPLATE_XML_LIBRARY.render(path=path, tracks=tracks_XML)

    return xml.dom.minidom.parseString(rendered).toprettyxml()