import sqlite3


class Database():
    """
    Class used for communicating with the DB
    Tables: received_nuggets, available_nuggets
    Columns: username | amount
    """

    def set(self, table, username, amount):
        self.c.execute(f"""
            INSERT OR REPLACE INTO {table}
            VALUES("{username}", {amount});
        """)
        self.conn.commit()

    def get(self, table, username) -> int:
        self.c.execute(
            f'SELECT amount FROM {table} WHERE "username"="{username}"')
        results = self.c.fetchone()
        return results[0] if results is not None else None

    def __init__(self):
        self.conn = sqlite3.connect('nug.db')
        self.c = self.conn.cursor()
