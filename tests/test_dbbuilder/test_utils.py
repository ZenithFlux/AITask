import unittest as ut

import requests

from dbbuilder.utils import *


class TestUtilsFunctions(ut.TestCase):

    def test_extract_text_from_html(self):
        res_json = requests.get("https://wplift.com/wp-json/wp/v2/pages/").json()
        html = res_json[1]["content"]["rendered"]
        self.assertIn("</div>", html)

        text = extract_text_from_html(html)
        self.assertNotIn("</div>", text)
