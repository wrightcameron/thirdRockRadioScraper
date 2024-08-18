import os
import sqlite3
import logging

dir_path = os.getcwd()
database_path = os.path.join(dir_path, "data/thirdRockRadio.db")
logger = logging.getLogger(__name__)


def add_entry(song: str, band: str, broadcast_epoch: int):
    """Add song, band, and time song was broadcast to sqlite database

    Args:
        song (str): Artist's song
        band (str): Artist/band name
        broadcast_epoch (int): When song was broadcast as unix epoch
    """
    band_id = add_band(band)
    song_id = add_song(song, band_id)
    add_broadcast(broadcast_epoch, song_id)


def setup_sqlite():
    """Setup database with DDL queries if database doesn't exist."""
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    # Create band table
    cur.execute(
        """CREATE TABLE IF NOT EXISTS band(
                band_id INTEGER PRIMARY KEY,
                band_name TEXT NOT NULL UNIQUE
                )"""
    )
    # Create song table
    cur.execute(
        """CREATE TABLE IF NOT EXISTS song(
                song_id INTEGER PRIMARY KEY,
                song_name TEXT NOT NULL,
                band_id INTEGER NOT NULL,
                UNIQUE(song_name, band_id),     
                FOREIGN KEY(band_id) REFERENCES band(band_id)
                )"""
    )
    # Create broadcast
    cur.execute(
        """CREATE TABLE IF NOT EXISTS broadcast(
                broadcast_id INTEGER PRIMARY KEY,
                broadcast_datetime INT NOT NULL UNIQUE
                )"""
    )
    # Create broadcast_song table, M:M table
    cur.execute(
        """CREATE TABLE IF NOT EXISTS song_broadcast(
                song_id INTEGER,
                broadcast_id INTEGER,
                PRIMARY KEY (song_id, broadcast_id),
                FOREIGN KEY (song_id) REFERENCES song(song_id),
                FOREIGN KEY (broadcast_id) REFERENCES broadcast(broadcast_id)
                )"""
    )
    con.commit()


def add_band(name: str) -> int:
    """Add band by name to database, does nothing if band already added.

    Args:
        name (str): band/artist name

    Returns:
        int: band id
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    name = name.replace("'", "''")
    res = cur.execute(f"SELECT band_id FROM band WHERE band_name = '{name}'")
    band_id = res.fetchall()
    # If band id is null, add band
    if len(band_id) == 0:
        logger.debug(f'Didn\'t find band "{name}" in database, inserting it.')
        res = cur.execute(
            f"INSERT INTO band (band_name) VALUES ('{name}') ON CONFLICT DO NOTHING RETURNING band_id"
        )
        band_id = res.fetchall()
    band_id = band_id[0][0]
    con.commit()
    return band_id


def add_song(name: str, band_id: int) -> int:
    """Add song by name to database, does nothing if song already added.

    Args:
        name (str): Song name
        band_id (int): band's database id

    Returns:
        int: song database id
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    # TODO Might be a better way to sanatize this
    name = name.replace("'", "''")
    res = cur.execute(
        f"SELECT song_id FROM song WHERE song.song_name = '{name}' AND band_id = {band_id};"
    )
    song_id = res.fetchall()
    # If song id is null, add song
    if len(song_id) == 0:
        logger.debug(
            f'Didn\'t find song "{name}" for band id ({band_id}) in database, inserting it.'
        )
        res = cur.execute(
            f"INSERT INTO song (song_name, band_id) VALUES ('{name}', {band_id}) ON CONFLICT DO NOTHING RETURNING song_id"
        )
        song_id = res.fetchall()
    song_id = song_id[0][0]
    con.commit()
    return song_id


def add_broadcast(broadcast_time: int, song_id: int):
    """Add song broadcast to database, does nothing if broadcast already recorded.

    Args:
        broadcast_time (int): broadcast unix epoch
        song_id (int): song's database id
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(
        f"INSERT INTO broadcast (broadcast_datetime) VALUES ({broadcast_time}) ON CONFLICT DO NOTHING RETURNING broadcast_id"
    )
    broadcast_id = res.fetchall()
    if len(broadcast_id) > 0:
        broadcast_id = broadcast_id[0][0]
        logger.debug(
            f"Didn't find broadcast epoch {broadcast_time} for song_id ({song_id}) in database, inserting it."
        )
        cur.execute(
            f"INSERT INTO song_broadcast (song_id, broadcast_id) VALUES ({song_id}, {broadcast_id}) ON CONFLICT DO NOTHING"
        )
    con.commit()


def get_most_common_song(limit: int = 12) -> list:
    """Get most common song, the song with the most total plays

    Args:
        limit (int): number of songs to return

    Returns:
        list: list of songs
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(
        f"""SELECT song_name, band_name, count(*) as count
                        FROM song INNER
                        JOIN song_broadcast ON song.song_id = song_broadcast.song_id
                        JOIN band ON band.band_id = song.band_id
                        GROUP BY 1, 2
                        ORDER BY 3 DESC
                        LIMIT {limit}"""
    )
    songs = res.fetchall()
    con.commit()
    return songs


def get_least_common_song(limit: int = 10) -> list:
    """Get least common song, the song with the least total plays

    Args:
        limit (int): number of songs to return

    Returns:
        list: list of songs
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(
        f"""SELECT song_name, band_name, count(*) as count
                        FROM song INNER
                        JOIN song_broadcast ON song.song_id = song_broadcast.song_id
                        JOIN band ON band.band_id = song.band_id
                        GROUP BY 1, 2
                        ORDER BY 3 ASC
                        LIMIT {limit}"""
    )
    songs = res.fetchall()
    con.commit()
    return songs


def get_most_common_artist(limit: int = 12) -> list:
    """Get most common artist, the artist with the most total songs played

    Args:
        limit (int): number of artists to return

    Returns:
        list: list of artists
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(
        f"""SELECT band_name, count(*) as count
                        FROM band INNER
                        JOIN song ON song.band_id = band.band_id
                        GROUP BY 1
                        ORDER BY 2 DESC
                        LIMIT {limit};"""
    )
    songs = res.fetchall()
    con.commit()
    return songs


def get_least_common_artist(limit: int = 10) -> list:
    """Get least common artist, the artist with the least total songs played

    Args:
        limit (int): number of artists to return

    Returns:
        list: list of artists
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(
        f"""SELECT band_name, count(*) as count
                        FROM band INNER
                        JOIN song ON song.band_id = band.band_id
                        GROUP BY 1
                        ORDER BY 2 ASC
                        LIMIT {limit};"""
    )
    songs = res.fetchall()
    con.commit()
    return songs
