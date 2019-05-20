class UserSession(dict):
    def __init__(self, id, values, db=None, new=False, *args, **kwargs):
        self.id = id
        for key, value in values.items():
            dict.__setitem__(self, key, value)
        self.__db = db
        self.__changed = False
        self.new = new

    def __setitem__(self, key, value):
        self.__changed = True
        dict.__setitem__(self, key, value)

    def update_in_db(self):
        if self.__db and self.__changed:
            if self.new:
                self.__db.add(self.id, self)
                self.new = False
            else:
                self.__db.update(self.id, self)

