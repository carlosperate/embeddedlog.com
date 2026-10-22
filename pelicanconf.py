#!/usr/bin/env python
# -*- coding: utf-8 -*- #
"""
This file deals with all the different configuration options for Pelican.

It will configure the right settings based on the Build Mode set in 
pelicanbuildmode.py.
"""
from __future__ import unicode_literals
from distutils.version import LooseVersion
import datetime
import os
import sys

# Check version of Pelican
from pelican import __version__ as pelican_version
if LooseVersion(pelican_version) < LooseVersion('4.0.0'):
    print('Please upgrade Pelican to a version >= 4.0')
    exit(1)

# Check the Build Mode configured
this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(this_dir)
from pelicanbuildmode import get_build_mode, BuildMode

BUILD_MODE = get_build_mode()
print("Build Mode set to: {}".format(BUILD_MODE))

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Website data
AUTHOR = u'carlosperate'
SITENAME = u'Embedded Log'
TIMEZONE = 'Europe/London'
DEFAULT_DATE_FORMAT = '%d/%m/%Y'
LOCALE = 'C'
DEFAULT_LANG = u'en'
BUILD_YEAR = datetime.datetime.now().year

# Paths data
PORT = 8080
if BUILD_MODE == BuildMode.LOCALHOST_RELATIVE:
    SITEURL = ''
    RELATIVE_URLS = True
elif BUILD_MODE == BuildMode.LOCALHOST_ABSOLUTE:
    SITEURL = '//localhost:{}'.format(PORT)
    RELATIVE_URLS = False
elif BUILD_MODE == BuildMode.PUBLISH:
    SITEURL = '//www.embeddedlog.com'
    RELATIVE_URLS = False
else:
    raise Exception('Incorrect BUILD_MODE value: {}'.format(BUILD_MODE))
print(f"Site URL set to: {SITEURL}\nRelative URLs {'enabled' if RELATIVE_URLS else 'disabled'}")
PATH = os.path.join(PROJECT_ROOT, 'embeddedlog')
STATIC_PATHS = ['images']    # Relative to PATH
OUTPUT_RETENTION = []
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'output')

# Internal Pelican cache speeds up build time
if BUILD_MODE == BuildMode.LOCALHOST_RELATIVE:
    LOAD_CONTENT_CACHE = True
    DELETE_OUTPUT_DIRECTORY = False
elif BUILD_MODE in (BuildMode.LOCALHOST_ABSOLUTE, BuildMode.PUBLISH):
    LOAD_CONTENT_CACHE = False
    DELETE_OUTPUT_DIRECTORY = True

# Menu
DISPLAY_PAGES_ON_MENU = True
PAGES_SORT_ATTRIBUTE = 'page-order'
DISPLAY_CATEGORIES_ON_MENU = False
MENUITEMS = (('Blog', SITEURL + '/blog/'),
             ('About', SITEURL + '/about/'),)

# Sidebar
HIDE_SIDEBAR = True
DISPLAY_CATEGORIES_ON_SIDEBAR = True
DISPLAY_RECENT_POSTS_ON_SIDEBAR = True
DISPLAY_TAGS_ON_SIDEBAR = True
DISPLAY_TWITTER_TIMELINE_ON_SIDEBAR = True
TAG_CLOUD_MAX_ITEMS = 10
SOCIAL = (('github', 'https://github.com/carlosperate'),
          ('twitter', 'https://twitter.com/carlosperate'),
          ('medium', 'https://medium.com/@carlosperate'),)
LINKS = (('The Amp Hour podcast', 'http://www.theamphour.com'),
         ('Embedded.fm podcast', 'http://embedded.fm'),)

# Profile picture
AVATAR = SITEURL + '/images/theme/profile_large.jpg'

# Pages data (relative to PATH)
PAGE_PATHS = ['pages']
PAGE_URL = '{slug}/index.html'
PAGE_SAVE_AS = '{slug}/index.html'
PAGE_ORDER_BY = 'page-order'
IGNORE_FILES = ['README.md']

# Article and Categories data
ARTICLE_URL = '{category}/{slug}.html'
ARTICLE_SAVE_AS = '{category}/{slug}.html'
TEMPLATE_PAGES = {'tag-web-tech.html': 'tag/web-tech.html'}
CATEGORY_URL = '{slug}/index.html'
CATEGORY_SAVE_AS = '{slug}/index.html'
USE_FOLDER_AS_CATEGORY = True
DEFAULT_CATEGORY = 'Blog'
SUMMARY_MAX_LENGTH = 50    # In words

# Banner/Carousel in pages
BANNER = 'images/banners/default_banner.jpg'
BANNER_SUBTITLE = 'This is my subtitle'

# General navigation
DEFAULT_PAGINATION = 5
DISPLAY_BREADCRUMBS = True

# Markdown settings: http://pythonhosted.org/Markdown/reference.html#markdown
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.codehilite': {'css_class': 'highlight'},
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
        'markdown.extensions.toc': {},
    },
    'output_format': 'html5',
}

# Pelican can use Typogrify, but needs to 'pip install typogrify' first
TYPOGRIFY = False

# Plugin settings
PLUGIN_PATHS = [os.path.join(PROJECT_ROOT, 'plugins')]
PLUGINS = [
    'related_posts',
    'pelican_youtube',
    'embed_tweet',
    'social_card',
    'reading_time',
    # Don't use the medium scrapper plugin any more
    # 'medium_previews'
]

###############################################################################
# Plugins config
###############################################################################
# Plugin: Related Posts
RELATED_POSTS_MAX = 3
RELATED_POSTS_SKIP_SAME_CATEGORY = False

# Plugin: YouTube, manually created variable
PLUGIN_YOUTUBE_ADD_CSS = True

# Plugin: Embed Tweet, values 'left', 'right', 'center', None
EMBED_TWEET_ALIGN = 'center'

# Plugin: Medium, URL used in different parts of website/theme
MEDIUM_URL = 'https://medium.com/@carlosperate'

###############################################################################
# Theme specific configuration
###############################################################################
THEME = os.path.join(PROJECT_ROOT, 'themes', 'embeddedlog-theme')
THEME_STATIC_DIR = 'theme'
SHOW_ARTICLE_AUTHOR = False
SHOW_ARTICLE_CATEGORY = False
SHOW_DATE_MODIFIED = True

# CC license offered by the bootstrap theme
CC_LICENSE = 'CC-BY'

# GitHub active repositories (included in bootstrap theme)
GITHUB_USER = 'carlosperate'
GITHUB_REPO_COUNT = 5
GITHUB_SKIP_FORK = 'true'
GITHUB_SHOW_USER_LINK = 'true'

# Facebook/Twitter Cards (included in bootstrap theme)
USE_OPEN_GRAPH = True
TWITTER_CARDS = True
TWITTER_USERNAME = 'carlosperate'

# Share buttons (Shariff included in bootstrap theme)
SHARIFF = True
SHARIFF_LANG = 'en'
SHARIFF_ORIENTATION = 'horizontal'  # horizontal, vertical
SHARIFF_BUTTON_STYLE = 'standard'   # standard, icon, icon-count
SHARIFF_TWITTER_VIA = 'carlosperate'
SHARIFF_SERVICES = ['twitter', 'facebook', 'linkedin', 'reddit', 'whatsapp']

# In the EmbeddedLog theme this is the top box in the index.html only
ABOUT_ME = True

# Analytics
if BUILD_MODE in (BuildMode.LOCALHOST_RELATIVE, BuildMode.LOCALHOST_ABSOLUTE):
    GOOGLE_ANALYTICS = None
elif BUILD_MODE == BuildMode.PUBLISH:
    # We don't want any cookies or user tracking
    GOOGLE_ANALYTICS = None

###############################################################################
# Feed configuration
###############################################################################
# Feed generation is usually not desired when developing
if BUILD_MODE in (BuildMode.LOCALHOST_RELATIVE, BuildMode.LOCALHOST_ABSOLUTE):
    FEED_ATOM = None
    FEED_ALL_ATOM = None
    CATEGORY_FEED_ATOM = None
    FEED_RSS = None
    FEED_ALL_RSS = None
    CATEGORY_FEED_RSS = None
elif BUILD_MODE == BuildMode.PUBLISH:
    FEED_ATOM = 'feeds/feed.atom.xml'
    FEED_ALL_ATOM = 'feeds/all.atom.xml'
    CATEGORY_FEED_ATOM = 'feeds/{slug}.atom.xml'
    FEED_RSS = 'feeds/feed.rss.xml'
    FEED_ALL_RSS = 'feeds/all.rss.xml'
    CATEGORY_FEED_RSS = 'feeds/{slug}.rss.xml'
FEED_DOMAIN = SITEURL
TRANSLATION_FEED_ATOM = None
TRANSLATION_FEED_RSS = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
TAG_FEED_ATOM = None
TAG_FEED_RSS = None

print('Pelican configuration loaded successfully')
