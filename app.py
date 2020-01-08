from flask import Flask , render_template,request, redirect, url_for, session, flash
from functools import wraps
import sqlite3, os
from utl import db_builder, db_manager,cards_api
import random
#import urllib3, json, urllib
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
    money = db_manager.getMoney(user)
    '''def home(): homepage checks if user is in session and gets info on user'''
    return render_template("home.html", user=user, home="active", money=money)

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

def cardtotal(cards):
    ''' def cardtotal(cards): calculate blackjack value of list of cards '''
    total = 0
    aces = 0
    for card in cards:
        if card['value'] == 'ACE':
            aces += 1
            total += 11
        else:
            try:
                value = int(card['value'])
            except ValueError:
                # face cards will go here!
                value = 10
            total += value
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

@app.route("/blackjack",methods=['GET'])
@login_required
def blackjack_bet():
    return render_template('blackjack.html',mode='bet')

@app.route("/blackjack",methods=['POST'])
@login_required
def blackjack():
    if 'hit' in request.form:
        if not 'blackjack' in session:
            flash('No active game!','alert-danger')
            return redirect(url_for('blackjack_bet'))
        game = session['blackjack']
        newcard = cards_api.drawcards(game['deck'],1)
        game['player_cards'] += newcard
        if cardtotal( game['player_cards'] ) > 21:
            flash('Bust!','alert-danger')
            game['mode'] = 'end'
    elif 'stand' in request.form:
        if not 'blackjack' in session:
            flash('No active game!','alert-danger')
            return redirect(url_for('blackjack_bet'))
        game = session['blackjack']
        game['mode'] = 'end'
        player_total = cardtotal( game['player_cards'] )
        # play dealer's side
        dealer_total = cardtotal( game['dealer_cards'] )
        while dealer_total < 17:
            game['dealer_cards'] += cards_api.drawcards(game['deck'],1)
            print('card drawn for dealer: ',game['dealer_cards'][-1]['code'])
            dealer_total = cardtotal( game['dealer_cards'] )
        if dealer_total > 21:
            flash('Dealer Bust! you win!','alert-success')
            db_manager.updateMoney( session['username'], 2 * game['bet'] )
        elif player_total > dealer_total:
            flash('You Win!','alert-success')
            db_manager.updateMoney( session['username'], 2 * game['bet'] )
        elif player_total == dealer_total:
            flash('Push (tie)','alert-info')
            db_manager.updateMoney( session['username'], game['bet'] )
        else:
            flash('You lose.','alert-danger')
    elif 'bet' in request.form:
        # initialize a new game
        game = {}
        game['bet'] = int(request.form['bet'])
        game['deck'] = cards_api.newdeck()
        game['dealer_cards'] = cards_api.drawcards(game['deck'],2)
        game['player_cards'] = cards_api.drawcards(game['deck'],2)
        db_manager.updateMoney( session['username'], -game['bet'] )
        print(game)
        if cardtotal( game['player_cards'] ) == 21:
            flash('Blackjack! You win 150% of your original bet.','alert-success')
            db_manager.updateMoney( session['username'], 2.5 * game['bet'] )
            game['mode'] = 'end'
        else:
            flash('Game started. If you refresh or navigate away, your bet of ${} will be lost.'.format(game['bet']),'alert-info')
            game['mode'] = 'play'
    else:
        print("how did we get here?")

    if game['mode'] == 'end':
        del session['blackjack']
    else:
        session['blackjack'] = game
    return render_template('blackjack.html',mode=game['mode'],game=game)

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
        #u = urllib.request.urlopen("http://roll.diceapi.com/json/3d6")
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
            num = int(option[3:])
            print("NUM IS: ")
            print(num)
            print("SUM IS: ")
            print(sum)
            if sum == num:
                total_mult += multiplier[num - 4]
    total_mult -= len(options)
    print(total_mult)
    return total_mult

@app.route("/lottery")
@login_required
def lotto():
    '''def lotto(): scratch ticket generator and handles lotto transactions'''
    db_manager.updateMoney(session['username'],-10)
    num=[]
    while len(num)<13:
        num.append(random.randint(0,9))
    for i in range(len(num)):
        if(num[i]==1):
            num[i]="one.png"
        if(num[i]==2):
            num[i]="two.png"
        if(num[i]==3):
            num[i]="three.png"
        if(num[i]==4):
            num[i]="four.png"
        if(num[i]==5):
            num[i]="five.png"
        if(num[i]==6):
            num[i]="six.png"
        if(num[i]==7):
            num[i]="seven.png"
        if(num[i]==8):
            num[i]="eight.png"
        if(num[i]==9):
            num[i]="nine.png"
        if(num[i]==0):
            num[i]="zero.png"
    x=["307px","201px","95px","307px","201px","95px","307px","201px","95px","307px","201px","95px"]
    y=["270px","270px","270px", "340px", "340px","340px","415px","415px","415px","485px","485px","485px"]
    loop=[0,1,2,3,4,5,6,7,8,9,10,11]
    return render_template("lottery.html",xpos=x,ypos=y,numbers=num,index=loop)

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
    username = session['username']
    bank = db_manager.getMoney(username)
    if request.args.get('slotbet'):
        bet = request.args.get('slotbet')
        print(bet)
        if bet == "" or int(bet) < 10 or not db_manager.checkBet(username, int(bet)):
            bet = 10
            flash("Please place valid bet.", 'alert-danger')
            return render_template("slotmachine.html", primarybet = bet, bet = 0, image1 = dict[random.choice(slotImages)], image2 = dict[random.choice(slotImages)], image3 = dict[random.choice(slotImages)], money = 0, colour = "yellow", bank=bank)
        else:
            bet = int(bet)
            db_manager.updateMoney(session['username'], -bet)
            rand1 = random.choice(slotImages)
            rand2 = random.choice(slotImages)
            rand3 = random.choice(slotImages)
            money = 0
            if rand1 == rand2 and rand2 == rand3:
                if rand1 == "lemon":
                    db_manager.updateMoney(session['username'], bet)
                    money = bet
                if rand1 == "cherry":
                    db_manager.updateMoney(session['username'], 2 * bet)
                    money = 2 * bet
                if rand1 == "clover":
                    db_manager.updateMoney(session['username'], 3 * bet)
                    money = 3 * bet
                if rand1 == "heart":
                    db_manager.updateMoney(session['username'], 4 * bet)
                    money = 4 * bet
                if rand1 == "diamond":
                    db_manager.updateMoney(session['username'], 5 * bet)
                    money = 5 * bet
                if rand1 == "dollar":
                    db_manager.updateMoney(session['username'], 6 * bet)
                    money = 6 * bet
                colour = "green"
            else:
                colour = "yellow"
            bank = db_manager.getMoney(username)
            return render_template("slotmachine.html", primarybet = bet, bet = bet, image1 = dict[rand1], image2 = dict[rand2], image3 = dict[rand3], money = money, colour = colour, bank=bank)
    else:
        bet = 10
        money = 0
        return render_template("slotmachine.html", primarybet = bet, bet = 0, image1 = dict[random.choice(slotImages)], image2 = dict[random.choice(slotImages)], image3 = dict[random.choice(slotImages)], money = 0, colour = "yellow", bank=bank)

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
