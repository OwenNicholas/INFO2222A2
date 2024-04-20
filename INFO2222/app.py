'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, session
from flask_socketio import SocketIO
from flask_session import Session
import db
import secrets
import os
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import json
import hmac
import hashlib
from jinja2 import Environment

# making sure that the environment has autoescape
env = Environment(
    autoescape=True,  
)




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
    REMEMBER_COOKIE_DURATION=3600 # 1 hour only
)




Session(app)

# don't remove this!!
import socket_routes

# index page (Picking login/signup)
@app.route("/")
def index():
    session.clear() 
    
    return render_template("index.jinja")


#@app.after_request
#def set_csp(response):
    #response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline';"
    #return response


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404


# home page, where the messaging app is
@app.route("/home")
def home():
    username = session.get('username')
    friend = request.args.get("friend")
    if not username:
        return render_template("login.jinja")
    
    if request.args.get("friend") is None:
        abort(404)

    messages = db.get_messages(username, friend)
    iv = db.get_iv(username, friend)
    sender = db.get_sender(username,friend)
    macs = db.get_mac(username,friend)
    salt = db.get_salt(username)
    
    byte_key = salt.encode()
    def verify_mac(macs, messages, salt):
        calculated_mac = hmac.new(salt, messages.encode(), hashlib.sha256).hexdigest() 
        return hmac.compare_digest(macs, calculated_mac)

    friend_salt = db.get_salt(friend)
    friend_byte_key = friend_salt.encode()
    
    if messages : 

        for message, mac in zip(messages, macs):
            if not (verify_mac(mac, message, byte_key) or verify_mac(mac,message,friend_byte_key)):
                return f"Message authentication failed for message: {message}"
        
        
    return render_template("home.jinja", username=username, receiver = friend, messages = messages, iv = iv, sender = sender, macs = macs)

# handles when press chat (a friend)
@app.route("/chat/user", methods=["POST"])
def chat_user():
    if not request.is_json:
        abort(404)
    username = session.get('username')
    friend = request.json.get("friend")
    messages = db.get_messages(username, friend)
    iv = db.get_iv(username, friend)
    sender = db.get_sender(username,friend)
    macs = db.get_mac(username,friend)
    
    salt = db.get_salt(username)
    
    byte_key = salt.encode()
    def verify_mac(macs, messages, salt):
        calculated_mac = hmac.new(salt, messages.encode(), hashlib.sha256).hexdigest() 
        return hmac.compare_digest(macs, calculated_mac)

    friend_salt = db.get_salt(friend)
    friend_byte_key = friend_salt.encode()
    if messages : 

        for message, mac in zip(messages, macs):
            if not (verify_mac(mac, message, byte_key) or verify_mac(mac,message,friend_byte_key)):
                return f"Message authentication failed for message: {message}"
    
    
    return url_for('home', username=username, friend = friend, messages = messages, iv = iv, sender = sender, macs = macs)


# handles when send chat
@app.route("/chat/user/send", methods=["POST"])
def send_messages():
    if not request.is_json:
        abort(404)
    username = session.get('username')
    friend = request.json.get("friend")
    message = request.json.get("message")
    iv = request.json.get("iv")
    salt = db.get_salt(username)
    
    byte_key = salt.encode()
    
    mac = hmac.new(byte_key, message.encode(), hashlib.sha256).hexdigest() # salt as secret key

    db.add_messages(username,friend,message,iv,mac) 
    
    messages = db.get_messages(username, friend) 
    sender = db.get_sender(username,friend)
    iv = db.get_iv(username, friend)
    macs = db.get_mac(username,friend)
    
    def verify_mac(macs, messages, salt):
        calculated_mac = hmac.new(salt, messages.encode(), hashlib.sha256).hexdigest() 
        return hmac.compare_digest(macs, calculated_mac)
    
    friend_salt = db.get_salt(friend)
    friend_byte_key = friend_salt.encode()
    if messages: 

        for message, mac in zip(messages, macs):
            if not (verify_mac(mac, message, byte_key) or (verify_mac(mac,message,friend_byte_key))):
                return f"Message authentication failed for message: {message}"
        

    
    return url_for('home', username=username, friend = friend, messages = messages, iv = iv, sender = sender, macs = macs)


    



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
    salt = os.urandom(16).hex() # creates a random  constant salt for each user

    if db.get_user(username) is None:
        db.insert_user(username, password,salt)
        return url_for('index')
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
    
    
    session['username'] = username
    salt = db.get_salt(username)

    return url_for('friends_list', username=username, salt = salt, password = password)




#show friends list
@app.route('/friends_list')
def friends_list():
    username = session.get('username')
    if not username:
        return render_template("login.jinja")
    
    return render_template('friends_list.jinja', username=username, 
                           friends= db.get_friends(username), 
                           friend_requests = db.get_friend_requests(username),
                           sent_friend_requests = db.get_friend_requests_sent(username))

 

#when user presses add button
@app.route("/add_friend", methods=["POST"])
def add_friend():
    if not request.is_json:
        abort(404)
        
    username = session.get('username')
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
    username = session.get('username')
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





@app.route("/logout")
def logout():
    session.clear()     
    return url_for('login')




if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ssl_cert_path = os.path.join(script_dir, 'certs', 'davisowen.crt')
    ssl_key_path = os.path.join(script_dir, 'certs', 'davisowen.key')
    
    ssl_context = (ssl_cert_path, ssl_key_path)
    socketio.run(app, ssl_context=ssl_context, debug=True, host='localhost', port=5000)