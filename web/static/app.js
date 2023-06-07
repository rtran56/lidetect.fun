var socketio = io();

const chatBody = document.querySelector(".chat-body");
const chatInputDiv = document.querySelector(".chat-input");
const txtInput = document.querySelector("#txtInput");
const send = document.querySelector(".send");
const finalGuessForm = document.querySelector('.final-guess-form');

const chatBodyDisplay = chatBody.style.display;
const chatInputDivDisplay = chatInputDiv.style.display;

// bit of a hack to get the user's name from render_template (must be a better way to do this?)
const username = document.querySelector('#name').textContent;

send.addEventListener("click", () => renderUserMessage());

const renderWaitingStatus = (game_started) => {
  if (game_started) {
    txtInput.value = '';
    txtInput.removeAttribute('disabled');
    send.removeAttribute('disabled');
  } else {
    txtInput.value = 'Waiting for second player to arrive.';
    txtInput.setAttribute('disabled', 'disabled');
    send.setAttribute('disabled', 'disabled');
  }
}

renderWaitingStatus(false);

const renderTurn = (next_turn) => {
  if (next_turn === username) {
    txtInput.value = '';
    txtInput.removeAttribute('disabled');
    send.removeAttribute('disabled');
  } else {
    txtInput.value = 'Wait for the other player to respond.';
    txtInput.setAttribute('disabled', 'disabled');
    send.setAttribute('disabled', 'disabled');
  }
}

const renderEndgame = (game_over) => {
  if (game_over) {
    chatInputDiv.style.display = 'none';
    finalGuessForm.style.display = 'block';
  }
}

const renderMessage = (message) => {
  let name = message.name;
  let txt = message.message;
  if (txt.length == 0) {
    return;
  }

  let className;
  if (name === '<SYSTEM>') {
    className = 'system-message';
  } else if (name === username) {
    className = 'user-message';
  } else {
    className = 'chatbot-message';
  }
  
  const messageEle = document.createElement("div");
  messageEle.innerHTML = txt;
  // const txtNode = document.createTextNode(txt);
  messageEle.classList.add(className);

  return messageEle
} 

socketio.on("message", (data) => {
  var messageElems = data['messages'].map(message => renderMessage(message));
  chatBody.replaceChildren(...messageElems);
  chatBody.scrollTop = chatBody.scrollHeight;
  renderWaitingStatus(data['game_started']);
  if (data.members.length == 2) {
    renderTurn(data['next_turn']);
  }

  renderEndgame(data['game_over']);
});

txtInput.addEventListener("keyup", (event) => {
  if (event.keyCode === 13) {
    renderUserMessage();
  }
});

function replaceAll(string, search, replace) {
  return string.split(search).join(replace);
}

const renderUserMessage = () => {
  if (txtInput.getAttribute('disabled')) {
    return;
  }

  var userInput = txtInput.value;
  txtInput.value = "";

  // setTimeout(() => {
  //   renderChatbotResponse(userInput, history);
  // }, 200); //todo: make this have some latency over some random normal distribution
  if (userInput == "") return;
  socketio.emit("message", {data: userInput});
};


