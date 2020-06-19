import praw
import os
import sqlite3
import re
import time
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

    try:
        if not re.match(r'!(nug|nugget|gold)( \d)?', comment.body) or not comment.parent().stickied or not comment.parent().author.name == "GoldenNugBot":
            continue
    except AttributeError:  # raised if there is no parent comment
        continue

    try:
        amount_given = comment.body.split()[1]
    except IndexError:
        amount_given = 1

    # commenter too young and doesn't meet karma requirements
    if int((time.time() - comment.author.created_utc) / (60 * 60 * 24)) < 9 and comment.author.link_karma + comment.author.comment_karma < 100:
        comment.reply(os.getenv('ERROR_REQUIREMENTS'))
        continue

    # if author deletes their own post/account
    elif not comment.submission.author:
        comment.reply(os.getenv('ERROR_ACC_DELETED'))
        continue

    # trying to award self
    elif comment.author == comment.submission.author:
        comment.reply(os.getenv('ERROR_SELF_AWARD'))
        continue

    # giving more than five nugs
    elif amount_given > 5:
        comment.reply(os.getenv('ERROR_TOO_MANY_NUGS'))
        continue

    # trying to give negative nugs
    elif amount_given < 1:
        comment.reply(os.getenv('ERROR_NEGATIVE_NUGS'))

    # commenter doesn't have enough nugs
    elif db.get(comment.author.name)["available"] != None and db.get(comment.author)["available"] < amount_given:
        comment.reply(os.getenv('ERROR_NOT_ENOUGH_NUGS'))
        continue

    # gifter not in db yet
    if db.get(comment.author.name)["available"] == None:
        db.set_available(comment.author, 5)

    # receiver not in db yet
    if db.get(comment.submission.author)["received"] == None:
        db.set_received(comment.author, 0)

    # performs transactions
    db.set_received(comment.submission.author, db.get(
        comment.submission.author)["received"] + amount_given)
    db.set_available(comment.author, db.get(
        comment.author)["available"] - amount_given)
    comment.reply(os.getenv('SUCCESS'))
