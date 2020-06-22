from datetime import datetime


class Log():
    """Class used to display log messages"""

    def info(self, message: str):
        """Display an informational message"""
        n = datetime.now().isoformat()
        print(
            f'{n} -{self.colors["blue"]} [INFO]{self.colors["reset"]} - {message}')

    def warn(self, message: str):
        """Display a warning message"""
        n = datetime.now().isoformat()
        print(
            f'{n} -{self.colors["yellow"]} [WARN]{self.colors["reset"]} - {message}')

    def error(self, message: str):
        """Display an error message"""
        n = datetime.now().isoformat()
        print(
            f'{n} -{self.colors["red"]} [ERROR]{self.colors["reset"]} - {message}')

    def success(self, message: str):
        """Display a success message"""
        n = datetime.now().isoformat()
        print(
            f'{n} -{self.colors["green"]} [SUCCESS]{self.colors["reset"]} - {message}')

    def __init__(self):
        """Define color codes"""
        self.colors = {
            'reset': '\033[m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'red': '\033[31m',
            'blue': '\033[34m',
        }
