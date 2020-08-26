#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Downloads, analyzes, and reports all Youtube videos associated with a user's Google account.
"""

import json
import os
import pickle
import argparse
import getpass
import subprocess as sp
import sys

from collections import namedtuple
from pathlib import Path
from webbrowser import open_new_tab

import pandas as pd
import numpy as np

from wordcloud import WordCloud
from flask import Flask
from flask import render_template
from bs4 import BeautifulSoup
from emoji import emoji_lis

from grapher import Grapher, flatten_without_nones


DEPRECATION_NOTE = """
This method of downloading data is deprecated. 
It uses youtube-dl to login to your Google account.
This is error-prone, as Google may think you are a bot.
Instead, you should go to https://takeout.google.com/,
and follow directions there to download your "YouTube and YouTube Music" data.
Then you can re-run this program specifying the `--takeout` flag,
pointing to the *unzipped* directory you downloaded from Google.

Do you want to continue anyway? [y/n]: 
"""

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', analysis=analysis)


def launch_web():
    app.debug = False
    app.secret_key = 'this key should be complex'

    file1 = os.path.join(analysis.raw, '00001.info.json')
    some_data = os.path.isfile(file1)
    if some_data:
        url = 'http://127.0.0.1:5000'
        open_new_tab(url)
        app.run()


def make_fake_series(title='N/A', webpage_url='N/A', **kwargs):
    params = ['title', 'webpage_url'] + list(kwargs.keys())
    Mock = namedtuple('MockSeries', params)
    return Mock(title, webpage_url, **kwargs)


class Analysis:
    """Main class responsible for downloading and analyzing data.

    Parameters
    ----------
    takeout : Optional[str]
        'Path to an unzipped Takeout folder downloaded from https://takeout.google.com/'
    outpath : str (default='data')
        The path to the directory where both raw and computed results should be stored.
    delay : float (default=0)
        Amount of time in seconds to wait between requests.

    Attributes
    ----------
    raw : str
        Path to 'raw' directory in self.path directory
    ran : str
        Path to 'ran' directory in self.path directory
    df : Dataframe
        Pandas Dataframe used to store compiled results
    tags : [[str]]
        A list of tags for each downloaded video
    grapher : Grapher
        Creates the interactive graphs portion of the analysis

    seconds : int
        The sum of video durations
    formatted_time : str
        Seconds converted to W/D/H/M/S format
    most_viewed : Series
        Video with the most total views
    least_viewed : DataFrame
        Collection of at most 10 videos with single digit views
    best_per_decile : DataFrame
        10 videos, one per view_count decile, where each video as the highest average rating in that decile
    worse_per_decile : DataFrame
        Same as best_per_decile, but lowest average rating
    emojis: Series
        Video with the most unique emojis in the description
    oldest_videos : Dataframe
        First 10 videos watched on user's account.
    oldest_upload : Series
        Video with the oldest upload date to youtube.
    HD : int
        The number of videos that have high-definition resolution
    UHD : int
        The number of videos that have ultra-high-definition resolution
    top_uploaders : Series
        The most watched channel names with corresponding video counts
    funny_counts : int
        The max number of times a video's description says the word 'funny'
    funny : Series
        The 'funniest' video as determined by funny_counts
    """
    def __init__(self, takeout=None, outpath='data', delay=0):
        self.takeout = Path(takeout).expanduser()
        self.path = Path(outpath)
        self.delay = delay
        self.raw = os.path.join(self.path, 'raw')  # TODO use Path
        self.ran = os.path.join(self.path, 'ran')  # TODO use Path
        self.df = None
        self.tags = None
        self.grapher = None

        self.seconds = None
        self.formatted_time = None
        self.most_viewed = None
        self.least_viewed = None
        self.best_per_decile = None
        self.worst_per_decile = None
        self.emojis = None
        self.oldest_videos = None
        self.oldest_upload = None
        self.HD = None
        self.UHD = None
        self.top_uploaders = None
        self.funny = None
        self.funny_counts = None

    def download_data(self):
        """Uses Takeout to download individual json files for each video."""
        watch_history = self.takeout / 'YouTube and YouTube Music/history/watch-history.html'
        if not watch_history.is_file():
            raise ValueError(f'"{watch_history}" is not a file. Did you download your YouTube data? ')
        print('Extracting video urls from Takeout.'); sys.stdout.flush()
        soup = BeautifulSoup(watch_history.read_text(), 'html.parser')
        urls = [u.get('href') for u in soup.find_all('a')]
        videos = [u for u in urls if 'www.youtube.com/watch' in u]
        url_path = self.path / 'urls.txt'
        url_path.write_text('\n'.join(videos))
        print(f'Urls extracted. Downloading data for {len(videos)} videos now.')
        output = os.path.join(self.raw, '%(autonumber)s')
        cmd = f'youtube-dl -o "{output}" --skip-download --write-info-json -i -a {url_path}'
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
        line = True
        while line:
            line = p.stdout.readline().decode("utf-8").strip()
            print(line)

    def deprecated_download_data_via_youtube_dl_login(self):
        """Uses youtube_dl to download individual json files for each video."""
        result = input(DEPRECATION_NOTE)
        if result.lower() != 'y':
            sys.exit()
        print('Okay, Let\'s login and download some data.')
        successful_login = False
        while not successful_login:
            successful_login = True
            user = input('Google username: ')
            pw = getpass.getpass('Google password: ')
            files = os.path.join(self.raw, '%(autonumber)s')
            if not os.path.exists(self.raw):
                os.makedirs(self.raw)
            template = ('youtube-dl -u "{}" -p "{}" '
                        '-o "{}" --sleep-interval {} '
                        '--skip-download --write-info-json -i '
                        'https://www.youtube.com/feed/history ')
            fake = template.format(user, '[$PASSWORD]', files, self.delay)
            print(f'Executing youtube-dl command:\n\n{fake}\n')
            cmd = template.format(user, pw, files, self.delay)
            p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
            while True:
                line = p.stdout.readline().decode("utf-8").strip()
                print(line)
                if line == 'WARNING: unable to log in: bad username or password':
                    successful_login = False
                if not line:
                    break

    def df_from_files(self):
        """Constructs a Dataframe from the downloaded json files.

        All json keys whose values are not lists are compiled into the dataframe.
        The dataframe is then saved as a csv file in the self.ran directory.
        The tags of each video are pickled and saved as tags.txt
        """
        print('Creating dataframe...')
        num = len([name for name in os.listdir(self.raw) if not name[0] == '.'])
        files = os.path.join(self.raw, '~.info.json') # This is a weird hack
        files = files.replace('~', '{:05d}') # It allows path joining to work on Windows
        data = [json.load(open(files.format(i))) for i in range(1, num + 1)]

        columns = ['formats', 'tags', 'categories', 'thumbnails']
        lists = [[], [], [], []]
        deletes = {k: v for k, v in zip(columns, lists)}
        for dt in data:
            for col, ls in deletes.items():
                ls.append(dt[col])
                del dt[col]

        self.df = pd.DataFrame(data)
        self.df['upload_date'] = pd.to_datetime(self.df['upload_date'], format='%Y%m%d')
        self.df.to_csv(os.path.join(self.ran, 'df.csv'))

        self.tags = deletes['tags']
        pickle.dump(self.tags, open(os.path.join(self.ran, 'tags.txt'), 'wb'))

    def make_wordcloud(self):
        """Generate the wordcloud file and save it to static/images/."""
        print('Creating wordcloud')
        wordcloud = WordCloud(width=1920,
                              height=1080,
                              relative_scaling=.5)
        flat_tags = flatten_without_nones(self.tags)
        wordcloud.generate(' '.join(flat_tags))
        wordcloud.to_file(os.path.join('static', 'images', 'wordcloud.png'))

    def check_df(self):
        """Create the dataframe and tags from files if file doesn't exist."""
        if not os.path.exists(self.ran):
            os.makedirs(self.ran)
        df_file = os.path.join(self.ran, 'df.csv')
        if os.path.isfile(df_file):
            self.df = pd.read_csv(df_file, index_col=0, parse_dates=[-11])
            self.tags = pickle.load(open(os.path.join(self.ran, 'tags.txt'), 'rb'))
            self.df['upload_date'] = pd.to_datetime(self.df['upload_date'])
        else:
            self.df_from_files()

    def total_time(self):
        """The amount of time spent watching videos."""
        self.seconds = self.df.duration.sum()
        seconds = self.seconds
        intervals = (
            ('years', 31449600),  # 60 * 60 * 24 * 7 * 52
            ('weeks', 604800),    # 60 * 60 * 24 * 7
            ('days', 86400),      # 60 * 60 * 24
            ('hours', 3600),      # 60 * 60
            ('minutes', 60),
            ('seconds', 1)
            )

        result = []

        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(int(value), name))
        self.formatted_time = ', '.join(result)

    def best_and_worst_videos(self):
        """Finds well liked and highly viewed videos"""
        self.most_viewed = self.df.loc[self.df['view_count'].idxmax()]
        low_views = self.df[self.df['view_count'] < 10]
        self.least_viewed = low_views.sample(min(len(low_views), 10), random_state=0)
        self.df['deciles'] = pd.qcut(self.df['view_count'], 10, labels=False)
        grouped = self.df.groupby(by='deciles')
        self.best_per_decile = self.df.iloc[grouped['average_rating'].idxmax()]
        self.worst_per_decile = self.df.iloc[grouped['average_rating'].idxmin()]

    def most_emojis_description(self):
        def _emoji_variety(desc):
            return len({x['emoji'] for x in emoji_lis(desc)})

        counts = self.df['description'].apply(_emoji_variety)
        self.emojis = self.df.iloc[counts.idxmax()]

    def funniest_description(self):
        """Counts number of times 'funny' is in each description. Saves top result."""
        funny_counts = []
        descriptions = []
        index = []
        for i, d in enumerate(self.df.description):
            try:
                funny_counts.append(d.lower().count('funny'))
                descriptions.append(d)
                index.append(i)
            except AttributeError:
                pass
        funny_counts = np.array(funny_counts)
        funny_counts_idx = funny_counts.argmax()
        self.funny_counts = funny_counts[funny_counts_idx]
        if self.funny_counts > 0:
            self.funny = self.df.iloc[index[funny_counts_idx]]
        else:
            title = 'Wait, 0? You\'re too cool to watch funny videos on youtube?'
            self.funny = make_fake_series(title, average_rating='N/A')

    def three_randoms(self):
        """Finds results for video resolutions, most popular channels, and funniest video."""
        height = self.df['height'].astype(int)
        self.HD = self.df[(720 <= height) & (height <= 1080)].shape[0]
        self.UHD = self.df[height > 1080].shape[0]
        self.top_uploaders = self.df.uploader.value_counts().head(n=15)
        self.funniest_description()

    def compute(self):
        print('Computing...')
        self.total_time()
        self.best_and_worst_videos()
        self.most_emojis_description()
        self.oldest_videos = self.df[['title', 'webpage_url']].tail(n=10)
        self.oldest_upload = self.df.loc[self.df['upload_date'].idxmin()]
        self.three_randoms()

    def graph(self):
        self.grapher = Grapher(self.df, self.tags)
        self.grapher.average_rating()
        self.grapher.duration()
        self.grapher.views()
        self.grapher.gen_tags_plot()

    def start_analysis(self):
        self.check_df()
        if WordCloud is not None:
            self.make_wordcloud()
        self.compute()
        self.graph()

    def run(self):
        """Main function for downloading and analyzing data."""
        file1 = os.path.join(self.raw, '00001.info.json')
        some_data = os.path.isfile(file1)
        if not some_data:
            if self.takeout is not None:
                self.download_data()
            else:
                self.deprecated_download_data_via_youtube_dl_login()
        some_data = os.path.isfile(file1)
        if some_data:
            self.start_analysis()
        else:
            print('No data was downloaded.')


if __name__ == '__main__':
    print('Welcome!'); sys.stdout.flush()
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", '--out', default='data',
                        help="Path to empty directory for data storage.")
    parser.add_argument('-d', '--delay', default=0,
                        help='Time to wait between requests. May help avoid 2FA.')
    parser.add_argument('-t', '--takeout',
                        help='Path to an unzipped Takeout folder downloaded from https://takeout.google.com/')
    args = parser.parse_args()
    analysis = Analysis(args.takeout, args.out, float(args.delay))
    analysis.run()
    launch_web()
