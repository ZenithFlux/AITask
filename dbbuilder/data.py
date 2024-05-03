from urllib.parse import urljoin
from collections.abc import Iterator

import requests


def fetch_wordpress_site_content(api_root: str) -> Iterator[dict[str, str]]:
    """Fetches and yields all the content of a Wordpress site."""
    content_types = ["pages", "posts", "comments"]
    for content_type in content_types:
        route = urljoin(api_root, f"wp/v2/{content_type}/")
        res = requests.get(route, {"per_page": 100, "page": 1})
        total_pages = int(res.headers["X-WP-TotalPages"])
        for i in range(1, total_pages+1):
            if i != 1:
               res = requests.get(route, {"per_page": 100, "page": i})
            res_json = res.json()

            for item in res_json:
                if content_type == "comments":
                    item["title"] = {"rendered": "Comment"}

                yield {
                    "id": str(item["id"]),
                    "type" : item["type"],
                    "title": item["title"]["rendered"],
                    "link" : item["link"],
                    "content": item["content"]["rendered"],
                }
