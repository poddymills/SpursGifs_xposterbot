#!/usr/bin/env python

"""
Based on what I learned creeping the source code for
https://github.com/cris9696/PlayStoreLinks_Bot
"""

import praw  		# reddit wrapper
import time 		# obvious
import pickle 		# dump list and dict to file
import os  			# OS-related stuff
import sys 			# ""
import atexit 		# To handle unexpected crashes or just normal exiting
import logging 		# logging

# tagline
commentTag = "------\n\n*Hi! I'm a bot created to x-post gifs/vines/gfycats" + \
    " from /r/coys over to /r/SpursGifs.*\n\n*Feedback/bug reports? Send a" + \
    " message to [pandanomic](http://www.reddit.com/message/compose?to=pan" + \
    "danomic).*\n\n*[Source code](https://github.com/pandanomic/Spurs" + \
    "Gifs_xposterbot)*"

# DB for caching previous posts
dbFile = "spursgifs_xposterDB"

# File with login credentials
propsFile = "login.properties"

# flag to check if db file's already checked
fileOpened = False

# subreddit to x-post to. Changes if testing
global postSub
postSub = "SpursGifs"

# for cron jobs
global cron
cron = False


# Called when exiting the program
def exit_handler():
    if fileOpened:
        pickle.dump(already_done, f)
        f.close()
    print("(Shutting Down)")
    os.remove("BotRunning")

# Register the function that get called on exit
atexit.register(exit_handler)


# Function to exit the bot
def exitBot():
    sys.exit()


# Main bot runner
def bot(subreddit):
    print "(Parsing new 30)"
    newCount = 0
    for submission in coys_subreddit.get_new(limit=30):
        if validateSubmission(submission):
            already_done.append(submission.id)
            print "(New Post)"
            submit(spursgifs_subreddit, submission)

    if newCount == 0:
        print "(Nothing new)"


# Submission
def submit(subreddit, submission):
    print "\tSubmitting to /r/" + postSub + ")"
    try:
        subreddit.submit(
            submission.title + " (x-post from /r/coys)", url=submission.url)
        followupComment(submission)
    except praw.errors.AlreadySubmitted:
        # logging.exception("Already submitted")
        print "\t--Already submitted, caching"
        if submission.id not in already_done:
            already_done.append(submission.id)
    except praw.errors.RateLimitExceeded:
        print "\t--Rate Limit Exceeded"
        already_done.remove(submission.id)
    except praw.errors.APIException:
        logging.exception("Error on link submission.")


# Retrieves the extension
def extension(url):
    return os.path.splitext(url)[1]


# Validates if a submission should be posted
def validateSubmission(submission):
    if submission.id not in already_done and \
        (submission.domain in allowedDomains or
         extension(submission.url) in allowedExtensions):
        return True
    return False


# Followup Comment
def followupComment(submission):
    print("\tFollowup Comment...")
    user = r.get_redditor("spursgifs_xposterbot")
    newSubmission = user.get_submitted(limit=1).next()
    followupCommentText = "Originally posted [here](" + \
        submission.permalink + ") by /u/" + \
        submission.author.name + \
        ".\n\n"
    followupCommentText += commentTag

    try:
        newSubmission.add_comment(followupCommentText)
        notifyComment(newSubmission.permalink, submission)
    except praw.errors.RateLimitExceeded:
        print "\t--Rate Limit Exceeded"
    except praw.errors.APIException:
        logging.exception("Error on followupComment")


# Notifying comment
def notifyComment(newURL, submission):
    print("\tNotify Comment...")
    notifyCommentText = "X-posted to [here](" + newURL + ").\n\n"
    notifyCommentText += commentTag

    try:
        submission.add_comment(notifyCommentText)
    except praw.errors.RateLimitExceeded:
        print "\t--Rate Limit Exceeded"
    except praw.errors.APIException:
        logging.exception("Error on notifyComment")

# If the bot is already running
if(os.path.isfile('BotRunning')):
    print("The bot is already running, shutting down")
    exitBot()

# The bot was not running
# create the file that tell the bot is running
open('BotRunning', 'w').close()

print "(Starting)"

args = sys.argv

if len(args) > 1:
    print "\tGetting args..."
    if "--testing" in args:
        postSub = "pandanomic_testing"
    if "--cron" in args:
        cron = True
    print "\t(Args: " + str(args[1:]) + ")"

print "\tLogging in..."
try:
    # reading login info from a file, it should be username (newline) password
    with open("login.properties", "r") as loginFile:
        loginInfo = loginFile.readlines()

    loginInfo[0] = loginInfo[0].replace('\n', '')
    loginInfo[1] = loginInfo[1].replace('\n', '')

    r = praw.Reddit('/u/spursgifs_xposterbot by /u/pandanomic')
    r.login(loginInfo[0], loginInfo[1])

    # read off /r/coys
    coys_subreddit = r.get_subreddit('coys')

    # submit to /r/SpursGifs or /r/pandanomic_testing
    spursgifs_subreddit = r.get_subreddit(postSub)

except:
    print "FAILURE"
    exitBot()

allowedDomains = ["gfycat.com", "vine.co", "giant.gfycat.com"]
allowedExtensions = [".gif"]

# Array with previously linked posts
# Check the db cache first
print "\tChecking cache..."
already_done = []
if(os.path.isfile(dbFile)):
    f = open(dbFile, 'r+')

    # If the file isn't at its end or empty
    if f.tell() != os.fstat(f.fileno()).st_size:
        already_done = pickle.load(f)
    f.close()
f = open(dbFile, 'w+')

print '(Cache size: ' + str(len(already_done)) + ")"

fileOpened = True

counter = 0

if cron:
    print "(Cron job)"
    bot(spursgifs_subreddit)
else:
    print "(Looping)"
    while True:
        bot(spursgifs_subreddit)
        counter += 1
        print '(Looped - ' + str(counter) + ')'
        time.sleep(60)
