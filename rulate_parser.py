import re
import asyncio
import aiohttp
from io import BytesIO
from PIL import Image
import base64
import hashlib
import lxml.html
from lxml.etree import tostring
from lxml.html.clean import Cleaner

from fb2book import FB2book

base_url = 'https://tl.rulate.ru'

parse_page_info = re.compile(r'\<h1\>(?P<title>.+)\<\/h1\>\n\<div\sid\=\'Info\'[\s\S]+\<img\ssrc\=\"(?P<img>\/i\/book\/[a-z0-9\/\.]+)\"')

parse_chapters = re.compile(r'\<tr\sid\=\'(c\_|vol\_title\_)(?P<index>[0-9]+)\'[^>]*class\=\'(?P<type>chapter\_row|volume_helper)\s*(?P<volume_to>[^\' ]*)(\s|\s\sinfo)?\'\>\<td(\scolspan\=\'14\'\sonclick\=\'\$\(\".(?P<volume>volume\_[0-9a-z]+)\"\)[^<]+\<strong\>(?P<title>[^<]+)|\>\<\/td\>\<td\sclass\=\'t\'\>\<a\shref\=\'(?P<url>[^\']+)\'\>(?P<name>[^<]+)\<\/a\>)')

class Picture:
    def __init__(self, url, row):
        self.url = url
        self.rows = [row] if row is not None else []
        self.type = 'image/jpeg'
        self.binary = None
        self.hash = None
    
    @property
    def full_url(self):
        return base_url + self.url if self.url[0] == '/' else self.url

    @property
    def name(self):
        return self.url.replace('/', '').replace('.', '_')
    
    @property
    def content(self):
        buffer = BytesIO(self.binary) #Load picture from response to buffer
        img = Image.open(buffer) #Load from buffer
        new_img = img.convert('RGB')#To ignore error with RGBA
        new_img.save(buffer, format='JPEG') #Format picture to .jpg
        return base64.b64encode(buffer.getvalue()).decode() #Encode to base64 and return as string
    
    async def load_picture(self, session):
        async with session.get(self.full_url) as resp:
            self.check_content(await resp.read())
    
    def check_content(self, content):
        self.hash = hashlib.md5(content).hexdigest()
        self.binary = content
    
    def replace(self, pic):
        for row in pic.rows:
            self.rows.append(row)
            row.set('l:href', self.name)
    
    def __eq__(self, other):
        return self.url == other.url or (self.hash and self.hash == other.hash)

class Chapter:
    def __init__(self, result):
        self.is_chapter = result['type'] == 'chapter_row'
        self.url = result['url'] if self.is_chapter else None
        self.name = result['name'] if self.is_chapter else result['title']
        self.volume = result['volume'] if not self.is_chapter else None
        self.volume_to = result['volume_to'] if self.is_chapter else None
        self.rows = []
        self.chapters = []
        self.pictures = []
        self.urls = []

    @property
    def full_url(self):
        return base_url + self.url

    @property
    def content(self):
        return ''.join(map(lambda row: tostring(row, encoding='unicode'), self.rows))
    
    def append(self, chapter):
        self.chapters.append(chapter)

    async def load_chapter(self, session):
        if self.is_chapter:
            async with session.get(base_url + self.url) as resp:
                self.check_content(await resp.text())
    
    def change_link(self, row, link):
        row.set('l:href', link)
    
    def check(self, row):
        if row.tag == 'img':
            url = row.attrib.pop('src')
            if url:
                pic = Picture(url, row)
                self.pictures.append(pic)
                row.tag = 'image'
                self.change_link(row, pic.name)
        elif row.tag == 'a':
            url = row.attrib.pop('src')
            if not url:
                row.tag = 'p'
            else:
                self.change_link(row, url)
        self.rows.append(row)
        
    def check_content(self, content): #Оптимизация под книгу
        page = lxml.html.fromstring(content).xpath('//div[@class = "content-text"]')
        if page:
            cleaner = Cleaner(
                page_structure=False,
                style=True,
                allow_tags=['p', 'a', 'img', 'td', 'tr', 'strong', 'br'],
                remove_unknown_tags=False
            )
            for row in cleaner.clean_html(page[0]):
                self.check(row)

    def __repr__(self):
        return '> {}\nName: {}\nUrl: {}\nVolume_to: {}\nVolume: {}'.format(
            'Chapter' if self.is_chapter else 'Volume', self.name, self.url, self.volume_to, self.volume)

class Book:
    def __init__(self, id_, session=None):
        self.id = id_
        self.title = None #Название
        self.thumbnail = None #Cсылка на картинку
        self.chapters = [] #Главы
        self.pictures = []
        self.session = session
        self.load_main()
    
    @property
    def full_url(self):
        return base_url + '/book/{}'.format(self.id)

    def load_main(self):
        page = self.get(self.full_url) #Download page
        info = parse_page_info.search(page) #Find all info on page
        if info:
            self.title = info['title']
            self.thumbnail = Picture(info['img'], None)
            for row in parse_chapters.finditer(page): #Parse rows from document
                self.add_to_chapters(Chapter(row)) #Create Row and save to list
            
    def add_to_chapters(self, chapter_):
        if chapter_.volume_to: #Is connected
            for chapter in self.chapters: #Check chapter to connect
                if chapter.volume and chapter.volume == chapter_.volume_to: #Finded
                    chapter.append(chapter_) #Connecting
                    return
        self.chapters.append(chapter_) #Add to main
            
    def load_chapters(self):
        async def get_pages(list_):
            async with aiohttp.ClientSession(headers=self.session.headers if self.session else {}, cookies=self.session.cookies if self.session else {}) as session:
                return await asyncio.gather(*[asyncio.ensure_future(one.load_chapter(session)) for one in list_])
        chapters = []
        for chapter in self.chapters:
            if chapter.is_chapter:
                chapters.append(chapter)
            else:
                for ch in chapter.chapters:
                    chapters.append(ch)
        asyncio.new_event_loop().run_until_complete(get_pages(chapters))

    def the_same_picture(self, pic):
        for picture in self.pictures:
            if pic == picture:
                return picture
    
    def check_pictures(self, pics):
        for pic in pics:
            picture = self.the_same_picture(pic)
            if picture:
                picture.replace(pic)
            else:
                self.pictures.append(pic)
    
    def get_pictures_from_chapters(self):
        self.pictures = [self.thumbnail]
        for chapter in self.chapters:
            if chapter.is_chapter:
                self.check_pictures(chapter.pictures)
            else:
                for ch in chapter.chapters:
                    self.check_pictures(ch.pictures)
            
    def check_pictures_after_download(self):
        pictures, self.pictures = self.pictures, [self.thumbnail]
        self.check_pictures(pictures)
        
    def load_pictures(self):
        self.get_pictures_from_chapters()
        async def get_pics(list_):
            async with aiohttp.ClientSession() as session:
                return await asyncio.gather(*[asyncio.ensure_future(one.load_picture(session)) for one in list_])
        asyncio.new_event_loop().run_until_complete(get_pics(self.pictures))
        self.check_pictures_after_download()

    async def auth(self, session):
        async with session.post(base_url, data={'login[login]': self.session.login, 'login[pass]': self.session.password}) as resp:
            return await resp.text()

    async def approve_book(self, session):
        async with session.post(base_url + '/mature?path={}'.format(self.id), data={'path': '/book/{}'.format(self.id), 'ok': 'Да'}) as resp:
            return await resp.text()

    def get(self, url):
        async def fetch_get(url, session):
            async with session.get(url) as resp:
                return await resp.text()
        async def gget(url):
            async with aiohttp.ClientSession(headers=self.session.headers if self.session else {}, cookies=self.session.cookies if self.session else {}) as session:
                if self.session:
                    await self.auth(session)
                    await self.approve_book(session)
                    self.session.set_cookies(session)
                return await fetch_get(url, session)
        return asyncio.new_event_loop().run_until_complete(gget(url))

    def fb2_serialize(self):
        book = FB2book(self.title, self.full_url, self.thumbnail.name)
        for chapter in self.chapters:
            book.add_chapter(chapter)
        for pic in self.pictures:
            book.add_picture(pic)
        return book.result()

    def format_to_fb2(self, filename=None, io=False):
        fb2_result = self.fb2_serialize()
        if filename:
            with open(filename, 'wb') as f:
                f.write(fb2_result)
        elif io:
            return BytesIO(fb2_result)
        else:
            return fb2_result

class Session:
    def __init__(self, login, password, session=None):
        self.login = login
        self.password = password
        self.headers = {}
        self.cookies = {'phpsession': session} if session else {}

    def set_cookies(self, session):
        self.cookies = {cookie.key:cookie.value for cookie in session.cookie_jar}

    @property
    def session(self):
        return self.cookies.get('phpsession')

