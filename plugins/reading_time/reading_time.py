"""
Reading Time plugin for Pelican
===============================

Adds `reading_time`, in minutes, to every article by reading its Markdown
source. Prose, code blocks and images are timed separately.
"""
import re

from pelican import signals
from pelican.contents import Article
from pelican.utils import pelican_open

# Average silent reading rate for English non-fiction (Brysbaert, 2019).
WORDS_PER_MINUTE = 238
# Code has no measured reading rate: ~3 s per line is ~half prose speed, code review is ~7 s.
SECONDS_PER_CODE_LINE = 7

# Only ``` fences at the start of a line, the one code block style the posts use.
CODE_BLOCK = re.compile(r"^```.*?\n(.*?)^```", re.MULTILINE | re.DOTALL)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)|<img\b[^>]*>")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
LINK_DEFINITION = re.compile(r"^\[[^\]]+\]:.*$", re.MULTILINE)


def reading_time(source):
    """Minutes to read a Markdown source."""
    body = source.split("\n\n", 1)[-1]  # Drops the metadata header
    code = "".join(CODE_BLOCK.findall(body))
    prose = CODE_BLOCK.sub("", body)
    prose, images = IMAGE.subn("", prose)
    prose = LINK.sub(r"\1", prose)  # Keeps the link text, drops the URL
    prose = LINK_DEFINITION.sub("", prose)

    words = len(prose.split())
    code_lines = sum(1 for line in code.splitlines() if line.strip())
    seconds = (
        words / WORDS_PER_MINUTE * 60
        + code_lines * SECONDS_PER_CODE_LINE
        + sum(max(12 - i, 3) for i in range(images))  # Medium and Ghost's image scale
    )
    return max(1, round(seconds / 60))


def add_reading_time(content):
    if isinstance(content, Article):
        with pelican_open(content.source_path) as source:
            content.reading_time = reading_time(source)


def register():
    signals.content_object_init.connect(add_reading_time)
