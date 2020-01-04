from flask import Flask , render_template,request, redirect, url_for, session, flash
from functools import wraps
import sqlite3, os
from utl import db_builder, db_manager,cards_api
import urllib3, json, urllib
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
    '''def auth(): authenticating login and flashing corresponding errors'''
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
    '''def signupcheck(): Checking if sign up form is filled out correctly; i.e. username taken, passwords match, all fields filled out'''
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
    user = session['username']
    '''def home(): homepage checks if user is in session and gets info on user'''
    return render_template("home.html", user=user, home="active")

@app.route("/profile")
@login_required
def profile():
    user = session['username']
    '''def profile(): allows user to update their profile and view their purchases'''
    return render_template("profile.html", user=user, profile="active")

@app.route("/resetpasswd", methods=["POST"])
@login_required
def password():
    '''def password(): backend of password changes, makes sure form is filled out correctly'''
    password = request.form['password']
    verif = request.form['verif']
    oldpass = request.form['oldpass']
    if (password == "" or verif == "" or oldpass == ""):
        flash("Please fill out all fields!", 'alert-danger')
        return redirect("/profile")
    if (password != verif):
        flash("Passwords do not match!", 'alert-danger')
        return redirect("/profile")
    username = session['username']
    if (not db_manager.userValid(username, oldpass)):
        flash("Wrong password!", 'alert-danger')
        return redirect("/profile")
    db_manager.changePass(username, password)
    flash("Password successfully changed!", 'alert-success')
    return redirect("/home")

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
#WORK HERE JACKIE
@app.route("/dice", methods=["GET", "POST"])
@login_required
def dice():
    '''def dice(): allows user to place bet for dice game'''
    user = session['username']
    if request.method == 'GET':
        money = db_manager.getMoney(user)
        return render_template("dice.html", betting=True, money=money)
    else:
        bet = int(request.form['bet'])
        options = request.form.getlist('options')
        print(db_manager.checkBet(user, bet))
        if len(options) == 0 or not db_manager.checkBet(user, bet):
            flash("Please enter a valid bet and choose at least one betting option!", 'alert-danger')
            return redirect(url_for("dice"), code=303)
        u = urllib.request.urlopen("http://roll.diceapi.com/json/3d6")
        response = json.loads(u.read())['dice']
        dice = []
        for roll in response:
            dice.append(roll['value'])
        multiplier = diceH(dice, options)
        amount = multiplier * bet
        db_manager.updateMoney(user, amount)
        money = db_manager.getMoney(user)
        return render_template("dice.html", dice=dice, betting=False, money=money, options=options, bet=bet, amount=amount)

def diceH(dice, options):
    '''def diceH(): helper function to check dice rolls'''
    print(options)
    multiplier = [60, 20, 18, 12, 8, 6, 6, 6, 6, 8, 12, 18, 20, 60]
    sum = 0;
    total_mult = 0
    for die in dice:
        sum += int(die)
    for option in options:
        if option == "big" :
            if sum >= 11 and sum <= 17:
                total_mult += 2
        elif option == "small":
            if sum <= 10 and sum >= 4:
                total_mult += 2
        elif "triple" in option:
            num = option[-1]
            if dice[0] == num and dice[1] == num and dice[2] == num:
                total_mult += 180
        else:
            num = int(option[-1])
            if sum == num:
                total_mult += multiplier[num - 4]
    total_mult -= len(options)
    print(total_mult)
    return total_mult

@app.route("/lottery")
@login_required
def lotto():
    return render_template("lottery.html")

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
