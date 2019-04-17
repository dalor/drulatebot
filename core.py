from flask import Flask, request, send_file
from dtelbot import Bot, inputmedia as inmed, reply_markup as repl, inlinequeryresult as iqr
from parser import Book
import re
import os
from uuid import uuid4 as random_token

BOT_ID = os.environ['BOT_ID']

app = Flask(__name__)

b = Bot(BOT_ID)

fix_symbols = re.compile('[^0-9A-Za-z\ ]')

working = []

temp_files = {}

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

def edit_caption(chat_id, message_id, caption):
    b.editcaption(chat_id=chat_id, message_id=message_id, caption=caption, parse_mode='HTML').send()

@b.message('.+tl\.rulate\.ru\/book\/([0-9]+)')
@b.message('\/book[_\s]([0-9]+)')
@load_book
def load(a, book):
    reply_markup = [[repl.inlinekeyboardbutton('<<Download book>>', callback_data='download_all {}'.format(book.id))]]
    a.photo(book.thumbnail.full_url,
    caption='<a href=\"{}\">{}</a>'.format(book.full_url, book.title),
    parse_mode='HTML',
    reply_markup=repl.inlinekeyboardmarkup(reply_markup)).send()

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
                rand_filename = '{}_{}'.format(a.data['message']['from']['id'], random_token())
                with open(rand_filename, 'wb') as f:
                    f.write(result.read())
                temp_files[rand_filename] = name
                b.msg('This file is so big...\nYou can get it <a href=\"https://drulatebot.herokuapp.com/load/{}\">here</a>'.format(rand_filename), chat_id=chat_id, parse_mode='HTML', reply_to_message_id=message_id).send()
            else:
                result.name = name
                edit_caption(chat_id, message_id, caption + '<i>Sending...</i>')
                b.document(chat_id=chat_id, data={'document': result}, reply_to_message_id=message_id).send()
            edit_caption(chat_id, message_id, caption)
        except:
            edit_caption(chat_id, message_id, caption + '<i>Error!!!</i> Write to developer')
        working.remove(chat_id)
    else:
        a.answer(text='Other is loading').send()

@app.route('/load/<token>')
def load_by_browser(token):
    file = temp_files.pop(token)
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
