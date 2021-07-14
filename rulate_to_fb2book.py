from rulate_parser.book import Book
from fb2book import FB2book


def book_to_fb2(book: Book):
    fb2 = FB2book(book.data.title, book.full_url, book.data.thumbnails[0])
    for chapter in book.chapters:
        fb2.add_chapter(chapter)
    for pic in book.pictures:
        fb2.add_picture(pic)
    return fb2.result()
