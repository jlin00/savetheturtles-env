from flask import Flask , render_template,request, redirect, url_for, session, flash
from functools import wraps
import sqlite3, os
from utl import db_builder, db_manager
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

#====================================================
#WORK HERE JACKIE
@app.route("/dice", methods=["GET", "POST"])
@login_required
def dice():
    '''def dice(): allows user to place bet for dice game'''
    user = session['username']
    if request.method == 'GET':
        return render_template("dice.html", user=user, dice=['1', '2', '3'])
    if request.method == 'POST':
        bet = request.form['bet']
        u = urllib.request.urlopen("http://roll.diceapi.com/json/3d6")
        response = json.loads(u.read())['dice']
        dice = []
        for roll in response:
            dice.append(roll['value'])
        return render_template("dice.html", user=user, dice=dice)
    return render_template("dice.html", user=user)

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
