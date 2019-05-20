class CallbackQuery:
    def __init__(self, type, data, args, bot):
        self.data = data
        self.args = args
        self.type = 'callback_query'
        self.bot = bot
        self._session = None

    @property
    def session(self):
        if not self._session:
            self._session = self.bot.get_session(self)
        return self._session
        
    def answer(self, **kwargs):
        kwargs['callback_query_id'] = self.data['id']
        return self.bot.method('answerCallbackQuery', **kwargs)
    