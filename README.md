# Third Rock Radio Web Scraper

Web Scraper to harvest all songs played on the [Third Rock Radio](https://www.thirdrockradio.net/) Internet Radio site.

Used to listen to Third Rock a bunch, but don't much anymore.  But I'd still like to know what are songs I have never heard of playing on this station, and ignore the ones I have listened too.  This scraper is used for finding all songs that have played and then keeping track of the unique songs.

## Requirements

- Python 3 & Pip
- SQLite3 (If you want to access database from CLI, otherwise not needed)

## Setup

1. In repository run,`python3 -m venv venv`
2. Activate virtual environment, `source ./bin/activate`
3. Install required package, `pip install -r requirements.txt`

## Usage

Script will attempt to download HTML from *onlineradiobox.com/us/thirdrock/playlist/* for the past 7 days.  Each day is gained by adding a 1-6 at the end of the URL.  Each song, band, and time played that day are in a list.  Loop through that list and add data to *SQLite3* database in `./data/thirdRockRadio.db`.

Entry-point to script is `main.py`, usage: `main.py [-h] [--test] [-d] [-s] [-r]`

options:
  -h, --help     show this help message and exit
  --test         Uses pre-downloaded song list, used for testing purposes.
  -d, --debug    Set log level to debug, default is INFO
  -s, --skip     Skip scrape, if you only care about looking at results add -r flag.
  -r, --results  Get results most common, least common, and new songs

Results can either be seen by running Python script with `--results` flag or using SQLite3 shell and opening thirdRockRadio.db.

### Automate With Cronjob

Script can be automated with cron with example below.  Example would run at 23:50 on Sunday.  This example assumes the system Python was where packages to use this script will installed too.  If that isn't the case replace Python with path to Python interpreter created by venv.  `2>&1 /dev/null` throws away any output so cron's log doesn't get filled.

```text
50 23 * * 0 python /path/to/main.py 2>&1 /dev/null
```

## Resources

- [Online Radio Box](https://onlineradiobox.com/us/thirdrock/playlist/)
- [Command Line Shell For SQLite](https://www.sqlite.org/cli.html)
