#!/usr/bin/env python2.7

# =============================================================================
# IMPORTS
# =============================================================================
import praw
from time import time, sleep
from sys import exc_clear
from urllib import quote
import re
import sqlite3
import datetime

# =============================================================================
# GLOBALS
# =============================================================================
sleep_time = 60  # time (in seconds) the bot sleeps before performing a new check
post_grab_limit = 10  # how many new posts to check at a time. needs to be greater than the number of submissions that could be made in the amount of time the bot sleeps (sleep_time)
subreddit_name = "destinysherpa"

user_ignore_list = ['AutoModerator']
ps4_verified_users = ['D0cR3d' , 'Marshmellowsword' , 'SSJ2-Gohan' , 'Tahryl' , 'The--Marf' , 'Tomauro0115' , 'Whoosk' , 
            'YourFallingBehind' , 'ASublimed' , 'ClarkIR' , 'Deftones_132' , 'Deneeka' , 'dvdaap' , 'Fapiness' , 
            'Flatnic86' , 'FluffyALae' , 'gamaliel56' , 'iAlice' , 'iS3W3LL' , 'irishcman' , 'mark_graham' , 
            'diehardbruin' , 'POWERRL_RANGER' , 'Ps_Petrucci' , 'Rapioqt' , 'Rileystheman' , 'satish1986' , 
            'sejisoylam' , 'tacoflame' , 'thefrasca' , 'TheMisneach' , 'TheWorstType' , 'Tsujin' , 'Xangster' , 
            'OmegaTrademark' , 'GreatLono' , 'UberMcTastic' , 'bitsnbullets' , 'N1COLASPR1ME' , 'Hattrix86' , 
            'Illegalbusiness' , 'ForcaBarca1899' , 'Findolpoi']
xb1_verified_users = ['Incredigasmic', 'ScheduledCargo', 'Skifurd', 'SmolderingEgo', 'The--Marf', 'totallytexan', 
                'Chrisg2003bt', 'datadilemma', 'Deneeka', 'mastermml', 'Ollair', 'PerfectedHavok', 'zathegfx', 
                'theBigButtQuake', 'ThatUncleJack', 'millerb7', 'Maloonagins']
mod_users = ['Tahryl', 'SSJ2', 'Incredigasmic', 'Ruley9', 'Marshmellowsword', 'Clarkey7163', 'YourFallingBehind', 
            'SmolderingEgo', 'totallytexan', 'Whoosk', 'Tomauro0115', 'Skifurd', 'ScheduledCargo', 'D0cR3d', 'The--Marf']

r = praw.Reddit('For Ego!')
r.login([username], [pass], disable_warning='True')

# =============================================================================
# FUNCTIONS
# =============================================================================

# define function main()
def main():
    print 'Starting...'
    
    createSqlite()  # create the database if the tables do not exist
     
    # if the database ever needs to be reinitialized with defined users   
    # type values: 
    #   0 = verified
    #   1 = mods
    #   2 = other
    # platform values:
    #   ps4 = playstation 4
    #   ps3 = playstation 3
    #   xb1 = xbox 1
    #   xb3 = xbox 360
    
    #initializeDatabase(xb1_verified_users, 0, "xb1")
    #initializeDatabase(ps4_verified_users, 0, "ps4")
    #initializeDatabase(mod_users, 1, "all")
    
    already_done_s = []
    already_done_c = []
    
    # start endless loop
    while True:
        
        # try-catch runtime issues. Prevents bot from crashing when a problem is encountered.
        # Most frequent trigger is a connection problem (reddit is down)
        try:
            already_done_s = selectProcessed_S(already_done_s)
            already_done_c = selectProcessed_C(already_done_c)
            
            # open connection to db
            conn = sqlite3.connect('sherpa.db')
            
            # get newest submissions
            for s in r.get_subreddit( subreddit_name ).get_new(limit=post_grab_limit):
                # check if submission has already been processed
                if s.id not in already_done_s:
                    # ignore users in ignore list
                    if s.author not in user_ignore_list:
                        date = datetime.datetime.now().strftime("%m/%d/%y")
                        insertNewSubmission(conn, s.id, date, s.author, s.short_link, s.title)
                    
            # get newest comments
            for c in r.get_comments( subreddit_name ):
                # check if submission has already been processed
                if c.id not in already_done_c:
                    # ignore users in ignore list
                    if c.author not in user_ignore_list:
                        date = datetime.datetime.now().strftime("%m/%d/%y")
                        insertNewComments(conn, c.id, date, c.author, c.permalink, c.body)
                    
            # close connection
            conn.close()      
        #handles runtime errors.
        except Exception as e:
            print 'Handling run-time error:', e
        sleep( sleep_time )

# create the SQLite3 database   
def createSqlite():
    conn = sqlite3.connect('sherpa.db')
    print "Opened database successfully";
    
    conn.execute('''CREATE TABLE IF NOT EXISTS SUBMISSIONS (
                    ID              INTEGER PRIMARY KEY AUTOINCREMENT,
                    SUBMISSIONID    TEXT NOT NULL,
                    DATE            TEXT NOT NULL,
                    AUTHOR          TEXT NOT NULL,
                    PERMALINK       TEXT NOT NULL,
                    TITLE           TEXT NOT NULL);
                ''')
    print "SUBMISSIONS table created successfully";
    
    conn.execute('''CREATE TABLE IF NOT EXISTS COMMENTS (
                    ID              INTEGER PRIMARY KEY AUTOINCREMENT,
                    COMMENTID       TEXT NOT NULL,
                    DATE            TEXT NOT NULL,
                    AUTHOR          TEXT NOT NULL,
                    PERMALINK       TEXT NOT NULL,
                    BODY            TEXT NOT NULL);
                ''')
    print "COMMENTS table created successfully";
    
    conn.execute('''CREATE TABLE IF NOT EXISTS USERS (
                    ID              INTEGER PRIMARY KEY AUTOINCREMENT,
                    USERNAME        TEXT NOT NULL,
                    TYPE            INTEGER NOT NULL,
                    PLATFORM        TEXT NOT NULL);
                ''')
    print "USERS table created successfully";
    
    conn.close()
    
# initialize USERS table with defined users
def initializeDatabase(users, type, platform):
    conn = sqlite3.connect('sherpa.db')
    for u in users:

        sql = "INSERT INTO USERS (USERNAME, TYPE, PLATFORM) VALUES (?, ?, ?)"
        cursor = conn.execute(sql, (str(u), type, platform))
        conn.commit()
    conn.close()

# add processed submissions to a list
def selectProcessed_S(already_done_s):
    conn = sqlite3.connect('sherpa.db')
    sql = "SELECT SUBMISSIONID from SUBMISSIONS where SUBMISSIONID not in ({seq})".format(seq=','.join(['?']*len(already_done_s)))

    cursor = conn.execute(sql, already_done_s)
    
    for row in cursor:
       already_done_s.append(row[0]);
       
    conn.close()
       
    return already_done_s
  
# add processed comments to a list  
def selectProcessed_C(already_done_c):
    conn = sqlite3.connect('sherpa.db')
    sql = "SELECT COMMENTID from COMMENTS where COMMENTID not in ({seq})".format(seq=','.join(['?']*len(already_done_c)))

    cursor = conn.execute(sql, already_done_c)
    
    for row in cursor:
       already_done_c.append(row[0]);
       
    conn.close()
       
    return already_done_c
    
# insert new submissions 
def insertNewSubmission(conn, submissionId, date, author, permalink, title):
    sql = "INSERT INTO SUBMISSIONS (SUBMISSIONID, DATE, AUTHOR, PERMALINK, TITLE) VALUES (?, ?, ?, ?, ?)"
    conn.execute(sql, ( str(submissionId), str(date), str(author), str(permalink), str(title) ))
    conn.commit()
    print("S - " + submissionId)
    
# insert new comments
def insertNewComments(conn, commentId, date, author, permalink, body):
    sql = "INSERT INTO COMMENTS (COMMENTID, DATE, AUTHOR, PERMALINK, BODY) VALUES (?, ?, ?, ?, ?)"
    conn.execute(sql, ( str(commentId), str(date), str(author), str(permalink), str(body)))
    conn.commit()
    print("C - " + commentId)

# call main
main()