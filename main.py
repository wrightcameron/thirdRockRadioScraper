import os
import argparse
import requests
import sqlite3
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# Globals
third_rock_playlist_url = "https://onlineradiobox.com/us/thirdrock/playlist/"
dir_path = os.getcwd()
database_path = os.path.join(dir_path, "data/thirdRockRadio.db")
logger = logging.getLogger(__name__)

def run():
    # Get songs for today
    page = requests.get(third_rock_playlist_url)
    parse_page(page.content)
    # Loop through all days, with 1 being yesturday, and 6 being 7 days ago.
    for i in range(1, 6):
        logger.debug(f"Scraping {i} day's ago. URL: {third_rock_playlist_url}/{i}")
        page = requests.get(f"{third_rock_playlist_url}{i}")
        parse_page(page.content)


def test_run():
    # Test today and yesturday
    for i in ("data/index.html", "data/yesturday.html"):
        print(f"Scanning {i}")
        index_path = os.path.join(dir_path, "data/index.html")
        # Check if file doesn't exist, if it doesn't bounce.
        if not os.path.exists(index_path):
            print(f"index.html doesn't exist in data dir, run the downloadPage.sh shell script in tools dir and retry.")
            continue
        with open(index_path, "r") as file:
            index_content = file.read()
        parse_page(index_content)
    

def parse_page(content: str):
    soup = BeautifulSoup(content, "html.parser")
    date = soup.find_all("ul", {"class": "playlist__schedule"})
    print(date)
    date = date[0].find("span").text.split(" ", 1)
    day_month = date[1].split(".", 1)
    day = int(day_month[0])
    month = int(day_month[1])
    schedule = soup.find_all("table", {"class": "tablelist-schedule"})
    if len(schedule) == 0:
        print("Schedule couldn't be found, doing nothing and exiting.")
        exit()
    elif len(schedule) > 1:
        print("More than one table schedule was found, this shouldn't have happened.")
    schedule = schedule[0]
    # Before looping through all songs, setup database
    setup_sqlite()
    # Get all songs in schedule
    songs = schedule.find_all("tr")
    for song in songs:
        time = song.find("td", class_="tablelist-schedule__time")
        band_and_name = song.find("td", class_="track_history_item")
        band_and_name = band_and_name.text.split("-", 1)
        band_name = band_and_name[0].strip()
        song_name = band_and_name[1].strip()
        time = time.text.strip()
        # print(f"\"{song_name}\" by \"{band_name}\" played at {time}")
        epoch = get_epoch(month, day, time)
        add_entry(song_name, band_name, epoch)

def get_epoch(month: int, day: int, time: str) -> int:
    # Not accurate if pulling from text html, but should be fine for pulling live
    if time == "Live":
        hour = datetime.now().hour 
        minute = datetime.now().minute
    else:
        split_time = time.split(":", 1)
        hour = int(split_time[0])
        minute = int(split_time[1])
    return datetime(datetime.now().year, month, day, hour, minute).strftime('%s')

def add_entry(song: str, band: str, broadcast_epoch: int):
    band_id = add_band(band)
    song_id = add_song(song, band_id)
    add_broadcast(broadcast_epoch, song_id)


def setup_sqlite():
    """Setup database with DDL queries if database doesn't exist.
    """
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    # Create band table
    cur.execute("""CREATE TABLE IF NOT EXISTS band(
                band_id INTEGER PRIMARY KEY,
                band_name TEXT NOT NULL UNIQUE
                )""")
    # Create song table
    cur.execute("""CREATE TABLE IF NOT EXISTS song(
                song_id INTEGER PRIMARY KEY,
                song_name TEXT NOT NULL,
                band_id INTEGER NOT NULL,
                UNIQUE(song_name, band_id),     
                FOREIGN KEY(band_id) REFERENCES band(band_id)
                )""")
    # Create broadcast
    cur.execute("""CREATE TABLE IF NOT EXISTS broadcast(
                broadcast_id INTEGER PRIMARY KEY,
                broadcast_datetime INT NOT NULL UNIQUE
                )""")
    # Create broadcast_song table, M:M table
    cur.execute("""CREATE TABLE IF NOT EXISTS song_broadcast(
                song_id INTEGER,
                broadcast_id INTEGER,
                PRIMARY KEY (song_id, broadcast_id),
                FOREIGN KEY (song_id) REFERENCES song(song_id),
                FOREIGN KEY (broadcast_id) REFERENCES broadcast(broadcast_id)
                )""")
    con.commit()


def add_band(name: str) -> int:
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    name = name.replace("'","''")
    res = cur.execute(f"SELECT band_id FROM band WHERE band_name = '{name}'")
    band_id = res.fetchall()
    # If band id is null, add band
    if len(band_id) == 0:
        logger.debug(f"Didn't find band \"{name}\" in database, inserting it.")
        res = cur.execute(f"INSERT INTO band (band_name) VALUES ('{name}') ON CONFLICT DO NOTHING RETURNING band_id")
        band_id = res.fetchall()
    band_id = band_id[0][0]
    con.commit()
    return band_id

def add_song(name: str, band_id: int) -> int:
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    # TODO Might be a better way to sanatize this
    name = name.replace("'","''")
    res = cur.execute(f"SELECT song_id FROM song WHERE song.song_name = '{name}' AND band_id = {band_id};")
    song_id = res.fetchall()
    # If song id is null, add song
    if len(song_id) == 0:
        logger.debug(f"Didn't find song \"{name}\" for band id ({band_id}) in database, inserting it.")
        res = cur.execute(f"INSERT INTO song (song_name, band_id) VALUES ('{name}', {band_id}) ON CONFLICT DO NOTHING RETURNING song_id")
        song_id = res.fetchall()
    song_id = song_id[0][0]
    con.commit()
    return song_id

def add_broadcast(broadcast_time: int, song_id: int):
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(f"INSERT INTO broadcast (broadcast_datetime) VALUES ({broadcast_time}) ON CONFLICT DO NOTHING RETURNING broadcast_id")
    broadcast_id = res.fetchall()
    if len(broadcast_id) > 0:
        broadcast_id = broadcast_id[0][0]
        logger.debug(f"Didn't find broadcast epoch {broadcast_time} for song_id ({song_id}) in database, inserting it.")
        cur.execute(f"INSERT INTO song_broadcast (song_id, broadcast_id) VALUES ({song_id}, {broadcast_id}) ON CONFLICT DO NOTHING")
    con.commit()

def get_song_counts():
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    res = cur.execute(f"""SELECT song_name, band_name, count(*) as count 
                        FROM song INNER 
                        JOIN song_broadcast ON song.song_id = song_broadcast.song_id
                        JOIN band ON band.band_id = song.band_id
                        GROUP BY 1, 2
                        ORDER BY 3 DESC""")
    songs = res.fetchall()
    con.commit()
    return songs
    

def check_web_robot():
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', help='Uses pre-downloaded song list, used for testing purposes.', action="store_true")
    parser.add_argument('-d', '--debug', help='Set log level to debug, default is INFO', action="store_false")
    args = parser.parse_args()
    if args.debug == True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    print(f"Collecting Third Rock Radio Song's at { datetime.now() }")
    if not args.test:
        run()
    else:
        print("Running Test")
        test_run()
    print("********************************************")
    # for song in get_song_counts():
    #     print(f"Song \"{song[0]}\" by \"{song[1]}\" played {song[2]}")
