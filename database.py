from bson import ObjectId
from pymongo import MongoClient
import os 

MONGODB_KEY = os.getenv('MONGODB_KEY')

client = MongoClient(MONGODB_KEY)

class User:
    def __init__(self, name, elo, is_bot) -> None:
        self.name = name
        self.elo = elo
        self.is_bot = is_bot

class Room:
    def __init__(self, members, messages, first_player, guesses, prev_elos) -> None:
        self.members = members
        self.messages = messages
        self.first_player = first_player
        self.guesses = guesses
        self.prev_elos = prev_elos

game_db = client.get_database("cs384")
users_collection = game_db.get_collection("users")
rooms_collection = game_db.get_collection("rooms")

# clear databases
users_collection.drop()
rooms_collection.drop()

def create_user(name, elo, is_bot):
    user = users_collection.insert_one({
        '_id': name,
        'elo': elo,
        'is_bot': is_bot 
    })
    return user.inserted_id

def get_user(name):
    user_data = users_collection.find_one({'_id': name})
    return User(user_data['_id'], user_data['elo'], user_data['is_bot']) if user_data else None

def update_user_feature(user_id, feature, updated_value):
    users_collection.update_one({'_id': user_id}, {'$set': {feature: updated_value}})

def create_room(members, messages, first_player):
    room = rooms_collection.insert_one({
        'members': members,
        'messages': messages,
        'first_player': first_player,
        'guesses': [None, None],
        'prev_elos': []
    })
    return str(room.inserted_id)

def get_room(room_id):
    room_data = rooms_collection.find_one({'_id': ObjectId(room_id)})
    return Room(
        room_data['members'], 
        room_data['messages'], 
        room_data['first_player'], 
        room_data['guesses'],
        room_data['prev_elos']
    ) if room_data else None

def update_room_feature(room_id, feature, updated_value):
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {feature: updated_value}})

def add_member(room_id, name):
    room_info = get_room(room_id)
    members = room_info.members
    members.append(name)
    update_room_feature(room_id, 'members', members)
    
    # also add player's previous elo
    prev_elos = room_info.prev_elos
    prev_elos.append(get_user(name).elo)
    update_room_feature(room_id, 'prev_elos', prev_elos)

def add_message(room_id, message):
    messages = get_room(room_id).messages
    messages.append(message)
    update_room_feature(room_id, 'messages', messages)

def add_guess(room_id, name, guess):
    room_data = get_room(room_id)
    guesses = room_data.guesses
    assert(name in room_data.members)
    if room_data.members[0] == name:
        guesses[0] = guess
    else:
        guesses[1] = guess
    update_room_feature(room_id, 'guesses', guesses)