import json

class InlineQuery:
    def __init__(self, type, data, args, bot):
        self.data = data
        self.args = args
        self.type = 'inline_query'
        self.bot = bot
        self._session = None

    @property
    def session(self):
        if not self._session:
            self._session = self.bot.get_session(self)
        return self._session
        
    def answer(self, results, **kwargs):
        kwargs['inline_query_id'] = self.data['id']
        kwargs['results'] = json.dumps(results)
        return self.bot.method('answerInlineQuery', **kwargs)
