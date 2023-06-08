from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
import time 

import database

import numpy as np

# from chatbots.dialogpt import DialoGPTAgent
from chatbots.gpt3 import GPT3Agent
from elo import EloRating

app = Flask(
    __name__,
    static_url_path='', 
    static_folder='web/static',
    template_folder='web/templates'
)
app.config["SECRET_KEY"] = "scrt213"
socketio = SocketIO(app)

#Room for DialoGPT
# DIALOGGPT_ROOM = "ABCD"
# GPT3AGENT_ROOM = "AAAA"

MAX_TURNS = 3

DEFAULT_ELO = 1200

player_queue = []
gpt3_room_ids = []

# create dialogue agent
# agent = DialoGPTAgent() # GPT3Agent(0, 0, 0)
# gpt3_agent = GPT3Agent(0, 3, 2)
bots = {
    'bot000': GPT3Agent(0, 0, 0),
    'bot111': GPT3Agent(1, 1, 1),
    #'bot333': GPT3Agent(3, 3, 3),
    'bot222': GPT3Agent(2, 2, 2),
    'bot663': GPT3Agent(6, 6, 3),
    #'bot444': GPT3Agent(4, 4, 4),
    #'bot550': GPT3Agent(5, 5, 0),
    #'bot884': GPT3Agent(8, 8, 4),
    'bot1665': GPT3Agent(16, 6, 6)

}

# add gpt3 agent to our user database
for bot in bots.keys():
    if database.get_user(bot) is None:
        database.create_user(bot, elo=DEFAULT_ELO, is_bot=True)


@app.route("/", methods=["POST", "GET"])
def home():
    # clears the session if they go to the home page
    session.clear()
    if request.method == "POST":
        is_leaderboard = request.form.get("leaderboard")
        if is_leaderboard is not None:
            return redirect(url_for("leaderboard"))

        name = request.form.get("name")
        if not name:
            return render_template("home.html", error="Please provide a name.", name=name)
        
        # add username to database if not already there
        if database.get_user(name) is None:
            name = database.create_user(name, DEFAULT_ELO, is_bot=False)
        
        is_bot = np.random.choice([False, True]) 

        if is_bot:
            first_player = random.choice([0, 1])
            room = database.create_room(members=[], messages=[], first_player=first_player)

            bot = random.choice(list(bots.keys()))
            # rooms[room] = {"members": 0, "messages": []}
            # gpt3_room_ids.append(room)

            database.add_member(room, bot)

            # add bot intro message to game room
            bot_intro_message = {
                "name": '<SYSTEM>', 
                "message": "A user has entered the room"
            }
            database.add_message(room, bot_intro_message)
        else:
            if len(player_queue) == 0:
                first_player = random.choice([0, 1])
                room = database.create_room(members=[], messages=[], first_player=first_player)
                player_queue.append(room)
            else:
                room = player_queue.pop()

        # Stores name and room of the user. no logging in or account
        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))
    
    # This only happens if method was not a post request
    return render_template("home.html")

def add_guess(room, player, guess):
    room_info = database.get_room(room)

    # if both players already guessed, then just return
    if not any([g is None for g in room_info.guesses]):
        return True

    # if no player has made a guess yet then add your guess and return
    if all([g is None for g in room_info.guesses]): 
        database.add_guess(room, player, guess)
        return False

    # after this line, both players have made a guess
    database.add_guess(room, player, guess)

    # update elo score!
    room_info = database.get_room(room)
    members = room_info.members
    elos = room_info.prev_elos 
    guesses = room_info.guesses

    # compare user's guesses to each other
    if guesses[0] == guesses[1]:
        # When Tie
        new_elos = EloRating(elos[0], elos[1], 20, 0.5)
    elif guesses[0]:
        # When player A wins
        new_elos = EloRating(elos[0], elos[1], 20, 1)
    elif guesses[1]:
        # When player B wins
        new_elos = EloRating(elos[0], elos[1], 20, 0)
    
    database.update_user_feature(members[0], 'elo', new_elos[0])
    database.update_user_feature(members[1], 'elo', new_elos[1])

    # reroute to socketio page
    destination = "endscreen"
    socketio.emit("redirect", destination, to=room)
    return True

@app.route("/leaderboard", methods=['POST', 'GET'])
def leaderboard():
    if request.method == "POST":
        return redirect(url_for("home"))
        
    users = database.get_users_sorted_elo()
    return render_template('leaderboard.html', users=users)

@app.route("/room", methods=['POST', 'GET'])
def room():
    room = session.get("room")
    name = session.get('name')
    # can't directly go to room page
    if room is None or name is None or database.get_room(room) is None:
        return redirect(url_for("home"))
    
    if request.method == 'GET':
        return render_template("room.html", name=name, game_over=False, guessed_correctly=False)
    elif request.method == 'POST':
        room = session.get("room")
        name = session.get('name')

        human = request.form.get('human', False)
        robot = request.form.get('robot', False)

        members = database.get_room(room).members
        other_player = members[0] if members[0] != name else members[1]

        if human != False: # bit of weird syntax, but human is either False or None
            correct = not database.get_user(other_player).is_bot
        elif robot != False:
            correct = database.get_user(other_player).is_bot

        if add_guess(room, name, correct):
            return redirect(url_for('endscreen'))
        return render_template('endscreen.html', name=name, game_over=False)
    
@app.route("/endscreen", methods=['POST', 'GET'])
def endscreen():
    if request.method == "GET":
        room = session.get("room")
        name = session.get("name")

        room_info = database.get_room(room)
        my_guess = room_info.guesses[0] if name == room_info.members[0] else room_info.guesses[1]
        opponent_guess = room_info.guesses[0] if name != room_info.members[0] else room_info.guesses[1]

        prev_elo = room_info.prev_elos[room_info.members.index(name)]
        new_elo = database.get_user(name).elo

        won = (my_guess and not opponent_guess)
        tie = (my_guess == opponent_guess)
        return render_template('endscreen.html', game_over=True, name=name, guessed_correctly=my_guess, opponent_guess=opponent_guess, prev_elo=prev_elo, new_elo=new_elo, won=won, tie=tie)

    elif request.method == "POST":
        return redirect(url_for("home"))


def get_game_info(room_id):
    room_info = database.get_room(room_id)
    # identify next player
    n_mesages_sent = len([m for m in room_info.messages if m['name'] != '<SYSTEM>'])
    next_turn = None
    if len(room_info.members) == 2:
        next_turn = room_info.members[(n_mesages_sent + room_info.first_player) % 2]

    return {
        'messages': room_info.messages,
        'members': room_info.members,
        'turns': len(room_info.messages),
        'next_turn': next_turn,
        'game_started': len(room_info.messages) >= 2,
        'game_over': len(room_info.messages) >= (MAX_TURNS + 1) * 2
    }


@socketio.on("message")
def message(data):
    room = session.get("room")
    name = session.get('name')
    if database.get_room(room) is None:
        return
    
    content = {
        "name": name,
        "message": data["data"]
    }

    database.add_message(room, content)

    game_info = get_game_info(room)
    send(game_info, to=room) 

    next_player = database.get_user(game_info['next_turn'])

    # Add delay

    if next_player.is_bot and not game_info['game_over']:
        bot = bots[next_player.name]

        chatbot_response = bot.answer(game_info['members'], game_info['messages'])
        chatbot_content = {
            "name": next_player.name,
            "message": chatbot_response
        }

        database.add_message(room, chatbot_content)
        game_info = get_game_info(room)
        send(game_info, to=room)

    # if the game is over and a bot is playing, we can make a guess!
    if game_info['game_over'] and any([database.get_user(name).is_bot for name in game_info['members']]):
        members = game_info['members']
        bot_name = members[0] if database.get_user(members[0]).is_bot else members[1]

        bot = bots[bot_name]

        # guess whether other player is human or not
        guess = bot.evaluate(game_info['members'], game_info['messages'])

        add_guess(room, bot_name, guess)


    # if room in gpt3_room_ids:
    #     members = database.get_room(room).members
    #     messages = database.get_room(room).messages

    #     # get chat history, skipping the first two SYSTEM messages
    #     chat_history = [f'{members[i % 2]}: {messages[i]}' for i in range(2, len(messages))]

    #     chatbot_response = gpt3_agent.answer('\n'.join(chat_history))

    #     chatbot_content = {
    #         "name": gpt3_agent.name,
    #         "message": chatbot_response
    #     }

    #     database.add_message(room, chatbot_content)

    #     send(get_game_info(room), to=room)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")

    if not room or not name:
        return
    if database.get_room(room) is None:
        leave_room(room)
        return
    
    join_room(room)

    # if reconnecting at the end of the game, then we should stop here!
    if get_game_info(room)['game_over']:
        return

    # add human player to the room
    database.add_member(room, name)

    intro_message = {
        "name": '<SYSTEM>', 
        "message":"A user has entered the room"
    }
    database.add_message(room, intro_message)

    game_info = get_game_info(room)
    send(game_info, to=room)

    # if both players joined the game, it could be that the bot is first to go!
    if len(game_info['members']) == 2:
        next_player = database.get_user(game_info['next_turn'])
        if next_player.is_bot:
            bot = bots[next_player.name]

            chatbot_response = bot.answer(game_info['members'], game_info['messages'], first_message=True)
            chatbot_content = {
                "name": next_player.name,
                "message": chatbot_response
            }

            database.add_message(room, chatbot_content)
            send(get_game_info(room), to=room)
    
@socketio.on("disconnect")
def disconnect():
    ###########################################################################################
    # for now, don't have player leave the room!                                              #
    # we use this information in making guesses (plus, might want to keep this for posterity) #
    ###########################################################################################

    room = session.get("room")
    leave_room(room)

    # if database.get_room(room):
    #     members = database.get_room(room).members
    #     members.remove(name)
    #     database.update_room_feature(room, 'members', members)

    # outro_message = {
    #     "name": '<SYSTEM>', 
    #     "message": name + " has left the room"
    # }
    # database.add_message(room, outro_message)

    # send(get_game_info(room), to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080)

