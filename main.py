import os
import argparse
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import thirdRockDatabase

# Globals
third_rock_playlist_url = "https://onlineradiobox.com/us/thirdrock/playlist/"
dir_path = os.getcwd()
logger = logging.getLogger(__name__)


def run():
    """Loop though past 7 days of ThirdRockRadio song's adding them to the database"""
    # Before looping through all songs, setup database
    thirdRockDatabase.setup_sqlite()
    # Get songs for today
    page = requests.get(third_rock_playlist_url)
    parse_page(page.content)
    # Loop through all days, with 1 being yesturday, and 6 being 7 days ago.
    for i in range(1, 6):
        logger.debug(f"Scraping {i} day's ago. URL: {third_rock_playlist_url}/{i}")
        page = requests.get(f"{third_rock_playlist_url}{i}")
        parse_page(page.content)


def test_run():
    """If the index.html and yesturday.html files are in data, scan them and
    add them to the sqlite database.  Useful for testing.
    """
    # Before looping through all songs, setup database
    thirdRockDatabase.setup_sqlite()
    # Test today and yesturday
    for i in ("data/index.html", "data/yesturday.html"):
        print(f"Scanning {i}")
        index_path = os.path.join(dir_path, "data/index.html")
        # Check if file doesn't exist, if it doesn't bounce.
        if not os.path.exists(index_path):
            print(
                f"index.html doesn't exist in data dir, run the downloadPage.sh shell script in tools dir and retry."
            )
            continue
        with open(index_path, "r") as file:
            index_content = file.read()
        parse_page(index_content)


def parse_page(content: str):
    """Parse the html page for date, and all songs in the list.

    Args:
        content (str): html content
    """
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
        thirdRockDatabase.add_entry(song_name, band_name, epoch)


def get_epoch(month: int, day: int, time: str) -> int:
    """Take month, day, hour, minute and produce epoch

    Args:
        month (int): month
        day (int): day
        time (str): hour and minute seperated by :

    Returns:
        int: unix epoch
    """
    # Not accurate if pulling from text html, but should be fine for pulling live
    if time == "Live":
        hour = datetime.now().hour
        minute = datetime.now().minute
    else:
        split_time = time.split(":", 1)
        hour = int(split_time[0])
        minute = int(split_time[1])
    return datetime(datetime.now().year, month, day, hour, minute).strftime("%s")


def check_web_robot():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        help="Uses pre-downloaded song list, used for testing purposes.",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Set log level to debug, default is INFO",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--skip",
        help="Skip scrap, if you only care about looking at results add -r flag.",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--results",
        help="Get results most common, least common, and new songs",
        action="store_true",
    )
    args = parser.parse_args()
    if args.debug == True:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    if not args.skip:
        print(f"Collecting Third Rock Radio Song's at { datetime.now() }")
        if not args.test:
            run()
        else:
            print("Running Test")
            test_run()
        print("********************************************")
    else:
        logger.debug("Skipping scrape.")
    if args.results:
        print("Results")
        print("Most Common Song's")
        for song in thirdRockDatabase.get_most_common_song():
            print(f'\tSong "{song[0]}" by "{song[1]}" played {song[2]}')
        print("Least Common Song's")
        for song in thirdRockDatabase.get_least_common_song():
            print(f'\tSong "{song[0]}" by "{song[1]}" played {song[2]}')
        print("Most Common Artist's")
        for artist in thirdRockDatabase.get_most_common_artist():
            print(f'\tArtist "{artist[0]}" songs {artist[1]}')
        print("Least Common Artist's")
        for artist in thirdRockDatabase.get_least_common_artist():
            print(f'\tArtist "{artist[0]}" songs {artist[1]}')
