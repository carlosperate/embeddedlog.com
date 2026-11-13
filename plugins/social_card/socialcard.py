# -*- coding: utf-8 -*-
import io
import os
import re
import html
import json
import hashlib
import logging
import tempfile
from bisect import bisect_right
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from PIL import Image

from pelican import signals

logger = logging.getLogger(__name__)

MARKDOWN_DIRECTIVE_NAME = "SocialCard"
DIRECTIVE = re.compile(r"::{}\[([^\s\]]+)\]".format(MARKDOWN_DIRECTIVE_NAME))
OPTION_KEYS = {"title", "description"}

# Named first: NXP and Arm block fake browser agents, Pimoroni rate-limits the requests default
HEADERS = {"User-Agent": "EmbeddedLogSocialCard/1.0 (+https://www.embeddedlog.com)"}
# Retried with a real browser agent for sites that only serve browsers
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
}
TIMEOUT = 20

# Generated images belong to the build output and are refreshed each build.
IMAGES_DIR = os.path.join("images", "social-cards")

# Must match .social-card-media in the theme's style.css (268x140)
SLOT_RATIO = 268 / 140

IMAGE_EXTENSIONS = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
    "image/webp": ".webp", "image/svg+xml": ".svg",
    "image/x-icon": ".ico", "image/vnd.microsoft.icon": ".ico",
}

TITLE_SEPARATORS = (" | ", " - ", " – ", " — ", " · ")

HTML = """<a class="social-card social-card-{kind}" href="{url}" target="_blank" rel="noopener">\
<span class="social-card-media">{media}</span>\
<span class="social-card-content">\
<span class="social-card-body"><span class="social-card-text">\
<span class="social-card-title">{title}</span>{description}</span></span>\
<span class="social-card-source">{favicon}<span class="social-card-site">{site}</span></span>\
</span></a>"""


class CardTextParser(HTMLParser):
    """Read visible text while keeping its source offsets and code/link boundaries."""

    EXCLUDED = {"code", "pre", "a", "script", "style"}
    BLOCKS = {"p", "div", "pre", "br", "li", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self, content):
        super().__init__(convert_charrefs=False)
        self.lines = [0] + [m.end() for m in re.finditer("\n", content)]
        self.parts, self.starts, self.offsets, self.excluded = [], [], [], []
        self.length = self.depth = 0
        self.feed(content)
        self.close()
        self.text = "".join(self.parts)

    def handle_data(self, data):
        line, column = self.getpos()
        self.parts.append(data)
        self.starts.append(self.length)
        self.offsets.append(self.lines[line - 1] + column)
        self.excluded.append(self.depth > 0)
        self.length += len(data)

    def handle_entityref(self, name):
        # Keep entities encoded until after JSON parsing, so &quot; cannot end a string.
        self.handle_data("&{};".format(name))

    def handle_charref(self, name):
        self.handle_data("&#{};".format(name))

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKS:
            self.handle_data("\n")
        if tag in self.EXCLUDED:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag in self.EXCLUDED:
            self.depth = max(0, self.depth - 1)
        if tag in self.BLOCKS:
            self.handle_data("\n")

    def source_offset(self, position):
        index = bisect_right(self.starts, position) - 1
        return self.offsets[index] + position - self.starts[index]

    def is_excluded(self, position):
        return self.excluded[bisect_right(self.starts, position) - 1]


def get_socialcard_entries(content):
    """Return (start, end, url, options) for directives outside code and links."""
    parsed = CardTextParser(content)
    decoder = json.JSONDecoder()
    entries = []
    consumed = 0
    for m in DIRECTIVE.finditer(parsed.text):
        if m.start() < consumed or parsed.is_excluded(m.start()):
            continue
        url, end, options = html.unescape(m.group(1)), m.end(), {}
        # Warned about, not raised: Pelican drops an article whose plugin raises
        if parsed.text.startswith("{", end):
            # Decoded rather than matched, so braces inside the strings don't end it
            try:
                options, end = decoder.raw_decode(parsed.text, end)
            except ValueError:
                logger.warning("SocialCard options for %s are not valid JSON", url)
            ignored = [k for k, v in options.items() if k not in OPTION_KEYS or not isinstance(v, str)]
            if ignored:
                logger.warning("SocialCard ignoring options for %s, only title and description strings "
                               "are supported: %s", url, ", ".join(ignored))
            # Inline tags were stripped before decoding; now decode text entities too.
            options = {k: BeautifulSoup(v, "html.parser").get_text()
                       for k, v in options.items() if k not in ignored}
        consumed = end
        start, end = parsed.source_offset(m.start()), parsed.source_offset(end - 1) + 1
        # A standalone card replaces its paragraph; inline cards preserve surrounding prose.
        before = re.search(r"<p>\s*$", content[:start])
        after = re.match(r"\s*</p>", content[end:])
        if before and after:
            start, end = before.start(), end + after.end()
        entries.append((start, end, url, options))
    return entries


def image_size(data):
    """Return (width, height), or None for formats Pillow cannot read (SVG)."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            return img.size
    except (OSError, Image.DecompressionBombError):
        return None


def get(url):
    """GET with the named agent, retrying as a browser if the site refuses it."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r
    except requests.HTTPError:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r


def download(url, output_path):
    """Download url into the output and return (site path, width, height).

    Raises requests.RequestException or ValueError, for the caller to report.
    """
    name = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    folder = os.path.join(output_path, IMAGES_DIR)
    r = get(url)
    content_type = r.headers.get("Content-Type", "").split(";")[0].strip()
    ext = IMAGE_EXTENSIONS.get(content_type) or \
        os.path.splitext(urlparse(url).path)[1].lower()
    data = r.content
    # Error pages can come back with a 200 from a URL ending in .png or .ico
    readable = image_size(data) or (ext == ".svg" and b"<svg" in data)
    if ext not in IMAGE_EXTENSIONS.values() or not readable:
        raise ValueError("{} is not an image ({})".format(url, content_type or "no type"))
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, name + ext)
    # Renamed into place so other threads never read a half-written file
    fd, tmp_path = tempfile.mkstemp(dir=folder, prefix=".")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp_path, file_path)
    site_path = "/" + "/".join([*IMAGES_DIR.split(os.sep), os.path.basename(file_path)])
    size = image_size(data)
    return (site_path, *size) if size else (site_path, None, None)


def pick_favicon(soup, page_url):
    """Prefer the largest declared icon, apple-touch-icon first, then /favicon.ico."""
    candidates = []
    for link in soup.find_all("link", href=True):
        rel = " ".join(link.get("rel", [])).lower()
        # mask-icon is Safari's monochrome outline, not a colour icon
        if "icon" not in rel or "mask-icon" in rel:
            continue
        sizes = re.findall(r"(\d+)x\d+", link.get("sizes", ""))
        size = max(map(int, sizes)) if sizes else (180 if "apple" in rel else 16)
        candidates.append((size, urljoin(page_url, link["href"])))
    if candidates:
        return max(candidates, key=lambda c: c[0])[1]
    return urljoin(page_url, "/favicon.ico")


def site_tokens(host):
    """Words in the host name, e.g. docs.python-guide.org -> {python, guide}."""
    labels = host.split(".")[:-1]
    return {t for label in labels for t in re.split(r"[^a-z0-9]+", label) if len(t) > 2} - {"www", "docs"}


def site_score(segment, site, host):
    """How much a title segment looks like the site name, from 0 to 1."""
    segment = segment.strip()
    if site and segment.casefold() == site.casefold():
        return 1
    words = [w for w in re.split(r"[^a-z0-9]+", segment.casefold()) if len(w) > 2]
    tokens = site_tokens(host)
    matches = [w for w in words if any(w in t or t in w for t in tokens)]
    return len(matches) / len(words) if words else 0


def clean_title(title, site, host):
    """Drop the site name from page titles; returns (title, site name)."""
    title = " ".join(title.split())
    github = re.match(r"^GitHub - ([^/\s]+/[^:\s]+)", title)
    if github:
        return github.group(1), site or "GitHub"
    for sep in TITLE_SEPARATORS:
        if sep not in title:
            continue
        head, _, suffix = title.rpartition(sep)
        prefix, _, rest = title.partition(sep)
        # Scored both ways: "Git - git-submodule Documentation" names the site first
        options = []
        if len(head) > 2:
            options.append((site_score(suffix, site, host), head, suffix))
        # "Arduino - Home" stays whole: a one-word remainder says too little
        if len(rest.split()) > 1 or len(rest) > 7:
            options.append((site_score(prefix, site, host), rest, prefix))
        best = max(options, key=lambda o: o[0], default=None)
        if best and best[0] >= 0.5:
            return best[1], site or best[2]
    return title, site


def clean_description(description, title):
    description = " ".join((description or "").split())
    description = re.sub(r"^Extension for Visual Studio Code - ", "", description)
    # GitHub appends " - owner/repo" to every repository description
    if description.endswith(" - " + title):
        description = description[:-len(" - " + title)]
    return "" if description == "None" else description


def classify(width, height):
    """Sort a preview image into how the card should show it."""
    if not width or not height:
        return "picture", "contain"
    if max(width, height) < 100:
        return "none", None
    ratio = width / height
    if ratio > 2.4 and width <= 800:
        return "logo", "tile"
    if 0.8 <= ratio <= 1.25 and width <= 512:
        return "icon", "tile"
    # Close to the slot's ratio: fill it, trimming at most about 6% per side
    if SLOT_RATIO * 0.88 < ratio < SLOT_RATIO * 1.14:
        return "picture", "cover"
    return "picture", "contain"


def fetch_card(url, options, output_path):
    host = urlparse(url).hostname or url
    host = re.sub(r"^www\.", "", host)
    card = {"url": url, "host": host, "title": host, "site": None,
            "description": "", "image": None, "favicon": None}
    try:
        r = get(url)
        # Without a charset header requests assumes Latin-1, bs4 reads <meta charset> instead
        declared = "charset" in r.headers.get("Content-Type", "").lower()
        soup = BeautifulSoup(r.content, "html.parser", from_encoding=r.encoding if declared else None)

        def meta(*names):
            for n in names:
                tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
                if tag and tag.get("content"):
                    return tag["content"].strip()
            return None

        raw_title = meta("og:title", "twitter:title") or (soup.title.string if soup.title else None) or host
        card["title"], card["site"] = clean_title(raw_title, meta("og:site_name"), host)
        card["description"] = clean_description(meta("og:description", "description", "twitter:description"), card["title"])
        image = meta("og:image", "twitter:image", "twitter:image:src")
        if image:
            try:
                card["image"] = download(urljoin(r.url, image), output_path)
            except (requests.RequestException, ValueError) as e:
                logger.warning("SocialCard using the site icon for %s, its preview image failed: %s", url, e)
        try:
            card["favicon"] = download(pick_favicon(soup, r.url), output_path)
        except (requests.RequestException, ValueError) as e:
            logger.warning("SocialCard has no site icon for %s: %s", url, e)
    except requests.RequestException as e:
        logger.warning("SocialCard could not fetch %s, the card only shows its address: %s", url, e)
    card["title"] = options.get("title", card["title"])
    card["description"] = options.get("description", card["description"])
    return card


def card_html(card):
    kind, fit = classify(*card["image"][1:]) if card["image"] else ("none", None)
    favicon = card["favicon"][0] if card["favicon"] else None
    image = card["image"][0] if kind != "none" else favicon
    if image:
        css = "social-card-image social-card-{}".format(fit or "tile")
        media = '<img class="social-card-wash" src="{0}" alt="" aria-hidden="true" loading="lazy">' \
                '<img class="{1}" src="{0}" alt="" loading="lazy">'.format(html.escape(image), css)
    else:
        media = '<span class="social-card-image social-card-tile"><i class="fas fa-link" aria-hidden="true"></i></span>'
    description = card["description"]
    site = card["site"] or card["host"]
    return HTML.format(
        kind=kind,
        url=html.escape(card["url"]),
        media=media,
        title=html.escape(card["title"]),
        description='<br><span class="social-card-desc">{}</span>'.format(html.escape(description)) if description else "",
        favicon='<img class="social-card-favicon" src="{}" alt="" loading="lazy">'.format(html.escape(favicon)) if favicon else "",
        site=html.escape(site if site == card["host"] else "{} · {}".format(site, card["host"])),
    )


def inject_socialcards(content, output_path):
    entries = get_socialcard_entries(content)
    if not entries:
        return content
    with ThreadPoolExecutor(max_workers=10) as executor:
        cards = list(executor.map(lambda e: fetch_card(e[2], e[3], output_path), entries))
    # Replace recorded ranges backwards so identical examples and later offsets stay intact.
    for (start, end, _, _), card in reversed(list(zip(entries, cards))):
        content = content[:start] + card_html(card) + content[end:]
    return content


def embed_socialcard(content):
    if content and content._content:
        content._content = inject_socialcards(content._content, content.settings["OUTPUT_PATH"])


def register():
    signals.content_object_init.connect(embed_socialcard)
