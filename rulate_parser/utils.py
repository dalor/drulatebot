from .config import base_url


def url(url: str) -> str:
    if url and not url.startswith('http'):
        return base_url + url
    return url
