# Youtube History Analysis

This package locally downloads the metadata for all video in a user's Youtube history and performs a fun analysis. The results are then displayed in the browser.

## Example

The final results of the analysis should look pretty similar to mine (circa 2016):

https://jessime.github.io/youtube_gh_pages/

## Installation

This project requires Python 3.x. 

Copy or clone this repo from Github.

Open the Terminal/Command Line and navigate to where you clone the repo:

    $ cd path/to/cloned/directory

Then run:

    $ pip install -r requirements.txt

to install the dependencies.

## Usage

To run the analysis, you first need to download your raw data from [Google Takeout](https://takeout.google.com/).
Make sure `YouTube and YouTube Music` is checked and follow directions to download the zip file.
It'll take 10-30 minutes to receive an email from Google saying your job is done.
Unzip your downloaded file and pass it as a command line parameter:

    $ python youtube_history.py --takeout /path/to/Takeout
    
The specific file we're looking for is `YouTube and YouTube Music/history/watch-history.html`.
So make sure at least that one file exists in the `Takeout` directory.
    
### Downloading with `yt-dlp`

As of 2024, we've upgraded to downloading video metadata using `yt-dlp`, which is the successor to `youtube-dl`. So far, it seems pretty stable, but we'll need more testing from other people to know for sure. 

### Running with a second Takeout

If you have another Takeout folder you want to analyses, specify a name for the results dir:

    $ python youtube_history.py  --takeout /path/to/Takeout --name jill


## Questions and Comments

Feel free to direct any questions or comments to the Issues page of the repository.

