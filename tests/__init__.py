#!/usr/bin/env python3

"""Unit tests for main module."""

import asyncio
import contextlib
import logging
import os
import socket
import unittest
import unittest.mock
import warnings

import PIL.Image
import requests
import web_cache

import dacad

web_cache.DISABLE_PERSISTENT_CACHING = True


def is_internet_reachable():
    """Return True if we can reach remote servers."""
    try:
        # open TCP socket to Google DNS server
        with socket.create_connection(("8.8.8.8", 53)):
            pass
    except OSError as e:
        if e.errno == 101:
            return False
        raise
    return True


def download(url, filepath=None):
    """Download URL."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

        with contextlib.closing(
            requests.get(
                url,
                timeout=5,
                verify=False,
                stream=(filepath is not None),
                headers={"User-Agent": "Mozilla/5.0 (nope) Gecko/20100101 Firefox/90.0"},
            )
        ) as response:
            response.raise_for_status()
            if filepath is None:
                return response.content
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(2**14):
                    f.write(chunk)


def sched_and_run(coroutine, delay=0):
    """Schedule, run and wait for the result of a coroutine."""

    async def delay_coroutine(coroutine, delay):
        r = await coroutine
        if delay > 0:
            # time to cleanup aiohttp objects
            # see https://aiohttp.readthedocs.io/en/stable/client_advanced.html#graceful-shutdown
            await asyncio.sleep(delay)
        return r

    return asyncio.run(delay_coroutine(coroutine, delay))


@unittest.skipUnless(is_internet_reachable(), "Need Internet access")
class TestDacad(unittest.TestCase):
    """Test suite for main module."""

    @staticmethod
    def getImgInfo(img_filepath):
        """Get image file metadata."""
        with open(img_filepath, "rb") as img_file:
            img = PIL.Image.open(img_file)
            format = img.format.lower()
            format = dacad.SUPPORTED_IMG_FORMATS[format]
            width, height = img.size
        return format, width, height

    def test_getMasterOfPuppetsCover(self):
        """Search and download cover for 'Master of Puppets'."""
        for format in dacad.cover.CoverImageFormat:
            with self.subTest(format=format):
                with dacad.mkstemp_ctx.mkstemp(
                    prefix="dacad_test_", suffix=f".{format.name.lower()}"
                ) as tmp_filepath:
                    coroutine = dacad.search_and_download(
                        "Master of Puppets",
                        "Metallica",
                        format,
                        tmp_filepath,
                    )
                    sched_and_run(coroutine, delay=0.5)
                    if os.path.getsize(tmp_filepath):
                        out_format, out_width, out_height = __class__.getImgInfo(tmp_filepath)
                        self.assertEqual(out_format, format)
                        self.assertGreater(out_width, 0)
                        self.assertGreater(out_height, 0)
                    else:
                        self.fail("No result")

    @unittest.skipIf(os.getenv("CI") is not None, "Test is not reliable on CI servers")
    def test_getImageUrlMetadata(self):
        """Download the beginning of image files to guess their format and resolution."""
        refs = {
            "https://raw.githubusercontent.com/python-pillow/Pillow/main/Tests/images/hopper.jpg": (
                dacad.cover.CoverImageFormat.JPEG,
                (128, 128),
                1,
            ),
            "http://img2-ak.lst.fm/i/u/55ad95c53e6043e3b150ba8a0a3b20a1.png": (
                dacad.cover.CoverImageFormat.PNG,
                (600, 600),
                1,
            ),
        }
        for url, (ref_fmt, ref_size, block_read) in refs.items():
            dacad.CoverSourceResult.guessImageMetadataFromData = unittest.mock.Mock(
                wraps=dacad.CoverSourceResult.guessImageMetadataFromData
            )
            source = unittest.mock.Mock()
            source.http = dacad.http_helpers.Http()
            source.updateHttpHeaders = lambda headers: headers.update({"User-Agent": f"dacad/{dacad.__version__}"})
            cover = dacad.CoverSourceResult(
                url,
                None,
                None,
                source=source,
                source_quality=0,
                check_metadata=dacad.cover.CoverImageMetadata.ALL,
            )
            coroutine = cover.updateImageMetadata()
            sched_and_run(coroutine, delay=0.5)
            self.assertEqual(cover.size, ref_size)
            self.assertEqual(cover.format, ref_fmt)
            self.assertGreaterEqual(dacad.CoverSourceResult.guessImageMetadataFromData.call_count, 0)
            self.assertLessEqual(dacad.CoverSourceResult.guessImageMetadataFromData.call_count, block_read)

    @unittest.skipIf(os.getenv("CI") is not None, "Test is not reliable on CI servers")
    def test_coverSources(self):
        """Check all sources return valid results."""
        sources = [
            dacad.sources.ItunesCoverSource(),
            dacad.sources.LastFmCoverSource(),
            dacad.sources.DeezerCoverSource(),
            dacad.sources.DiscogsCoverSource(),
        ]
        for artist, album in zip(("Michael Jackson", "Björk"), ("Thriller", "Vespertine")):
            for source in sources:
                with self.subTest(source=source, artist=artist, album=album):
                    coroutine = source.search(album, artist)
                    results = sched_and_run(coroutine, delay=0.5)
                    coroutine = dacad.CoverSourceResult.preProcessForComparison(results)
                    results = sched_and_run(coroutine, delay=0.5)
                    self.assertGreaterEqual(len(results), 1)

                    for result in results:
                        self.assertTrue(result.urls)
                        self.assertIn(result.format, dacad.cover.CoverImageFormat)
                        self.assertGreater(result.size[0], 0)

        # check last.fm handling of queries with punctuation
        for artist, album in zip(("Megadeth", "Royal City"), ("So Far, So Good, So What?", "Little Heart's Ease")):
            source = dacad.sources.LastFmCoverSource()
            coroutine = source.search(album, artist)
            results = sched_and_run(coroutine, delay=0.5)
            self.assertGreaterEqual(len(results), 1)

    def test_unaccentuate(self):
        """Check unaccentuate remove accents."""
        self.assertEqual(dacad.sources.base.CoverSource.unaccentuate("EéeAàaOöoIïi"), "EeeAaaOooIii")

    def test_is_square(self):
        """Check is_square identify squares."""
        for x in range(1, 100):
            if x in (1, 4, 9, 16, 25, 36, 49, 64, 81):
                self.assertTrue(dacad.cover.is_square(x), x)
            else:
                self.assertFalse(dacad.cover.is_square(x), x)


# logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.CRITICAL + 1)


if __name__ == "__main__":
    # run tests
    unittest.main()
