#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Downloads, analyzes, and reports all Youtube videos associated with a user's Google account.
"""

import json
import os
import pickle
import argparse
import subprocess as sp
import sys

from collections import namedtuple
from pathlib import Path
from uuid import uuid4
from webbrowser import open_new_tab

import pandas as pd
import numpy as np

from bs4 import BeautifulSoup
from emoji import emoji_list
from flask import Flask
from flask import render_template
from loguru import logger
from tqdm import tqdm
from wordcloud import WordCloud

from grapher import Grapher, flatten_without_nones


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
    out_base : str (default='data')
        The path to the directory where both raw and computed results should be stored.
    name : Optional[str]
        Subdir of out_base where this particular analysis should be stored (e.g. 'jessime')

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
    def __init__(self, takeout=None, out_base='data', name=None):
        self.takeout = None if takeout is None else Path(takeout).expanduser()
        if name is None:
            name = str(uuid4())
        self.path = Path(out_base) / name
        self.raw = self.path / 'raw'
        self.ran = self.path / 'ran'
        self.df = None
        self.tags = None
        self.grapher = None

        self.ad_count = None
        self.seconds = None
        self.formatted_time = None
        self.most_viewed = None
        self.least_viewed = None
        self.best_per_decile = None
        self.worst_per_decile = None
        self.emojis = None
        self.oldest_videos = None
        self.oldest_upload = None
        self.most_comments = None
        self.highest_comment_ratio = None
        self.top_uploaders = None
        self.funny = None
        self.funny_counts = None

    def setup_dirs(self):
        self.raw.mkdir(parents=True, exist_ok=True)
        self.ran.mkdir(parents=True, exist_ok=True)

    def parse_soup(self, soup):
        """Extract ad counts and video urls from html soup"""
        mdl_grid = next(soup.body.children)
        ad_count = 0
        videos = []
        for outer_cell in mdl_grid.children:
            inner_cell = next(outer_cell.children)
            inner_children = list(inner_cell.children)
            div_with_vid_url = inner_children[1]
            div_with_ads_info = inner_children[3]
            if "From Google Ads" not in str(div_with_ads_info):
                try:
                    videos.append(div_with_vid_url.a["href"])
                except TypeError:
                    pass
            else:
                ad_count += 1
        deduped_vids = list(dict.fromkeys(videos))
        return deduped_vids, ad_count
    
    def download_data(self):
        """Uses Takeout to download individual json files for each video."""
        watch_history = self.takeout / 'YouTube and YouTube Music/history/watch-history.html'
        if not watch_history.is_file():
            raise ValueError(f'"{watch_history}" is not a file. Did you download your YouTube data? ')
        logger.info('Extracting video urls from Takeout.'); sys.stdout.flush()
        try:
            text = watch_history.read_text()
        except UnicodeDecodeError:
            text = watch_history.read_text(encoding='utf-8')
        soup = BeautifulSoup(text, 'lxml')
        videos, self.ad_count = self.parse_soup(soup)
        url_path = self.path / 'urls.txt'
        url_path.write_text('\n'.join(videos))
        logger.info(f'Urls extracted. Downloading data for {len(videos)} videos now.')
        output = self.raw / '%(autonumber)s'
        cmd = f'yt-dlp -o "{output}" --skip-download --write-info-json -i -a {url_path}'
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
        line = True
        while line:
            line = p.stdout.readline().decode("utf-8").strip()
            logger.info(line)

    def df_from_files(self):
        """Constructs a Dataframe from the downloaded json files.

        All json keys whose values are not lists are compiled into the dataframe.
        The dataframe is then saved as a pickle file in the self.ran directory.
        The tags of each video are pickled and saved as `tags.pkl`
        """
        logger.info('Creating dataframe...')
        raw_paths = sorted(self.raw.glob("*.json"))
        video_metas = []
        keys_and_defaults = {"like_count": pd.NA,
                             "comment_count": pd.NA, 
                             "duration": pd.NA, 
                             "view_count": pd.NA, 
                             "upload_date": pd.NaT, 
                             "description": "", 
                             "height": pd.NA, 
                             "title": "", 
                             "webpage_url": "", 
                             "uploader": ""}
        tags = []
        for raw_path in tqdm(raw_paths):
            meta = json.load(open(raw_path))
            tags.append(meta.get("tags", []))
            meta_to_keep = {k: meta.get(k, d) for k, d in keys_and_defaults.items()}
            video_metas.append(meta_to_keep)
        self.df = pd.DataFrame(video_metas)
        self.df['upload_date'] = pd.to_datetime(self.df['upload_date'], format='%Y%m%d')
        self.tags = tags


    def make_wordcloud(self):
        """Generate the wordcloud file and save it to static/images/."""
        logger.info('Creating wordcloud')
        wordcloud = WordCloud(width=1920,
                              height=1080,
                              relative_scaling=.5)
        flat_tags = flatten_without_nones(self.tags)
        wordcloud.generate(' '.join(flat_tags))
        wordcloud.to_file(os.path.join('static', 'images', 'wordcloud.png'))

    def check_df(self):
        """Create the dataframe and tags from files if file doesn't exist."""
        df_file = self.ran / 'df.pkl'
        if df_file.is_file():
            self.df = pd.read_pickle(df_file)
            self.tags = pickle.load(open(self.ran / 'tags.pkl', 'rb'))
        else:
            self.df_from_files()
            self.df.to_pickle(self.ran / 'df.pkl')
            pickle.dump(self.tags, open(self.ran / 'tags.pkl', 'wb'))

    def total_time(self):
        """The amount of time spent watching videos."""
        self.seconds = self.df["duration"].sum()
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
        """Finds well liked and highly viewed videos
        
        Note that Youtube has removed the dislike count, 
        so we have to get a bit creative about what we're analyzing.
        """
        self.most_viewed = self.df.loc[self.df['view_count'].idxmax()]
        low_views = self.df[self.df['view_count'] < 10]
        self.least_viewed = low_views.sample(min(len(low_views), 10), random_state=0)
        self.df['likes_to_views'] = self.df["like_count"] / self.df["view_count"]
        self.df['deciles'] = pd.qcut(self.df['view_count'].fillna(0), 10, labels=False)
        grouped = self.df.groupby(by='deciles')
        self.best_per_decile = self.df.iloc[grouped['likes_to_views'].idxmax()]
        self.worst_per_decile = self.df.iloc[grouped['likes_to_views'].idxmin()]

    def most_emojis_description(self):
        def _emoji_variety(desc):
            return len({x['emoji'] for x in emoji_list(desc)})

        counts = self.df['description'].apply(_emoji_variety)
        self.emojis = self.df.iloc[counts.idxmax()]

    def funniest_description(self):
        """Counts number of times 'funny' is in each description. Saves top result."""
        funny_counts = []
        descriptions = []
        index = []
        for i, d in enumerate(self.df["description"]):
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

    def chatty(self):
        self.most_comments = self.df.iloc[self.df["comment_count"].idxmax()]
        self.df["comment_to_view"] = self.df["comment_count"] / self.df["view_count"]
        chatty = self.df[self.df["comment_count"] > 100]
        self.highest_comment_ratio = chatty.iloc[chatty["comment_to_view"].idxmax()]

    def three_randoms(self):
        """Finds results for video resolutions, most popular channels, and funniest video."""
        self.chatty()
        self.top_uploaders = self.df["uploader"].value_counts().head(n=15)
        self.funniest_description()

    def compute(self):
        logger.info('Computing...')
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
        self.make_wordcloud()
        self.compute()
        self.graph()

    def run(self):
        """Main function for downloading and analyzing data."""
        self.setup_dirs()
        some_data = (self.raw /'00001.info.json').is_file()
        if not some_data:
            self.download_data()
        some_data = (self.raw /'00001.info.json').is_file()
        if some_data:
            self.start_analysis()
        else:
            logger.info('No data was downloaded.')


if __name__ == '__main__':
    logger.info('Welcome!')
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", '--out', default='data',
                        help="Path to empty directory for data storage.")
    parser.add_argument('-n', '--name',
                        help='Name of analyses (e.g. jessime)')
    parser.add_argument('-t', '--takeout',
                        help='Path to an unzipped Takeout folder downloaded from https://takeout.google.com/')
    args = parser.parse_args()
    analysis = Analysis(args.takeout, args.out, args.name)
    analysis.run()
    launch_web()
