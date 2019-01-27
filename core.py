from flask import Flask, request, render_template, redirect
from dtelbot import Bot, inputmedia as inmed, reply_markup as repl, inlinequeryresult as iqr
from parser import Book
import re
import os

BOT_ID = os.environ['BOT_ID']

app = Flask(__name__)

b = Bot(BOT_ID)

fix_symbols = re.compile('[^0-9A-Za-z\ ]')

working = []

def load_book(old):
    def new(a):
        if a.args[1]:
            book = Book(a.args[1])
            if book.title:
                old(a, book)
            else:
                a.msg('Can`t load(if book exists write to @dalor_dandy(Will add new features))').send()
        return old
    return new
        

@b.message('.+tl\.rulate\.ru\/book\/([0-9]+)')
@b.message('\/book[_\s]([0-9]+)')
@load_book
def load(a, book):
    reply_markup = [[repl.inlinekeyboardbutton('<<Download book>>', callback_data='download_all {}'.format(book.id))]]
    a.photo(book.base_url + book.img_url,
    caption='<a href=\"{}\">{}</a>'.format(book.url, book.title),
    parse_mode='HTML',
    reply_markup=repl.inlinekeyboardmarkup(reply_markup)).send()

@b.callback_query('download_all ([0-9]+)')
@load_book
def download_all_book(a, book):
    chat_id = a.data['message']['chat']['id']
    if not chat_id in working:
        try:
            a.answer(text='Loading book: {}'.format(book.title)).send()
            working.append(chat_id)
            #print('Start loading book {}'.format(book.title))
            result = book.format_to_fb2(io=True)
            #print('End loading book {}'.format(book.title))
            result.name = '{}_{}.fb2'.format(book.id, fix_symbols.sub('', book.title).replace('  ', '').replace(' ', '_'))
            b.document(chat_id=chat_id, data={'document': result}).send()
        except:
            pass
        working.remove(chat_id)
    else:
        a.answer(text='Other is loading').send()

@app.route('/{}'.format(BOT_ID), methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run()
