import unittest as ut

from dbbuilder.data import fetch_wordpress_site_content
from httmock import response, urlmatch, HTTMock


class TestDataFunctions(ut.TestCase):

    def test_fetch_wordpress_site_content(self):
        with HTTMock(self.mock_collection_api):
            data_fetcher = fetch_wordpress_site_content("https://www.example.com/wp-json/")
            for data in data_fetcher:
                for key in ["title", "link", "content"]:
                    self.assertIn(key, data)
                    self.assertIsInstance(data[key], str)

    @staticmethod
    @urlmatch(path="/wp-json/wp/v2/[a-z]*/?$")
    def mock_collection_api(url, request):
        if "/pages" in url.path:
            content_type = "page"
        elif "/posts" in url.path:
            content_type = "post"
        elif "/comments" in url.path:
            content_type = "comment"

        res_json = [{
            "link": f"https://www.example.com/{content_type}",
            "content": {"rendered": f"<html><body><div>{content_type} content</div></body></html>"},
        }]
        if content_type != "comment":
            res_json[0]["title"] = {"rendered": f"{content_type} mock title"}

        return response(200, res_json, headers={"X-WP-TotalPages": 1})
