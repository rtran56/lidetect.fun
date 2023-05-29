from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")

app = Flask(__name__)
app.config["SECRET_KEY"] = "scrt213"
socketio = SocketIO(app)

#Room for DialoGPT
dialoggpt_room = "ABCD"
# Stores names of rooms that exists
rooms = {}


#AI CHATBOT INFORMATION
def get_chat_response(msg_text):
    # Let's chat for x lines
    # encode the new user input, add the eos_token and return a tensor in Pytorch
    new_user_input_ids = tokenizer.encode(str(msg_text) + tokenizer.eos_token, return_tensors='pt')

    # append the new user input tokens to the chat history
    bot_input_ids = torch.cat([session["chat_history"], new_user_input_ids], dim=-1) if session.get("step") > 0 else new_user_input_ids

    # generated a response while limiting the total chat history to 1000 tokens, 
    chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token_id)

    # pretty print last ouput tokens from bot
    output = "DialoGPT: {}".format(tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True))
    session["step"] = session["step"] + 1
    session["chat_history"] = chat_history_ids
    return output

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    return code
    
@app.route("/", methods=["POST", "GET"])
def home():
    # clears the session if they go to the home page
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)  #Get the value associated with them
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error="Please provide a name.", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        # if not the default option, key does exist
        if create != False:
            # Allow to create a specific room with a bot with specific code
            if room != dialoggpt_room: 
                room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []} #boilerplate starting data
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)

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
    # can't directly go to room page
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

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
    if room == dialoggpt_room:  
        chatbot_response = get_chat_response(data["data"])
        # AI INFORMATION
        chatbot_content = {
            "name": "Dialogbot",
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
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    # leave the room on refresh (if only person in room) it exits and deletes the room entirely 
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has entered the room"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)

