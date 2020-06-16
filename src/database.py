import sqlite3


class Database():
    """Class used for communicating with the DB"""

    def give(self, table, username, amount):
        self.c.execute(
            f'INSERT INTO {table} VALUES("{username}", {amount});')
        self.conn.commit()

    def __init__(self):
        self.conn = sqlite3.connect('../nug.db')
        self.c = self.conn.cursor()
