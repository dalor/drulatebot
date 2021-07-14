from .utils import url
from lxml.html import tostring


class HTML:

    def __init__(self, html=None, text: str = '', tag: str = 'p') -> None:
        self.html = html
        self.text = text
        self.tag = tag

    @property
    def from_text(self):
        return u"<{}>{}</{}>".format(self.tag, self.text, self.tag)

    @property
    def content(self):
        if not self.html is None:
            return tostring(self.html, method='xml', encoding='unicode')
        else:
            return self.from_text

    def __repr__(self) -> str:
        return self.content


class Link:

    def __init__(self, text: str, link: str) -> None:
        self.text = text
        self.link = url(link)

    def __repr__(self) -> str:
        self.text
