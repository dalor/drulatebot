class Session:
    def __init__(self, login: str = None, password: str = None, session: str = None):
        self.login = login
        self.password = password
        self.headers = {}
        self.cookies = {'phpsession': session} if session else {}

    def set_cookies(self, session):
        self.cookies = {
            cookie.key: cookie.value for cookie in session.cookie_jar}

    @property
    def has_auth(self):
        return self.login and self.password

    @property
    def session(self):
        return self.cookies.get('phpsession')
