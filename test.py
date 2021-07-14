from rulate_parser import Book
import asyncio
from ebooklib import epub
from rulate_to_epub import book_to_epub

ID = '' # Edit

book = Book(ID)

asyncio.run(book.load())

print('Loading chapters...')
asyncio.run(book.load_chapters())

print('Loading pictures...')
asyncio.run(book.load_pictures())

print('Converting to epub...')
epub_book = book_to_epub(book)

epub.write_epub('{}.epub'.format(ID), epub_book, {})
