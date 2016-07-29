# Youtube History Analysis
--------------------------

This package locally downloads the metadata for all video in a user's Youtube history and performs a quick analysis. The results are then displayed in the browser.

## Usage

To run from the command-line, just do:

    $ python youtube_history.py

You'll be prompted for your Google username and password if you haven't downloaded the raw metadata yet. These are used only by youtube-dl.py

To specify any non-default directory for the data, run:

    $ python youtube_history.py -o /path/to/empty/data/directory/

## TODO

* Make into pip package
* Try PyInstaller for easier access
* Finish README
* Licence