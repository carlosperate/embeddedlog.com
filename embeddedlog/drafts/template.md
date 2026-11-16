Title: Template Article Title
Author: carlosperate
Date: 2000-12-30
Modified: 2019-12-27
Category: Blog
Tags: github, documentation, web, raspberry-pi, sbc, arduino, microbit, micropython, python, javascript
Slug: template
Summary: Summary in 50 words?
Lang: en
Status: draft
og_image: /images/something.jpg
related_posts: static-docs-from-github-wiki, static-docs-from-github-wiki, static-docs-from-github-wiki


This is a template. Ideally if I add extra tags I should add them here as well.

<!-- This is a comment -->

<!-- Note: I still need to test the `og_image` page attribute. -->

Contents:

[TOC]


## Adding Tweets

Here is a text tweet with link:

@carlosperate/status/802144214628921344

Here is a text tweet with media:

@carlosperate/status/333995782304825344

Link to a tweeter username: @carlosperate


## Adding Images

![Talk Schedule Saturday](/images/theme/background_tile.png)


### Additional Formatting with HTML

These two images fit side to side:

<img src="/images/theme/background_tile.png" alt="alt 1" width="49%">
<img src="/images/theme/background_tile.png" alt="alt 2" width="49%">

This one is just slightly wider than the container (only works with no
sidebar):

<img src="/images/banners/quickhue_banner.png" alt="alt 3" class="wider-than-parent">

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.

And for a full width image (only works with no sidebar):

<img src="/images/banners/quickhue_banner.png" alt="alt 3" class="full-width">


## Adding YouTube Videos

Here is a responsive embedded YouTube video, only first key mandatory, the
others are shown with their default value:

[[{
    "YouTube": "8dc4siImaz8",
    "allowfullscreen": True,
    "seamless": True
}]]

Here is a embedded YouTube video with a fix width and height.
This is not recommended as it not responsive and will break the layout in
lower resolutions:

[[{
    "YouTube": "8dc4siImaz8",
    "width": 640,
    "height": 480
}]]

Minimal:

[[{"YouTube": "8dc4siImaz8"}]]


## Adding Social Cards

Here are 3 social cards, 1st often without image, 2nd often with image, 3rd
has the title & description hardcoded:

::SocialCard[https://google.com]

::SocialCard[https://bing.com]

::SocialCard[https://embeddedlog.com]{
    "title": "Embedded Log",
    "description": "Overrides the fetched title and description"
}


## Adding Tables

Markdown tables use a soft blue header and alternating row shades automatically:

| Interface | Typical use |
|-----------|-------------|
| UART | Serial logs and a command-line console. |
| I2C | Connecting sensors with a shared clock and data line. |
| SPI | Communicating with displays and external memory. |
| SWD | Programming and debugging a microcontroller. |

Use colons in the separator row to align individual columns. This example uses
illustrative measurements, inline code and right-aligned numbers:

| Build | Flags | Size (KiB) |
|:------|:-----:|-----------:|
| Debug | `-Og` | 128 |
| Release | `-O2` | 96 |
| Small | `-Os` | 80 |


## Adding Code Snippets

Just like any other code snippet in MarkDown:

```python
'''
Conway's Game Of Life for the micro:bit
Press button A or tap the micro:bit to generate a fresh layout.
'''

import microbit
import random

arena1 = bytearray(7 * 7)
arena2 = bytearray(7 * 7)

def show():
    img = microbit.Image(5,5)
    for y in range(5):
        for x in range(5):
            img.set_pixel(x, y, arena1[8 + y * 7 + x]*9)
    microbit.display.show(img)

# do 1 iteration of Conway's Game of Life
def conway_step():
    global arena1, arena2
    for i in range(5 * 5): # loop over pixels
        i = 8 + (i // 5) * 7 + i % 5
        # count number of neighbours
        num_neighbours = (arena1[i - 8] +
                arena1[i - 7] +
                arena1[i - 6] +
                arena1[i - 1] +
                arena1[i + 1] +
                arena1[i + 6] +
                arena1[i + 7] +
                arena1[i + 8])
        # check if the centre cell is alive or not
        self = arena1[i]
        # apply the rules of life
        if self and not (2 <= num_neighbours <= 3):
            arena2[i] = 0 # not enough, or too many neighbours: cell dies
        elif not self and num_neighbours == 3:
            arena2[i] = 1 # exactly 3 neighbours around an empty cell: cell is born
        else:
            arena2[i] = self # stay as-is
    # swap the buffers (arena1 is now the new one to display)
    arena1, arena2 = arena2, arena1

while True:
    # randomise the start
    for i in range(5 * 5): # loop over pixels
        i = 8 + (i // 5) * 7 + i % 5
        arena1[i] = random.randrange(2) # set the pixel randomly
    show()
    microbit.sleep(1) # need to yield to update accelerometer (not ideal...)

    # loop while button a is not pressed
    while not microbit.button_a.is_pressed() and microbit.accelerometer.get_z() < -800:
        conway_step()
        show()
        microbit.sleep(150)
```

## Conclusion

This is a quote:

> *Any sufficiently advanced technology is indistinguishable from magic.*
>
> - Arthur C. Clarke

Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.
