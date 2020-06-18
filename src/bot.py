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
    try:
        # checks reply is on one of the bot's stickies
        if not re.match(r'(!(?:nug|nugget|gold))', comment.body) or not comment.parent().stickied or not comment.parent().author.name == "GoldenNugBot":
            continue
    except AttributeError: # raised if there is no parent comment
        continue

    # splitting the comment into single words
    # i. e. `!nug 20` will become ['!nug', '20']
    amount_given = comment.body.split(' ')[1:]

    # exception handling
    # author too young and doesn't meet karma requirements
    if int((time.time() - comment.author.created_utc) / (60 * 60 * 24)) < 9 and comment.author.link_karma + comment.author.comment_karma < 100:
        comment.reply("ERROR_MESSAGE")
        continue

    # invalid gift arg
    elif not int_conv(amount_given) or amount_given < 0 or not amount_given in ("max", "full", "all"):
        comment.reply("ERROR_MESSAGE")
        continue
       
    # checks commenter doesn't have empty balance
    elif db.get(comment.author) != None and db.get(comment.author)["available"] < amount_given:
        comment.reply("ERROR MESSAGE")
        continue

    # creates database entry if required
    if db.get(comment.author)["available"] == None:
        db.set_available(comment.author, 5)
