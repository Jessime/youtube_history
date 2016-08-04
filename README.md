# Youtube History Analysis

This package locally downloads the metadata for all video in a user's Youtube history and performs a quick analysis. The results are then displayed in the browser.

## Example

The final results of the analysis should look pretty similar to mine:

https://jessime.github.io/youtube_gh_pages/

## Installation 
This script uses Python 3.x. If you don't have Python, I would recommend downloading it from [Anaconda](https://www.continuum.io/downloads).

Copy or clone this package from Github.

Open the Terminal/Command Line and navigate to where you copied the package:

    cd path/to/copied/directory

### Linux and MacOS

Install the dependencies by entering:

    pip install -r requirements.txt

### Windows

Windows is a bit trickier. Compiling Numpy can be difficult. 
And personally, I haven't had any luck getting `wordcloud` up and running yet.
Hopefully this will be addressed soon. 
Anyway, the best method I've found for Windows is to use conda environments.
You can read more about them [here](http://conda.pydata.org/docs/using/envs.html#list-all-environments).
Assuming you have installed Anaconda, do:

    $conda create -n youtube Flask matplotlib numpy pandas
    $activate youtube
    $pip install plotly

This final step may fail. It's okay if it does:

    $pip install wordcloud

## Usage

To run from the command-line, just do:

    $ python youtube_history.py

You'll be prompted for your Google username and password if you haven't downloaded the raw metadata yet. These are used only by youtube-dl.py

To specify any non-default directory for the data, run:

    $ python youtube_history.py -o /path/to/empty/data/directory/

## Questions and Comments

Feel free to direct any questions or comments to the Issues page of the repository. 

## TODO

* Docstrings
* Address "error: Unable to find vcvarsall.bat" issues.
* Fix bugs for "No funnies" and youtube-dl error.
