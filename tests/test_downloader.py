import unittest
import datetime
from image_retrieval.downloader import ImageDowloader


class TestDowloader(unittest.TestCase):
    def test_query_s2_2a(self):
        dl = ImageDowloader()
        satsearch_args = dict(bbox=[-100.1, 39, -100, 39.1],
                              datetime='2018-04-01/2018-04-06',
                              url='https://earth-search.aws.element84.com/v0',
                              collections=['sentinel-s2-l2a'])
        dl.search(**satsearch_args)
        self.assertTrue(len(dl.items['sentinel-s2-l2a'].dates()) == 1)
        self.assertTrue(dl.items['sentinel-s2-l2a'].dates()[0] ==
                        datetime.date(2018, 4, 3))

    def test_query_s2_1c(self):
        dl = ImageDowloader()
        satsearch_args = dict(bbox=[-100.1, 39, -100, 39.1],
                              datetime='2018-04-01/2018-04-06',
                              url='https://earth-search.aws.element84.com/v0',
                              collections=['sentinel-s2-l1c'])
        dl.search(**satsearch_args)
        self.assertTrue(len(dl.items['sentinel-s2-l1c'].dates()) == 1)
        self.assertTrue(dl.items['sentinel-s2-l1c'].dates()[0] ==
                        datetime.date(2018, 4, 3))
