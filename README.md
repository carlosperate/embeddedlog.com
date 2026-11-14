# Pelican project to build embeddedlog.com

## Installation instructions

This repository has submodules, so make sure they are initialised after clone:

```
git clone --recursive https://github.com/carlosperate/carlosperate.github.io.git 
```

General documentation also found in the
[Pelican website](http://docs.getpelican.com/en/stable/install.html).

This project dependencies are a dependency group in `pyproject.toml`.
Use pip >= 25.1 in a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
pip install --group site
```

## Repository structure

* **embeddedlog**: Pelican content directory.
* **plugins**: Pelican plugins used (downloaded or created this website).
* **themes**: Tested themes, and the theme created for the website.


## Building the website

From the root directory of this repository:

```
pelican -s pelicanconf.py
```

To automatically build on each file change and automatically serving files
to http://127.0.0.1:8080 :

```
pelican -s pelicanconf.py --autoreload --listen
```

For the final publishing output the `pelicanconfpublish.py` script imports the
`pelicanconf.py` and updates or adds values:

```
pelican -s pelicanconfpublish.py
```
