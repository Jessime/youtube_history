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

## Usage

There are currently two options for downloading data.
The prefered method is to use [Google Takeout](https://takeout.google.com/).
Make sure `YouTube and YouTube Music` is checked and follow directions to download the zip file.
It'll take 10-30 minutes to recieve an email from Google saying your job is done.
Unzip your downloaded file and pass it as a command line parameter:

    $ python youtube_history.py --takeout /path/to/Takeout
    
The specific file we're looking for is `YouTube and YouTube Music/history/watch-history.html`.
So make sure at least that one file exists in the `Takeout` directory.
    
### Downloading with `youtube-dl`
If you're more of a gambler, you can try using `youtube-dl` to download your data.
Just do:

    $ python youtube_history.py

and you'll be prompted for your Google username and password if you haven't downloaded the raw metadata yet.
These are used only by `youtube-dl` and not saved in any way (even locally).

This is a "gamble" because `youtube-dl` is constantly fighting Google bot detection and losing more often than not.
So your login attempts may trigger 2-Factor Authentication or fail completely.
To help avoid triggering Google's protective measures, you can rate-limit your requests.
This will slow down download time, but increase the likelihood of being able to download everything.
To delay requests for a second, do:

    $ python youtube_history.py -d 1

### Running with fresh data

To specify any non-default directory for the data, run:

    $ python youtube_history.py -o /path/to/empty/data/directory/

Once raw metadata is downloaded to the default data directory, this step is skipped in future runs to save time.
If you want to download a second dataset, you'll have to point the script to a new directory.
(Or you can manually clear out the default `/data` folder). 

## Questions and Comments

Feel free to direct any questions or comments to the Issues page of the repository.

## TODO

* Add a pip package and command line tool.
* Add more complicated analyses, like Reddit's best method.
