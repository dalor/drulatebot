from flask import Flask, request, send_file
from dtelbot import Bot
from dtelbot.inline import article as iarticle
from dtelbot.inline_keyboard import markup, button
from rulate_parser import Book, base_url, Session
import re
import os
from uuid import uuid4 as random_token
import requests

from database import DB

BOT_ID = os.environ['BOT_ID']
DATABASE_URL = os.environ['DATABASE_URL']

app = Flask(__name__)

b = Bot(BOT_ID, db=DB(DATABASE_URL))

fix_symbols = re.compile(r'[^0-9A-Za-z\ ]')

working = []

temp_files = {}

def get_session(a):
    sess = a.session
    if 'login' in sess and 'password' in sess and 'session' in sess:
        return Session(sess['login'], sess['password'], session=sess['session'])

def load_book(old):
    def new(a):
        if a.args[1]:
            book = Book(a.args[1], session=get_session(a))
            if book.title:
                old(a, book)
                a.session['session'] = book.session.session
            else:
                a.msg('Can`t load(if book exists write to @dalor_dandy(Will add new features))').send()
        return old
    return new

def edit_caption(chat_id, message_id, caption):
    b.editcaption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode='HTML').send()

@b.message('.+tl\.rulate\.ru\/book\/([0-9]+)')
@b.message('\/book[_\s]([0-9]+)')
@load_book
def load(a, book):
    reply_markup = [[button('<<Download book>>', callback_data='download_all {}'.format(book.id))]]
    a.photo(book.thumbnail.full_url,
    caption='<a href=\"{}\">{}</a>'.format(book.full_url, book.title),
    parse_mode='HTML',
    reply_markup=markup(reply_markup)).send()

@b.message('/search')
def search_button(a):
    a.msg('Button for search', reply_markup=markup([[button('Tap here', switch_inline_query_current_chat='')]])).send()

@b.message('/auth (.+) (.+)')
def auth(a):
    session = a.session
    session['login'] = a.args[1]
    session['password'] = a.args[2]
    session['session'] = None
    b.more([
        a.msg('Saved'),
        a.delete()
    ])

@b.callback_query('download_all ([0-9]+)')
@load_book
def download_all_book(a, book):
    chat_id = a.data['message']['chat']['id']
    if not chat_id in working:
        message_id = a.data['message']['message_id']
        caption = '<a href=\"{}\">{}</a>\n'.format(book.full_url, book.title)
        try:
            a.answer(text='Starting...').send()
            working.append(chat_id)
            edit_caption(chat_id, message_id, caption + '<i>Loading chapters...</i>')
            book.load_chapters()
            edit_caption(chat_id, message_id, caption + '<i>Loading pictures...</i>')
            book.load_pictures()
            edit_caption(chat_id, message_id, caption + '<i>Converting to fb2...</i>')
            result = book.format_to_fb2(io=True)
            name = '{}_{}.fb2'.format(book.id, fix_symbols.sub('', book.title).replace('  ', '').replace(' ', '_'))
            if result.getbuffer().nbytes > 50000000:
                rand_filename = '{}_{}'.format(a.data['message']['from']['id'], str(random_token()))
                with open(rand_filename, 'wb') as f:
                    f.write(result.read())
                temp_files[rand_filename] = name
                b.msg('This file is so big...\nYou can get it <a href=\"https://drulatebot.herokuapp.com/load/{}\">here</a>'.format(rand_filename), chat_id=chat_id, parse_mode='HTML', reply_to_message_id=message_id).send()
            else:
                result.name = name
                edit_caption(chat_id, message_id, caption + '<i>Sending...</i>')
                b.document(result, chat_id=chat_id, reply_to_message_id=message_id).send()
            edit_caption(chat_id, message_id, caption)
        except:
            edit_caption(chat_id, message_id, caption + '<i>Error!!!</i> Write to developer')
        working.remove(chat_id)
    else:
        a.answer(text='Other is loading').send()

@b.inline_query('(.{3,})')
def search(a):
    result = requests.get('https://tl.rulate.ru/search/autocomplete', params={'query': a.args[1]}).json()
    results = []; i = 0
    for res in result:
        results.append(iarticle(id=i, title='{} | {}'.format(res['title_one'], res['title_two']), input_message_content={'message_text': base_url + res['url']}, thumb_url=base_url + res['img']))
        i += 1
    a.answer(results).send()

@app.route('/load/<token>')
def load_by_browser(token):
    file = temp_files.get(token)
    if file:
        return send_file(token, mimetype='text/xml', as_attachment=True, attachment_filename=file)
    else:
        return 'Not found', 404

@app.route('/{}'.format(BOT_ID), methods=['POST']) #Telegram should be connected to this hook
def webhook():
    b.check(request.get_json())
    return 'ok', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
