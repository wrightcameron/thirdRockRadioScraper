import requests
from datetime import datetime
from bs4 import BeautifulSoup

thirdRockPlayListUrl = "https://onlineradiobox.com/us/thirdrock/playlist/"

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

def add_entry(song, band, datetime):
    pass

def setup_sqlite():
    import sqlite3
    con = sqlite3.connect("thirdRockRadio.db")
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
    print(f"Collecting Third Rock Radio Song's at { datetime.now() }")
    run()
    print("********************************************")
