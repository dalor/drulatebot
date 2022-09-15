from typing import Callable
import asyncio
import re
from io import BytesIO

from ebooklib import epub
from rulate_to_epub import book_to_epub
from rulate_parser import Book

from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .bot import bot
from.sender import Sender


dp = Dispatcher(bot)

sender = Sender(dp)

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


async def load_book(book: Book, progress_callback: Callable, result_callback: Callable) -> str:

    await progress_callback('Loading chapters...')

    await book.load_chapters()

    await progress_callback('Loading pictures...')

    await book.load_pictures()

    await progress_callback('Converting to epub...')

    epub_book = book_to_epub(book)
    epub_file = BytesIO()
    epub.write_epub(epub_file, epub_book, {})
    epub_file.name = '{}_{}.epub'.format(
        book.id, clear_book_title(book.data.title)
    )

    epub_file.seek(0)

    async def sending_status(part: int, all: int):
        await progress_callback(f'Sending... {int(part / all * 100)}%')

    file_id = await sender.send_file(epub_file, progress_callback=sending_status)

    await progress_callback('Success!!!')

    await result_callback(file_id)


@dp.callback_query_handler(lambda c: epub_id.match(c.data))
async def epub_(cq: types.CallbackQuery):

    id_ = epub_id.match(cq.data)[1]

    book = Book(id_)

    try:
        await cq.answer('Loading book...')
    except:
        return

    is_loaded = await book.load()

    if is_loaded:

        async def status(st: str):
            try:
                await cq.message.edit_caption('{}\n\n<i>{}</i>'.format(book_to_text(book), st))
            except:
                pass

        asyncio.ensure_future(
            load_book(book,
                      progress_callback=status,
                      result_callback=cq.message.reply_document)
        )

    else:

        await cq.message.delete()
