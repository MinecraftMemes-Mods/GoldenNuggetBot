import praw
import os
import sqlite3
import re
import time
from dotenv import load_dotenv
from database import Database
load_dotenv()

# static responses
invalid_format = "I wasn't able to understand your request. Valid format is\n\n```!nug (amount of awarded nuggets)```"
award_yourself = "Nice try OP, but you cannot award your own posts! Award your voting nuggets to deserving posts from others!"
stickied_message = "Reply to this comment to award nugget(s) to OP if you feel this meme is deserving."
not_in_db = "You have not gifted or received any nugs yet."""

# dynamic responses
def reply_account_too_new(commenter):
    ret = f"""Hi There {commenter}! Unfortunately, I am unable to fullfill your request.
    
    To prevent cheating users with low karma and/or new accounts are unable to award nuggets. However, **you can still receive them!**"""
    return ret


def reply_not_enough_nugs(commenter, award_nugs):
    ret = f"""Hi There {commenter}! Unfortunately, I am unable to fullfill your request.
    
    You don't have enough voting nugs to do that. You have **{award_nugs}** available to reward."""
    return ret


def reply_success(commenter, amount_given, award_nugs, op, received_nugs, bonus_nugs):
    ret = f"{commenter}, you gave **{amount_given}** nugget(s) to {op}, bringing their total nuggets received to **{received_nugs}**. "
    if bonus_nugs:
        ret += f"Because of your award, {op} has received **{bonus_nugs}** additional nugget(s) that they can award to others."

    return ret


def int_conv(string: str) -> bool:
    """Returns whether the string can be converted to an integer"""
    try:
        int(string)
        return True
    except ValueError:
        return False


reddit = praw.Reddit(
    username=os.getenv('BOT_USERNAME'),
    password=os.getenv('PASSWORD'),
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=f"r/{os.getenv('SUBREDDIT')}'s {os.getenv('BOT_USERNAME')}"
)

db = Database()

start_time = time.time()
next_refresh_time = start_time + 1 * 60  # 50 minutes after

# listening for new comments + submissions
submission_stream = reddit.subreddit(os.getenv('SUBREDDIT')).stream.submissions(
    skip_existing=True, pause_after=0)
comment_stream = reddit.subreddit(os.getenv('SUBREDDIT')).stream.comments(
    skip_existing=True, pause_after=0)
print("awaiting comments/posts")

while True:
    # check if needed to refresh token
    if time.time() > next_refresh_time:
        print("50 min cycle completed")
        next_refresh_time += 1 * 60  # 50 minutes after

    for submission in submission_stream:
        if not submission or db.check_post(submission.id):
            break

        print(f'Detected post: {submission.id}')
        db.add_post(submission.id)
        comment_made = submission.reply(stickied_message)
        comment_made.mod.distinguish("yes", sticky=True)
        print("made comment")

    for comment in comment_stream:
        if not comment or db.check_comment(comment.id):
            break

        print(f'Detected comment: {comment.body}')
        
        # mark comment as checked
        db.add_comment(comment.id)

        # checking the validity of the comment
        if comment.is_root() or comment.author.name == os.getenv('BOT_USERNAME') or not comment.parent().author.name:
            continue

        # *** Commands ***
        if comment.body.startswith('!nug'):

            # setting some helpful variables
            commenter = comment.author.name  # person who is giving award
            op = comment.submission.author.name  # person receiving award

            # exception handling
            # author too young and doesn't meet karma requirements
            # (moved from other exception handling to make it so db entry isn't created if author is invalid)
            if int((time.time() - comment.author.created_utc) / (60 * 60 * 24)) < 9 and (comment.author.link_karma + comment.author.comment_karma) < 100:  # 9 days for the first part
                comment_made = comment.reply(reply_account_too_new(commenter))
                comment_made.mod.distinguish()
                print("commenter doesn't meet account reqs, continuing")
                continue

            # creates database entry for commenter if required
            if db.get(commenter) == None:
                print("creating commenter db")
                db.set_available(commenter, 10000)
                db.set_received(commenter, 0)

            # setting some more helpful variables
            commenter_award_nugs = db.get(commenter)["available"]

            # splitting the comment into single words
            # i. e. `!nug 20` will become ['!nug', '20']
            try:
                nugs_given = comment.body.split(' ')[1]
            except IndexError:  # because if someone just did !nug meaning 1 nugget
                nugs_given = 1

            # converts valid text synonyms to their nugget amounts
            if nugs_given in ("max", "full", "all", "everything"):
                nugs_given = commenter_award_nugs

            try:
                amount_given = int(nugs_given)
            except (TypeError, ValueError):
                print("invalid format, continuing")
                comment_made = comment.reply(invalid_format)
                comment_made.mod.distinguish()
                continue

            # more exception handling
            # invalid gift arg
            if not int_conv(amount_given) or amount_given <= 0:
                print("invalid format, continuing")
                comment_made = comment.reply(invalid_format)
                comment_made.mod.distinguish()
                continue

            # checks commenter has enough nuggets to award
            elif commenter_award_nugs < amount_given:
                print("not enough nugs, continuing")
                comment_made = comment.reply(
                    reply_not_enough_nugs(commenter, commenter_award_nugs))
                comment_made.mod.distinguish()
                continue

            # checks poster is not awarding themselves
            elif commenter == op:
                print("op tried to award themselves, continuing")
                comment_made = comment.reply(award_yourself)
                comment_made.mod.distinguish()
                continue

            # creates database entry for op if required
            if db.get(op) == None:
                print("creating db for op")
                db.set_available(op, 5)
                db.set_received(op, 0)

            # setting some more helpful variables
            op_award_nugs = db.get(op)["available"]
            op_received_nugs = db.get(op)["received"]
            if op_received_nugs == None:
                op_received_nugs = 0

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

            dif_from_5 = 5 - op_received_nugs % 5
            bonus_nugs = 0

            if amount_given >= dif_from_5:
                amount_given -= dif_from_5
                bonus_nugs += amount_given // 5 + 1
                op_award_nugs += bonus_nugs
                amount_given += dif_from_5

            # increasing op's received nugs
            op_received_nugs += amount_given

            # updating db
            db.set_available(commenter, commenter_award_nugs)
            db.set_received(op, op_received_nugs)
            db.set_available(op, op_award_nugs)

            # update nugflair
            reddit.subreddit(os.getenv('SUBREDDIT')).flair.set(
                commenter, f"Available Nugs: {commenter_award_nugs}|Received Nugs: {commenter_award_nugs}")
            reddit.subreddit(os.getenv('SUBREDDIT')).flair.set(
                op, f"Available Nugs: {op_award_nugs}|Received Nugs: {op_award_nugs}")

            # log comment

            comment_made = comment.reply(reply_success(
                commenter, amount_given, commenter_award_nugs, op, op_received_nugs, bonus_nugs))
            comment_made.mod.distinguish()
            print("successful transaction")

            continue

        # bal command
        elif comment.body.startswith('!bal'):
            if db.get(comment.author.name)["available"] == None and db.get(comment.author.name)["received"] == None:
                print("user not in database")
                comment_made = comment.reply(not_in_db)
                comment_made.mod_distinguish()
            else:   
                comment.reply(f"""**Here is your balance**:
                Vote nugs: {db.get(comment.author.name)['available']}
                Received nugs: {db.get(comment.author.name)['received']}""")
            continue

    # other things?
    time.sleep(1)
