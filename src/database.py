import sqlite3


class Database():
    """
    Class used for communicating with the DB
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

    # *** Managing Processed Posts ***

    def add_post(self, postid: str) -> None:
        """Add a post to the DB"""

        self.c.execute(
            'INSERT INTO posts VALUES (?) ON CONFLICT DO NOTHING;', (postid,))
        self.conn.commit()

    def check_post(self, postid: str) -> bool:
        """Check whether the post is already in DB"""

        self.c.execute('SELECT 1 FROM posts WHERE "postid"=?;', (postid,))
        return True if self.c.fetchall() is not None else False

    # *** Managing Processed Comments ***

    def add_comment(self, commentid: str):
        """Add a comment to the DB"""

        self.c.execute(
            'INSERT INTO comments VALUES (?) ON CONFLICT DO NOTHING;', (commentid,))
        self.conn.commit()

    def check_comment(self, commentid: str):
        """Check whether the comment has already been processed"""

        self.c.execute(
            'SELECT 1 FROM comments WHERE "commentid"=?', (commentid,))
        return True if self.c.fetchall() is not None else False

    # *** Leaderboard ***

    def get_leaderboard(self) -> list:
        """Returns top 10 users ordered by the amount of received """

        self.c.execute(
            'SELECT username, amount_received FROM nuggets ORDER BY amount_received DESC;'
        )
        return self.c.fetchmany(10)

    def ban(self, username: str, admin: str) -> None:
        """Ban a user from the bot"""

        self.c.execute(
            'INSERT OR IGNORE INTO banned VALUES(?, ?);',
            (username, admin)
        )
        self.conn.commit()

    def check_ban(self, username: str) -> bool:
        """Check whether a user is banned"""

        self.c.execute('SELECT 0 FROM banned WHERE "username"=?', (username,))

        return True if self.c.fetchone() is not None else False

    def unban(self, username: str) -> None:
        """Unban a user"""

        self.c.execute('DELETE FROM banned WHERE "username"=?', (username,))
        self.conn.commit()

    def __init__(self):
        self.conn = sqlite3.connect('nug.db')
        self.c = self.conn.cursor()
