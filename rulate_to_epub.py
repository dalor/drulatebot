from rulate_parser import Book, Picture, Link, Chapter, HTML
from ebooklib import epub


def chapter_filename(chapter: Chapter) -> str:
    return (chapter.url.replace('/', '_') if chapter.url else chapter.volume) + '.xhtml'


def picture_filename(pic: Picture) -> str:
    return 'images/' + pic.filename


def row_to_html(row) -> str:
    if type(row) is Picture:
        return u'<img src="{}" />'.format(picture_filename(row))
    elif type(row) is Link:
        return u'<a href="{}">{}</a>'.format(row.link, row.text)
    elif type(row) is HTML:
        return row.content
    return u''


def chapter_volume_to_html(chapter: Chapter) -> epub.EpubHtml:
    content = u'<h1>{}</h1>'.format(chapter.name)
    html = epub.EpubHtml(title=chapter.name,
                         file_name=chapter_filename(chapter))
    html.content = content
    return html


def chapter_with_rows_to_html(chapter: Chapter) -> epub.EpubHtml:
    content = u'<h1>{}</h1>'.format(chapter.name)
    html = epub.EpubHtml(title=chapter.name,
                         file_name=chapter_filename(chapter))
    for row in chapter.rows:
        content += row_to_html(row)
    html.content = content
    return html


def chapter_to_html(chapter: Chapter, docs, sections) -> str:
    if chapter.is_volume:
        html = chapter_volume_to_html(chapter)
        docs.append(html)
        chapters = []
        section = (
            epub.Section(chapter.name, href=chapter_filename(chapter)),
            chapters
        )
        sections.append(section)
        for ch in chapter.chapters:
            ch_html = chapter_with_rows_to_html(ch)
            docs.append(ch_html)
            chapters.append(ch_html)
    else:
        html = chapter_with_rows_to_html(chapter)
        docs.append(html)
        sections.append(html)


def picture_to_html(picture: Picture) -> str:
    return epub.EpubItem(uid=picture.name, file_name=picture_filename(picture), media_type=picture.type, content=picture.bytes)


def book_to_epub(book: Book) -> epub.EpubBook:
    e = epub.EpubBook()

    e.set_title(book.data.title)
    e.set_language('ru')

    for thumb in book.data.thumbnails:
        e.set_cover(picture_filename(thumb), thumb.bytes)

    docs = []
    toc = []

    for ch in book.chapters:
        chapter_to_html(ch, docs, toc)

    for d in docs:
        e.add_item(d)

    e.toc = toc

    for pic in book.all_pictures:
        e.add_item(picture_to_html(pic))

    e.add_item(epub.EpubNcx())
    e.add_item(epub.EpubNav())

    e.spine = docs

    return e
