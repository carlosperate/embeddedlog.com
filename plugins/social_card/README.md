# Social Cards

Custom made Pelican plugin to fetch a website's preview (title, description,
image and icon) and embed it into the article as a static link card.

```
::SocialCard[https://bing.com]
::SocialCard[https://bing.com]{"title": "Bing", "description": "Search engine"}
```

The optional JSON overrides the fetched `title` and `description`, for pages
that block the build or publish unhelpful metadata. Both are plain text:
Markdown formatting inside them is dropped.

Directives in inline code, fenced or indented code blocks, existing links and
HTML comments stay literal and do not fetch a card. Markdown links and code
inside override values are converted to plain text before parsing the JSON.

Preview images and site icons are downloaded on every build directly into
`OUTPUT_PATH/images/social-cards/` (normally `output/images/social-cards/`).
They are generated assets and are not committed. Custom output directories
passed with `pelican -o` are respected. Pelican's default reader-level content
cache keeps the Markdown, so cards and their images are still refreshed on
cached builds; generator-level caching would skip the plugin.

Pillow reads each image's size to pick how the card shows it: whole on a blurred
wash of its own colours, filling the card's 1.91:1 image slot, or as an icon on a
white tile.
If an image cannot be fetched, the card falls back to the site icon and the
build prints a warning.

Run the parser regression checks from the repository root:

```sh
pipenv run python -m unittest plugins.social_card.test_socialcard
```
