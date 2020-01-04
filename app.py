from flask import Flask , render_template,request, redirect, url_for, session, flash
from functools import wraps
import sqlite3, os
from utl import db_builder, db_manager
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
    return "HOME"

#====================================================
@app.route("/logout")
@login_required
def logout():
    '''def logout(): logging out of session, redirects to login page'''
    session.clear()
    flash('You were successfully logged out.', 'alert-success')
    return redirect('/')


@app.route("/slotmachine")
@login_required
def slot():
    '''def slot(): placing and checking bets'''
    print("here's bet")
    if request.args.get('slotbet'):
        bet = request.args.get('slotbet')
        print(bet)
        if bet == "" or int(bet) < 100:
            bet = 100
            flash("Please place a bet of $100 or more.", 'alert-danger')
            return render_template("slotmachine.html", primarybet = bet, bet = 0, image1 = dict[random.choice(slotImages)], image2 = dict[random.choice(slotImages)], image3 = dict[random.choice(slotImages)], win = "No", colour = "yellow")
        else:
            bet = int(bet)
            rand1 = random.choice(slotImages)
            rand2 = random.choice(slotImages)
            rand3 = random.choice(slotImages)
            if rand1 == rand2 and rand2 == rand3:
                win = rand1
                colour = "red"
            else:
                win = "No"
                colour = "yellow"
            return render_template("slotmachine.html", primarybet = bet, bet = bet, image1 = dict[rand1], image2 = dict[rand2], image3 = dict[rand3], win = win, colour = colour)
    else:
        bet = 100
        return render_template("slotmachine.html", primarybet = bet, bet = 0, image1 = dict[random.choice(slotImages)], image2 = dict[random.choice(slotImages)], image3 = dict[random.choice(slotImages)], win = "No", colour = "yellow")

dict = {}
slotImages = []
file = open("slotimages.csv", "r") #opens second file with links
content = file.readlines() #parse through files by line
content = content[1:len(content)] #take out the table heading
for line in content:
    line = line.strip() #removes \n
    line = line.split(",") #if line does not contain quotes, split by comma
    dict[line[0]] = (line[1]) #key value pair
    slotImages.append(line[0])
# print(dict) #testing results
file.close()


if __name__ == "__main__":
    db_builder.build_db()
    app.debug = True
    app.run()
