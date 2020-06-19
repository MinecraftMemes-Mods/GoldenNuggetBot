import sqlite3


class NugDatabase():
    """
    Class used for communicating with the DB
    Table: nuggets
    0|username|TEXT|0||1
    1|amount_received|INTEGER|0||0
    2|amount_available|INTEGER|0||0
    """

    def set_available(self, username: str, amount: int) -> None:
        """Set available nuggets (the ones you can spend)"""
        self.c.execute(f"""
            INSERT INTO nuggets(username, amount_available)
            VALUES (?, ?)
            ON CONFLICT(username) DO
            UPDATE SET amount_available = ?;
        """, (username, amount, amount))
        self.conn.commit()

    def set_received(self, username: str, amount: int) -> None:
        """Set received nuggets"""
        self.c.execute(f"""
            INSERT INTO nuggets(username, amount_received)
            VALUES (?, ?)
            ON CONFLICT(username) DO
            UPDATE SET amount_received = ?;
        """, (username, amount, amount))
        self.conn.commit()

    def get(self, username: str):
        """Returns a dictionary with available nuggets and received nuggets or none if user doesn't exist in DB"""
        self.c.execute(
            f'SELECT amount_received, amount_available FROM nuggets WHERE "username"="{username}"')
        results = self.c.fetchone()

        if results is None:
            return results
        else:
            return {
                'received': results[0],
                'available': results[1]
            }

    def __init__(self):
        self.conn = sqlite3.connect('nug.db')
        self.c = self.conn.cursor()


class PostDb():
    """Database used for logging posts"""

    def add_post(self, postid: str) -> None:
        """Add a post to the DB"""

        self.c.execute(
            'INSERT INTO posts VALUES (?) ON CONFLICT DO NOTHING;', (postid,))
        self.conn.commit()

    def check_post(self, postid: str) -> bool:
        """Check whether the post is already in DB"""
        self.c.execute('SELECT 1 FROM posts WHERE "postid"=?;', (postid,))
        return True if self.c.fetchall() is not None else False

    def __init__(self):
        self.conn = sqlite3.connect('nug.db')
        self.c = self.conn.cursor()
