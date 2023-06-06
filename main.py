from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, emit, SocketIO
import random
from string import ascii_uppercase
import math

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
# Stores names of rooms that exists
rooms = {}

# create dialogue agent
agent = DialoGPTAgent() # GPT3Agent(0, 0, 0)
gpt3_agent = GPT3Agent(0, 3, 2)

<<<<<<< Updated upstream
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    return code
    
=======
def probability(rating1, rating2):
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

def EloRating(Ra, Rb, K, d):
    # To calculate the Winning
    # Probability of Player B
    Pb = probability(Ra, Rb)
    # To calculate the Winning
    # Probability of Player A
    Pa = probability(Rb, Ra)
    # Case -1 When Player A wins
    # Updating the Elo Ratings
    if (d == 1):
        Ra = Ra + K * (1 - Pa)
        Rb = Rb + K * (0 - Pb)
    # Case -2 When Player B wins
    # Updating the Elo Ratings
    elif (d == 0):
        Ra = Ra + K * (0 - Pa)
        Rb = Rb + K * (1 - Pb)
    # Case -3 When Player A and Player B ties
    else:
        Ra = Ra + K * (0.5 - Pa)
        Rb = Rb + K * (0.5 - Pb)
    return Ra, Rb

>>>>>>> Stashed changes
@app.route("/", methods=["POST", "GET"])
def home():
    # clears the session if they go to the home page
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)  #Get the value associated with them
        create = request.form.get("create", False)

<<<<<<< Updated upstream
        if not name:
            return render_template("home.html", error="Please provide a name.", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        # if not the default option, key does exist
        if create != False:
            # Allow to create a specific room with a bot with specific code
            if room != DIALOGGPT_ROOM and room != GPT3AGENT_ROOM: 
                room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []} #boilerplate starting data
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
=======
        if is_bot:
            room = database.create_room(members=[], messages=[], guesses=[None], elos=[None])
            # rooms[room] = {"members": 0, "messages": []}
            gpt3_room_ids.append(room)
        else:
            if len(player_queue) == 0:
                room = database.create_room(members=[], messages=[], guesses=[None, None], elos=[None, None])
                player_queue.append(room)
            else:
                room = player_queue.pop()
>>>>>>> Stashed changes


        # Stores name and room of the user. no logging in or account
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    
    # This only happens if method was not a post request
    return render_template("home.html")

@app.route("/room")
def room():
    session["step"] = 0
    session["chat_history"] = ""

    room = session.get("room")
    name = session.get("name")
    
    # can't directly go to room page
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
<<<<<<< Updated upstream
    return render_template("room.html", code=room, name=session['name'], messages=rooms[room]["messages"])
=======
    if request.method == 'GET':
        return render_template("room.html", name=session['name'], game_over=False, guessed_correctly=False)
    else:
        # What is your guess?
        human = request.form.get('human', False)
        robot = request.form.get('robot', False)

        if human != False: # bit of weird syntax, but human is either False or None
            correct = (room not in gpt3_room_ids)
            # If guess is human, then it will be correct if room is not in gpt3_room_ids
        elif robot != False:
            correct = (room in gpt3_room_ids)
            # If guess is robot, then it will be correct if room is in gpt3_room_ids
        
        # Look into more: Add guess to the database
        database.add_guess(room, session["name"], correct)
        if None not in database.get_room(room).guesses:
            print("ALL GUESSES MADE!")
            # update elo score!
            room_info = database.get_room(room)
            members = room_info.members
            elos = room_info.prev_elos 
            guesses = room_info.guesses
            # Who won?
            if len(guesses) == 1:
                # For bot case, make the bot always lose
                if guesses[0] == True:
                    new_elos = EloRating(elos[0], elos[1], 20, 1)
                else:
                    new_elos = EloRating(elos[0], elos[1], 20, 0)
                database.update_elo(members[0], new_elos[0])
            else:
                # Otherwise compare user's guesses to each other
                if guesses[0] == guesses[1]:
                    # When Tie
                    new_elos = EloRating(elos[0], elos[1], 20, 0.5)
                elif guesses[0] == True:
                    # When player A wins
                    new_elos = EloRating(elos[0], elos[1], 20, 1)
                elif guesses[1] == True:
                    # When player B wins
                    new_elos = EloRating(elos[0], elos[1], 20, 0)
                database.update_elo(members[0], new_elos[0])
                database.update_elo(members[1], new_elos[1])
            # reroute to socketio page
            destination = "endscreen"
            socketio.emit("redirect", destination)
            # Is return valid?
            #my_guess, opponent_guess = database.get_guess(room, name)
            #prev_elo = database.get_room(room).prev_elos[database.get_room(room).members.index(name)]
            #new_elo = database.get_user(name).elo

            #won = my_guess == True and opponent_guess == False
            #tie = my_guess == opponent_guess
            return redirect(url_for("endscreen"))
            #return render_template('endscreen.html', game_over=True, name=session['name'], guessed_correctly=my_guess, opponent_guess=opponent_guess, prev_elo=prev_elo, new_elo=new_elo, won=won, tie=tie) 
        #return render_template('room.html', name=session['name'], game_over=True, guessed_correctly=correct)
        return render_template('endscreen.html', name=session['name'], game_over=False, guessed_correctly=correct)

@app.route("/endscreen", methods=['POST', 'GET'])
def endscreen():
    if request.method == "GET":
        room = session.get("room")
        name = session.get("name")
        print("IN THE END SCREEN NOW")
        my_guess, opponent_guess = database.get_guess(room, name)
        prev_elo = database.get_room(room).prev_elos[database.get_room(room).members.index(name)]
        new_elo = database.get_user(name).elo
        #database.update_elo(previous_elo - 100)
        #new_elo = previous_elo - 100
        won = my_guess == True and opponent_guess == False
        tie = my_guess == opponent_guess
        return render_template('endscreen.html', game_over=True, name=session['name'], guessed_correctly=my_guess, opponent_guess=opponent_guess, prev_elo=prev_elo, new_elo=new_elo, won=won, tie=tie)
    elif request.method == "POST":
        print("CLICKED!")
        return redirect(url_for("home"))
    return

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
>>>>>>> Stashed changes

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room) # Prob can send ai content from here?

    rooms[room]["messages"].append(content)

    ''' Dialog GPT ROOM'''
    if room == DIALOGGPT_ROOM:  
        session['chat_history'] += f"User: {str(data['data']).strip()}\n"
        chatbot_response = agent.answer(session['chat_history'])
        session["step"] = session["step"] + 1
        session["chat_history"] += f"You: {chatbot_response.strip()}\n"
        # chatbot_response = get_chat_response(data["data"])
        # AI INFORMATION
        chatbot_content = {
            "name": "Dialogbot",
            "message": chatbot_response
        }
        send(chatbot_content, to=room)
        rooms[room]["messages"].append(chatbot_content)
    
    if room == GPT3AGENT_ROOM:
        session['chat_history'] += f"User: {str(data['data']).strip()}\n"
        print(session["chat_history"])
        chatbot_response = gpt3_agent.answer(session['chat_history'])
        session["step"] = session["step"] + 1
        session["chat_history"] += f"You: {chatbot_response.strip()}\n"

        chatbot_content = {
            "name": gpt3_agent.name,
            "message": chatbot_response
        }
        send(chatbot_content, to=room)
        rooms[room]["messages"].append(chatbot_content)




    #1:11:00 print(f"{session.get('name')} said: {data["data"]}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
<<<<<<< Updated upstream
    send({"name": name, "message": "<SYSTEM>" + name + " has entered the room"}, to=room)
    if room == GPT3AGENT_ROOM and session["step"] == 0: # i would like to phase out dialogGPT
        send({"name": gpt3_agent.name, "message": "<SYSTEM>" + gpt3_agent.name + " has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")
=======

    # add human player to the room
    if name not in database.get_room(room).members:
        database.add_member(room, name)

    intro_message = {
        "name": '<SYSTEM>', 
        "message": name + " has entered the room"
    }
    database.add_message(room, intro_message)

    send(get_game_info(room), to=room)

    if room in gpt3_room_ids and len(database.get_room(room).messages) < 2:
        # add gpt3 agent to the room, GPT3 agent is added to the room!
        database.add_member(room, gpt3_agent.name)

        bot_intro_message = {
            "name": '<SYSTEM>', 
            "message": gpt3_agent.name + " has entered the room"
        }
        database.add_message(room, bot_intro_message)

        send(get_game_info(room), to=room)
>>>>>>> Stashed changes
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    # leave the room on refresh (if only person in room) it exits and deletes the room entirely 
<<<<<<< Updated upstream
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "<SYSTEM>" + name + " has left the room"}, to=room)
    print(f"{name} has left the room {room}")
=======
    ''' LOOK INTO THIS MORE! possibly have to make a separate room for correct/incorrect guesses so you don't enter back into /ro
    if database.get_room(room):
        members = database.get_room(room).members
        members.remove(name)
        database.update_room_feature(room, 'members', members)
    '''

    outro_message = {
        "name": '<SYSTEM>', 
        "message": name + " has left the room"
    }
    database.add_message(room, outro_message)

    # Look into more!
    '''
    send(get_game_info(room), to=room)
    '''
>>>>>>> Stashed changes

if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080)

