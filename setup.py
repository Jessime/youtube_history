from distutils.core import setup

# Adapted from http://peterdowns.com/posts/first-time-with-pypi.html
setup(
  name = 'youtube_history',
  packages = ['youtube_history'], # this must be the same as the name above
  version = '0.1',
  description = 'Downloads and analyzes metadata for all video in your Youtube history.',
  author = 'Jessime Kirk',
  author_email = 'jessime.kirk@gmail.com',
  url = 'https://github.com/Jessime/youtube_history', # use the URL to the github repo
  download_url = 'https://github.com/Jessime/youtube_history/tarball/0.1',
  keywords = ['youtube', 'data analysis'], # arbitrary keywords
  classifiers = [],
  requires = ['Flask',
              'matplotlib',
              'numpy',
              'pandas',
              'plotly',
              'scipy',
              'wordcloud']
)
