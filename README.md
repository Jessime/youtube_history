# Youtube History Analysis

This package locally downloads the metadata for all video in a user's Youtube history and performs a quick analysis. The results are then displayed in the browser.

## Installation 
This script uses Python 3.x. If you don't have Python, I would recommend downloading it from [Anaconda](https://www.continuum.io/downloads).

Copy or clone this package from Github.

Open the Terminal/Command Line and navigate to where you copied the package:

    cd path/to/copied/directory

Install the dependencys by entering:

    pip install -r requirements.txt

## Usage

To run from the command-line, just do:

    $ python youtube_history.py

You'll be prompted for your Google username and password if you haven't downloaded the raw metadata yet. These are used only by youtube-dl.py

To specify any non-default directory for the data, run:

    $ python youtube_history.py -o /path/to/empty/data/directory/

## Example

The final results of the analysis should look pretty similar to mine:

https://jessime.github.io/youtube_gh_pages/

## TODO

* Try PyInstaller (or similar) for easier access.
* Fix bugs for "No funnies" and youtube-dl error.
