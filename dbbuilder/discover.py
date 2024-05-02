import requests


def find_api_root(site_url: str) -> str:
    """
    Find the WordPress REST API root route for a given website.
    """
    res = requests.get(site_url)
    res.raise_for_status()
    return res.links["https://api.w.org/"]['url']


def supports_wp_v2(api_root: str) -> bool:
    """
    Check if the API supports core (wp/v2) endpoints.
    """
    res = requests.get(api_root)
    res.raise_for_status()
    res = res.json()
    return "wp/v2" in res["namespaces"]
