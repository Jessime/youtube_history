import numpy as np

import plotly
import plotly.graph_objs as go

from collections import Counter


def flatten_without_nones(seq):
    flat = []
    for nested in seq:
        if nested is not None:
            flat += nested
    return flat


class Grapher():
    """Creates html-embeddable interactive graphs of Youtube data using plotly.
    
    Parameters
    ----------
    df : Dataframe
        Users youtube data
    tags : [[str]]
        A list of tags for each downloaded video
        
    Attributes
    ----------
    plot : func
        Alias for plotly's main plotting function
    avg_rate_plot : str
        html <div> of a plotly histogram of the average ratings for each video
    duration : str
        html <div> of a plotly histogram of video durations on a log scale
    views_plot : str
        html <div> of a plotly histogram of video views on a log scale
    tags_plot : str
        html <div> of a plotly scatterplot of most common rollings tags
    """
    def __init__(self, df, tags):
        self.df = df
        self.tags = tags
        
        self.plot = plotly.offline.plot
        self.avg_rate_plot = None
        self.duration_plot = None
        self.views_plot = None
        self.tags_plot = None        
        
    def make_log_data(self, series, dec=2):
        """Log10 transforms all data before plotting.
        
        Parameters
        ----------
        series : Series
            The data values to log transform
        dec : int (default=2)
            The number of decimals to round to for tick labels
            
        Returns
        -------
        log : Series
            The log transformed series
        ticks : ndarray
            Physical locations (positions) of the tick labels on the plot
        ticks_txt : ndarray
            Tick labels, on log scale, at each of the tick positions"""
        log = np.log10(series)
        ticks = np.linspace(min(log), max(log), 10)
        ticks_txt = np.round(np.power(10, ticks), decimals=dec)
        return log, ticks, ticks_txt

    def humanize(self, num):
        """Converts large int values into human readable strings
        
        Parameters
        ----------
        num : int
            The large value to convert
            
        Returns
        -------
        num : str
            Formatted value
        """
        millnames = ['',' K',' M',' B',' T']
        n = float(num)
        log = np.log10(abs(n))/3
        millidx = max(0,min(len(millnames)-1,
                            int(np.floor(0 if n == 0 else log))))
        num_str = '{:.0f}{}'.format(n / 10**(3 * millidx), millnames[millidx])
        return num_str
        
    def average_rating(self):
        data = [go.Histogram(x=self.df.average_rating,
                             marker=dict(color='#673AB7'))]
        layout = dict(title='All Rating',
                      xaxis = dict(title = 'Rating'),
                      yaxis = dict(title = 'Count'))
        fig = dict(data=data, layout=layout)
        self.avg_rate_plot = self.plot(fig,  output_type='div')
    
    def duration(self):  

        dur, ticks, ticks_txt = self.make_log_data(self.df.duration/60)
        data = [go.Histogram(x=dur,
                             marker=dict(color='#673AB7'))]
        layout = dict(title='All Durations',
                      yaxis = dict(title = 'Count'),
                      xaxis = dict(title = 'Duration (min)',
                                   tickmode='array',
                                   tickvals=ticks,
                                   ticktext=ticks_txt))
        fig = dict(data=data, layout=layout)
        self.duration_plot = self.plot(fig,  output_type='div')
        
    def views(self):
        views, ticks, ticks_txt = self.make_log_data(self.df.view_count, 0)
        ticks_txt = [self.humanize(t) for t in ticks_txt]
        data = [go.Histogram(x=views,
                             marker=dict(color='#673AB7'))]
        layout = dict(title='All View Counts',
                      yaxis = dict(title = 'Views'),
                      xaxis = dict(title = 'Count',
                                   tickmode='array',
                                   tickvals=ticks,
                                   ticktext=ticks_txt))
        fig = dict(data=data, layout=layout)
        self.views_plot = self.plot(fig, output_type='div')
        
    def get_max_tags_and_vals(self):
        """Finds the rolling tags and their value counts over chunks of 100 videos
        
        Returns
        -------
        max_tags : [str]
            Most popular tags in each chunk of videos
        max_values : [int]
            The number of times the most popular tag appears
        """
        max_tags = []
        max_values = []
        chunk_starts = [i for i in range(0, len(self.tags), 100)]
        
        for i in chunk_starts:
            chunk = flatten_without_nones(self.tags[i:i+100])
            counted_chunk = Counter(chunk)
            top = counted_chunk.most_common(1)
            max_tags.append(top[0][0])
            max_values.append(top[0][1]) 
        return max_tags, max_values

    def gen_tags_plot(self):
        chunk_starts = [i for i in range(0, len(self.tags), 100)]
        max_tags, max_values = self.get_max_tags_and_vals()
        data = [go.Scatter(x=chunk_starts,
                           y=max_values[::-1],
                           mode='lines+markers',
                           text=max_tags[::-1], 
                           marker=dict(color='#ff4081'))]
        layout = dict(title='Rolling Counts of Most Popular Tag over 50 videos',
                      yaxis = dict(title = 'Tag Count'),
                      xaxis = dict(title = 'Position of first video in history'))
        fig = dict(data=data, layout=layout)
        self.tags_plot = self.plot(fig, output_type='div')
        
