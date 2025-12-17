# DACAD

## Dumb(er) Automatic Cover Art Downloader

[![License](https://img.shields.io/github/license/shrx/dacad.svg?style=flat)](https://github.com/shrx/dacad/blob/master/LICENSE)

---

This tool is a dumbed-down fork of [SACAD](https://github.com/desbma/sacad).

### Changes from SACAD

The following features have been removed from the original SACAD:

- Images are downloaded in their original resolution, no resizing is performed
- Format conversion is simplified: images are converted to match the output file extension
- Removed image similarity detection
- No longer prefers covers based on source reliability rankings
- Removed progressive JPEG conversion
- Removed image crunching

The sorting algorithm has been simplified to: _select the highest resolution cover available_ (preferring square aspect ratios).

---

DACAD is a multi platform command line tool to download album covers without manual intervention, ideal for integration in scripts, audio players, etc.

DACAD also provides a second command line tool, `dacad_r`, to scan a music library, read metadata from audio tags, and download missing covers automatically, optionally embedding the image into audio audio files.

## Features

- Automatically finds and downloads the highest resolution cover available
- Supports JPEG and PNG formats
- Customizable output: save image along with the audio files / in a different directory named by artist/album / embed cover in audio files...
- Currently support the following cover sources:
  - Deezer
  - Discogs
  - Last.fm
  - Itunes
- Simple sorting algorithm: always selects the highest resolution cover available
- Cache search results locally for faster future search
- Do everything to avoid getting blocked by the sources: hide user-agent and automatically take care of rate limiting
- Multiplatform (Windows/Mac/Linux)

DACAD is designed to be robust and be executed in batch of thousands of queries:

- HTML parsing is done without regex but with the LXML library, which is faster, and more robust to page changes
- When the size of an image reported by a source is not reliable (ie. Google Images), automatically download the first KB of the file to get its real size from the file header
- Process several queries simultaneously (using [asyncio](https://docs.python.org/3/library/asyncio.html)), to speed up processing
- Automatically reuse TCP connections (HTTP Keep-Alive), for better network performance
- Automatically retry failed HTTP requests
- Music library scan supports all common audio formats (MP3, AAC, Vorbis, FLAC..)
- Cover sources page or API changes are quickly detected, thanks to high test coverage, and DACAD is quickly updated accordingly

## Installation

DACAD requires [Python](https://www.python.org/downloads/) >= 3.10.

### From source

1. If you don't already have it, [install setuptools](https://pypi.python.org/pypi/setuptools#installation-instructions) for Python 3
2. Clone this repository: `git clone https://github.com/shrx/dacad`
3. Install DACAD: `python3 setup.py install`

## Command line usage

Two tools are provided: `dacad` to search and download one cover, and `dacad_r` to scan a music library and download all missing covers.

Run `dacad -h` / `dacad_r -h` to get full command line reference.

### Examples

To download the cover of _Master of Puppets_ from _Metallica_, to the file `AlbumArt.jpg`: `dacad "metallica" "master of puppets" AlbumArt.jpg`.

To download covers for your library: `dacad_r library_directory AlbumArt.jpg`.

## Limitations

- Only supports front covers

## Adding cover sources

Adding a new cover source is very easy if you are a Python developer, you need to inherit the `CoverSource` class and implement the following methods:

- `getSearchUrl(self, album, artist)`
- `parseResults(self, api_data)`
- `updateHttpHeaders(self, headers)` (optional)

See comments in the code for more information.

## License

[Mozilla Public License Version 2.0](https://www.mozilla.org/MPL/2.0/)
