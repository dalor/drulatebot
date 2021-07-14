import asyncio
from asyncio.tasks import ensure_future
from aiohttp import ClientSession, ClientResponse
from .session import Session
from lxml import html, etree
from .config import base_url
from .utils import url
from .chapter import parse_chapter
from .picture import Picture


class BookData:

    def __init__(self) -> None:
        self.title = None
        self.thumbnails = []

    def parse(self, tree: etree) -> bool:
        self.title = tree.xpath(
            '//ul[contains(@class,"book-header")]/following-sibling::h1')[0].text
        images = tree.xpath('//div[@class="images"]')[0]
        self.thumbnails = list(filter(lambda x: x, map(
            lambda img: Picture(img.attrib.get('src')), images.xpath('.//img'))))
        return bool(self.title)


class Book:
    def __init__(self, id_, session: Session = None):
        self.id = id_
        self.chapters = []
        self.__volumes = {}
        self.session: Session = session if session else Session()
        self.data: BookData = BookData()

    def __repr__(self) -> str:
        return "Book: {} | Chapters:\n{}".format(self.data.title, '\n'.join(map(str, self.chapters)))

    @property
    def full_url(self):
        return '{}/book/{}'.format(base_url, self.id)

    async def __auth(self, session: ClientSession) -> bool:
        async with session.post(base_url, data={'login[login]': self.session.login, 'login[pass]': self.session.password}) as resp:
            return True

    async def __approve_book(self, session: ClientSession) -> bool:
        async with session.post(base_url + '/mature?path={}'.format(self.id), data={'path': '/book/{}'.format(self.id), 'ok': 'Да'}) as resp:
            return True

    async def __get_main_page(self, session: ClientSession) -> ClientResponse:
        async with session.get(self.full_url, allow_redirects=False) as resp:
            return resp, await resp.text()

    async def load(self) -> bool:
        async with ClientSession(headers=self.session.headers, cookies=self.session.cookies) as session:
            if self.session.has_auth:
                await self.__auth(session)
            resp, page = await self.__get_main_page(session)
            if resp.status == 200:
                self.session.set_cookies(session)
                return await self.__parse_response(resp, page)
            elif resp.status == 302:
                await self.__approve_book(session)
                resp, page = await self.__get_main_page(session)
                self.session.set_cookies(session)
                return await self.__parse_response(resp, page)
            else:
                return False

    async def __parse_response(self, resp: ClientResponse, page: str) -> bool:
        if resp.status == 200:
            return self.__parse_main_page(page)
        return False

    def __parse_main_page(self, page_str: str) -> bool:
        tree = html.fromstring(page_str)
        if not self.data.parse(tree):
            return False
        self.chapters = []
        for ch in tree.xpath('//table[@id="Chapters"]/tbody/*'):
            chapter = parse_chapter(ch)
            if chapter:
                if chapter.volume:
                    if chapter.is_volume:
                        self.__volumes[chapter.volume] = chapter
                        self.chapters.append(chapter)
                    elif chapter.is_chapter and chapter.volume in self.__volumes:
                        self.__volumes[chapter.volume].append(chapter)
                else:
                    self.chapters.append(chapter)
        return bool(len(self.chapters))

    @property
    def all_chapters(self):
        chapters = []
        for chapter in self.chapters:
            if chapter.is_chapter:
                chapters.append(chapter)
            elif chapter.is_volume:
                chapters.extend(chapter.chapters)
        return chapters

    async def _load_chapters(self, chapters) -> None:
        async with ClientSession(headers=self.session.headers, cookies=self.session.cookies) as session:
            await asyncio.gather(*[one.load_chapter(session) for one in chapters if one.is_chapter])

    async def load_chapters(self) -> None:
        await self._load_chapters(self.all_chapters)

    @property
    def all_pictures(self):
        pictures = []
        for chapter in self.chapters:
            if chapter.is_chapter:
                pictures.extend(chapter.pictures)
            elif chapter.is_volume:
                for ch in chapter.chapters:
                    pictures.extend(ch.pictures)
        return pictures

    async def _load_pictures(self, pictures) -> None:
        async with ClientSession() as session:
            await asyncio.gather(*[asyncio.ensure_future(one.load_picture(session)) for one in pictures])

    async def load_pictures(self) -> None:
        await self._load_pictures(self.data.thumbnails + self.all_pictures)

    async def load_all(self) -> None:
        await self.load()
        await self.load_chapters()
        await self.load_pictures()
