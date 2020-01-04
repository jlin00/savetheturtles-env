from flask import Flask , render_template,request, redirect, url_for, session, flash
from functools import wraps
import sqlite3, os
from utl import db_builder, db_manager, cards_api
import random

app = Flask(__name__)
app.secret_key = os.urandom(32)
#====================================================
def login_required(f):
    """Decorator for making sure user is logged in"""
    @wraps(f)
    def dec(*args, **kwargs):
        '''dec (*args, **kwargs): Decorator for checking login and if user in session'''
        if 'username' in session:
            for arg in args:
                print(arg)
            return f(*args, **kwargs)
        flash('You must be logged in to view this page!', 'alert-danger')
        return redirect('/')
    return dec

def no_login_required(f):
    """Decorator for making sure user is not logged in"""
    @wraps(f)
    def dec(*args, **kwargs):
        '''dec(*args, **kwargs): Decorator for checking no login'''
        if 'username' not in session:
            return f(*args, **kwargs)
        flash('You cannot view this page while logged in!', 'alert-danger')
        return redirect('/home')
    return dec
#====================================================

@app.route("/")
def root():
    '''def root(): Redirects to login page if not in session, redirects to home if in session'''
    if 'username' in session:
        return redirect('/home')
    return redirect('/login')

@app.route("/login")
@no_login_required
def login():
    '''def login(): login requirement'''
    return render_template('login.html')

@app.route("/auth", methods=["POST"])
@no_login_required
def auth():
    '''auth(): authenticating login and flashing corresponding errors'''
    enteredU = request.form['username']
    enteredP = request.form['password']
    if(enteredU == "" or enteredP == ""): #if fields empty
        flash('Please fill out all fields!', 'alert-danger')
        return redirect(url_for('login'))
    if (db_manager.userValid(enteredU, enteredP)): #returns true if login successful
        flash('You were successfully logged in!', 'alert-success')
        session['username'] = enteredU
        return redirect(url_for('home'))
    else:
        flash('Wrong Credentials!', 'alert-danger')
        return redirect(url_for('login'))

@app.route("/signup")
@no_login_required
def signup():
    '''def signup(): sign up route, takes in a form for signing up'''
    return render_template("signup.html")

@app.route("/signupcheck", methods=["POST"])
@no_login_required
def signupcheck():
    '''signupcheck(): Checking if sign up form is filled out correctly; i.e. username taken, passwords match, all fields filled out'''
    username = request.form['username']
    password = request.form['password']
    confirm = request.form['confirmation']
    #preliminary checks on entered fields
    if(username == "" or password == "" or confirm == ""):
        flash('Please fill out all fields!', 'alert-danger')
        return render_template("signup.html", username=username, password=password, confirm=confirm)
    if ("," in username):
            flash('Commas are not allowed in username!', 'alert-danger')
            return render_template("signup.html", username=username, password=password, confirm=confirm)
    if (confirm!=password):
        flash('Passwords do not match!', 'alert-danger')
        return render_template("signup.html", username=username, password=password, confirm=confirm)
    #form information delivered to backend
    added = db_manager.addUser(username,password) #returns True if user was sucessfully added
    if (not added):
        flash('Username taken!', 'alert-danger')
        return render_template("signup.html", username=username, password=password, confirm=confirm)
    flash('You have successfully created an account! Please log in!', 'alert-success')
    return redirect(url_for('login'))

#====================================================
#STARTING FROM HERE USER MUST BE LOGGED IN

@app.route("/home")
@login_required
def home():
    '''home(): homepage checks if user is in session and gets info on user'''
    return render_template("home.html")

#====================================================
#WORK HERE KIRAN

@app.route("/holdem")
@login_required
def holdem():
    ''' def holdem(): renders texas holdem game selector for players who have not joined a game, renders game for players in a game '''
    game_id = db_manager.current_game(session['username'])
    if(game_id):
        # if game id exists, then the user is in a game and said game should be rendered
        return render_template("holdem_game.html")
    else:
        # if game id is 0, then the game selection page should be rendered
        
        return render_template("holdem_lobby.html")
    return 'yikes'

@app.route("/holdem/join",methods=['GET'])
@login_required
def join_holdemgame():
    if not 'game_id' in request.args or request.args['game_id'] == '':
        flash('please choose a game to join!','alert-danger')
        return redirect(url_for('holdem'))
    game_id = request.args['game_id']
    cards = cards_api.drawcards(game_id,2)
    db_manager.addplayer(game_id,username,cards)
    flash('You [{}] have successfully joined game {}'.format(username,game_id),'alert-success')
    return redirect(url_for('holdem'))
    

@app.route("/holdem/create")
@login_required
def create_holdem():
    ''' def create_holdem(): create a new texas holdem game '''
    game_id = cards_api.newdeck()
    # add 'board' player to game
    board_cards = cards_api.drawcards(game_id,5)
    db_manager.addplayer(game_id,'board',board_cards)
    #add first player to game
    player_cards = cards_api.drawcards(game_id,2)
    db_manager.addplayer(game_id,session['username'],player_cards)

    flash('game successfully created.','alert-success')
    
    return redirect(url_for('holdem'))
#====================================================

#====================================================
@app.route("/logout")
@login_required
def logout():
    '''def logout(): logging out of session, redirects to login page'''
    session.clear()
    flash('You were successfully logged out.', 'alert-success')
    return redirect('/')

if __name__ == "__main__":
    db_builder.build_db()
    app.debug = True
    app.run()
