import os
import argparse
import requests
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup

# Globals
thirdRockPlayListUrl = "https://onlineradiobox.com/us/thirdrock/playlist/"
dir_path = os.getcwd()
database_path = os.path.join(dir_path, "data/thirdRockRadio.db")

def run():
    page = requests.get(thirdRockPlayListUrl)
    soup = BeautifulSoup(page.content, "html.parser")
    schedule = soup.find_all("table", {"class": "tablelist-schedule"})
    if len(schedule) == 0:
        print("Schedule couldn't be found, doing nothing and exiting.")
        exit()
    elif len(schedule) > 1:
        print("More than one table schedule was found, this shouldn't have happened.")
    schedule = schedule[0]
    print(schedule.prettify())
    # Get all songs in schedule
    songs = schedule.find_all("tr")
    for song in songs:
        time = song.find("td", class_="tablelist-schedule__time")
        band_and_name = song.find("td", class_="track_history_item")
        
        time = time.text.strip()
        band_and_name = band_and_name.text.split("-", 1)
        band_name = band_and_name[0].strip()
        song_name = band_and_name[1].strip()
        print(f"\"{song_name}\" by \"{band_name}\" played at {time}")


def run_test_run():
    index_path = os.path.join(dir_path, "data/index.html")
    # Check if file doesn't exist, if it doesn't bounce.
    if not os.path.exists(index_path):
        print(f"index.html doesn't exist in data dir, run the downloadPage.sh shell script in tools dir and retry.")
        exit(0)
    with open(index_path, "r") as file:
        index_content = file.read()
    soup = BeautifulSoup(index_content, "html.parser")
    # TODO Repeat Code
    date = soup.find_all("ul", {"class": "playlist__schedule"})
    date = date[0].find("span").text.split(" ", 1)
    _day_of_week = date[0]
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
    # TODO Before looping through all songs, setup database
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
        print(f"\"{song_name}\" by \"{band_name}\" played at {time}")
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
                song_name TEXT NOT NULL UNIQUE,
                band_id INTEGER NOT NULL,
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
    # If band id is null, get band id of conflict
    if len(song_id) == 0:
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
    args = parser.parse_args()
    print(f"Collecting Third Rock Radio Song's at { datetime.now() }")
    if not args.test:
        run()
    else:
        print("Running Test")
        run_test_run()
    print("********************************************")
    for song in get_song_counts():
        print(f"Song \"{song[0]}\" by \"{song[1]}\" played {song[2]}")
