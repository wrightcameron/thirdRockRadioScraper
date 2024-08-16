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
    index_path = os.path.join(dir_path, "data/index.htm")
    # Check if file doesn't exist, if it doesn't bounce.
    if not os.path.exists(index_path):
        print("index.html doesn't exist in data dir, run the downloadPage.sh shell script in tools dir and retry.")
        exit(0)
    with open(index_path, "r") as file:
        index_content = file.read()
    soup = BeautifulSoup(index_content, "html.parser")
    # TODO Repeat Code
    schedule = soup.find_all("table", {"class": "tablelist-schedule"})
    if len(schedule) == 0:
        print("Schedule couldn't be found, doing nothing and exiting.")
        exit()
    elif len(schedule) > 1:
        print("More than one table schedule was found, this shouldn't have happened.")
    schedule = schedule[0]
    print(schedule.prettify())
    # TODO Before looping through all songs, setup database
    setup_sqlite()
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

def add_entry(song: str, band: str, datetime: datetime):
    pass

def setup_sqlite():
    con = sqlite3.connect(database_path)
    cur = con.cursor()
    # Create band table
    cur.execute("""CREATE TABLE IF NOT EXISTS band(
                band_id INTEGER PRIMARY KEY,
                band_name NOT NULL UNIQUE,
                )""")
    # Create song table
    cur.execute("""CREATE TABLE IF NOT EXISTS song(
                song_id INTEGER PRIMARY KEY,
                song_name NOT NULL UNIQUE,
                )""")
    # Create broadcast
    cur.execute("""CREATE TABLE IF NOT EXISTS broadcast(
                broadcast_id INTEGER PRIMARY KEY,
                broadcast_datetime NOT NULL UNIQUE,
                )""")
    # Create broadcast_song table, M:M table
    cur.execute("""CREATE TABLE IF NOT EXISTS broadcast(
                broadcast_id INTEGER PRIMARY KEY,
                broadcast_datetime NOT NULL UNIQUE,
                )""")

def create_checkpoint_file():
    pass

def read_checkpoint_file():
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
