from bson import ObjectId
from pymongo import MongoClient

MONGODB_KEY = 'mongodb+srv://amirzur:S3KoEzfbmS4RyjMM@cs384.hixpjty.mongodb.net/'

client = MongoClient(MONGODB_KEY)

class User:
    def __init__(self, name, elo) -> None:
        self.name = name
        self.elo = elo

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

def update_elo(user_id, new_elo):
    update_user_feature(user_id, "elo", new_elo)

def create_room(members, messages, guesses, elos):
    room = rooms_collection.insert_one({
        'members': members,
        'messages': messages,
        'first_player': 0,
        'guesses': guesses,
        'prev_elos': elos,
    })
    return str(room.inserted_id)

def get_room(room_id):
    room_data = rooms_collection.find_one({'_id': ObjectId(room_id)})
    return Room(room_data['members'], room_data['messages'], room_data['first_player'], room_data['guesses'], room_data["prev_elos"]) if room_data else None

def update_room_feature(room_id, feature, updated_value):
    rooms_collection.update_one({'_id': ObjectId(room_id)}, {'$set': {feature: updated_value}})

def add_member(room_id, name):
    members = get_room(room_id).members
    members.append(name)
    update_room_feature(room_id, 'members', members)
    
    # ADD ELOS
    room_data = rooms_collection.find_one({'_id': ObjectId(room_id)})
    elos = room_data["prev_elos"]

    user_data = users_collection.find_one({'_id': name})
    elo = user_data["elo"]

    if members[0] == name:
        elos[0] = elo
    elif members[1] == name:
        elos[1] = elo
    
    print(elos)
    update_room_feature(room_id, 'prev_elos', elos)


def add_message(room_id, message):
    messages = get_room(room_id).messages
    messages.append(message)
    update_room_feature(room_id, 'messages', messages)

def add_guess(room_id, player_name, guess):
    room_data = rooms_collection.find_one({'_id': ObjectId(room_id)})
    members = room_data["members"]
    guesses = room_data["guesses"]
    if members[0] == player_name:
        guesses[0] = guess
        print(f"{player_name} guessed {guesses[0]}")
    elif members[1] == player_name:
        guesses[1] = guess 
        print(f"{player_name} guessed {guesses[1]}")
    print(f"+++++++++++++")
    print(f"{members}")
    print(f"{guesses}")
    print(f"+++++++++++++")
    update_room_feature(room_id, 'guesses', guesses)

def get_guess(room_id, player_name):
    room_data = rooms_collection.find_one({'_id': ObjectId(room_id)})
    members = room_data["members"]
    guesses = room_data["guesses"]
    guess = None
    if members[0] == player_name:
        guess = (guesses[0], guesses[1])
    elif members[1] == player_name:
        guess = (guesses[1], guesses[0])
    return guess
