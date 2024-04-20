'''
db
database file, containing all the logic to interface with the sql database
'''

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
def insert_user(username: str, password: str):
    with Session(engine) as session:
        
        user = User(username=username)
        user.set_password(password)  #hashed password

        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
    
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
            session.delete(friend_request)
            session.commit()
            
            
            
#rejected request to database
def reject_friend_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        friend_request = session.query(FriendRequest).filter_by(sender_id=sender_username, receiver_id = receiver_username, status = "pending").first()
        if friend_request:
            friend_request.status = 'reject'
            session.delete(friend_request)
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
    



def check_existing_request(sender_username: str, receiver_username: str):
    with Session(engine) as session:
        existing_request = session.query(FriendRequest).filter(
            ((FriendRequest.sender_id == sender_username) & (FriendRequest.receiver_id == receiver_username)) |
            ((FriendRequest.sender_id == receiver_username) & (FriendRequest.receiver_id == sender_username))
        ).first()

        return existing_request


def save_public_key(username: str, public_key: str):
    with Session(engine) as session:
        user = session.get(User, username)
        if user:
            user.public_key = public_key
            session.commit()
        else:
            raise ValueError("User does not exist")


def get_public_key(username: str):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).one_or_none()
        return user.public_key if user else None

