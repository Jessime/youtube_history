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

import pandas as pd
import numpy as np

from sys import stdout

try:
    from wordcloud import WordCloud
except ImportError:
    WordCloud = None

from webbrowser import open_new_tab
from flask import Flask
from flask import render_template

from grapher import Grapher


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


class Analysis():
    """Main class responsible for downloading and analyzing data.

    Parameters
    ----------
    path : str (default='data')
        The path to the directory where both raw and computed results should be stored.
    delay: float (default=0)
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
    all_likes : Series
        Video that has the most likes without a single dislike
    most_likes : Series
        Video with the most total likes
    most_viewed : Series
        Video with the most total views
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
    def __init__(self, path='data', delay=0):
        self.path = path
        self.delay = delay
        self.raw = os.path.join(self.path, 'raw')
        self.ran = os.path.join(self.path, 'ran')
        self.df = None
        self.tags = None
        self.grapher = None

        self.seconds= None
        self.formatted_time = None
        self.all_likes = None
        self.most_liked = None
        self.most_viewed = None
        self.oldest_videos = None
        self.oldest_upload = None
        self.HD = None
        self.UHD = None
        self.top_uploaders = None
        self.funny = None
        self.funny_counts = None

    def download_data(self):
        """Uses youtube_dl to download individual json files for each video."""
        print('There\'s no data in this folder. Let\'s download some.')
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
        num = len([name for name in os.listdir(self.raw) if not name[0]=='.'])
        files = os.path.join(self.raw, '~.info.json') # This is a weird hack
        files = files.replace('~', '{:05d}') # It allows path joining to work on Windows
        data = [json.load(open(files.format(i))) for i in range(1, num + 1)]

        columns = ['formats', 'tags', 'categories', 'thumbnails']
        lists = [[], [], [], []]
        deletes = {k:v for k, v in zip(columns, lists)}
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
        #plt.rcParams['figure.figsize'] = [24.0, 18.0]
        print('Creating wordcloud')
        flat_tags = [item for sublist in self.tags for item in sublist]
        wordcloud = WordCloud(width=1920,
                              height=1080,
                              relative_scaling=.5)
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
            ('weeks', 604800),  # 60 * 60 * 24 * 7
            ('days', 86400),    # 60 * 60 * 24
            ('hours', 3600),    # 60 * 60
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
                result.append("{} {}".format(value, name))
        self.formatted_time = ', '.join(result)

    def worst_videos(self):
        """Finds the lowest rated and most disliked videos"""
        self.df['total_votes'] = self.df['like_count'] + self.df['dislike_count']
        self.df['average_rating'] = self.df['like_count'] / self.df['total_votes']
        df_voted = self.df[self.df['total_votes'] > 0]
        self.lowest_rating = df_voted.loc[df_voted['average_rating'].idxmin()]
        self.most_disliked = self.df.loc[self.df['dislike_count'].idxmax()]

    def best_videos(self):
        """Finds well liked and highly viewed videos"""
        all_likes = self.df[(self.df['like_count'] > 0) & (self.df['dislike_count'] == 0)]
        all_likes = all_likes.sort_values('like_count', ascending=False)
        self.all_likes = all_likes.iloc[0]

        self.most_liked = self.df.loc[self.df['like_count'].idxmax()]
        self.most_viewed = self.df.loc[self.df['view_count'].idxmax()]

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
            self.funny = 'Wait, 0? You\'re too cool to watch funny videos on youtube?'

    def three_randoms(self):
        """Finds results for video resolutions, most popular channels, and funniest video."""
        self.HD = self.df[(720 <= self.df.height) & (self.df.height <= 1080)].shape[0]
        self.UHD = self.df[self.df.height > 1080].shape[0]
        self.top_uploaders = self.df.uploader.value_counts().head(n=15)
        self.funniest_description()

    def compute(self):
        print('Computing...')
        self.total_time()
        self.worst_videos()
        self.best_videos()
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
            self.download_data()
        some_data = os.path.isfile(file1)
        if some_data:
            self.start_analysis()
        else:
            print('No data was downloaded.')

if __name__ == '__main__':
    print('Welcome!'); stdout.flush()
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", '--out', default='data',
                        help="Path to empty directory for data storage.")
    parser.add_argument('-d', '--delay', default=0,
                        help='Time to wait between requests. May help avoid 2FA.')
    args = parser.parse_args()
    analysis = Analysis(args.out, float(args.delay))
    analysis.run()
    launch_web()
