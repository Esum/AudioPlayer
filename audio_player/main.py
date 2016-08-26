import sqlite3 as sql
from .audio_file import AudioFile, audio_files
from .track import track, tracks


def init_musics(db=r"..\music.db"):
    conn = sql.connect(db)
    cursor = conn.cursor()
    for tupl in cursor.execute("SELECT * FROM audio_files"):
        identifier, path, formt = tupl
        identifier = int(identifier)
        audio_files[identifier] = AudioFile(path, formt)
    for tupl in cursor.execute("SELECT * FROM tracks"):
        identifier, files, begin, end = tupl
        identifier = int(identifier)
        files = [int(n) for n in files.split(';')]
        begin = [int(n) for n in begin.split(';')]
        end = [int(n) for n in end.split(';')]
        tracks[identifier] = track(files, [(begin, end) for begin, end in zip(begin, end)])
    conn.close()


def main(db=r"..\music.db"):
    init_musics(db)