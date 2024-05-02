import unittest as ut

from dbbuilder.discover import *


class TestDiscoverFunctions(ut.TestCase):

    def test_find_api_root(self):
        self.assertEqual(
            find_api_root("https://developer.wordpress.org/"),
            "https://developer.wordpress.org/wp-json/"
        )

    def test_supports_wp_v2(self):
        self.assertTrue(supports_wp_v2("https://developer.wordpress.org/wp-json/"))
