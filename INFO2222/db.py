'''
db
database file, containing all the logic to interface with the sql database
'''
import base64

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str, salt:str):
    with Session(engine) as session:
        
        user = User(username=username, salt = salt)
        user.set_password(password) #hash in server
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)

# get salt of user from database
def get_salt(username):
    with Session(engine) as session:
        user = session.query(User).filter_by(username=username).first()
        if user:
            return user.salt
        else:
            return None  
    
    
#Friend successfully added to database
def add_friend(username: str, friend_username: str):
    with Session(engine) as session:
        session.add(Friendship(user_id=username, friend_id=friend_username))
        session.add(Friendship(user_id=friend_username, friend_id=username))
        session.commit()
   
#request added to database
def send_friend_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        session.add(FriendRequest(sender_id=sender_username, receiver_id=receiver_username, status='pending'))
        session.commit()
        



#accepted request to database
def accept_friend_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        friend_request = session.query(FriendRequest).filter_by(sender_id=sender_username, receiver_id = receiver_username, status = "pending").first()
        if friend_request:
            friend_request.status = 'accepted'
            add_friend(friend_request.sender_id, friend_request.receiver_id) 
            session.commit()
            
            
            
#rejected request to database
def reject_friend_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        friend_request = session.query(FriendRequest).filter_by(sender_id=sender_username, receiver_id = receiver_username, status = "pending").first()
        if friend_request:
            friend_request.status = 'reject'
            session.commit()

#get friends from database
def get_friends(username: str):
    with Session(engine) as session:
        friendships = session.query(Friendship).filter((Friendship.user_id == username) | (Friendship.friend_id == username)).all()
        friends = set()
        for friendship in friendships:
            if friendship.user_id != username:
                friends.add(friendship.user_id)
            else:
                friends.add(friendship.friend_id)
        return list(friends)

#get friend requests from database
def get_friend_requests(receiver_username: str):
    with Session(engine) as session:
        return session.query(FriendRequest).filter_by(receiver_id=receiver_username, status='pending').all()
    
    
#get sent friend requests from database
def get_friend_requests_sent(sender_username: str):
    with Session(engine) as session:
        return session.query(FriendRequest).filter_by(sender_id=sender_username).all()


# gets a user from the database 
def get_sender(username: str):
    with Session(engine) as session:
        return session.query(FriendRequest).filter(FriendRequest.sender_id == username).all()

    
# gets a user from the database
def get_receiver(username: str):
    with Session(engine) as session:
        return session.query(FriendRequest).filter(FriendRequest.receiver_id == username).all()
    

# check if already requested
def check_existing_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        existing_request = session.query(FriendRequest).filter(
            ((FriendRequest.sender_id == sender_username) & (FriendRequest.receiver_id == receiver_username)) |
            ((FriendRequest.sender_id == receiver_username) & (FriendRequest.receiver_id == sender_username))
        ).first()

        return existing_request


#Message history section

# gets sender from the database for messages
def get_user_id(username: str):
    with Session(engine) as session:
        return session.query(Message).filter(Message.user_id == username).all()
    
    
# gets receiver from the database for messages
def get_friend_id(username: str):
    with Session(engine) as session:
        return session.query(Message).filter(Message.friend_id == username).all()
    
    

# adding messages to the database
def add_messages(username: str, friend_username: str, message : str, iv:str, mac:str):
    with Session(engine) as session:
        session.add(Message(user_id=username, friend_id=friend_username, content = message, iv = iv, mac = mac))
        session.commit()
    
    
# gets messages from the database for messages
def get_messages(username: str, friend_username:str):
    with Session(engine) as session:
       messagesAll = session.query(Message).filter(
            (Message.user_id == username) & (Message.friend_id == friend_username)
            | (Message.user_id == friend_username) & (Message.friend_id == username)
        ).all()
    messages_list = []
    if messagesAll: 
        for message in messagesAll:
            if message == None:
                return
            messages_list.append(message.content)
        return messages_list
    
# gets iv from the database for messages
def get_iv(username: str, friend_username:str):
    with Session(engine) as session:
       ivAll = session.query(Message).filter(
            (Message.user_id == username) & (Message.friend_id == friend_username)
            | (Message.user_id == friend_username) & (Message.friend_id == username)
        ).all()
    iv_list = []
    if ivAll: 
        for iv in ivAll:
            if iv == None:
                return
            iv_list.append(iv.iv)
        return iv_list
    
    
# gets sender from the database for messages
def get_sender(username: str, friend_username:str):
    with Session(engine) as session:
       senderAll = session.query(Message).filter(
            (Message.user_id == username) & (Message.friend_id == friend_username)
            | (Message.user_id == friend_username) & (Message.friend_id == username)
        ).all()
    sender_list = []
    if senderAll: 
        for sender in senderAll:
            if sender == None:
                return
            sender_list.append(sender.user_id)
        return sender_list

# gets mac from the database for messages
def get_mac(username: str, friend_username:str):
    with Session(engine) as session:
       macAll = session.query(Message).filter(
            (Message.user_id == username) & (Message.friend_id == friend_username)
            | (Message.user_id == friend_username) & (Message.friend_id == username)
        ).all()
    mac_list = []
    if macAll: 
        for mac in macAll:
            if mac == None:
                return
            mac_list.append(mac.mac)
        return mac_list