'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, Session, relationship

from collections import defaultdict
from typing import Dict, Set
from werkzeug.security import generate_password_hash, check_password_hash



# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    public_key: Mapped[str] = mapped_column(String)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)



class Friendship(Base):
    __tablename__ = 'friendship'
    user_id = Column(String, ForeignKey('user.username'), primary_key=True)
    friend_id = Column(String, ForeignKey('user.username'), primary_key=True)

class FriendRequest(Base):
    __tablename__ = 'friend_request'
    sender_id = Column(String, ForeignKey('user.username'), primary_key=True)
    receiver_id = Column(String, ForeignKey('user.username'), primary_key=True)
    status = Column(String, nullable=False)
    def __repr__(self):
        return f"<Frie  ndRequest(sender_id={self.sender_id}, receiver_id={self.receiver_id}, status={self.status})>"

    def __str__(self):
        return f"From {self.sender_id}   , Status: {self.status}"
    
    def sent_to(self):
        return f"Request sent to {self.receiver_id}"




# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}
        self.room_users: Dict[int, Set[str]] = defaultdict(set)

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        #self.room_users[room_id].update({sender, receiver})  # Adding both users to the set of the room
        return room_id
    
    def join_room(self,  username: str, room_id: int) -> int:
        self.dict[username] = room_id
        self.room_users[room_id].add(username)

    def leave_room(self, username):
        if username in self.dict:
            room_id = self.dict[username]
            self.room_users[room_id].remove(username)
            if not self.room_users[room_id]:
                del self.room_users[room_id]
            del self.dict[username]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
    def get_room_users(self, room_id: int) -> Set[str]:
        return self.room_users.get(room_id, set())

    def can_chat(self, room_id: int) -> bool:
        """ Check if the room has more than one user to enable chat. """
        print(len(self.room_users[room_id]))
        return len(self.room_users[room_id]) > 1
    
