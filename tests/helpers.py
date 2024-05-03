from urllib.parse import parse_qs
from httmock import response, all_requests


@all_requests
def mock_wordpress_api(url, request):
    if not "/wp-json" in url.path:
        api_root = f"https://{url.hostname}/wp-json/"
        return response(200, headers = {
            "Link": f'<{api_root}>; rel="https://api.w.org/"'
        })

    if not "/wp/v2" in url.path:
        return response(200, {"namespaces": ["wp/v2"]})

    if "/pages" in url.path:
        content_type = "page"
    elif "/posts" in url.path:
        content_type = "post"
    elif "/comments" in url.path:
        content_type = "comment"

    qs = parse_qs(url.query)
    res_json = [{
        "id": i + 1000 * int(qs["page"][0]),
        "type": content_type,
        "link": f"https://www.example.com/{content_type}",
        "content": {
            "rendered": ("<html><body>"
                         + f"<div> {content_type} content </div>" * 20
                         + "</body></html>")
        },
    } for i in range(10000, 10100)]
    if content_type != "comment":
        for item in res_json:
            item["title"] = {"rendered": f"{content_type} mock title"}
    return response(200, res_json, headers={"X-WP-TotalPages": 3})
