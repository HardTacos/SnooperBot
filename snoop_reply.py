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

r = praw.Reddit('For Ego!')
r.login([username], [pass], disable_warning='True')

# =============================================================================
# FUNCTIONS
# =============================================================================

# define function main()
def main():
    print 'Starting...'
    
    # start endless loop
    while True:
        
        # try-catch runtime issues. Prevents bot from crashing when a problem is encountered.
        # Most frequent trigger is a connection problem (reddit is down)
        try:
            # open connection to db
            conn = sqlite3.connect('sherpa.db')
            
            read_pm(conn)
                    
            # close connection
            conn.close()
        #handles runtime errors.
        except Exception as e:
            print 'Handling run-time error:', e
        sleep( sleep_time )
    
# checking inbox for new requests
def read_pm(conn):
    try:
        for m in r.get_unread(unset_has_mail=True, update_user=True):
            prawobject = isinstance(m, praw.objects.Message)
            #print(vars(m))
            
            # confirm that the message we recieve is one to process
            if (m.subject == "Snoop Run"):
                # retrieve data
                if (m.body.startswith("- get")):
                    # parse message into parameters
                    msg = m.body.split()
                    selectedUser = ""
                    
                    if (msg[2] == "all"):
                        selectedUser = "all " + msg[3]
                    elif (msg[2] == "verified"):
                        selectedUser = "verified " + msg[3]
                    elif (msg[2] == "mods"):
                        selectedUser = "mod " + msg[3]
                    
                    if ("--exclude-no-activity" in msg):
                        printOnlyUsersWithActivity(conn, m.author, getSelectedUsers(conn, selectedUser))
                    else:
                        getUserData(conn, m.author, getSelectedUsers(conn, selectedUser))
                # update verified users       
                elif (m.subject == "Update Verified"):
                    print "updating from verified list"
                # update mod users
                elif (m.subject == "Update Mods"):
                    print "updating from mod list"

            m.mark_as_read()
            
    except Exception as err:
        print err

# get the selected users
def getSelectedUsers(conn, userInput):
    ui = userInput.split()
    selectedUsers = []
    sql = "SELECT USERNAME FROM USERS WHERE " 
    
    for i in ui:
        if(i == ui[0]):
            sql += str(options[i]())
        else:
            sql += " and " + str(options[i]())
        
    cursor = conn.execute(sql)
    for row in cursor:
        selectedUsers.append(row[0]);
    return selectedUsers

# get data on requested users    
def getUserData(conn, author, users_to_retrieve):
    
    r = praw.Reddit('For Ego!')
    r.login('zathegfx', 'Mittens1@3', disable_warning='True')
    
    generated_message = ""
    
    for u in users_to_retrieve:
        
        # get all submissions for selected user
        generated_message += "###Submissions for " + u + "\n"
        generated_message += "Date | Title | Permalink\n"
        generated_message += "---|---|---\n"
        
        sql_s = "select DATE, substr(TITLE,0,20), PERMALINK from SUBMISSIONS where AUTHOR = '" + u + "'"
        cursor = conn.execute(sql_s)
        
        for row in cursor:
            generated_message += row[0] + " | " + row[1] + " | " + row[2] + " \n"
            
        
        #get all comments for selected user 
        generated_message += "\n###Comments for " + u + "\n"
        generated_message += "Date | Title | Permalink\n"
        generated_message += "---|---|---\n"
                            
        sql_c = "select DATE, substr(BODY,0,20), PERMALINK from COMMENTS where AUTHOR = '" + u + "'"
        cursor = conn.execute(sql_c)
        
        for row in cursor:
           generated_message += row[0] + " | " + row[1] + " | " + row[2] + " \n"
           
        generated_message += "\n---\n"
        
    r.send_message(author, 'SnooperBot Reply', generated_message)
    print "Sent Reply to " + str(author)

# prints only users that have had activity during the selected query    
def printOnlyUsersWithActivity(conn, author, users_to_retrieve):
    generated_message = ""
    for u in users_to_retrieve:
            
        sql_s = "select DATE, substr(TITLE,0,20), PERMALINK from SUBMISSIONS where AUTHOR = '" + u + "'"
        cursor_s = conn.execute(sql_s)
        sCount = conn.execute(sql_s).fetchone()
        
        sql_c = "select DATE, substr(BODY,0,20), PERMALINK from COMMENTS where AUTHOR = '" + u + "'"
        cursor_c = conn.execute(sql_c)
        cCount = conn.execute(sql_c).fetchone()
        
        if (sCount is None and cCount is None):
            continue
        else:
            # get all submissions for selected user
            generated_message += "###Submissions for " + u + "\n"
            generated_message += "Date | Title | Permalink\n"
            generated_message += "---|---|---\n"
            
            for row in cursor_s:
                generated_message += row[0] + " | " + row[1] + " | " + row[2] + " \n"
            
            #get all comments for selected user 
            generated_message += "\n###Comments for " + u + "\n"
            generated_message += "Date | Title | Permalink\n"
            generated_message += "---|---|---\n"
            
            for row in cursor_c:
               generated_message += row[0] + " | " + row[1] + " | " + row[2] + " \n"
       
    generated_message += "\n---\n"  
    r.send_message(author, 'SnooperBot Reply', generated_message)
    print "Sent Reply to " + str(author)
        
# define the function blocks
def verified():
    return "TYPE = 0"
def mod():
    return "TYPE = 1"
def allUsers():
    return ""
def ps4():
    return "PLATFORM = 'ps4'"
def ps3():
    return "PLATFORM = 'ps3'"
def xb1():
    return "PLATFORM = 'xb1'"
def xb3():
    return "PLATFORM = 'xb3'"
def new():
    return "USERNAME = ''"
    
options = {
    "verified" : verified,
    "mod" : mod,
    "all" : allUsers,
    "--ps4" : ps4,
    "--ps3" : ps3,
    "--xb1" : xb1,
    "--xb3" : xb3,
    "--new" : new,
}

# call main
main()

    
