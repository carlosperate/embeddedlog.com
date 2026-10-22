# Pelican Plugins

This directory contains hard copies of the pelican pluggins used for the website.

* Related Posts: https://github.com/getpelican/pelican-plugins/tree/master/related_posts
    - Updated and expanded for this website, details in its README
* Pelican Youtube: https://github.com/kura/pelican_youtube
    - Updated to work with Markdown, details in its README
* Embed Tweet: https://github.com/professorsloth/pelican-embed-tweet
    - Updated and expanded for this website, details in its README
* Social Card
    - Custom plugin to fetch URLs social media cards during build and add it to
      the article as static HTML
* Reading Time
    - Custom plugin to estimate the reading time of an article from its
      Markdown source, timing prose, code and images separately
* Medium Preview
    - Custom built for this website to include Medium Post previews
    - Quite likely not used any more and not part of the website
    - The `scrapy`, `html2text`, `feedparser` and `requests `dependencies
      are needed, but they are not installed by default in this project
