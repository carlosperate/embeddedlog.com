import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import markdown
import requests
from bs4 import BeautifulSoup
from PIL import Image
from pelican import Pelican, signals
from pelican.readers import MarkdownReader
from pelican.settings import read_settings

from plugins.social_card import socialcard


class DirectiveTests(unittest.TestCase):
    def render(self, source):
        rendered = markdown.markdown(source, extensions=["extra", "codehilite"])

        def card(url, options, output_path):
            return {
                "url": url, "host": "example.com", "site": None,
                "title": options.get("title", "Example"),
                "description": options.get("description", ""),
                "image": None, "favicon": None,
            }

        with patch.object(socialcard, "fetch_card", side_effect=card) as fetch:
            result = socialcard.inject_socialcards(rendered, "/unused")
        return rendered, result, fetch.call_args_list

    def test_code_examples_are_unchanged_and_never_fetched(self):
        directive = "::SocialCard[https://example.com]"
        for source in [
            "`{}`".format(directive),
            "```text\n{}\n```".format(directive),
            "    " + directive,
            "<pre><code>{}</code></pre>".format(directive),
            '<a href="https://example.org">{}</a>'.format(directive),
            "<!-- {} -->".format(directive),
            '<span title="{}">Example</span>'.format(directive),
        ]:
            with self.subTest(source=source):
                rendered, result, calls = self.render(source)
                self.assertEqual(result, rendered)
                self.assertEqual(calls, [])

    def test_identical_code_and_real_directives_replace_only_prose(self):
        directive = "::SocialCard[https://example.com]"
        _, result, calls = self.render("`{0}`\n\n{0}\n\n`{0}`".format(directive))
        soup = BeautifulSoup(result, "html.parser")
        self.assertEqual(len(calls), 1)
        self.assertEqual([code.get_text() for code in soup.find_all("code")], [directive, directive])
        self.assertEqual(len(soup.select("a.social-card")), 1)
        self.assertEqual(soup.select("p a.social-card"), [])

    def test_markdown_links_in_overrides_become_plain_text(self):
        _, result, calls = self.render(
            '::SocialCard[https://example.com]{"title": "See [the guide](https://example.org)", '
            '"description": "Read [more](https://example.net)"}'
        )
        soup = BeautifulSoup(result, "html.parser")
        self.assertEqual(calls[0].args[1], {"title": "See the guide", "description": "Read more"})
        self.assertEqual(soup.select_one(".social-card-title").get_text(), "See the guide")
        self.assertEqual(soup.select_one(".social-card-desc").get_text(), "Read more")
        self.assertEqual(len(soup.find_all("a")), 1)
        self.assertFalse(soup.get_text().endswith("}"))

    def test_emphasis_and_inline_code_in_overrides_become_plain_text(self):
        _, _, calls = self.render(
            '::SocialCard[https://example.com]{"title": "Use `foo` and **bold**"}'
        )
        self.assertEqual(calls[0].args[1], {"title": "Use foo and bold"})

    def test_entities_and_escaped_quotes_preserve_valid_json(self):
        _, result, calls = self.render(
            '::SocialCard[https://example.com?a=1&b=2]'
            '{"title": "Use \\"quotes\\" & &quot;entities&quot;", "description": "A &lt; B"}'
        )
        self.assertEqual(calls[0].args[0], "https://example.com?a=1&b=2")
        self.assertEqual(calls[0].args[1], {"title": 'Use "quotes" & "entities"', "description": "A < B"})
        self.assertIn("&lt;", result)

    def test_multiple_cards_preserve_order_options_and_surrounding_unicode(self):
        _, result, calls = self.render(
            'Before café.\n\n::SocialCard[https://example.com]{"title": "First"}\n\n'
            'Between.\n\n::SocialCard[https://example.com]{"title": "Second"}\n\nAfter.'
        )
        soup = BeautifulSoup(result, "html.parser")
        self.assertEqual(len(calls), 2)
        self.assertEqual([a.get_text() for a in soup.select(".social-card-title")], ["First", "Second"])
        self.assertEqual([p.get_text() for p in soup.find_all("p")], ["Before café.", "Between.", "After."])

    def test_directive_inside_override_is_not_fetched_or_replaced(self):
        title = "Literal ::SocialCard[https://example.org]"
        _, result, calls = self.render('::SocialCard[https://example.com]{"title": "' + title + '"}')
        self.assertEqual(len(calls), 1)
        self.assertEqual(BeautifulSoup(result, "html.parser").select_one(".social-card-title").get_text(), title)

    def test_invalid_json_warns_without_dropping_the_article(self):
        with self.assertLogs(socialcard.logger, level="WARNING"):
            _, result, calls = self.render('::SocialCard[https://example.com]{"title": invalid}')
        self.assertEqual(len(calls), 1)
        self.assertIn('class="social-card ', result)

    def test_inline_card_preserves_surrounding_prose(self):
        _, result, calls = self.render("Before ::SocialCard[https://example.com] after.")
        self.assertEqual(len(calls), 1)
        self.assertTrue(result.startswith("<p>Before <a "))
        self.assertTrue(result.endswith("</a> after.</p>"))


def png(width, height, colour):
    data = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(data, format="PNG")
    return data.getvalue()


def response(url, data, content_type):
    result = requests.Response()
    result.status_code = 200
    result.url = url
    result._content = data
    result.headers["Content-Type"] = content_type
    return result


class DownloadTests(unittest.TestCase):
    def test_existing_output_image_is_downloaded_again(self):
        url = "https://example.com/preview.png"
        first, second = png(320, 160, "red"), png(640, 320, "blue")
        with tempfile.TemporaryDirectory() as output:
            with patch.object(socialcard, "get", side_effect=[
                response(url, first, "image/png"), response(url, second, "image/png"),
            ]) as fetch:
                before = socialcard.download(url, output)
                after = socialcard.download(url, output)
            self.assertEqual(fetch.call_count, 2)
            self.assertEqual(before[0], after[0])
            self.assertEqual(after[1:], (640, 320))
            self.assertEqual((Path(output) / after[0].lstrip("/")).read_bytes(), second)


class BuildTests(unittest.TestCase):
    def test_cached_article_refreshes_cards_in_the_configured_output(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            content = root / "content"
            content.mkdir()
            (content / "sample.md").write_text(
                "Title: Sample\nDate: 2020-01-01\nSlug: sample\n\n"
                "::SocialCard[https://example.com/page]", encoding="utf-8"
            )
            image = png(320, 160, "red")
            icon = png(16, 16, "black")
            title = "First preview"

            def fetch(url):
                if url.endswith("/page"):
                    return response(url, (
                        '<title>{}</title><meta property="og:image" content="/preview.png">'
                        '<link rel="icon" href="/icon.png">'.format(title)
                    ).encode(), "text/html")
                return response(url, image if url.endswith("/preview.png") else icon, "image/png")

            read_markdown = MarkdownReader.read
            try:
                with patch.object(socialcard, "get", side_effect=fetch) as get:
                    with patch.object(MarkdownReader, "read", autospec=True, side_effect=read_markdown) as read:
                        for name in ["first-output", "second-output"]:
                            output = root / name
                            settings = read_settings(override={
                                "PATH": str(content), "OUTPUT_PATH": str(output),
                                "CACHE_PATH": str(root / "cache"), "CACHE_CONTENT": True,
                                "LOAD_CONTENT_CACHE": True, "DELETE_OUTPUT_DIRECTORY": True,
                                "PLUGINS": [socialcard], "AUTHOR": "Test", "SITENAME": "Test",
                                "SITEURL": "https://site.example", "TIMEZONE": "UTC",
                                "ARTICLE_SAVE_AS": "{slug}.html",
                            })
                            self.assertEqual(settings["CONTENT_CACHING_LAYER"], "reader")
                            Pelican(settings).run()
                            soup = BeautifulSoup((output / "sample.html").read_text(), "html.parser")
                            self.assertEqual(soup.select_one(".social-card-title").get_text(), title)
                            for img in soup.select(".social-card img"):
                                path = output / img["src"].lstrip("/")
                                self.assertTrue(path.is_file())
                                self.assertEqual(path.read_bytes(), image if "social-card-image" in img["class"]
                                                 or "social-card-wash" in img["class"] else icon)
                            title, image = "Updated preview", png(320, 160, "blue")
                self.assertEqual(read.call_count, 1, "The second build should reuse cached Markdown")
                self.assertEqual(get.call_count, 6, "Both builds should fetch the page, preview and icon")
                self.assertFalse((content / "images").exists())
            finally:
                signals.content_object_init.disconnect(socialcard.embed_socialcard)


if __name__ == "__main__":
    unittest.main()
