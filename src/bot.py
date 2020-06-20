import praw
import os
import sqlite3
import re
import time
from dotenv import load_dotenv
from database import Database
load_dotenv()

#static responses
invalid_format = "I wasn't able to understand your request. Valid format is\n\n```!nug (amount of awarded nuggets)```"
award_yourself = "Nice try OP, but you cannot award your own posts! Award your voting nuggets to deserving posts from others!"
stickied_message = "Reply to this comment to award nugget(s) to OP if you feel this meme is deserving."

#dynamic responses
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
    user_agent="r/MinecraftMemes' GoldenNuggetBot"
)

db = Database()

# database for logging already processed comments
comment_db = sqlite3.connect('comments.db')
comm_curs = comment_db.cursor()

start_time = time.time()

# listening for new comments + submissions
submission_stream = reddit.subreddit("Minecraftmeme").stream.submissions(skip_existing=True, pause_after=0)
comment_stream = reddit.subreddit('Minecraftmeme').stream.comments(skip_existing=True, pause_after=0)
print("awaiting comments/posts")

while True:
    for submission in submission_stream:
        if not submission or db.check_comment(comment.id): 
            break
            
        print("detected post")
        db.add_post(submission.id)
        comment_made = submission.reply(stickied_message)
        comment_made.mod.distinguish("yes", sticky=True)
        print("made comment")
        
    for comment in comment_stream:
        if not comment or db.check_comment(comment.id):
            break
            
        print("detected comment")
        """
        Possible ways of awarding are !nugget, !nug and !gold
        the first argument must be the username (should not matter whether preceded by u/ or not)
        the second argument must either be a number or max, full or all
        i. e. `!nugget max` will transfer all nuggets to poster
        """
    
        try:
            if not re.match(r'!(nug|nugget|gold)( \d)?', comment.body) or not comment.parent().stickied or not comment.parent().author.name == "GoldenNugBot":
                print("not a nug action, continuing")
                continue
        except AttributeError:  # raised if there is no parent comment
            continue
        
        #checks if comment has already been checked
        db.add_comment(comment.id)
    
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
            db.set_available(commenter, 3)
            db.set_received(commenter, 0)
    
        # setting some more helpful variables
        commenter_award_nugs = db.get(commenter)["available"]
    
        # splitting the comment into single words
        # i. e. `!nug 20` will become ['!nug', '20']
        # placeholder, since you can't just declare variables in python REEEEEEEEEEEEEEEEEEEEE
        amount_given = 0
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
            print("invalid format, continuing")
            comment_made = comment.reply(invalid_format)
            comment_made.mod.distinguish()
            continue

        # checks commenter has enough nuggets to award
        elif commenter_award_nugs < amount_given:
            print("not enough nugs, continuing")
            comment_made = comment.reply(reply_not_enough_nugs(commenter, commenter_award_nugs))
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
            db.set_available(op, 3)
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
        if (amount_given >= dif_from_5):
            amount_given -= dif_from_5
            # hopefully doesn't modify amount_given at all my python is rusty
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
        reddit.subreddit("minecraftmeme").flair.set(commenter, f"Available Nugs: {commenter_award_nugs}|Received Nugs: {commenter_award_nugs}")
        reddit.subreddit("minecraftmeme").flair.set(op, f"Available Nugs: {op_award_nugs}|Received Nugs: {op_award_nugs}")
        
        # log comment
    
        comment_made = comment.reply(reply_success(commenter, amount_given, commenter_award_nugs, op, op_received_nugs, bonus_nugs))
        comment_made.mod.distinguish()
        print("successful transaction")
        
    #other things?
    time.sleep(60)
