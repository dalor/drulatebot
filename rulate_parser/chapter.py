from lxml.html.clean import Cleaner
from lxml import html, etree
from aiohttp import ClientSession
import re

from .picture import Picture
from .utils import url

from .rows import HTML, Link


class Chapter:
    def __init__(self, url: str, name: str = 'chapter',  is_chapter: bool = True, volume: str = None):
        self.is_chapter = is_chapter
        self.url = url
        self.name = name
        self.volume = volume
        self.rows = []
        self.chapters = []
        self.pictures = []

    @property
    def is_volume(self):
        return not self.is_chapter

    @property
    def full_url(self):
        return url(self.url)

    def append(self, chapter) -> None:
        self.chapters.append(chapter)

    async def load_chapter(self, session: ClientSession) -> None:
        if self.is_chapter:
            async with session.get(self.full_url) as resp:
                self._prepare_content(await resp.text())

    def _add_picture(self, element: etree.ElementTree) -> Picture:
        url = element.attrib.get('src')
        if url:
            pic = Picture(url)
            self.pictures.append(pic)
            return pic

    def _convert(self, row: etree.ElementTree):
        img = row.find('img')
        if not img is None:
            return self._add_picture(img)
        elif row.tag == 'a':
            url = row.attrib.get('href')
            if url and row.text:
                return Link(row.text, url)
            elif row.text:
                return HTML(html=row)
        else:
            return HTML(html=row)

    def _prepare_content(self, content):  # Оптимизация под книгу
        page = html.fromstring(content).xpath(
            '//div[@class="content-text"]'
        )
        if page:
            cleaner = Cleaner(
                page_structure=False,
                style=True,
                inline_style=True,
                remove_unknown_tags=True
            )
            for row in cleaner.clean_html(page[0]):
                new_row = self._convert(row)
                if new_row:
                    self.rows.append(new_row)

    def __repr__(self):
        return '> {}: {} (Url: {}; Volume: {})'.format(
            'Chapter' if self.is_chapter else 'Volume', self.name, self.url, self.volume)


volume_parser = re.compile('.*volume\_([\d\w]+)')


def match_chapter_volume(tree: etree.ElementTree) -> str:
    for cl in tree.classes:
        match = volume_parser.match(cl)
        if match:
            return match[1]


def parse_chapter(tree: etree.ElementTree) -> Chapter:
    is_chapter = 'chapter_row' in tree.classes
    if is_chapter:
        t_a = tree.xpath('.//td[@class="t"]/a')
        if not len(t_a):
            return
        name = t_a[0].text
        url = t_a[0].attrib.get('href')
        if not url:
            return
        volume = match_chapter_volume(tree)
    else:
        name_t = tree.xpath('.//strong')
        if not len(name_t):
            return
        name = tree.xpath('.//strong')[0].text
        url = None
        td_t = tree.xpath('.//td')
        if not len(td_t):
            return
        volume_match = volume_parser.match(td_t[0].attrib.get('onclick'))
        if volume_match:
            volume = volume_match[1]
        else:
            volume = None
    return Chapter(name=name, url=url, is_chapter=is_chapter, volume=volume)
