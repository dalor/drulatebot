class ChosenInlineResult:
    def __init__(self, type, data, args, bot):
        self.data = data
        self.args = args
        self.type = 'chosen_inline_result'
        self.bot = bot
        self._session = None

    @property
    def session(self):
        if not self._session:
            self._session = self.bot.get_session(self)
        return self._session