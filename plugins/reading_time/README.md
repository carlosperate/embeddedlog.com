# Reading Time

Custom made Pelican plugin that adds `reading_time`, in whole minutes, to every
article by reading its Markdown source:

```
{{ article.reading_time }} min read
```

Prose, code and images are timed separately, as code is not read at prose
speed:

* Prose: 238 words per minute, the average silent reading rate for English
  non-fiction found by a meta-analysis of 190 studies ([Brysbaert, 2019][1]).
  The metadata header, link URLs and link definitions are not counted, and
  inline `code` counts as prose.
* Code: 3 seconds per non-blank line in ```` ``` ```` fenced blocks. There is
  no measured reading rate for code, so this is roughly half prose speed for a
  typical line, while careful [code review][2] runs at around 7 seconds per
  line.
* Images (`![alt](src)` and `<img>` tags): 12 seconds for the first, one second
  less for each one after, and never less than 3 seconds, as [Medium][3] and
  [Ghost][4] do.

The result is rounded to whole minutes, with a minimum of one.

Only ```` ``` ```` fences at the start of a line are seen as code. `~~~` fences,
indented code blocks and fences inside list items are counted as prose. The
text of other Markdown syntax, HTML comments and embed directives (YouTube,
Tweets, Social Cards) is counted as words too, which only adds a few seconds.

[1]: https://doi.org/10.1016/j.jml.2019.104047
[2]: https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/
[3]: https://help.medium.com/hc/en-us/articles/214991667-Read-time
[4]: https://docs.ghost.org/themes/helpers/utility/reading_time
