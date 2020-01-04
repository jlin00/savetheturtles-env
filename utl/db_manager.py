import sqlite3
from utl.db_builder import exec, execmany

#====================================================
#sign up and login functions

#authenticates user
def userValid(username,password):
    '''def userValid(username,password): determines if username is in database and password corresponds to username'''
    q = "SELECT username FROM user_tbl;"
    data = exec(q)
    for uName in data:
        if uName[0] == username:
            q = "SELECT password from user_tbl WHERE username=?"
            inputs = (username,)
            data = execmany(q, inputs)
            for passW in data:
                if (passW[0] == password):
                    return True
    return False

#add user-provided credentials to database
def addUser(username, password):
    '''def addUser(username, password): adding user from sign up, taking in form inputs and writing to data table'''
    q = "SELECT * FROM user_tbl WHERE username=?"
    inputs = (username,)
    data = execmany(q, inputs).fetchone()
    if (data is None):
        q = "INSERT INTO user_tbl VALUES(?, ?, '', 500, 0, '')"
        inputs = (username, password)
        execmany(q, inputs)
        return True
    return False #if username already exists

#reset password
def changePass(username, password):
    '''def changePass(username, password): updating data table of user in session with new password'''
    q = "UPDATE user_tbl SET password=? WHERE username=?"
    inputs = (password, username)
    execmany(q, inputs)

#====================================================
#WORK HERE KIRAN

#texas_tbl (
    #game_id TEXT,
    #player TEXT,
    #card1 TEXT,
    #card2 TEXT,
    #card3 TEXT,
    #card4 TEXT,
    #card5 TEXT,
    #bet INT,
    #folded INT
#)

def current_game(username):
    ''' def current_game(username): returns game id of a game the user has already entered, or 0 if they have not entered a game '''
    q = "SELECT game_id,player FROM texas_tbl WHERE player = ?;"
    v = (username,)
    data = execmany(q,v).fetchone()
    print(data)
    if(data):
        return data[0]
    return None

def addplayer(game_id,name,cards):
    ''' def addplayer(game_id,name,cards): adds player with game_id specified and with list of cards to texas tbl database '''
    q = """
INSERT INTO texas_tbl
    (game_id,player,bet,folded,card1,card2,card3,card4,card5)
    VALUES(?, ?, 0, 0, ?, ?, ?, ?, ?);
"""
    values = [game_id,name]
    for i in range(5):
        if i < len(cards):
            values += [ cards[i]['code'] ]
        else:
            values += [ '' ]
    print(values)
    execmany(q,values)
#====================================================
#WORK HERE JACKIE
def getMoney(username):
    '''def getMoney(username): get current amount of money of user in session'''
    q = "SELECT money from user_tbl WHERE username=?"
    inputs = (username, )
    data = execmany(q, inputs).fetchone()[0]
    return data

def checkBet(username, bet):
    '''def checkBet(username, bet): check if user is betting a valid amount'''
    money = getMoney(username)
    bet = int(bet)
    return money >= bet

def updateMoney(username, amount):
    '''def updateMoney(username, amount): updating data table of user in session with new amount'''
    q = "UPDATE user_tbl SET money=? WHERE username=?"
    money = getMoney(username)
    amount += money
    inputs = (amount, username)
    execmany(q, inputs)
