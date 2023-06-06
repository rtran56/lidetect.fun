from bson import ObjectId
from pymongo import MongoClient

MONGODB_KEY = 'mongodb+srv://amirzur:S3KoEzfbmS4RyjMM@cs384.hixpjty.mongodb.net/'

client = MongoClient(MONGODB_KEY)

class User:
    def __init__(self, name, elo) -> None:
        self.name = name
        self.elo = elo

class Room:
    def __init__(self, members, messages, first_player) -> None:
        self.members = members
        self.messages = messages
        self.first_player = first_player


game_db = client.get_database("cs384")
users_collection = game_db.get_collection("users")
rooms_collection = game_db.get_collection("rooms")

# clear databases
users_collection.drop()
rooms_collection.drop()

def create_user(name, elo):
    user = users_collection.insert_one({
        '_id': name,
        'elo': elo
    })
    return user.inserted_id

def get_user(name):
    user_data = users_collection.find_one({'_id': name})
    return User(user_data['_id'], user_data['elo']) if user_data else None

def update_user_feature(user_id, feature, updated_value):
    users_collection.update_one({'_id': user_id}, {'$set': {feature: updated_value}})

def create_room(members, messages):
    room = rooms_collection.insert_one({
        'members': members,
        'messages': messages,
        'first_player': 0
    })
    return str(room.inserted_id)

def get_room(room_id):
    room_data = rooms_collection.find_one({'_id': ObjectId(room_id)})
    return Room(room_data['members'], room_data['messages'], room_data['first_player']) if room_data else None

def update_room_feature(room_id, feature, updated_value):
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {feature: updated_value}})

def add_member(room_id, name):
    members = get_room(room_id).members
    members.append(name)
    update_room_feature(room_id, 'members', members)

def add_message(room_id, message):
    messages = get_room(room_id).messages
    messages.append(message)
    update_room_feature(room_id, 'messages', messages)