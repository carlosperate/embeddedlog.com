#!/usr/bin/env python
"""
Retrieves Medium articles via RSS using FeedParser
"""
from abc import ABCMeta, abstractmethod
from importlib import import_module


class MediumParser(object):
    __metaclass__ = ABCMeta

    def __init__(self, username):
        self.username = username
        self.medium_url = 'https://www.medium.com/@{}'.format(self.username)
        self.extra_imports()

    def _import(self, module_name):
        globals()[module_name] = __import__(module_name)

    def extra_imports(self):
        """We only use one of these at a time, so to save load-time we only
        import the additional dependencies needed during class initialisation.
        """
        pass

    @abstractmethod
    def get_preview_content(self):
        """ This should return a list of dictionaries with this format.
        {
            'title': 'Strig here',
            'thumbnailUrl': 'String with URL here',
            'summary': 'String here',
            'url': 'String with value full URL here'
        }
        """
        raise NotImplementedError


class MediumParserFake(MediumParser):
    """
    Retrieves Medium articles via RSS using FeedParser
    """

    def get_preview_content(self):
        return [{
                'title': 'Post one',
                'thumbnailUrl': '/theme/images/background_tile.png',
                'summary': 'This is the text for blog post one',
                'url': 'http://github.com'
            }, {
                'title': 'Post two',
                'thumbnailUrl': '/images/banners/ardublockly_banner.png',
                'summary': 'This is the text for blog post two',
                'url': 'http://github.com'
            }, {
                'title': 'Post three',
                'thumbnailUrl': '/images/banners/default_banner.jpg',
                'summary': 'This is the text for blog post three',
                'url': 'http://github.com'
            }
        ]


class MediumParserRss(MediumParser):
    """
    Retrieves Medium articles via RSS using FeedParser.
    """

    def extra_imports(self):
        self._import('feedparser')
        self._import('html2text')

    def get_preview_content(self):
        medium_rss_url = 'https://medium.com/feed/@{}'.format(self.username)
        parsed_feed = feedparser.parse(medium_rss_url)
        # RSS summary comes with all the post HTML, so we'll extract text
        text_maker = html2text.HTML2Text()
        text_maker.ignore_links = True
        text_maker.bypass_tables = True
        text_maker.ignore_images = True
        text_maker.ignore_emphasis = True
        parsed_data = []
        for post in parsed_feed.entries:
            short_summary = text_maker.handle(post['summary'])
            # The summary is the majority of blog post content, cap it
            if len(short_summary) > 250:
                short_summary = short_summary[:250].rsplit(" ", 1)[0] + '...'
            parsed_data.append({
                'title': post['title'],
                'thumbnailUrl': '',
                'summary': short_summary,
                'url': post['link']
            })
        return parsed_data


class MediumParserJson(MediumParser):
    """
    Retrieves Medium articles via JSON using Requests.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.medium_json_url = 'https://medium.com/@{}/latest?format=json'.format(self.username)
        self.json_escape_str = '])}while(1);</x>'

    def extra_imports(self):
        self._import('json')
        self._import('requests')

    def get_preview_content(self):
        json_str = requests.get(self.medium_json_url)
        json_dict = json.loads(json_str.text.replace(self.json_escape_str, '').strip())
        posts = json_dict['payload']['references']['Post']
        parsed_data = []
        for post_id in posts:
            thumb_id = posts[post_id]['virtuals']['previewImage']['imageId']
            parsed_data.append({
                'id': post_id,
                'title': posts[post_id]['title'],
                'thumbnailId': thumb_id,
                'thumbnailUrl': 'https://miro.medium.com/fit/c/1400/420/{}'.format(thumb_id),
                'summary': posts[post_id]['content']['subtitle'],
                'url': 'http://medium.com/p/{}'.format(post_id)
            })
        return parsed_data


class MediumParserScrapper(MediumParser):
    """
    Retrieves Medium articles scrapping the website.
    """

    def get_preview_content(self):
        from . import medium_scrapper
        return medium_scrapper.scrapped_medium(self.username)
