import re
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .bot import bot
from io import BytesIO

from rulate_parser import Book

from rulate_to_epub import book_to_epub
from ebooklib import epub

dp = Dispatcher(bot)

fix_symbols = re.compile(r'[^0-9A-Za-z\ ]')


def clear_book_title(title: str) -> str:
    return fix_symbols.sub('', title).replace('  ', '').replace(' ', '_')


id_pattern = re.compile(r'[0-9]+')


def book_to_text(book: Book) -> str:
    return '<a href="{}">{}</a>\nChapters: <b>{}</b>'.format(book.full_url, book.data.title, len(book.all_chapters))


@dp.message_handler(regexp=r'.+tl\.rulate\.ru\/book\/([0-9]+)')
@dp.message_handler(regexp=r'\/book[_\s]([0-9]+)')
async def book(message: types.Message):

    id_ = id_pattern.findall(message.text)[0]
    book = Book(id_)

    is_loaded = await book.load()

    if is_loaded:
        reply_markup = InlineKeyboardMarkup()
        reply_markup.add(InlineKeyboardButton(
            'EPUB', callback_data='epub {}'.format(book.id)))
        await message.reply_photo(
            book.data.thumbnails[0].full_url,
            caption=book_to_text(book),
            reply_markup=reply_markup
        )
    else:
        await message.reply("No such book...")

epub_id = re.compile(r'epub ([0-9]+)')


@dp.callback_query_handler(lambda c: epub_id.match(c.data))
async def epub_(cq: types.CallbackQuery):

    id_ = epub_id.match(cq.data)[1]

    book = Book(id_)

    await cq.answer('Loading book...')

    is_loaded = await book.load()

    if is_loaded:

        book_text = book_to_text(book)

        async def status(st: str):
            await cq.message.edit_caption(book_text + '\n\n' + st)

        await status('<i>Loading chapters...</i>')
        await book.load_chapters()

        await status('<i>Loading pictures...</i>')
        await book.load_pictures()

        await status('<i>Converting to epub...</i>')
        epub_book = book_to_epub(book)
        epub_file = BytesIO()
        epub.write_epub(epub_file, epub_book, {})
        epub_file.name = '{}_{}.epub'.format(
            book.id, clear_book_title(book.data.title)
        )

        await status('<i>Sending...</i>')
        epub_file.seek(0)
        await cq.message.reply_document(epub_file)

        await status('<i>Success!!!</i>')

    else:

        await cq.message.delete()
