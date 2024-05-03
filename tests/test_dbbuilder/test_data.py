import unittest as ut

from httmock import HTTMock

from dbbuilder.data import fetch_wordpress_site_content
from tests.helpers import mock_wordpress_api


class TestDataFunctions(ut.TestCase):

    def test_fetch_wordpress_site_content(self):
        with HTTMock(mock_wordpress_api):
            data_fetcher = fetch_wordpress_site_content("https://www.example.com/wp-json/")
            for data in data_fetcher:
                self.assertEqual(len(data), 5)
                for key in ["id", "type", "title", "link", "content"]:
                    self.assertIn(key, data)
                    self.assertIsInstance(data[key], str)
                self.assertTrue(data["id"].isnumeric())
                self.assertIn(data["type"], ["page", "post", "comment"])
