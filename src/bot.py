import praw
import os
import sqlite3
import re
from dotenv import load_dotenv
from database import Database
load_dotenv()


def int_conv(string: str) -> bool:
    """Returns whether the string can be converted to an integer"""
    try:
        int(string)
        return True
    except ValueError:
        return False


reddit = praw.Reddit(
    username=os.getenv('USERNAME'),
    password=os.getenv('PASSWORD'),
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent="r/MinecraftMemes' GoldenNuggetBot"
)

db = Database()

# database for logging already processed comments
comment_db = sqlite3.connect('comments.db')
comm_curs = comment_db.cursor()

# listening for new comments
for comment in reddit.subreddit('xeothtest').stream.comments():
    """
    Possible ways of awarding are !nugget, !nug and !gold
    the first argument must be the username (should not matter whether preceded by u/ or not)
    the second argument must either be a number or max, full or all
    i. e. `!nugget max` will transfer all nuggets to poster
    """

    # the weird thing below is regex.
    # it validates whether the command the user put in actually makes sense
    # you can see an explenation here: https://regex101.com/r/t6N7q2/1
    if not re.match(r'(!(?:nug|nugget|gold)) ((?:u/)?[\w-]{3,20}) ((?:\d+|(?:max|full|all)))', comment.body):
        continue

    # splitting the comment into single words
    # i. e. `!nug u/xeoth 20` will become ['u/xeoth', '20']
    args = comment.body.split(' ')[1:]

    # removing the u/ if present cause it's unnecessary
    if args[1].startswith('u/'):
        args[1] = args[1][2:]

    if int_conv(args[2]):
        pass
    elif args[2] in ('max', 'full', 'all'):
        pass
