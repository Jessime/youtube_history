# -*- coding: utf-8 -*-
"""
Created on Sat Jul 23 19:04:55 2016

@author: jessime
"""

import json
import os
import pickle
import argparse
import getpass
import subprocess as sp

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sys import stdout
#from scipy.stats import describe
from wordcloud import WordCloud
from webbrowser import open_new_tab

from flask import Flask
from flask import render_template
#from flask import send_from_directory

from grapher import Grapher

app = Flask(__name__)
app.secret_key = 'this key should be complex'
                               
@app.route('/', methods=['GET', 'POST'])    
def index():
    return render_template('index.html',
                           analysis=analysis,
                           avg_rate_plot=Grapher.avg_rate_plot,
                           duration_plot=Grapher.duration_plot,
                           views_plot=Grapher.views_plot,
                           tags_plot=Grapher.tags_plot)

def launch_web():
    app.debug = False
    url = 'http://127.0.0.1:5000'
    open_new_tab(url)
    app.run()
    
class Analysis():
    
    def __init__(self, path='data'):
        self.path = path
        self.raw = os.path.join(self.path, 'raw')
        self.ran = os.path.join(self.path, 'ran')
        self.df = None
        self.tags = None
        
        self.seconds= None
        self.formatted_time = None
        self.all_likes = None
        self.most_liked = None
        self.most_viewed = None
        self.num_4k = None
        self.oldest_videos = None
        self.oldest_upload = None
        self.HD = None
        self.UHD = None
        self.top_uploaders = None
        self.funny = None
        self.funny_counts = None

        
    def download_data(self):
        print('There\'s no data in this folder. Let\'s download some.')
        user = input('Google username: ')
        pw = getpass.getpass('Google password: ')
        files = os.path.join(self.raw, '%(autonumber)s')
        if not os.path.exists(self.raw):
            os.makedirs(self.raw)
        cmd = ('youtube-dl -u "{}" -p "{}" '+
               '-o "{}" '+
               '--skip-download --write-info-json -i '+
               'https://www.youtube.com/feed/history ').format(user, pw, files)
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT, shell=True)
        while True:
          line = p.stdout.readline()
          print(line)
          if not line: break
    
    def df_from_files(self):
        print('Creating dataframe...')
        num = len([name for name in os.listdir(self.raw)])
        files = os.path.join(self.raw, '{:05d}.info.json')
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
        self.df.to_csv(os.path.join(self.ran,'df.csv'))  

        self.tags = deletes['tags']                
        pickle.dump(self.tags, open(os.path.join(self.ran, 'tags.txt'), 'wb'))
        
    def make_wordcloud(self):
        """Generate the wordcloud file if it doesn't exist."""
        plt.rcParams['figure.figsize'] = [24.0, 18.0]
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
        df_liked = self.df[self.df.like_count > 0]
        self.lowest_rating = df_liked.ix[df_liked['average_rating'].idxmin()]
        self.most_disliked = self.df.ix[self.df['dislike_count'].idxmax()]

    def best_videos(self):
        """Finds well liked and highly viewed videos"""
        all_likes = self.df[self.df.average_rating == 5]
        all_likes = all_likes.sort_values('like_count', ascending=False)
        self.all_likes = all_likes.iloc[0]
        
        self.most_liked = self.df.ix[self.df['like_count'].idxmax()]
        self.most_viewed = self.df.ix[self.df['view_count'].idxmax()]
    
    def funniest_description(self):
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
        self.HD = self.df[(720 <= self.df.height) & (self.df.height <= 1080)].shape[0]
        self.UHD = self.df[self.df.height > 1080].shape[0]
        self.top_uploaders = self.df.uploader.value_counts().head(n=15)
        self.funniest_description()
        
    def compute(self):
        print('Computing...')
        self.total_time()
        self.worst_videos()
        self.best_videos()
        self.num_4k = self.df[self.df.width >= 3840].shape[0]
        self.oldest_videos = self.df[['title', 'webpage_url']].tail(n=10)
        self.oldest_upload = self.df.ix[self.df['upload_date'].idxmin()]
        self.three_randoms()

    def graph(self):
        grapher = Grapher(self.df, self.tags)
        grapher.average_rating()
        grapher.duration()
        grapher.views()
        grapher.gen_tags_plot()
        
    def start_analysis(self):
        self.check_df()
        self.make_wordcloud()
        self.compute()
        self.graph()
        
    def run(self):
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
    parser.add_argument("-o", '--out', default='data', help="Path to empty directory for data storage.")
    args = parser.parse_args()
    analysis = Analysis(args.out)
    analysis.run()
    launch_web()
