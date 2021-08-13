from io import BytesIO
from PIL import Image
import base64
import hashlib
from aiohttp import ClientSession

from .utils import url


class Picture:
    def __init__(self, url_) -> None:
        self.url: str = url_
        self.type: str = 'image/jpeg'
        self.binary: BytesIO = None
        self.hash: str = None

    def __repr__(self) -> str:
        return "Piture: {}".format(self.full_url)

    @property
    def full_url(self) -> str:
        return url(self.url)

    @property
    def name(self) -> str:
        return self.url.replace('/', '_').replace('.', '_')

    @property
    def filename(self) -> str:
        return self.name + '.jpeg'

    @property
    def bytes(self) -> bytes:
        if self.binary:
            return self.binary.getvalue()

    @property
    def base64(self) -> str:
        if self.binary:
            return base64.b64encode(self.binary.getvalue()).decode()

    async def load_picture(self, session: ClientSession) -> None:
        try:
            async with session.get(self.full_url) as resp:
                self.prepare_content(await resp.read())
        except:
            pass

    def convert(self, binary: bytes) -> BytesIO:
        buffer = BytesIO(binary)  # Load picture from response to buffer
        img = Image.open(buffer)  # Load from buffer
        new_img = img.convert('RGB')  # To ignore error with RGBA
        new_img.save(buffer, format='jpeg')
        return buffer

    def prepare_content(self, content: bytes) -> None:
        self.hash = hashlib.md5(content).hexdigest()
        self.binary = self.convert(content)

    def __eq__(self, other) -> bool:
        return self.url == other.url or (self.hash and self.hash == other.hash)
