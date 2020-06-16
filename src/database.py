import sqlite3


class Database():
    """Class used for communicating with the DB"""

    def give(self, table, username, amount):
        self.c.execute(
            f'INSERT INTO {table} VALUES("{username}", {amount});')
        self.conn.commit()

    def get(self, table, username) -> int:
        self.c.execute(
            f'SELECT nuggets FROM {table} WHERE "username"="{username}"')
        return self.c.fetchone()[0]

    def __init__(self):
        self.conn = sqlite3.connect('../nug.db')
        self.c = self.conn.cursor()
