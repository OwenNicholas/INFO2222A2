'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify
from flask_socketio import SocketIO
from flask_session import Session
import db
import secrets
from werkzeug.security import generate_password_hash, check_password_hash



# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)


# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

#session (use filesystem instead of cookies)
app.config["SESSION_PERMANENT"] = False
app.config['SESSION_TYPE'] = 'filesystem'
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

Session(app)

# don't remove this!!
import socket_routes

# index page (Picking login/signup)
@app.route("/")
def index():
    return render_template("index.jinja")

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404


# home page, where the messaging app is
@app.route("/home")
def home():
    if request.args.get("friend") is None:
        abort(404)
    elif request.args.get("username") is None:
        abort(404)
        
    return render_template("home.jinja", username=request.args.get("username"), receiver = request.args.get("friend"))

# handles when press chat (a friend)
@app.route("/chat/user", methods=["POST"])
def chat_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    friend = request.json.get("friend")
    public_key = request.json.get("public_key")

    db.save_public_key(username, public_key)
    return url_for('home', username=username, friend=friend)



@app.route('/getPublicKey', methods=['POST'])
def get_public_key():
    print("masuk get public key")
    username = request.json.get('username')
    if not username:
        print("No username provided")
        return jsonify({'error': 'Username is required'}), 400

    public_key = db.get_public_key(username)
    if public_key:
        return jsonify({'public_key': public_key})
    else:
        return jsonify({'error': 'Public key not found'}), 404



# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")



# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    print("password: ", password)

    if db.get_user(username) is None:
        db.insert_user(username, password)
        return url_for('friends_list', username=username)
    return "Error: User already exists!"



# login page 
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"
    
    
    if not user.check_password(password):
        return "Error: Password does not match!"

    return url_for('friends_list', username=request.json.get("username"))





@app.route('/friends_list')
def friends_list():
    username = request.args.get("username")
    if not username:
        abort(404)
    return render_template('friends_list.jinja', username=username, 
                           friends= db.get_friends(username), 
                           friend_requests = db.get_friend_requests(username),
                           sent_friend_requests = db.get_friend_requests_sent(username))



#when user presses add button
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if not request.is_json:
        abort(404)
        
    username = request.json.get('username')  
    friend_username = request.json.get('friend_username')   
    if db.get_user(friend_username) is None or username == friend_username:
        return "Invalid User"
    existing_request = db.check_existing_request(username, friend_username)
    if existing_request:
        return 'Request already sent or received.'

    elif friend_username:  
        db.send_friend_request(username, friend_username)  
        return "Friend request sent"
    else:
        return "Invalid request"





#when user clicks the accept/reject
@app.route('/friend_requests/user', methods=['POST'])
def respond_to_request():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    if not username:
        return url_for('login')

    action = request.json.get('action')
    sender = request.json.get('sender')

    if action == 'accept':
        db.accept_friend_request(sender,username)
        return "Accepted friend request"
    elif action == 'reject':
        db.reject_friend_request(sender,username)
        return "Rejected friend request"

    return url_for('friends_list')







if __name__ == '__main__':
    #ssl_context = ('/Users/davis/INFO2222/certs/davisowen.crt', '/Users/davis/INFO2222/certs/davisowen.key') #change to own path to key
    #socketio.run(app, ssl_context=ssl_context, debug=True, host='localhost', port=5000)
    socketio.run(app)

