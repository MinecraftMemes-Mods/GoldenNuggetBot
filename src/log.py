from datetime import datetime


class Log():
    """Class used to display log messages"""

    def info(self, message: str):
        """Display an info-like message"""
        n = datetime.now()
        print(
            f'{n.year}.{n.month}.{n.day} {n.hour}:{n.minute}:{n.second}.{n.microsecond} - {message}')
