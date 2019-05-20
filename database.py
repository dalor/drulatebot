import psycopg2

class DB:
    def __init__(self, dburl):
        self.conn = psycopg2.connect(dburl, sslmode='require')
        self.create_table()

    def create_table(self):
        cur = self.conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users 
        (chat_id INTEGER NOT NULL PRIMARY KEY,
        login TEXT NOT NULL,
        password TEXT NOT NULL,
        session TEXT)
        ''')
        self.conn.commit()
        cur.close()

    def update(self, key, value):
        cur = self.conn.cursor()
        cur.execute('UPDATE users SET login = %s, password = %s, session = %s WHERE chat_id = %s',
                (value['login'], value['password'], value['session'], key))
        self.conn.commit()
        cur.close()

    def add(self, key, value):
        print(value)
        cur = self.conn.cursor()
        cur.execute('INSERT INTO users (chat_id, login, password, session) VALUES (%s, %s, %s, %s)',
                (key, value['login'], value['password'], value['session']))
        self.conn.commit()
        cur.close()

    def get_all(self):
        cur = self.conn.cursor()
        cur.execute('SELECT chat_id, login, password, session FROM users')
        users = cur.fetchall()
        self.conn.commit()
        cur.close()
        return [(user[0], {'login': user[1], 'password': user[2], 'session': user[3]}) for user in users]
        
