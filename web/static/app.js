var socketio = io();

const chatBody = document.querySelector(".chat-body");
const chatInputDiv = document.querySelector(".chat-input");
const txtInput = document.querySelector("#txtInput");
const waitingMessage = document.querySelector('#waiting-message');
const send = document.querySelector(".send");

const chatBodyDisplay = chatBody.style.display;
const chatInputDivDisplay = chatInputDiv.style.display;
const waitingMessageDisplay = waitingMessage.style.display;

// bit of a hack to get the user's name from render_template (must be a better way to do this?)
const username = document.querySelector('#name').textContent;
var n_players = parseInt(document.querySelector('#n_players').textContent);

send.addEventListener("click", () => renderUserMessage());

socketio.on("message", (data) => {
  // createMessage(data.name, data.message);
  renderMessageEle(data.message, data.name);
});

// const sendMessage = () => {
//   const message = document.getElementById("message");
//   if (message.value == "") return;
//   socketio.emit("message", {data: message.value}); //emits to the create message function which is used for both ai and other chat partner
//   message.value = "";
//   //console.log("send");
// };

txtInput.addEventListener("keyup", (event) => {
  if (event.keyCode === 13) {
    renderUserMessage();
  }
});

function replaceAll(string, search, replace) {
  return string.split(search).join(replace);
}

const renderUserMessage = () => {
  var userInput = txtInput.value;
  // renderMessageEle(userInput, "user");
  txtInput.value = "";

  // // grab history of conversation
  // var history = replaceAll(chatBody.innerHTML, "</div>", "\n");
  // var history = replaceAll(history, "<div class=\"user-message\">", "User: ")
  // var history = replaceAll(history, "<div class=\"chatbot-message\">", "You: ")

  // // remove all question marks in query to prevent flask error
  // history = replaceAll(history, "?", "");
  // userInput = replaceAll(userInput, "?", "");

  // setTimeout(() => {
  //   renderChatbotResponse(userInput, history);
  // }, 200); //todo: make this have some latency over some random normal distribution
  if (userInput == "") return;
  socketio.emit("message", {data: userInput});
};

const renderChatbotResponse = (userInput, history) => {

  fetch(`/ai_response/${userInput}/${history}`)
  .then(response => response.json())
  .then(data => {
    // Output the string and array using console.log
    renderMessageEle(data, "chatbot-message");
    
  });
};

const updateWaitingStatus = (n_players) => {
  if (n_players == 2) {
    chatBody.style.display = chatBodyDisplay;
    chatInputDiv.style.display = chatInputDivDisplay;
    waitingMessage.style.display = 'none';
  } else {
    chatBody.style.display = 'none';
    chatInputDiv.style.display = 'none';
    waitingMessage.style.display = waitingMessageDisplay;
  }
}

const renderMessageEle = (txt, name) => {
  if (txt.length == 0) {
    return;
  }
  let className = "user-message";
  // check whether this message was sent by the user or somebody else
  if (name !== username) {
    className = "chatbot-message";
  }
  if (txt.includes("<SYSTEM>")) {
    className = "system-message";
    n_players += 1;
    updateWaitingStatus(n_players);
  }
  console.log(n_players);
  
  const messageEle = document.createElement("div");
  messageEle.innerHTML = txt;
  // const txtNode = document.createTextNode(txt);
  messageEle.classList.add(className);
  // messageEle.append(txtNode);
  chatBody.append(messageEle);
  chatBody.scrollTop = chatBody.scrollHeight;
};


// renderMessageEle("Hi you are going to be talking to a chatbot", "chatbot-message")

