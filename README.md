# Youtube History Analysis

This package locally downloads the metadata for all video in a user's Youtube history and performs a quick analysis. The results are then displayed in the browser.

## Example

The final results of the analysis should look pretty similar to mine:

https://jessime.github.io/youtube_gh_pages/

## Installation
This script uses Python 3.x. If you don't have Python, I would recommend downloading it from [Anaconda](https://www.continuum.io/downloads).

Copy or clone this package from Github.

Open the Terminal/Command Line and navigate to where you copied the package:

    $ cd path/to/copied/directory

Then, just run:

    $ pip install -r requirements.txt

to install the dependencies.
Hopefully, a direct `pip install youtube_history` will be coming soon!

## Usage

To run from the command line, just do:

    $ python youtube_history.py

You'll be prompted for your Google username and password if you haven't downloaded the raw metadata yet.
These are used only by `youtube-dl`, and not saved in any way (even locally).

To specify any non-default directory for the data, run:

    $ python youtube_history.py -o /path/to/empty/data/directory/

All interactions with YouTube are handled through `youtube-dl`, which isn't perfect.
In particular, interacting with Google services like 2-Factor Authentication is an on-going effort.
To help avoid triggering Google's protective measures, you can rate-limit your requests.
This will slow down download time, but increase the likelihood of being able to download everything.
To delay requests for a second, do:

    $ python youtube_history.py -d 1

## Questions and Comments

Feel free to direct any questions or comments to the Issues page of the repository.

## TODO

* Add a pip package and command line tool.
* Add more complicated analyses, like Reddit's best method.
