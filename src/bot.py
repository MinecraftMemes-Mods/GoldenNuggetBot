import praw
import os
import sqlite3
import re
import time
import database
from dotenv import load_dotenv
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

db = database.Database()

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

    # setting some helpful variables
    commenter = comment.author.name  # person who is giving award
    op = comment.submission.author.name  # person receiving award

    # exception handling
    # author too young and doesn't meet karma requirements
    # (moved from other exception handling to make it so db entry isn't created if author is invalid)
    if int((time.time() - comment.author.created_utc) / (60 * 60 * 24)) < 9 and (comment.author.link_karma + comment.author.comment_karma) < 100:  # 9 days for the first part
        comment.reply("ERROR_MESSAGE")
        continue

    # creates database entry for commenter if required
    if db.get(commenter) == None:
        db.set_available(commenter, 3)
        db.set_received(commenter, 0)

    # setting some more helpful variables
    commenter_award_nugs = db.get(commenter)["available"]

    # splitting the comment into single words
    # i. e. `!nug 20` will become ['!nug', '20']
    # placeholder, since you can't just declare variables in python REEEEEEEEEEEEEEEEEEEEE
    try:
        amount_given = comment.body.split(' ')[1]
    except IndexError:  # because if someone just did !nug meaning 1 nugget
        amount_given = 1

    # converts valid text synonyms to their nugget amounts
    if amount_given in ("max", "full", "all", "everything"):
        amount_given = commenter_award_nugs

    # more exception handling
    # invalid gift arg
    if not int_conv(amount_given) or amount_given <= 0:
        comment.reply("ERROR_MESSAGE")
        continue

    # checks commenter has enough nuggets to award
    elif commenter_award_nugs < amount_given:
        comment.reply("ERROR MESSAGE")
        continue

    # checks poster is not awarding themselves
    elif commenter == op:
        comment.reply("ERROR_MESSAGE")
        continue

    # creates database entry for op if required
    if db.get(op) == None:
        db.set_available(op, 3)
        db.set_received(op, 0)

    # setting some more helpful variables
    op_award_nugs = db.get(op)["available"]
    op_received_nugs = db.get(op)["received"]

    # reducing commenter's award nugs by the number they give
    # should moderators have infinite award nugs?
    commenter_award_nugs -= amount_given

    """
    This section gives the OP an award nug for hitting a multiple of 5 received nuggets
    
    Now, this might look weird, you might think "why isn't this just if op_received_nugs % 5 == 0, op_award_nugs += 1"
    Well, I (coder) thought about it some, and it turns out that doesn't really work. Let me elaborate
    
    Since you can award multiple nuggets to the same poster, and since in theory someone could obtain more than 5 award
    nuggets (either via award nug resets or receivals), someone could in theory award an amount that causes OP to go past
    a multiple of 5 but not stay on it, and potentially multiple times. 
    
    For example, OP has received 4, someone awards them 2. They would have received 6 total, they should gain 1 award nug, 
    but the former check wouldn't work. Or more extreme, OP has received 4, someone awards them 8. They would have received
    12 total, they should gain 2 award nugs (for 5 and 10 received nuggets), but again the check wouldn't work
    
    This little bit of code accounts for that, by finding the difference needed for the next level, and then seeing how much
    it goes over and adds accordingly. It should work
    """

    difFrom5 = 5 - op_received_nugs % 5
    bonusNugs = 0
    if (amount_given >= difFrom5):
        amount_given -= difFrom5
        # hopefully doesn't modify amount_given at all my python is rusty
        bonusNugs += amount_given // 5 + 1
        op_award_nugs += bonusNugs
        amount_given += difFrom5

    # increasing op's received nugs
    op_received_nugs += amount_given

    # updating db
    db.set_available(commenter, commenter_award_nugs)
    db.set_received(op, op_received_nugs)
    db.set_received(op, op_award_nugs)

    # update nugflair

    # log comment

    if (bonusNugs == 0):
        comment.reply("SUCCESS_MESSAGE")
    else:
        comment.reply("SUCCESS_MESSAGE")

    for post in reddit.subreddit("xeothtest").new(limit=10):
        comment.mod.distinguish(os.getenv('STICKIED_MESSAGE'), sticky=True)
