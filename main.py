from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

import database

import numpy as np

from chatbots.dialogpt import DialoGPTAgent
from chatbots.gpt3 import GPT3Agent

app = Flask(
    __name__,
    static_url_path='', 
    static_folder='web/static',
    template_folder='web/templates'
)
app.config["SECRET_KEY"] = "scrt213"
socketio = SocketIO(app)

#Room for DialoGPT
DIALOGGPT_ROOM = "ABCD"
GPT3AGENT_ROOM = "AAAA"

MAX_TURNS = 1

DEFAULT_ELO = 1200

player_queue = []
gpt3_room_ids = []

# create dialogue agent
# agent = DialoGPTAgent() # GPT3Agent(0, 0, 0)
gpt3_agent = GPT3Agent(0, 3, 2)


@app.route("/", methods=["POST", "GET"])
def home():
    # clears the session if they go to the home page
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return render_template("home.html", error="Please provide a name.", name=name)
        
        # add username to database if not already there
        if not database.get_user(name):
            name = database.create_user(name, DEFAULT_ELO)
        
        # is_bot = np.random.choice([False, True])
        is_bot = False

        if is_bot:
            room = database.create_room(members=[], messages=[])
            # rooms[room] = {"members": 0, "messages": []}
            gpt3_room_ids.append(room)
        else:
            if len(player_queue) == 0:
                room = database.create_room(members=[], messages=[])
                player_queue.append(room)
            else:
                room = player_queue.pop()

        # Stores name and room of the user. no logging in or account
        session["room"] = room
        session["name"] = name

        return redirect(url_for("room"))
    
    # This only happens if method was not a post request
    return render_template("home.html")

@app.route("/room", methods=['POST', 'GET'])
def room():
    room = session.get("room")
    # can't directly go to room page
    if room is None or session.get("name") is None or database.get_room(room) is None:
        return redirect(url_for("home"))
    
    if request.method == 'GET':
        return render_template("room.html", name=session['name'], game_over=False, guessed_correctly=False)
    else:
        human = request.form.get('human', False)
        robot = request.form.get('robot', False)

        if human != False: # bit of weird syntax, but human is either False or None
            correct = (room not in gpt3_room_ids)
        elif robot != False:
            correct = (room in gpt3_room_ids)
        
        return render_template('room.html', name=session['name'], game_over=True, guessed_correctly=correct)


def get_game_info(room_id):
    room_info = database.get_room(room_id)
    # identify next player
    if len(room_info.members) == 2:
        next_turn = room_info.members[(len(room_info.messages) + room_info.first_player) % 2]
    else:
        next_turn = '<SYSTEM>'
    return {
        'messages': room_info.messages,
        'members': room_info.members,
        'turns': len(room_info.messages),
        'next_turn': next_turn,
        'game_over': len(room_info.messages) >= (MAX_TURNS + 1) * 2
    }

@socketio.on("message")
def message(data):
    room = session.get("room")
    name = session.get('name')
    if database.get_room(room) is None:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    database.add_message(room, content)

    send(get_game_info(room), to=room) 
    
    if room in gpt3_room_ids:
        members = database.get_room(room).members
        messages = database.get_room(room).messages

        # get chat history, skipping the first two SYSTEM messages
        chat_history = [f'{members[i % 2]}: {messages[i]}' for i in range(2, len(messages))]

        chatbot_response = gpt3_agent.answer('\n'.join(chat_history))

        chatbot_content = {
            "name": gpt3_agent.name,
            "message": chatbot_response
        }

        database.add_message(room, chatbot_content)

        send(get_game_info(room), to=room)

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

    # add human player to the room
    database.add_member(room, name)

    intro_message = {
        "name": '<SYSTEM>', 
        "message": name + " has entered the room"
    }
    database.add_message(room, intro_message)

    send(get_game_info(room), to=room)

    if room in gpt3_room_ids and len(database.get_room(room).messages) < 2:
        # add gpt3 agent to the room
        database.add_member(room, gpt3_agent.name)

        bot_intro_message = {
            "name": '<SYSTEM>', 
            "message": gpt3_agent.name + " has entered the room"
        }
        database.add_message(room, bot_intro_message)

        send(get_game_info(room), to=room)
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    # leave the room on refresh (if only person in room) it exits and deletes the room entirely 
    if database.get_room(room):
        members = database.get_room(room).members
        members.remove(name)
        database.update_room_feature(room, 'members', members)

    outro_message = {
        "name": '<SYSTEM>', 
        "message": name + " has left the room"
    }
    database.add_message(room, outro_message)

    send(get_game_info(room), to=room)

if __name__ == "__main__":
    # add gpt3 agent to our user database
    database.create_user(gpt3_agent.name, elo=DEFAULT_ELO)

    socketio.run(app, debug=True, port=8080)

